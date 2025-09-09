# This file holds all of the prompts that are used in the LLMs in the state graph


# Used to generate themes for user input and the scripture that is retrieved from the bible tools
# TODO: Need to make this so it can handle summarize both, or just the user input.
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
    
def init_system_prompt() -> str:
    return (
        """
            The user is going to give you a sitation they are struggling with. They will also either provide you with bible verse you ask you to flip to a chapter.
        
            You are only to call and execute the tools that are avaiable to you. Your job is to only call the functions to retrieve a result depending on what the user is asking for.
            
            These tools are random_chapter and select_chapter.
            
            random_chapter does not require any parameters as is used when the user asks for a chapter.
            
            select_chapter requires:
                book_name: str
                book_chapter: str
                
            select chapter is called when the user provides you with scripture.
        """
    )
    