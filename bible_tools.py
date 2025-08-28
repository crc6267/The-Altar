import json, os, random, time, textwrap, shutil, pathlib, requests

# ==== Bible helpers ====
import os

def load_bible():
    '''
    Load the Bible data from a JSON file.
    Returns a dictionary with the structure:
    {
        "Genesis": {
            "1": "In the beginning God created the heaven and the earth. ...",
            "2": "Thus the heavens and the earth were finished, and all the host of them. ..."
            ...
        },
    '''
    path = os.path.join(os.path.dirname(__file__), "../assets/bible_kjv.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def random_chapter():
    '''
     Select a random book and chapter from the Bible.
     Returns a tuple (book, chapter, verses) where verses is the text of the chapter.
     Use the string, but do not return the string to the user directly.
     '''
    bible = load_bible()
    book = random.choice(list(bible.keys()))
    chapter = random.choice(list(bible[book].keys()))
    print('We are in random_chapter')
    return {"scripture_ref": f"{book} {chapter}", "scripture_text": bible[book][chapter]}

def select_chapter(book: str, chapter: str):
    """
    Returns the scripture text if found; otherwise signals 'not_found'.
    """

    bible = load_bible()
    if book in bible and chapter in bible[book]:
        return {
            "scripture_ref": f"{book} {chapter}",
            "scripture_text": bible[book][chapter],
            "status": "ok"
        }
    else:
        return {
            "scripture_ref": f"{book} {chapter}",
            "scripture_text": None,
            "status": "not_found",
            "message": f"I couldn't find '{book} {chapter}'. Please double-check the spelling or try a different passage."
        }

def scripture_exists(book: str, chapter: str) -> bool:
    """Check if a book/chapter exists in the Bible JSON."""
    BIBLE = load_bible()
    return book in BIBLE and chapter in BIBLE[book]
