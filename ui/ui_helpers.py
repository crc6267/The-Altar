import json, os, random, time, textwrap, shutil, pathlib, requests
from ascii_altar import ASCII

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