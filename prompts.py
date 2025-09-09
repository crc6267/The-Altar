# This file holds all of the prompts that are used in the LLMs in the state graph

def summarize_themes(book: str, chapter: str, verses: str, user_input: str) -> str:
    return (
        f"""
            You are a summarizer and literary analyzer. Your job is to provide a 3 word summary or analysis of two things - The users statement and the bible verse provided.
            
            The bible summarization will serve as the anchor theme for the rest of this program.
            
            Here is the Bible verse to summarize: {book} {chapter}: \n{verses}
            
            \nHere is the user's input: {user_input}
            
            Please return as a json with the keys "anchor_theme" and "user_theme"
        """
    )