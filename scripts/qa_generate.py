"""Generate Q&A parquet from filtered wiki jsonl using an Ollama cloud model.

Reads data/wiki/{domain}.jsonl (articles), sends each article to an Ollama
model (cloud or local) using data/wiki/prompt-templates.md as the system
prompt, collects the returned Q&A objects, and writes data/wiki_qa/{domain}.parquet.

Corresponds to issue I2.2b (sub-tasks I2.2b4-9).

Run (inside .venv):
    python scripts/qa_generate.py --domain lich_su --model gemma4:31b-cloud --limit 100
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://localhost:11434/api/chat"
PROMPT_FILE = Path("data/wiki/prompt-templates.md")

# Everything before the "Bài viết:" block is the system instruction;
# the article text is sent as the user message.
_SPLIT_MARKER = "Bài viết:"


def load_system_prompt(domain: str) -> str:
    """Extract the first fenced code block of prompt-templates.md as system prompt."""
    text = PROMPT_FILE.read_text(encoding="utf-8")
    fence_start = text.find("```")
    fence_end = text.find("```", fence_start + 3)
    if fence_start == -1 or fence_end == -1:
        idx = text.find(_SPLIT_MARKER)
        body = text[:idx] if idx != -1 else text
        return body.replace("{DOMAIN}", domain).strip()
    return text[fence_start + 3 : fence_end].strip().replace("{DOMAIN}", domain)


def call_model(model: str, system: str, article: str, base_url: str) -> str:
    """Send one chat request; returns the assistant content (raw text)."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Bài viết:\n\"\"\"\n{article}\n\"\"\""},
        ],
        "stream": False,
    }
    req = urllib.request.Request(
        base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["message"]["content"]


def extract_json_objects(raw: str) -> list[dict]:
    """Extract a JSON array from model output (tolerates markdown fences)."""
    raw = raw.strip()
    # drop ```json ... ``` fences
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # fall back to first [...] slice
        start = raw.find("[")
        end = raw.rfind("]")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model output is not valid JSON")
        parsed = json.loads(raw[start : end + 1])
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("qa", "questions", "data", "results"):
            if isinstance(parsed.get(key), list):
                return parsed[key]
    raise ValueError("No Q&A array found in model output")


def main() -> None:
    ap = argparse.ArgumentParser(description="Wiki -> Q&A parquet via Ollama")
    ap.add_argument("--domain", required=True, help="lich_su | dia_ly | van_hoa | khoa_hoc | xa_hoi")
    ap.add_argument("--model", default="gemma4:31b-cloud", help="Ollama model name")
    ap.add_argument("--input", default=None, help="input jsonl (default: data/wiki/{domain}.jsonl)")
    ap.add_argument("--output", default=None, help="output parquet (default: data/wiki_qa/{domain}.parquet)")
    ap.add_argument("--limit", type=int, default=None, help="max articles to process")
    ap.add_argument("--per-article", type=int, default=5, help="Q&A expected per article (unused except logs)")
    ap.add_argument("--sleep", type=float, default=1.0, help="seconds between requests (rate limit)")
    ap.add_argument("--base-url", default=DEFAULT_URL, help="Ollama API URL")
    ap.add_argument("--resume", action="store_true", help="skip articles already in output parquet")
    args = ap.parse_args()

    import pandas as pd

    domain = args.domain
    in_path = Path(args.input) if args.input else Path(f"data/wiki/{domain}.jsonl")
    out_path = Path(args.output) if args.output else Path(f"data/wiki_qa/{domain}.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    existing: set[str] = set()
    rows: list[dict] = []
    if args.resume and out_path.exists():
        old = pd.read_parquet(out_path)
        rows = old.to_dict("records")
        existing = {f"{r.get('wiki_id')}|{r.get('question')}" for r in rows}
        print(f"Resuming: {len(rows)} existing rows loaded.")

    system = load_system_prompt(domain)
    print(f"Domain: {domain}")
    print(f"Model : {args.model}")
    print(f"Input : {in_path}")
    print(f"System prompt len: {len(system)} chars")

    articles = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                articles.append(json.loads(line))
    if args.limit:
        articles = articles[: args.limit]
    print(f"Articles to process: {len(articles)}")

    ok = skipped = failed = 0
    for i, art in enumerate(articles):
        title = art.get("title", "")
        text = art.get("text", "")
        art_id = art.get("id")
        if len(text) > 2500:
            text = text[:2500]  # keep within LLM window

        for attempt in range(3):
            try:
                raw = call_model(args.model, system, text, args.base_url)
                qas = extract_json_objects(raw)
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    print(f"  [{i+1}/{len(articles)}] FAILED {title}: {e}")
                    failed += 1
                    time.sleep(2)
                    qas = None
                else:
                    time.sleep(2 * (attempt + 1))
        if qas is None:
            continue

        new = 0
        for q in qas:
            question = str(q.get("question", "")).strip()
            answer = str(q.get("answer", "")).strip()
            if not question or not answer:
                continue
            key = f"{art_id}|{question}"
            if args.resume and key in existing:
                skipped += 1
                continue
            rows.append({
                "question": question,
                "answer": answer,
                "domain": domain,
                "wiki_id": art_id,
                "title": title,
            })
            existing.add(key)
            new += 1
        ok += 1
        print(f"  [{i+1}/{len(articles)}] {title} -> +{new} Q&A "
              f"(tot {len(rows)})")

        if (i + 1) % 5 == 0:
            pd.DataFrame(rows).to_parquet(out_path, index=False, engine="pyarrow")
        time.sleep(args.sleep)

    df = pd.DataFrame(rows)
    df.to_parquet(out_path, index=False, engine="pyarrow")
    print(f"\nDONE: {len(df)} Q&A rows -> {out_path}")
    print(f"  articles ok={ok}, failed={failed}, skipped_dup={skipped}")


if __name__ == "__main__":
    main()