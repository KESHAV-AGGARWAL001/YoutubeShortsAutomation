import os
import json
from fastapi import APIRouter
from server.models.schemas import BookInfo
from server.services.state import PROJECT_ROOT

router = APIRouter()


@router.get("/books")
async def list_books():
    books_dir = os.path.join(PROJECT_ROOT, "books")
    if not os.path.exists(books_dir):
        return {"books": [], "current_book": None}

    progress_file = os.path.join(books_dir, "progress.json")
    progress = {}
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            progress = json.load(f)

    book_files = sorted([f for f in os.listdir(books_dir) if f.endswith(".pdf")])
    books = []

    for filename in book_files:
        display_name = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
        total_pages = 0
        try:
            import PyPDF2
            with open(os.path.join(books_dir, filename), "rb") as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
        except Exception:
            pass

        current_page = 0
        end_page = -1
        if progress.get("current_book") == filename:
            current_page = progress.get("current_page", 0)
            end_page = progress.get("end_page", -1)

        books.append(BookInfo(
            filename=filename,
            display_name=display_name,
            total_pages=total_pages,
            current_page=current_page,
            end_page=end_page,
        ))

    return {
        "books": [b.model_dump() for b in books],
        "current_book": progress.get("current_book"),
    }
