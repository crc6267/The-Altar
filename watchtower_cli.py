from bible.bible_helpers import *
from ui.ui_helpers import *

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

    input("\nPress Enter to end session…")
    print("\n— Release. —")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGrace and peace.")
