import json, os, random, time, textwrap, shutil, pathlib, requests

# ==== Bible helpers ====
import os

def load_bible():
    path = os.path.join(os.path.dirname(__file__), "../assets/bible_kjv.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def random_chapter(bible):
    book = random.choice(list(bible.keys()))
    chapter = random.choice(list(bible[book].keys()))
    print('We are in random_chapter')
    return book, chapter, bible[book][chapter]

def chapter_text_from(verses):
    # handle dict of verse_no -> text, or raw string
    if isinstance(verses, dict):
        ordered_keys = sorted(verses, key=lambda x: int(x) if str(x).isdigit() else str(x))
        return "\n".join(f"{v}. {verses[v]}" for v in ordered_keys)
    print('We are in chapter_text_from else')
    return str(verses)