#!/usr/bin/env python3
"""Run one LLM-backed platform adapter on StableEval prompt packets."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from stableeval.policy import generate_prediction, prompt_text, token_count_approx


OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
DEFAULT_MODEL = "qwen/qwen-2.5-72b-instruct"
VALID_STATUSES = {"stable", "watch", "stress"}
VALID_DIRECTIONS = {"below_peg", "above_peg", "two_sided_or_no_meaningful"}
PRIVATE_PACKET_PREFIX = "_stableeval_"

PLATFORM_IMPORTS = {
    "nanobot": ["nanobot"],
    "hermes_ai": ["hermes.core"],
    "evoagentx": ["evoagentx"],
    "openclaw": ["openclaw"],
    "nanoclaw": ["nanoclaw"],
}

PLATFORM_INSTRUCTIONS = {
    "nanobot": (
        "Adapter stance: Nanobot autonomous assistant. Do not call external tools; "
        "perform internal risk triage and return only the final JSON object."
    ),
    "hermes_ai": (
        "Adapter stance: Hermes/LlamaIndex agent. Synthesize evidence into a compact "
        "risk judgement before producing only the final JSON object."
    ),
    "evoagentx": (
        "Adapter stance: EvoAgentX workflow agent. Score peg stress, liquidity, supply, "
        "and market-context signals, then return only the final JSON object."
    ),
    "langgraph": (
        "Adapter stance: LangGraph state graph. Use the graph-produced signal summary "
        "as intermediate state, then return only the final JSON object."
    ),
    "openclaw": (
        "Adapter stance: OpenClaw/CMDOP orchestration wrapper. Use a deployment-aware, "
        "cost-aware risk forecast and return only the final JSON object."
    ),
    "nanoclaw": (
        "Adapter stance: NanoClaw/CMDOP container-agent wrapper. Use a compact, "
        "cost-aware risk forecast and return only the final JSON object."
    ),
}


RISK_VERIFIER_PROMPT = """You are a second-pass StableEval risk auditor.

You receive:
1. the same frozen 30-day lookback packet shown to the first agent, and
2. the first agent's structured prediction.

You must not use future labels, future prices, web search, or outside historical event knowledge. Use only the lookback-window evidence in the packet and the first prediction.

Audit whether the first prediction ignored or underweighted:
- recent max absolute deviation;
- duration above 25/50/100 bps;
- deviation volatility;
- volume spikes or drops;
- market-cap or supply changes;
- BTC/ETH stress context;
- mechanism-specific risk;
- asymmetric trustworthiness cost, where missing stress is worse than issuing a justified watch warning.

You may revise the final label, p_depeg_next_7d, predicted max deviation, direction, confidence, and rationale if the lookback evidence supports revision. Do not mechanically upgrade every case. Stress requires large, persistent, or operationally meaningful instability evidence. Watch is appropriate when risk signals are meaningful but not severe enough for stress. Stable is appropriate only when peg behavior is consistently normal and no meaningful stress signal appears.

Return exactly one strict JSON object with the original StableEval schema:
{
  "case_id": "case identifier from the packet",
  "platform": "agent platform name",
  "model_backend": "model backend route",
  "execution_mode": "execution mode",
  "price_stability_next_7d": "stable | watch | stress",
  "p_depeg_next_7d": 0.0,
  "predicted_max_abs_deviation_bps": 0.0,
  "predicted_direction": "below_peg | above_peg | two_sided_or_no_meaningful",
  "confidence": 0.0,
  "rationale": "short evidence-based explanation",
  "evidence_used": ["specific lookback signals used"],
  "verifier_action": "kept | upgraded_to_watch | upgraded_to_stress | downgraded | revised_probability_only",
  "verifier_notes": "short audit note"
}

