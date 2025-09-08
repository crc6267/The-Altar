import json, os, random, time, textwrap, shutil, pathlib, requests
from langchain_core.messages import AIMessage
from pathlib import Path
from langchain_core.tools import tool
from pydantic import BaseModel
from langchain.tools import StructuredTool

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

@tool()
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

from langchain.tools import Tool

@tool(
    description="This tool is used to select a chapter if the user provides one."
)
def select_chapter(book_name: str, book_chapter: str):
    '''
    Used to select the chapter the user provides from local resources

    Params:
        book_name: str - The name of the book in the Bible the user provides (e.g., "Psalms", "Esther", "James")
        book_chapter: str - The chapter number (as a string or int, e.g., "7", 99, etc.)
    '''
    print("SELECT_CHAPTER CALLED")
    
    # Load local Bible data
    bible = load_bible()

    # Normalize inputs
    book_name_clean = book_name.strip().title()  # e.g. "psalms" → "Psalms"
    book_chapter_clean = str(book_chapter).strip()  # Ensure chapter is a string and strip whitespace

    # Debug prints
    print(f"Normalized book: {book_name_clean}")
    print(f"Normalized chapter: {book_chapter_clean}")
    
    # Check if book and chapter exist
    if book_name_clean in bible:
        if book_chapter_clean in bible[book_name_clean]:
            return {
                "status": "success",
                "tool_result": {
                    "book": book_name_clean,
                    "chapter": book_chapter_clean,
                    "verses": bible[book_name_clean][book_chapter_clean]
                }
            }
        else:
            available_chapters = ', '.join(bible[book_name_clean].keys())
            return {
                "status": "not_found",
                "message": f"Chapter '{book_chapter_clean}' not found in '{book_name_clean}'. Available chapters: {available_chapters}"
            }
    else:
        available_books = ', '.join(bible.keys())
        return {
            "status": "not_found",
            "message": f"Book '{book_name_clean}' not found in Bible data. Check spelling. Available books include: {available_books[:300]}..."
        }

def scripture_exists(book: str, chapter: str) -> bool:
    """Check if a book/chapter exists in the Bible JSON."""
    BIBLE = load_bible()
    return book in BIBLE and chapter in BIBLE[book]
