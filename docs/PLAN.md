# Plan: Vietnamese Gen-Z SmolLM2

Iterative (tracer-bullet) plan. Each iteration is a thin vertical slice that de-risks the next. Decision gates separate iterations.

> **Timebox rule:** each task's **deadline = estimate × 1.5**. Estimates are optimistic; the 1.5× buffer absorbs setup, debugging, and re-runs.

## Iteration 0 — Vertical Slice (de-risk the stack)
Goal: prove QLoRA fits in 6GB AND base model speaks Vietnamese after SFT. Smallest possible pass.

| # | Task | Est | Deadline (×1.5) |
|---|------|-----|-----|
| I0.1 | Set up env (PyTorch, transformers, peft, trl, bitsandbytes, accelerate), pinned to 4050 CUDA | 0.5d | 0.75d |
| I0.2 | Smoke-test QLoRA: 360M-Base 4-bit, ~1–2k Atri samples, verify VRAM fit + no crash | 1d | 1.5d |
| I0.3 | Inference on tiny-trained model → confirm coherent Vietnamese | 0.5d | 0.75d |
| I0.4 | **Gate:** if works → I1. If VRAM fails → fall back to 135M or shrink config |

## Iteration 1 — Eval Set (build + freeze FIRST)
Goal: a defensible measurement tool, never contaminated by training.

| # | Task | Est | Deadline (×1.5) |
|---|------|-----|-----|
| I1.1 | Define eval schema `{id, domain, question, options, correct_answer}` | 0.5d | 0.75d |
| I1.2 | Generate ~200–300 MCQ via AI, ~50 per domain (5 domains) | 1.5d | 2.25d |
| I1.3 | Manually verify every answer (know ground truth to score) | 1d | 1.5d |
| I1.4 | Freeze + store in `eval/`, excluded from training path | 0.5d | 0.75d |

## Iteration 2 — Training Data (curate + blend)
Goal: assemble dataset within ~200–400M token budget.

| # | Task | Est | Deadline (×1.5) |
|---|------|-----|-----|
| I2.1 | Pull Atri-QA-100K, filter categories, inspect quality | 1d | 1.5d |
| I2.2 | Pull wikipedia_vi, curate 5-domain slices | 1.5d | 2.25d |
| I2.3 | Pull hoidap, clean real-world Q/A subset (LOW priority) | 1.5d | 2.25d |
| I2.4 | Build chat-template formatter (system + user + assistant) | 0.5d | 0.75d |
| I2.5 | Blend to budget, dedup (esp. vs eval), train/val split | 1d | 1.5d |
| I2.6 | **Gate:** eyeball a few hundred formatted samples before training |

## Iteration 3 — Training (full)
Goal: the real SFT run.

| # | Task | Est | Deadline (×1.5) |
|---|------|-----|-----|
| I3.1 | Write training script (r=32, full-attention, lr~2e-4, 2-3 epochs) | 1d | 1.5d |
| I3.2 | Full run (few days on 4050); save adapters/configs at checkpoints | 3d | 4.5d |
| I3.3 | **Gate:** if val loss flatlines/spikes → stop early + adjust |

## Iteration 4 — Evaluation
Goal: measure knowledge (number) + persona (show-and-tell).

| # | Task | Est | Deadline (×1.5) |
|---|------|-----|-----|
| I4.1 | Base vs Finetuned on frozen MCQ eval → accuracy | 1d | 1.5d |
| I4.2 | Side-by-side persona examples (~20–30 open questions) | 0.5d | 0.75d |
| I4.3 | **Gate:** if knowledge didn't improve → revisit data balance (I2) |

## Iteration 5 — Persona Garnish + Deploy
Goal: Gen-Z flavor (scale 4) + runnable locally.

| # | Task | Est | Deadline (×1.5) |
|---|------|-----|-----|
| I5.1 | Build slang glossary + generate ~500 garnish pairs via AI | 1.5d | 2.25d |
| I5.2 | Quick re-train (small) to blend garnish; re-run persona eval | 1d | 1.5d |
| I5.3 | Test local inference on 4050; draft light Gen-Z system prompt | 0.5d | 0.75d |
| I5.4 | Write README (pipeline, data, results, how to run) | 1d | 1.5d |

## Tracked as GitHub Issues
Each row above is filed as an issue with its estimate, deadline, and phase/priority labels. This PLAN.md is the source of truth for ordering; issues carry the deadlines.