Output strict JSON only. No markdown.
"""


@dataclass
class LLMCall:
    content: str
    model: str
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    raw_id: str = ""


@dataclass(frozen=True)
class ModelPricing:
    prompt_per_token_usd: float = 0.0
    completion_per_token_usd: float = 0.0

    def estimate(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            float(prompt_tokens) * self.prompt_per_token_usd
            + float(completion_tokens) * self.completion_per_token_usd
        )


@dataclass
class AdapterResult:
    raw_text: str
    prediction: dict[str, Any]
    execution_mode: str
    calls: list[LLMCall] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def prompt_tokens(self) -> int:
        return sum(call.prompt_tokens for call in self.calls)

    @property
    def completion_tokens(self) -> int:
        return sum(call.completion_tokens for call in self.calls)

    @property
    def total_tokens(self) -> int:
        return sum(call.total_tokens for call in self.calls)

    @property
    def cost_usd(self) -> float:
        return sum(call.cost_usd for call in self.calls)


class OpenRouterClient:
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.max_retries = int(os.getenv("STABLEEVAL_OPENROUTER_RETRIES", "4"))

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int | None = None,
        json_mode: bool = False,
        model: str | None = None,
    ) -> LLMCall:
        last_error: Exception | None = None
        for attempt in range(max(1, self.max_retries)):
            payload: dict[str, Any] = {
                "model": model or self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            body = json.dumps(payload).encode("utf-8")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://stableeval.local",
                "X-Title": "StableEval Arena",
            }
            request = urllib.request.Request(OPENROUTER_CHAT_URL, data=body, headers=headers, method="POST")
            try:
                with self._opener.open(request, timeout=180) as response:
                    data = json.loads(response.read().decode("utf-8"))

                choice = data.get("choices", [{}])[0]
                message = choice.get("message") or {}
                content = message.get("content") or ""
                if not content.strip():
                    provider_error = choice.get("error") or {}
                    raise RuntimeError(
                        "OpenRouter returned empty content"
                        f" (finish_reason={choice.get('finish_reason')!r}, "
                        f"provider_error={json.dumps(provider_error)[:240]}): {json.dumps(data)[:500]}"
                    )

                usage = data.get("usage") or {}
                return LLMCall(
                    content=content,
                    model=data.get("model") or payload["model"],
                    provider=data.get("provider") or "",
                    prompt_tokens=int(usage.get("prompt_tokens") or 0),
                    completion_tokens=int(usage.get("completion_tokens") or 0),
                    total_tokens=int(usage.get("total_tokens") or 0),
                    cost_usd=float(usage.get("cost") or 0.0),
                    raw_id=str(data.get("id") or ""),
                )
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if json_mode and exc.code == 400:
                    return self.chat(messages, max_tokens=max_tokens, json_mode=False, model=model)
                last_error = RuntimeError(f"OpenRouter HTTP {exc.code}: {detail[:500]}")
            except (TimeoutError, urllib.error.URLError, RuntimeError) as exc:
                last_error = exc

            if attempt + 1 < max(1, self.max_retries):
                time.sleep(min(2**attempt, 8))

        raise RuntimeError(f"OpenRouter call failed after {self.max_retries} attempts: {last_error!r}")


def read_system_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def import_platform(platform: str) -> tuple[bool, str, str]:
    if platform == "langgraph":
        try:
            importlib.import_module("langgraph.graph")
            return True, "langgraph_stategraph_openrouter_llm", ""
        except Exception as exc:
            return False, "import_failed", repr(exc)

    errors = []
    for module_name in PLATFORM_IMPORTS.get(platform, []):
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            errors.append(f"{module_name}: {exc!r}")
    if errors:
        return False, "import_failed", "; ".join(errors)
    return True, f"{platform}_openrouter_llm_adapter", ""


def visible_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Return only fields that are allowed to be shown to the LLM."""

    return {key: value for key, value in packet.items() if not str(key).startswith(PRIVATE_PACKET_PREFIX)}


def record_case_id(packet: dict[str, Any]) -> str:
    return str(packet.get("_stableeval_case_id") or packet["case_id"])


def record_stablecoin(packet: dict[str, Any]) -> str:
    return str(packet.get("_stableeval_stablecoin") or packet["stablecoin"])


def build_messages(system_prompt: str, packet: dict[str, Any], platform: str, extra_context: str = "") -> list[dict[str, str]]:
    system = system_prompt.strip() + "\n\n" + PLATFORM_INSTRUCTIONS.get(platform, "")
    system += (
        "\n\nReturn strict JSON only. Include these metadata fields in the JSON object when possible: "
        "case_id, platform, model_backend, execution_mode. Do not use tools, web search, future data, "
        "or hidden labels."
    )
    if extra_context:
        system += "\n\nIntermediate agent state:\n" + extra_context.strip()
    user = "Frozen evidence packet:\n" + json.dumps(visible_packet(packet), sort_keys=True, ensure_ascii=False)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    if start < 0:
        raise ValueError(f"No JSON object found in model output: {cleaned[:300]}")
    depth = 0
    in_string = False
    escape = False
    for idx, char in enumerate(cleaned[start:], start=start):
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(cleaned[start : idx + 1])
    raise ValueError(f"Unbalanced JSON object in model output: {cleaned[:300]}")


