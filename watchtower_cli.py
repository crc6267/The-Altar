import json, os, random, time, textwrap, shutil, pathlib, requests
from ascii_altar import ASCII

# ==== Config / Paths ====
BREATH_PATH = pathlib.Path("training/data/breath.txt")
BREATH = BREATH_PATH.read_text(encoding="utf-8").strip() if BREATH_PATH.exists() else ""
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
MODEL = os.environ.get("WATCHTOWER_MODEL", "phi3:mini")  # change to gpt-oss-20b when ready
ASSET = os.path.join("assets", "bible_kjv.json")

# ==== Ollama helpers ====
def have_ollama():
    try:
        requests.get("http://127.0.0.1:11434/", timeout=0.5)
        return True
    except Exception:
        return False

def chat_ollama(user_text, extra_context=None, max_tokens=256, temperature=0.2):
    """
    Sends a chat to Ollama with a system message = BREATH, plus optional context.
    Falls back to simple heuristics if Ollama is unavailable.
    """
    if not have_ollama():
        # Fallback: keep the app usable even without Ollama
        if user_text.strip().lower().startswith("return exactly one line"):
            return "Theme: Contemplation"
        return "In humility: consider the plain sense of the text; test it in prayer (1 Thess 5:21)."

    msgs = [{"role": "system", "content": BREATH}]
    if extra_context:
        msgs.append({"role": "user", "content": extra_context})
    msgs.append({"role": "user", "content": user_text})

    r = requests.post(
        OLLAMA_CHAT_URL,
        json={
            "model": MODEL,
            "messages": msgs,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature}
        },
        timeout=120
    )
    r.raise_for_status()
    data = r.json()
    # Ollama chat returns {"message":{"role":"assistant","content":"..."}}
    return (data.get("message") or {}).get("content", "").strip() or "(no reply)"

# ==== UI helpers ====
def clear():
    os.system("cls" if os.name=="nt" else "clear")
    print(center_text(ASCII))

def boxed(s, width=76):
    lines = [l for t in s.split("\n") for l in textwrap.wrap(t, width)]
    top = "┌" + "─"*width + "┐"
    mid = "\n".join("│"+l.ljust(width)+"│" for l in lines) if lines else "│"+" "*width+"│"
    bot = "└" + "─"*width + "┘"
    return f"{top}\n{mid}\n{bot}"

def wait_timer(seconds):
    for r in range(seconds, -1, -1):
        m, s = divmod(r, 60)
        bar_len = 30
        done = int(bar_len * (seconds-r) / max(1, seconds))
        bar = "■"*done + "·"*(bar_len-done)
        print(f"\r[{bar}] {m:02d}:{s:02d} remaining", end="")
        time.sleep(1)
    print()

def center_text(text: str) -> str:
    width = shutil.get_terminal_size((100, 20)).columns  # fallback 100 cols
    lines = text.splitlines()
    centered = []
    for line in lines:
        pad = max(0, (width - len(line)) // 2)
        centered.append(" " * pad + line)
    return "\n".join(centered)

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

# ==== Session logic ====
THEME_INSTR = (
    "Return exactly ONE line in the form: Theme: <WORD>.\n"
    "Base it ONLY on the chapter text provided.\n"
    "Rules:\n"
    "- Output must be a single line beginning with 'Theme: '.\n"
    "- Do NOT include questions, explanations, blessings, or extra lines.\n"
    "Forbidden tokens: 'Q', 'Answer:', 'Grounding:', '?', '—', '->'."
)

QA_INSTR = (
    "You are in CONSTRAINT MODE.\n"
    "You will receive a single user question and a Bible chapter.\n"
    "Your job is to answer the user's question based ONLY on THIS chapter.\n\n"
    "OUTPUT FORMAT (exactly two lines, no extras):\n"
    "Answer: <ONE WORD or SHORT PHRASE>\n"
    "Grounding: \"<ONE short, verbatim quote from THIS chapter>\"\n\n"
    "Hard Rules:\n"
    "- Never generate or restate any question (no lines starting with 'Q', 'Question:', etc.).\n"
    "- No first-person (no 'I', 'me', 'my').\n"
    "- Stay strictly inside THIS chapter.\n"
    "- No explanations, headings, bullet points, emojis, or extra whitespace.\n"
    "- If you cannot find an exact short quote, choose the shortest accurate phrase from THIS chapter and put it in double quotes.\n\n"
    "Positive example (structure only):\n"
    "Answer: Holiness Imperative\n"
    "Grounding: \"They shall be holy unto their God\"\n\n"
    "Negative examples (never do these):\n"
    "Q3: How does this apply to modern life?\n"
    "Answer: ...\n"
    "Grounding: ...\n"
    "(Any output that includes a 'Q' line, extra lines, commentary, or verses outside the chapter.)\n"
)

def get_theme(book, chapter, chapter_text):
    ctx = f"Selected: {book} {chapter}\n\nCHAPTER:\n{chapter_text}"
    out = chat_ollama(
        THEME_INSTR,
        extra_context=ctx,
        max_tokens=10,       # enough room for "Theme: <WORD>"
        temperature=0.2      # low, keeps it stable
    )
    for ln in out.splitlines():
        if ln.lower().startswith("theme:"):
            return ln.strip()
    return "Theme: Contemplation"

def answer_q(qnum, book, chapter, chapter_text, question, recent=None):
    ctx = f"{QA_INSTR}\n\nSelected: {book} {chapter}\n\nCHAPTER:\n{chapter_text}"
    if recent:
        ctx += f"\n\nRecent:\n{recent}"
    return chat_ollama(
        f"Q{qnum}: {question}\nA{qnum}:",
        extra_context=ctx,
        max_tokens=2787,       # enough for one short sentence + grounding
        temperature=0.3      # low but not zero
    )

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
    wait_timer(10)  # 3 minutes

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

    # === THEME (via Breath) ===
    theme = get_theme(book, chapter, text)
    print("\n" + boxed(theme) + "\n")

    # === 20 Q&A ===
    log = [f"# Watchtower Session\n\n**Selected:** {book} {chapter}\n\n**{theme}**\n"]
    q_count = 0
    while q_count < 20:
        q = input(f"Q{q_count+1}: ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        recent = "\n".join(log[-4:])
        a = answer_q(q_count+1, book, chapter, text, q, recent=recent)
        print(f"\nA{q_count+1}: {a}\n")
        log.append(f"**Q{q_count+1}:** {q}\n\n**A{q_count+1}:** {a}\n")
        q_count += 1

    input("\nPress Enter to end session…")
    print("\n— Release. —")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGrace and peace.")
