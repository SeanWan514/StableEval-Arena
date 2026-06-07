# Updated Pre-Scaling Decision Report

## 1. Did the improved 30-case result generalize?

30-case best agent `openclaw` macro-F1=0.434; best baseline `historical_persistence` macro-F1=0.333.

Partially. The best 120-case validation agent still beats the best baseline on macro-F1, but the effect is smaller than in the 30-case pilot and stress recall remains weak.

Intermediate selected variant `evaluation_base_calibrated` best agent `nanobot`: macro-F1=0.351, balanced accuracy=0.393, stress recall=0.095.
Best baseline in the same variant: `historical_persistence` macro-F1=0.285.

## 2. Did verifier-agent/risk-auditor improve stress recall?

Base calibrated best: `nanobot` macro-F1=0.351, balanced accuracy=0.393, stress recall=0.095, cost=$0.345.
Verifier calibrated best: `nanobot` macro-F1=0.349, balanced accuracy=0.388, stress recall=0.143, cost=$0.978.
The verifier improved the best observed stress recall from 0.095 to 0.143, but did not improve the best macro-F1 and roughly tripled the best-platform cost. It should be reported as a stress-recall/cost tradeoff, not as an unambiguous improvement.

## 3. Did calibrated mapping improve macro-F1 or stress recall?

Base raw best: `langgraph` macro-F1=0.301, balanced accuracy=0.368, stress recall=0.000, cost=$1.212.
Base calibrated best: `nanobot` macro-F1=0.351, balanced accuracy=0.393, stress recall=0.095, cost=$0.345.
Yes. The frozen calibration rule improved the best first-pass macro-F1 and raised stress recall from 0.000 to 0.095 without changing raw model outputs or labels.

## 4. Is parametric-memory leakage serious?

Maximum label-change rate was 0.333; mean absolute probability changes ranged from 0.017 to 0.062. This suggests sensitivity exists, but this subset does not show severe dependence on real names/dates.
This remains an audit, not a mathematical proof of no leakage.

## 5. Do agents still beat baselines?

Yes on macro-F1: best agent 0.351 versus best baseline 0.285. No on stress recall: the historical-persistence baseline recalls more stress cases, but with many more false alarms.

## 6. Is stress recall acceptable?

No. Stress recall remains too weak for a strong trustworthy-risk-agent claim.

## 7. Should we scale to full 507 cases now?

Do not scale yet. Run one more improvement or accept the weak-stress-recall result as a central limitation.

## 8. If yes, which exact protocol should be frozen?

If forced to scale now, freeze `evaluation_base_calibrated` with `qwen/qwen-2.5-72b-instruct`, temperature 0, revised risk-sensitive packets, same output schema/evaluator/baselines, no web search, and the pre-declared calibration rule. Do not choose the verifier as the main protocol unless the paper prioritizes stress recall over macro-F1 and cost.

## 9. If no, what remains broken?

The main blocker is stress recall. The benchmark is paper-reportable as an honest evaluation showing that current LLM-backed agentic wrappers remain conservative under stablecoin stress, but it should not be marketed as solved stablecoin stress prediction.