def as_float(value: Any, *, minimum: float, maximum: float, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        out = default
    return max(minimum, min(maximum, out))


def coerce_status(value: Any, probability: float, predicted_bps: float) -> str:
    status = str(value or "").strip().lower()
    if status in VALID_STATUSES:
        return status
    has_stable = "stable" in status
    has_watch = "watch" in status
    has_stress = "stress" in status
    if has_stress:
        return "stress"
    if has_watch and not has_stable:
        return "watch"
    if has_stable and not has_watch:
        return "stable"
    if has_stable and has_watch:
        return "watch" if probability >= 0.05 or predicted_bps >= 50 else "stable"
    if probability >= 0.30 or predicted_bps >= 150:
        return "stress"
    if probability >= 0.08 or predicted_bps >= 50:
        return "watch"
    return "stable"


def coerce_direction(value: Any) -> str:
    direction = str(value or "").strip().lower()
    if direction in VALID_DIRECTIONS:
        return direction
    if "below" in direction or "down" in direction:
        return "below_peg"
    if "above" in direction or "up" in direction:
        return "above_peg"
    return "two_sided_or_no_meaningful"


def normalize_prediction(raw: dict[str, Any], platform: str, model: str) -> dict[str, Any]:
    probability = round(as_float(raw.get("p_depeg_next_7d"), minimum=0.0, maximum=1.0), 4)
    predicted_bps = round(as_float(raw.get("predicted_max_abs_deviation_bps"), minimum=0.0, maximum=10000.0), 2)
    status = coerce_status(raw.get("price_stability_next_7d"), probability, predicted_bps)
    direction = coerce_direction(raw.get("predicted_direction"))

    evidence = raw.get("evidence_used") or []
    if isinstance(evidence, str):
        evidence = [evidence]
    if not isinstance(evidence, list):
        evidence = []

    normalized = {
        "price_stability_next_7d": status,
        "p_depeg_next_7d": probability,
        "predicted_max_abs_deviation_bps": predicted_bps,
        "predicted_direction": direction,
        "confidence": round(as_float(raw.get("confidence"), minimum=0.0, maximum=1.0), 3),
        "rationale": str(raw.get("rationale", "")).strip()[:1200],
        "evidence_used": [str(item)[:80] for item in evidence[:10]],
        "backend": "openrouter_llm",
        "model": model,
        "platform_adapter": platform,
    }
    if raw.get("verifier_action") is not None:
        normalized["verifier_action"] = str(raw.get("verifier_action", "")).strip()[:120]
    if raw.get("verifier_notes") is not None:
        normalized["verifier_notes"] = str(raw.get("verifier_notes", "")).strip()[:600]
    return normalized


def apply_label_calibration(prediction: dict[str, Any], mode: str) -> dict[str, Any]:
    if mode == "none":
        return prediction
    if mode != "risk_sensitive_v1":
        raise ValueError(f"Unsupported label calibration mode: {mode}")

    original_label = prediction.get("price_stability_next_7d")
    probability = as_float(prediction.get("p_depeg_next_7d"), minimum=0.0, maximum=1.0)
    predicted_bps = as_float(prediction.get("predicted_max_abs_deviation_bps"), minimum=0.0, maximum=10000.0)

    if predicted_bps >= 100 or (probability >= 0.35 and predicted_bps >= 75):
        calibrated = "stress"
    elif probability >= 0.15 or predicted_bps >= 40:
        calibrated = "watch"
    else:
        calibrated = "stable"

    prediction = dict(prediction)
    prediction["price_stability_next_7d"] = calibrated
    prediction["label_calibration"] = mode
    prediction["original_price_stability_next_7d"] = original_label
    return prediction


def parse_prediction(text: str, platform: str, model: str) -> dict[str, Any]:
    return normalize_prediction(extract_json_object(text), platform=platform, model=model)


def parse_prediction_with_repair(
    text: str,
    platform: str,
    model: str,
    client: OpenRouterClient,
) -> tuple[dict[str, Any], list[LLMCall], dict[str, Any]]:
    try:
        return parse_prediction(text, platform, model), [], {}
    except Exception as exc:
        repair_messages = [
            {
                "role": "system",
                "content": (
                    "You are a strict StableEval JSON repair adapter. Convert the supplied model output "
                    "into exactly one valid JSON object matching the schema. Choose exactly one status "
                    "from stable, watch, stress. Choose exactly one direction from below_peg, above_peg, "
                    "two_sided_or_no_meaningful. Use numeric probabilities and confidence in [0,1]. "
                    "Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Platform: {platform}\n"
                    f"Parser error: {type(exc).__name__}: {str(exc)[:500]}\n\n"
                    f"Model output to repair:\n{text[:4000]}"
                ),
            },
        ]
        repair_call = client.chat(repair_messages, max_tokens=500, json_mode=True)
        prediction = parse_prediction(repair_call.content, platform, repair_call.model)
        return prediction, [repair_call], {"json_repair_applied": True, "json_repair_error": repr(exc)[:500]}


def run_direct_openrouter(
    platform: str,
    packet: dict[str, Any],
    system_prompt: str,
    client: OpenRouterClient,
) -> AdapterResult:
    call = client.chat(build_messages(system_prompt, packet, platform), json_mode=True)
    prediction, repair_calls, repair_meta = parse_prediction_with_repair(call.content, platform, call.model, client)
    return AdapterResult(
        raw_text=call.content,
        prediction=prediction,
        execution_mode=f"{platform}_openrouter_llm_adapter",
        calls=[call] + repair_calls,
        metadata=repair_meta,
    )


def run_langgraph(packet: dict[str, Any], system_prompt: str, client: OpenRouterClient) -> AdapterResult:
    from typing import TypedDict

    from langgraph.graph import END, START, StateGraph

    class State(TypedDict, total=False):
        packet: dict[str, Any]
        summary: str
        final: str
        calls: list[LLMCall]

    def summarize(state: State) -> dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the first node in a LangGraph stablecoin-risk workflow. "
                    "Summarize only the evidence signals that matter for a seven-day peg-stability forecast. "
                    "Do not predict yet."
                ),
            },
            {"role": "user", "content": json.dumps(state["packet"], sort_keys=True, ensure_ascii=False)},
        ]
        call = client.chat(messages, max_tokens=260, json_mode=False)
        return {"summary": call.content, "calls": [call]}

    def predict(state: State) -> dict[str, Any]:
        call = client.chat(
            build_messages(system_prompt, state["packet"], "langgraph", extra_context=state["summary"]),
            json_mode=True,
        )
        return {"final": call.content, "calls": state["calls"] + [call]}

    graph = StateGraph(State)
    graph.add_node("summarize_signals", summarize)
    graph.add_node("forecast_json", predict)
    graph.add_edge(START, "summarize_signals")
    graph.add_edge("summarize_signals", "forecast_json")
    graph.add_edge("forecast_json", END)
    out = graph.compile().invoke({"packet": packet})
    final_call = out["calls"][-1]
    prediction, repair_calls, repair_meta = parse_prediction_with_repair(
        out["final"], "langgraph", final_call.model, client
    )
    return AdapterResult(
        raw_text=out["final"],
        prediction=prediction,
        execution_mode="langgraph_two_node_stategraph_openrouter_llm",
        calls=out["calls"] + repair_calls,
        metadata={"langgraph_summary": out.get("summary", "")[:1000], **repair_meta},
    )


