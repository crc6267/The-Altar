import json, os, glob

SRC = os.path.join("assets","kjv")
OUT = os.path.join("assets","bible_kjv.json")

def parse_book(obj):
    """
    Expected (your) shape:
    {
      "book": "1 Corinthians",
      "chapters": [
        { "chapter": "1", "verses": [ { "verse":"1","text":"..." }, ... ] },
        ...
      ]
    }
    Returns dict[str chapter] -> str(full chapter text)
    """
    chapters = {}
    if isinstance(obj, dict) and "chapters" in obj:
        for ch in obj["chapters"]:
            c = str(ch.get("chapter"))
            verses = ch.get("verses", [])
            text = " ".join(v.get("text","") for v in verses if isinstance(v, dict))
            chapters[c] = text.strip()
        return obj.get("book",""), chapters

    # Fallbacks (very light)
    if isinstance(obj, list):
        acc = {}
        for row in obj:
            if isinstance(row, dict) and "chapter" in row and "text" in row:
                c = str(row["chapter"]); acc.setdefault(c, []).append(row["text"])
        return None, {c:" ".join(vs) for c,vs in acc.items()}

    if isinstance(obj, dict):
        acc = {}
        for c_key, v_block in obj.items():
            c = str(c_key)
            if isinstance(v_block, dict):
                # dict of verse_no -> text
                try:
                    items = sorted(v_block.items(), key=lambda kv: int(str(kv[0])))
                except Exception:
                    items = v_block.items()
                acc[c] = " ".join(str(t) for _, t in items)
            elif isinstance(v_block, list):
                acc[c] = " ".join(str(t) for t in v_block)
            elif isinstance(v_block, str):
                acc[c] = v_block
        return None, acc

    return None, {}

# Build bundle
bundle = {}
files = [p for p in glob.glob(os.path.join(SRC, "*.json")) if os.path.basename(p).lower() != "books.json"]
if not files:
    raise SystemExit(f"No book JSON files found in {SRC}")

for path in files:
    with open(path, encoding="utf-8") as f:
        obj = json.load(f)
    name, chapters = parse_book(obj)
    if not name:
        # derive name from filename if missing
        base = os.path.splitext(os.path.basename(path))[0]
        name = base
    bundle[name] = chapters

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(bundle, f, ensure_ascii=False)

print(f"Wrote {OUT} with {len(bundle)} books and ~{sum(len(v) for v in bundle.values())} chapters.")
