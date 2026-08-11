# PRD: Vietnamese Gen-Z SmolLM2

## 1. Vision / Problem
SmolLM2-360M-Base answers poorly in Vietnamese and has no conversational persona. Goal: a small, locally-runnable model that answers everyday Vietnamese questions **correctly** (improved knowledge) **and** with a **light Gen-Z young-person voice**.

## 2. Target User & Use Case
- Everyday Vietnamese speakers asking normal questions (history, geography, culture, science, society).
- Expects friendly, casual, lightly-slang Vietnamese answers — not formal/stiff, not heavy internet slang.
- Slang intensity target: **scale 4 of 5** (modern, young, natural; light abbreviations + emoji; not obscure/meme-heavy).

## 3. Goals (measurable)
- **Knowledge:** Finetuned model scores measurably higher than Base on a held-out Vietnamese MCQ eval.
- **Persona:** Finetuned model's answers visibly sound more natural/Gen-Z than Base (qualitative side-by-side).
- **Runnable:** Final model runs locally on a 6GB RTX 4050 laptop (QLoRA-deployable).

## 4. Non-Goals
- Heavy/complex explanations; technical-user features; production-scale; general broad knowledge.
- No CPT, no Instruct checkpoint, no forum/TikTok crawling, no paid LLM API.

## 5. Constraints
- Hardware: 6GB RTX 4050 laptop. No LLM API — web-interface only.
- Data budget: ~200–400M tokens.
- Model: SmolLM2-360M-Base + QLoRA, custom chat template.
- Deadlines: each task's due date = `estimate × 1.5`.

## 6. Architecture / Flow
```
Build eval (frozen first)
  → Curate data (Atri + wiki-vi slices + hoidap[low] + slang garnish)
  → QLoRA SFT → deploy + system prompt
```

## 7. Deliverables
- Held-out MCQ eval set (~200–300 Q, labeled)
- Curated training dataset (blend + garnish)
- Trained model + configs
- Eval results (MCQ accuracy number + persona show-and-tell)
- README writeup

## 8. Risks
- Weak system-prompt following (360M) → mitigated by SFT-embedded voice
- Overfitting / knowledge ceiling at small scale → bounded to curated domains
- Tone inconsistency → garnish is small + hand-curated
- QLoRA not fitting in 6GB → de-risked in Iteration 0 before real data work
