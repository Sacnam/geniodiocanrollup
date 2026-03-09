from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List
import os
import shutil

from database import engine, init_db, get_session
from models import Feed, Article, Book
from rss_engine import sync_feed
from book_engine import extract_epub_content, get_epub_metadata
from search import create_fts_tables, index_item, search as search_func

app = FastAPI(title="Genio Lite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    create_fts_tables()

@app.get("/health")
def health():
    return {"status": "ok", "version": "lite"}

# RSS Feeds
@app.post("/feeds/", response_model=Feed)
def create_feed(feed: Feed, session: Session = Depends(get_session)):
    session.add(feed)
    session.commit()
    session.refresh(feed)
    sync_feed(session, feed.id)
    # Sync index all articles
    articles = session.exec(select(Article).where(Article.feed_id == feed.id)).all()
    for art in articles:
        index_item(art.id, "article", art.title, art.content)
    return feed

@app.get("/feeds/", response_model=List[Feed])
def list_feeds(session: Session = Depends(get_session)):
    return session.exec(select(Feed)).all()

# Articles
@app.get("/articles/", response_model=List[Article])
def list_articles(session: Session = Depends(get_session)):
    return session.exec(select(Article)).all()

# Search
@app.get("/search/")
def search_endpoint(q: str):
    return search_func(q)

# Books
@app.post("/books/")
async def upload_book(file: UploadFile = File(...), session: Session = Depends(get_session)):
    os.makedirs("books", exist_ok=True)
    file_path = os.path.join("books", file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    title, author = get_epub_metadata(file_path)
    content = extract_epub_content(file_path)
    
    book = Book(title=title, author=author, file_path=file_path, content=content)
    session.add(book)
    session.commit()
    session.refresh(book)
    
    # Index for search
    index_item(book.id, "book", book.title, book.content)
    return book

@app.get("/books/", response_model=List[Book])
def list_books(session: Session = Depends(get_session)):
    return session.exec(select(Book)).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
