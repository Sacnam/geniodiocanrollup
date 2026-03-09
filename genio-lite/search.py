from sqlmodel import Session, text
from database import engine

def create_fts_tables():
    with Session(engine) as session:
        # Create FTS5 tables for search
        session.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS search_idx USING fts5(title, content, type, original_id);"))
        session.commit()

def search(query: str):
    with Session(engine) as session:
        statement = text("SELECT original_id, type, title FROM search_idx WHERE search_idx MATCH :query ORDER BY rank;")
        results = session.execute(statement, {"query": query}).all()
        return results

def index_item(original_id: int, item_type: str, title: str, content: str):
    with Session(engine) as session:
        # Remove old if exists
        session.execute(text("DELETE FROM search_idx WHERE original_id = :id AND type = :type"), {"id": original_id, "type": item_type})
        # Insert new
        session.execute(text("INSERT INTO search_idx (title, content, type, original_id) VALUES (:title, :content, :type, :id)"), 
                        {"title": title, "content": content, "type": item_type, "id": original_id})
        session.commit()
