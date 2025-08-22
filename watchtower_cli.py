import json, os, random, time, textwrap, shutil, pathlib, requests
from ui.ui_helpers import *

ASSET = os.path.join("assets", "bible_kjv.json")

# ==== Bible helpers ====
def load_bible():
    with open(ASSET, encoding="utf-8") as f:
        return json.load(f)

def random_chapter(bible):
    book = random.choice(list(bible.keys()))
    chapter = random.choice(list(bible[book].keys()))
    return book, chapter, bible[book][chapter]

def chapter_text_from(verses):
    # handle dict of verse_no -> text, or raw string
    if isinstance(verses, dict):
        ordered_keys = sorted(verses, key=lambda x: int(x) if str(x).isdigit() else str(x))
        return "\n".join(f"{v}. {verses[v]}" for v in ordered_keys)
    return str(verses)

def main():
    clear()
    input("\nPress Enter to continue...")
    clear()
    print(boxed('Habakkuk 2:1 — "I will stand upon my watch..."'))
    if input("\nEnter watchtower? (y/n): ").strip().lower() != "y":
        return

    clear()
    print(boxed("Enter into prayer: Repent → Submit → Petition\n"))
    if input("\nBegin (y/n): ").strip().lower() != "y":
        return
    print("\n🕯️ 3-minute consecration timer starting…")
    time.sleep(1)
    wait_timer(0)  # 3 minutes

    clear()
    print(boxed('Proverbs 16:33 — "The lot is cast into the lap, but the whole disposing thereof is of the LORD."'))
    input("\nPress Enter to “flip” (random Book & Chapter)… ")

    bible = load_bible()
    book, chapter, verses = random_chapter(bible)
    text = chapter_text_from(verses)

    clear()
    print(boxed('Matthew 18:20 — "For where two or three are gathered together in my name, there am I in the midst of them."'))
    print(f"\nSelected: {book} {chapter}\n")
    print(text[:4000] + ("..." if len(text) > 4000 else ""))

    # === 20 Q&A ===
    # log = [f"# Watchtower Session\n\n**Selected:** {book} {chapter}\n\n**{theme}**\n"]
    # q_count = 0
    # while q_count < 20:
    #     q = input(f"Q{q_count+1}: ").strip()
    #     if q.lower() in {"exit", "quit"}:
    #         break
    #     recent = "\n".join(log[-4:])
    #     a = answer_q(q_count+1, book, chapter, text, q, recent=recent)
    #     print(f"\nA{q_count+1}: {a}\n")
    #     log.append(f"**Q{q_count+1}:** {q}\n\n**A{q_count+1}:** {a}\n")
    #     q_count += 1

    input("\nPress Enter to end session…")
    print("\n— Release. —")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGrace and peace.")