def run_evoagentx(packet: dict[str, Any], system_prompt: str, client: OpenRouterClient) -> AdapterResult:
    os.environ.setdefault("LITELLM_LOG", "ERROR")
    from evoagentx.models.model_configs import OpenRouterConfig
    from evoagentx.models.openrouter_model import OpenRouterLLM

    cfg = OpenRouterConfig(
        model=client.model,
        openrouter_key=client.api_key,
        temperature=client.temperature,
        max_tokens=client.max_tokens,
        stream=False,
        output_response=False,
    )
    llm = OpenRouterLLM(config=cfg)
    messages = build_messages(system_prompt, packet, "evoagentx")
    response = None
    content = ""
    last_error: Exception | None = None
    for attempt in range(max(1, client.max_retries)):
        try:
            response = llm._client.chat.completions.create(messages=messages, **llm.get_completion_params())
            message = response.choices[0].message
            content = message.content or ""
            if content.strip():
                break
            last_error = RuntimeError(f"EvoAgentX/OpenRouter returned empty content: {response!r}")
        except Exception as exc:
            last_error = exc
        if attempt + 1 < max(1, client.max_retries):
            time.sleep(min(2**attempt, 8))
    if response is None or not content.strip():
        raise RuntimeError(f"EvoAgentX/OpenRouter call failed after retries: {last_error!r}")
    usage = response.usage
    call = LLMCall(
        content=content,
        model=response.model,
        provider=str(getattr(response, "provider", "") or ""),
        prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
        completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
        total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
        cost_usd=float(getattr(usage, "cost", 0.0) or 0.0),
        raw_id=str(response.id),
    )
    prediction, repair_calls, repair_meta = parse_prediction_with_repair(content, "evoagentx", call.model, client)
    return AdapterResult(
        raw_text=content,
        prediction=prediction,
        execution_mode="evoagentx_openrouterllm_adapter",
        calls=[call] + repair_calls,
        metadata=repair_meta,
    )


