import json, os, random, time, textwrap, shutil, pathlib, requests
from langchain_core.messages import AIMessage
from pathlib import Path

# ==== Bible helpers ====
import os

def load_bible():
    """
    Load the Bible JSON file, dynamically locating the project root by traversing upward.
    """
    # Start from current file's path
    current_path = Path(__file__).resolve()

    # Traverse upward to find the 'assets/bible_kjv.json'
    for parent in current_path.parents:
        candidate = parent / "assets" / "bible_kjv.json"
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                return json.load(f)

    # If we exhaust all options and can't find it
    raise FileNotFoundError("📁 Could not locate 'assets/bible_kjv.json' in any parent directory.")

def random_chapter():
    '''
    Selects a random book and chapter from the Bible.
    Returns a state update including:
    - An AIMessage for model continuity
    - A tool_result for verification
    '''
    bible = load_bible()
    book = random.choice(list(bible.keys()))
    chapter = random.choice(list(bible[book].keys()))
    verses = bible[book][chapter]
    
    print("\n\n R A N D O M  C H A P T E R  C A L L E D")

    payload = {
        "status": "success",
        "tool_result": {"book": book, "chapter": chapter, "verses": verses}
    }
    # IMPORTANT: return JSON string; ToolMessage.content will be this string
    return payload

def select_chapter(book: str, chapter: str):
    """
    Returns the scripture text if found; otherwise signals 'not_found'.
    """

    print("\n\n S E L E C T  C H A P T E R  C A L L E D")
    
    bible = load_bible()
    if book in bible and chapter in bible[book]:
        return {
            "status": "success",
            "tool_result": {"book": book, "chapter": chapter, "verses": bible[book][chapter]}
        }
    else:
        return {
            "status": "not_found",
            "message": f"I couldn't find '{book} {chapter}'. Please double-check the spelling or try a different passage."
        }
    

def scripture_exists(book: str, chapter: str) -> bool:
    """Check if a book/chapter exists in the Bible JSON."""
    BIBLE = load_bible()
    return book in BIBLE and chapter in BIBLE[book]
