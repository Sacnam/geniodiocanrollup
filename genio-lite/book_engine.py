import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def extract_epub_content(file_path: str) -> str:
    book = epub.read_epub(file_path)
    content = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            content.append(soup.get_text())
    return "\n".join(content)

def get_epub_metadata(file_path: str):
    book = epub.read_epub(file_path)
    title = book.get_metadata('DC', 'title') or "Unknown Title"
    author = book.get_metadata('DC', 'creator') or "Unknown Author"
    
    if isinstance(title, list): title = title[0][0] if title else "Unknown Title"
    if isinstance(author, list): author = author[0][0] if author else "Unknown Author"
    
    return str(title), str(author)
