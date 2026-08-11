"""Load Vietnamese MCQ eval files for the 5 domains.

Reads eval/<domain>.json for each domain and returns a structured dict
so an LLM can be tested on all 5 domains.

Schema (see eval/validation_structure.md):
    { "id": int, "question": str, "domain": str,
      "options": [str x4], "true_answers": str }

Usage:
    from eval_loader import load_eval, DOMAINS
    data = load_eval("eval")           # {domain: [questions]}
    data = load_eval("eval", ["History", "Culture"])
"""
from __future__ import annotations

import json
from pathlib import Path

DOMAINS = ["History", "Culture", "Society", "Lifestyle", "Geography"]


def load_eval(eval_dir: str | Path = "eval", domains: list[str] | None = None) -> dict[str, list[dict]]:
    """Load eval questions grouped by domain.

    Args:
        eval_dir: directory containing <domain>.json files.
        domains: subset of DOMAINS to load (defaults to all 5).

    Returns:
        {domain_name: [question_dict, ...]}
    """
    eval_dir = Path(eval_dir)
    if not eval_dir.is_dir():
        raise FileNotFoundError(f"Eval directory not found: {eval_dir}")

    domains = domains or DOMAINS
    result: dict[str, list[dict]] = {}
    for domain in domains:
        path = eval_dir / f"{domain}.json"
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing eval file for domain '{domain}': {path}"
            )
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)

        questions = raw if isinstance(raw, list) else raw.get("questions", raw.get("data", []))
        for q in questions:
            q.setdefault("domain", domain)
        result[domain] = questions
    return result


def all_questions(eval_dir: str | Path = "eval") -> list[dict]:
    """Flatten all domain questions into one list (with domain field set)."""
    merged: list[dict] = []
    for questions in load_eval(eval_dir).values():
        merged.extend(questions)
    return merged


def summary(eval_dir: str | Path = "eval") -> dict[str, int]:
    """Return {domain: question_count}."""
    return {domain: len(qs) for domain, qs in load_eval(eval_dir).items()}


if __name__ == "__main__":
    data = load_eval()
    total = sum(len(qs) for qs in data.values())
    print(f"Loaded {total} questions across {len(data)} domains:")
    for domain, qs in data.items():
        print(f"  {domain}: {len(qs)}")
    if total and data:
        first_domain = next(iter(data))
        print(f"\nSample from {first_domain}:")
        print(json.dumps(data[first_domain][0], ensure_ascii=False, indent=2))