def patch_hermes_for_openrouter_models() -> None:
    import tiktoken
    import llama_index.llms.openai.base as openai_base
    import llama_index.llms.openai.utils as openai_utils

    original_context = openai_utils.openai_modelname_to_contextsize
    original_encoding = tiktoken.encoding_for_model

    def context_size(model_name: str) -> int:
        name = str(model_name)
        if "/" in name or name.endswith(":free"):
            return 131072
        return original_context(model_name)

    def encoding_for_model(model_name: str):
        try:
            return original_encoding(model_name)
        except Exception:
            return tiktoken.get_encoding("cl100k_base")

    openai_utils.openai_modelname_to_contextsize = context_size
    openai_base.openai_modelname_to_contextsize = context_size
    tiktoken.encoding_for_model = encoding_for_model


def run_hermes(packet: dict[str, Any], system_prompt: str, client: OpenRouterClient) -> AdapterResult:
    os.environ["OPENAI_API_KEY"] = client.api_key
    os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
    patch_hermes_for_openrouter_models()

    from hermes.core import Agent
    from llama_index.core.llms import ChatMessage, MessageRole

    async def invoke() -> Any:
        agent = Agent(
            provider="openai",
            model=client.model,
            api_key=client.api_key,
            name="hermes_stableeval",
            description="Stablecoin price-stability risk agent",
            prompt=system_prompt,
            temperature=client.temperature,
            token_limit=32000,
            max_chat_history_length=2,
        )
        agent.llm.max_tokens = client.max_tokens
        messages = build_messages(system_prompt, packet, "hermes_ai")
        chat_messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=messages[0]["content"]),
            ChatMessage(role=MessageRole.USER, content=messages[1]["content"]),
        ]
        return await agent.llm.achat(chat_messages)

    response = None
    content = ""
    last_error: Exception | None = None
    sdk_timeout = float(os.getenv("STABLEEVAL_SDK_CALL_TIMEOUT_SECONDS", "240"))
    for attempt in range(max(1, client.max_retries)):
        try:
            response = asyncio.run(asyncio.wait_for(invoke(), timeout=sdk_timeout))
            content = response.message.content or ""
            if content.strip():
                break
            last_error = RuntimeError(f"Hermes/OpenRouter returned empty content: {response!r}")
        except Exception as exc:
            last_error = exc
        if attempt + 1 < max(1, client.max_retries):
            time.sleep(min(2**attempt, 8))
    if response is None or not content.strip():
        raise RuntimeError(f"Hermes/OpenRouter call failed after retries: {last_error!r}")
    call = LLMCall(content=content, model=client.model)
    prediction, repair_calls, repair_meta = parse_prediction_with_repair(content, "hermes_ai", call.model, client)
    return AdapterResult(
        raw_text=content,
        prediction=prediction,
        execution_mode="hermes_agent_llamaindex_achat_openrouter_llm",
        calls=[call] + repair_calls,
        metadata=repair_meta,
    )


