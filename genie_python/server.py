from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import config
from pathlib import Path 
import json

DATA_ROOT = Path(config.DATABASE_DIRECTORY)

app = FastAPI()

# static endpoint for images 
app.mount("/static", StaticFiles(directory=str(DATA_ROOT)), name="static")


@app.get("/books")
def book_overview():
    """
    Returns a list of all available books in the file database.
    Each book is a folder inside DATA_ROOT containing book.json.
    """
    books = []

    if not DATA_ROOT.exists():
        return {"books": []}

    # Jeden Unterordner durchsuchen
    for book_dir in DATA_ROOT.iterdir(): 
        if not book_dir.is_dir():
            continue

        json_file = book_dir / "book.json"
        if not json_file.exists():
            continue

        # JSON lesen
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue  # falls eine Datei kaputt ist

        # Antwort-Objekt erstellen
        books.append({
            "id": data.get("id", None),
            "title": data.get("title", book_dir.name),
            "author": data.get("author"),
            "num_scenes": len(data.get("scenes", [])),
            "cover": data.get("cover", None)
        })

    return {"books": books}


@app.get("/books/{book_id}")
def get_book(book_id: str):
    """
    Gibt ein komplettes Buch zurück:
    - Metadaten
    - alle Szenen
    - pro Szene: Text, Prompt, Bild-URL
    """
    book_dir = DATA_ROOT / book_id

    if not book_dir.exists() or not book_dir.is_dir():
        raise HTTPException(status_code=404, detail="Book not found")

    json_file = book_dir / "book.json"
    if not json_file.exists():
        raise HTTPException(status_code=500, detail="book.json missing")

    with json_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    scenes_out = []
    for scene in data.get("scenes", []):
        image_file = scene.get("image_file")
        image_url = None

        if image_file:
            img_path = book_dir / image_file
            if img_path.exists():
                # URL, unter der FastAPI das Bild ausliefert
                image_url = f"/static/{book_id}/{image_file}"

        scenes_out.append({
            "index": scene.get("index"),
            "text": scene.get("text"),
            "image_prompt": scene.get("image_prompt"),
            "image_file": image_file,
            "image_url": image_url,
        })

    return {
        "id": book_id,
        "title": data.get("title", book_id),
        "author": data.get("author"),
        "source_file": data.get("source_file"),
        "created_at": data.get("created_at"),
        "num_scenes": len(scenes_out),
        "scenes": scenes_out,
    }