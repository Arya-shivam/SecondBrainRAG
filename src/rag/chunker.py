import re
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_markdown(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Cleans and splits a markdown string into smaller chunks.
    """
    # 1. Clean up excessive newlines and empty spaces
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 2. Use LangChain's RecursiveCharacterTextSplitter
    # It tries to split on paragraphs first, then sentences, then words.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", "?", "!", " ", ""],
        length_function=len,
    )
    
    chunks = splitter.split_text(text)
    return chunks
