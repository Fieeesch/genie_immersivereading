import json
import sys
from datetime import datetime
from pathlib import Path

from modules import panorama_generator as PG
from modules import scene_deconstructor as SD
import config


DATA_ROOT = Path(config.DATABASE_DIRECTORY)

def generate_vrbook(book_path: Path, book_name: str, author=None, prompts_only=False):
    # --- Prepare target directory ---
    vrbook_id = book_path.stem
    vrbook_dir = DATA_ROOT / vrbook_id
    vrbook_dir.mkdir(parents=True, exist_ok=True)

    print(f"Importing book: {book_path}")
    print(f"Output folder: {vrbook_dir}")

    # --- 1. Text Splitting ---
    print("Splitting book into scenes...")
    splitter = SD.SceneSplitterGPT()
    scenes = splitter.split_book(str(book_path))

    # --- 2. Prompt Generation ---
    print("Generating prompts...")
    prompter = SD.PromptGeneratorGPT()
    prompts = prompter.generate_prompts(scenes)

    # --- 3. Image Generation ---
    if not prompts_only:
        print("Generating panorama images...")
        pano_gen = PG.PanoramaGenerator(DATA_ROOT)

    scene_entries = []

    for i, (scene_text, prompt) in enumerate(zip(scenes, prompts)):
        img_filepath = f"{vrbook_id}/scene_{i}.png"

        if not prompts_only:
            # generate 360° image
            pano_gen.generate_360_panorama(prompt, "", img_filepath)

        # create scene entry
        scene_entries.append({
            "index": i,
            "text": scene_text,
            "image_prompt": prompt,
            "image_file": img_filepath
        })

    # --- 4. Write Book-JSON to Database ---
    vrbook_json = {
        "id": vrbook_id,
        "title": book_name,
        "author": None,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scenes": scene_entries
    }

    with (vrbook_dir / "book.json").open("w", encoding="utf-8") as f:
        json.dump(vrbook_json, f, ensure_ascii=False, indent=2)

    print("\nDone!")
    print(f"Book imported to: {vrbook_dir}")

def regenerate_vrbook_images(book_id: str):
    print("Regenerating panorama images...")
    pano_gen = PG.PanoramaGenerator(DATA_ROOT)
    pano_gen.regenerate_360_panoramas(book_id)
    print("Done!")


def main():
    args = sys.argv[1:]

    # ------------------------------------------------------------
    # Mode 1: generate VR book from text file
    # Usage: python generate_vrbook.py <path-to-book-file.txt> <book-title>
    # ------------------------------------------------------------
    if len(args) >= 2 and not args[0].startswith("-"):
        book_path = Path(args[0])
        book_title = args[1]

        if not book_path.exists():
            print(f"Error: file not found: {book_path}")
            sys.exit(1)

        author = None
        if len(args) == 3:
            author = args[2]

        generate_vrbook(book_path, book_title, author)
        return

    # ------------------------------------------------------------
    # Mode 2: generate only image prompts
    # Usage: python generate_vrbook.py --prompts-only <path-to-book-file.txt> <book-title>
    # ------------------------------------------------------------
    if len(args) == 3 and args[0] == "--prompts-only":
        book_path = Path(args[1])
        book_title = args[2]

        if not book_path.exists():
            print(f"Error: file not found: {book_path}")
            sys.exit(1)

        author = None
        if len(args) == 3:
            author = args[2]

        generate_vrbook(book_path, book_title, author, prompts_only=True)
        return

    # ------------------------------------------------------------
    # Mode 3: regenerate images for existing VR book
    # Usage: python generate_vrbook.py --regenerate-imgs <book-id>
    # ------------------------------------------------------------
    if len(args) == 2 and args[0] == "--regenerate-imgs":
        book_id = args[1]
        regenerate_vrbook_images(book_id)
        return

    # ------------------------------------------------------------
    # Ungültige Aufrufe
    # ------------------------------------------------------------
    print("Usage:")
    print("  Generate VR book from text file:")
    print("     python generate_vrbook.py <path-to-book-file.txt> <book-title> [<author>]")
    print("")
    print("  Regenerate images for existing VR book:")
    print("     python generate_vrbook.py --regenerate-imgs <book-id>")
    print("")
    print("  Generate only prompts (no images):")
    print("     python generate_vrbook.py --prompts-only <path-to-book-file.txt> <book-title> [<author>]")
    sys.exit(1)


if __name__ == "__main__":
    main()