def run_nanobot(packet: dict[str, Any], system_prompt: str, client: OpenRouterClient) -> AdapterResult:
    os.environ["LOGURU_LEVEL"] = "ERROR"
    try:
        from loguru import logger

        logger.remove()
        logger.add(sys.stderr, level="ERROR")
    except Exception:
        pass
    from nanobot.agent.tools.loader import ToolLoader
    from nanobot.nanobot import Nanobot

    ToolLoader.load = lambda self, ctx, registry, scope="core": []
    prompt = prompt_text(system_prompt + "\n\n" + PLATFORM_INSTRUCTIONS["nanobot"], visible_packet(packet))

    async def invoke(config_path: Path, workspace: Path) -> Any:
        bot = Nanobot.from_config(config_path, workspace=workspace)
        return await bot.run(prompt, session_key=f"stableeval:{packet['case_id']}")

    with tempfile.TemporaryDirectory(prefix="stableeval-nanobot-") as tmp:
        tmp_path = Path(tmp)
        workspace = tmp_path / "workspace"
        config = {
            "agents": {
                "defaults": {
                    "workspace": str(workspace),
                    "model": client.model,
                    "provider": "openrouter",
                    "max_tokens": client.max_tokens,
                    "context_window_tokens": 131072,
                    "temperature": client.temperature,
                    "max_tool_iterations": 1,
                    "bot_icon": "",
                    "bot_name": "nanobot",
                }
            },
            "providers": {
                "openrouter": {
                    "api_key": client.api_key,
                    "api_base": "https://openrouter.ai/api/v1",
                    "extra_body": {"response_format": {"type": "json_object"}},
                }
            },
            "tools": {
                "my": {"enable": False},
                "web": {"enable": False},
                "exec": {"enable": False},
                "image_generation": {"enable": False},
            },
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        result = None
        last_error: Exception | None = None
        for attempt in range(max(1, client.max_retries)):
            try:
                result = asyncio.run(invoke(config_path, workspace))
                if (result.content or "").strip():
                    break
                last_error = RuntimeError("Nanobot/OpenRouter returned empty content")
            except Exception as exc:
                last_error = exc
            if attempt + 1 < max(1, client.max_retries):
                time.sleep(min(2**attempt, 8))
        if result is None or not (result.content or "").strip():
            raise RuntimeError(f"Nanobot/OpenRouter call failed after retries: {last_error!r}")

    content = result.content or ""
    call = LLMCall(content=content, model=client.model)
    prediction, repair_calls, repair_meta = parse_prediction_with_repair(content, "nanobot", call.model, client)
    return AdapterResult(
        raw_text=content,
        prediction=prediction,
        execution_mode="nanobot_sdk_openrouter_agent_loop",
        calls=[call] + repair_calls,
        metadata={"tools_used": result.tools_used, **repair_meta},
    )


def cmdop_status(platform: str) -> dict[str, Any]:
    module_name = "openclaw" if platform == "openclaw" else "nanoclaw"
    class_name = "OpenClaw" if platform == "openclaw" else "NanoClaw"
    cls = getattr(importlib.import_module(module_name), class_name)
    try:
        client = cls.local()
    except Exception as exc:
        return {"cmdop_local_agent": "unavailable", "cmdop_error": f"{type(exc).__name__}: {str(exc)[:240]}"}
    try:
        status = {"cmdop_local_agent": "available", "cmdop_mode": getattr(client, "mode", "")}
    finally:
        client.close()
    return status


def run_adapter(platform: str, packet: dict[str, Any], system_prompt: str, client: OpenRouterClient) -> AdapterResult:
    if platform == "langgraph":
        return run_langgraph(packet, system_prompt, client)
    if platform == "evoagentx":
        return run_evoagentx(packet, system_prompt, client)
    if platform == "hermes_ai":
        return run_hermes(packet, system_prompt, client)
    if platform == "nanobot":
        return run_nanobot(packet, system_prompt, client)
    if platform in {"openclaw", "nanoclaw"}:
        result = run_direct_openrouter(platform, packet, system_prompt, client)
        status = cmdop_status(platform)
        if status.get("cmdop_local_agent") == "available":
            result.execution_mode = "native_cmdop"
        else:
            result.execution_mode = "stableeval_adapter"
        result.metadata.update(
            {
                "adapter_detail": f"{platform}_cmdop_sdk_imported_openrouter_llm",
                **status,
            }
        )
        return result
    return run_direct_openrouter(platform, packet, system_prompt, client)


def run_risk_verifier(
    platform: str,
    packet: dict[str, Any],
    first_result: AdapterResult,
    client: OpenRouterClient,
) -> AdapterResult:
    messages = [
        {"role": "system", "content": RISK_VERIFIER_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "packet": visible_packet(packet),
                    "first_prediction": first_result.prediction,
                    "first_execution_mode": first_result.execution_mode,
                },
                sort_keys=True,
                ensure_ascii=False,
            ),
        },
    ]
    call = client.chat(messages, max_tokens=min(client.max_tokens, 1200), json_mode=True)
    prediction, repair_calls, repair_meta = parse_prediction_with_repair(call.content, platform, call.model, client)
    metadata = dict(first_result.metadata)
    metadata.update(
        {
            "risk_verifier_applied": True,
            "base_prediction": first_result.prediction,
            "base_raw_agent_output": first_result.raw_text[:2400],
            **repair_meta,
        }
    )
    return AdapterResult(
        raw_text=call.content,
        prediction=prediction,
        execution_mode=f"{first_result.execution_mode}+risk_auditor_verifier",
        calls=first_result.calls + [call] + repair_calls,
        metadata=metadata,
    )


