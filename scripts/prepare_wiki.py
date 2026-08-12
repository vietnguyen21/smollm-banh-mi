"""Crawl + filter Vietnamese Wikipedia into 5 domains for Q&A generation.

Loads vietgpt/wikipedia_vi, filters by TITLE + KEYWORD in text for 5 domains,
cleans the raw wiki text, and saves data/wiki/{domain}.jsonl per domain.

Corresponds to issue I2.2b1 / sub-task [I2.2b1].

Run (inside .venv):
    python scripts/prepare_wiki.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from datasets import load_dataset

DATASET_ID = "vietgpt/wikipedia_vi"
OUT_DIR = Path("data/wiki")
DOMAINS = ["lich_su", "dia_ly", "van_hoa", "khoa_hoc", "xa_hoi"]

# title keywords + text keywords per domain
DOMAIN_KEYWORDS = {
    "lich_su": {
        "title": ["lịch sử", "triều", "vua", "chiến tranh", "khởi nghĩa", "phong trào", "cách mạng", "nhà Trần", "nhà Lý", "nhà Lê", "nhà Nguyễn"],
        "text": ["lịch sử", "triều đại", "năm", "cuộc chiến", "thời kỳ"],
    },
    "dia_ly": {
        "title": ["địa lý", "tỉnh", "thành phố", "sông", "núi", "vùng", "biển", "cao nguyên", "đồng bằng", "quần đảo", "huyện"],
        "text": ["km²", "diện tích", "tọa độ", "giáp", "dân số", "địa lý"],
    },
    "van_hoa": {
        "title": ["văn hóa", "lễ hội", "tết", "ẩm thực", "phong tục", "tập quán", "ca dao", "dân ca", "nhạc", "múa", "di sản"],
        "text": ["văn hóa", "truyền thống", "lễ hội", "phong tục", "tập quán"],
    },
    "khoa_hoc": {
        "title": ["khoa học", "vật lý", "hóa học", "sinh học", "toán học", "thiên văn", "công nghệ", "y học", "địa chất", "sinh vật"],
        "text": ["khoa học", "thí nghiệm", "nghiên cứu", "công thức", "phản ứng", "quá trình"],
    },
    "xa_hoi": {
        "title": ["xã hội", "giáo dục", "kinh tế", "luật", "y tế", "giao thông", "nghề", "gia đình", "cộng đồng", "pháp luật"],
        "text": ["xã hội", "đời sống", "cộng đồng", "giáo dục", "kinh tế", "luật pháp"],
    },
}

# Wiki markup / HTML artifacts to strip
WIKI_PATTERNS = [
    re.compile(r"<[^>]+>"),                     # HTML tags / templatestyles
    re.compile(r"\{\{.*?\}\}", re.S),           # templates {{...}}
    re.compile(r"\[\[([^\]|]*?)\|([^\]]*?)\]\]", re.S),  # [[link|label]] -> label
    re.compile(r"\[\[([^\]]*?)\]\]", re.S),     # [[link]] -> link
    re.compile(r"\{\{", re.S),
    re.compile(r"Category:"),
    re.compile(r"http\S+", re.I),
    re.compile(r"\s+"),
]


def clean_text(text: str) -> str:
    """Strip wiki markup/HTML artifacts and collapse whitespace."""
    if not text:
        return ""
    for pat in WIKI_PATTERNS:
        text = pat.sub(" ", text)
    return text.strip()


def matches_domain(title: str, text: str, kws: dict) -> bool:
    """True if article matches a domain via TITLE + KEYWORD in text."""
    t = title.lower()
    if any(k.lower() in t for k in kws["title"]):
        return True
    if any(k.lower() in text.lower() for k in kws["text"]):
        return True
    return False


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[1/3] Loading {DATASET_ID} ...")
    ds = load_dataset(DATASET_ID, split="train")
    print(f"  total rows: {len(ds)}")

    print("[2/3] Filtering by title + keyword per domain ...")
    for domain in DOMAINS:
        kws = DOMAIN_KEYWORDS[domain]
        out_path = OUT_DIR / f"{domain}.jsonl"
        count = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for row in ds:
                title = row.get("title", "") or ""
                text = row.get("text", "") or ""
                if not matches_domain(title, text, kws):
                    continue
                cleaned = clean_text(text)
                if len(cleaned) < 200:
                    continue
                f.write(json.dumps({
                    "id": row.get("id"),
                    "url": row.get("url"),
                    "title": title,
                    "text": cleaned,
                    "domain": domain,
                }, ensure_ascii=False) + "\n")
                count += 1
        print(f"  {domain}: {count} articles -> {out_path}")

    print("[3/3] Done.")


if __name__ == "__main__":
    main()