def resolve_api_key() -> str:
    return os.getenv("OPENROUTER_API_KEY") or ""


def packet_hash(packet: dict[str, Any]) -> str:
    raw = json.dumps(visible_packet(packet), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_packets(path: Path, max_cases: int = 0) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if max_cases and len(packets) >= max_cases:
                break
            packets.append(json.loads(line))
    return packets


def existing_output_case_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("case_id"):
                out.add(str(item["case_id"]))
    return out


def fetch_model_prices(model: str) -> tuple[float, float]:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(OPENROUTER_MODELS_URL, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return 0.0, 0.0
    for item in data.get("data", []):
        if item.get("id") == model:
            pricing = item.get("pricing") or {}
            return float(pricing.get("prompt") or 0.0), float(pricing.get("completion") or 0.0)
    return 0.0, 0.0


def fetch_model_pricing(model: str) -> ModelPricing:
    prompt_price, completion_price = fetch_model_prices(model)
    return ModelPricing(prompt_per_token_usd=prompt_price, completion_per_token_usd=completion_price)


def estimate_run_cost(
    packets: list[dict[str, Any]],
    system_prompt: str,
    platform: str,
    model: str,
    max_tokens: int,
) -> tuple[float, int]:
    prompt_price, completion_price = fetch_model_prices(model)
    multiplier = 2.0 if platform == "langgraph" else 1.0
    prompt_tokens = sum(token_count_approx(prompt_text(system_prompt, packet)) for packet in packets)
    estimated_tokens = int((prompt_tokens + len(packets) * max_tokens) * multiplier * 1.15)
    estimated_cost = (prompt_tokens * prompt_price + len(packets) * max_tokens * completion_price) * multiplier * 1.15
    return float(estimated_cost), estimated_tokens


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True)
    parser.add_argument("--input", default="data/benchmark/stableeval_507_natural/prompt_packets.jsonl")
    parser.add_argument("--system-prompt", default="prompts/templates/system_prompt.md")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--model", default=os.getenv("STABLEEVAL_MODEL", DEFAULT_MODEL))
    parser.add_argument("--temperature", type=float, default=float(os.getenv("STABLEEVAL_TEMPERATURE", "0")))
    parser.add_argument("--max-tokens", type=int, default=int(os.getenv("STABLEEVAL_MAX_TOKENS", "900")))
    parser.add_argument("--max-estimated-cost-usd", type=float, default=float(os.getenv("STABLEEVAL_MAX_COST_USD", "0")))
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--label-calibration", default=os.getenv("STABLEEVAL_LABEL_CALIBRATION", "none"))
    parser.add_argument("--risk-verifier", action="store_true")
    parser.add_argument("--allow-deterministic-fallback", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    os.environ.setdefault("NO_PROXY", "*")
    os.environ.setdefault("no_proxy", "*")

    platform = args.platform
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    system_prompt = read_system_prompt(Path(args.system_prompt))
    packets = load_packets(input_path, args.max_cases)
    pricing = fetch_model_pricing(args.model)

    import_ok, import_mode, import_error = import_platform(platform)
    api_key = resolve_api_key()
    provider_key_present = bool(api_key)
    if not provider_key_present and not args.allow_deterministic_fallback:
        raise SystemExit(
            "No LLM provider key found. Set OPENROUTER_API_KEY for a real LLM-backed run "
            "or pass --allow-deterministic-fallback explicitly."
        )
    estimated_cost, estimated_tokens = estimate_run_cost(
        packets=packets,
        system_prompt=system_prompt,
        platform=platform,
        model=args.model,
        max_tokens=args.max_tokens,
    )
    preflight = {
        "platform": platform,
        "cases": len(packets),
        "model": args.model,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "estimated_tokens_upper_bound": estimated_tokens,
        "estimated_cost_usd_upper_bound": round(estimated_cost, 6),
        "max_estimated_cost_usd": args.max_estimated_cost_usd,
    }
    print(json.dumps({"preflight": preflight}, indent=2))
    if args.max_estimated_cost_usd and estimated_cost > args.max_estimated_cost_usd:
        raise SystemExit(
            f"Estimated cost ${estimated_cost:.4f} exceeds limit ${args.max_estimated_cost_usd:.4f}; aborting."
        )
    if args.preflight_only:
        return
    client = OpenRouterClient(api_key=api_key, model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)

    existing_case_ids = existing_output_case_ids(output_path) if args.resume else set()
    count = len(existing_case_ids)
    total_cost = 0.0
    with output_path.open("a" if args.resume else "w", encoding="utf-8") as out:
        for packet in packets:
            if record_case_id(packet) in existing_case_ids:
                continue
            rendered_prompt = prompt_text(system_prompt, visible_packet(packet))
            start = time.perf_counter()
            error = ""
            result: AdapterResult | None = None
            prediction: dict[str, Any] | None = None
            execution_mode = import_mode
            try:
                if not import_ok:
                    raise RuntimeError(import_error)
                if provider_key_present:
                    result = run_adapter(platform, packet, system_prompt, client)
                    if args.risk_verifier:
                        result = run_risk_verifier(platform, packet, result, client)
                    prediction = result.prediction
                    execution_mode = result.execution_mode
                elif args.allow_deterministic_fallback:
                    prediction = generate_prediction(packet, platform=platform)
                    execution_mode = f"{platform}_deterministic_fallback"
                if prediction:
                    prediction = apply_label_calibration(prediction, args.label_calibration)
            except Exception as exc:
                error = repr(exc)

            latency = time.perf_counter() - start
            completion_text = result.raw_text if result else json.dumps(prediction, ensure_ascii=False, sort_keys=True) if prediction else ""
            prompt_tokens = result.prompt_tokens if result and result.prompt_tokens else token_count_approx(rendered_prompt)
            completion_tokens = (
                result.completion_tokens if result and result.completion_tokens else token_count_approx(completion_text)
            )
            total_tokens = result.total_tokens if result and result.total_tokens else prompt_tokens + completion_tokens
            cost = result.cost_usd if result else 0.0
            if provider_key_present and cost <= 0:
                cost = pricing.estimate(prompt_tokens, completion_tokens)
            total_cost += cost
            model_backend = f"openrouter/{args.model}" if provider_key_present else "deterministic_policy_explicit_fallback"
            if prediction:
                prediction.update(
                    {
                        "case_id": record_case_id(packet),
                        "platform": platform,
                        "model_backend": model_backend,
                        "execution_mode": execution_mode,
                    }
                )
            record = {
                "case_id": record_case_id(packet),
                "stablecoin": record_stablecoin(packet),
                "observation_time": packet.get("_stableeval_observation_time") or packet["observation_time"],
                "platform": platform,
                "framework_execution_mode": execution_mode,
                "execution_mode": execution_mode,
                "provider_key_present": provider_key_present,
                "model_backend": model_backend,
                "backend": prediction.get("backend") if prediction else "",
                "input_packet_hash": packet_hash(packet),
                "raw_agent_output": completion_text,
                "parsed_json": prediction,
                "valid_json": bool(prediction),
                "error_message": error,
                "prediction": prediction,
                "valid_output": bool(prediction),
                "error": error,
                "latency_seconds": latency,
                "prompt_tokens_approx": prompt_tokens,
                "completion_tokens_approx": completion_tokens,
                "total_tokens_approx": total_tokens,
                "estimated_cost_usd": cost,
                "cost_note": (
                    "OpenRouter LLM-backed run; cost is provider usage cost when returned by the API."
                    if provider_key_present
                    else "Explicit deterministic fallback; not a model-powered comparison."
                ),
                "llm_call_count": len(result.calls) if result else 0,
                "adapter_metadata": result.metadata if result else {},
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
            if args.max_estimated_cost_usd and total_cost > args.max_estimated_cost_usd:
                raise SystemExit(
                    f"Actual returned cost ${total_cost:.4f} exceeded limit ${args.max_estimated_cost_usd:.4f}; stopped."
                )

    print(
        json.dumps(
            {
                "platform": platform,
                "records": count,
                "output": str(output_path),
                "import_ok": import_ok,
                "mode": import_mode,
                "model": args.model,
                "llm_backed": provider_key_present,
                "estimated_cost_usd_upper_bound": round(estimated_cost, 6),
                "actual_reported_cost_usd": round(total_cost, 6),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
