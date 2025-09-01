from pathlib import Path
import os

# Global cache for books from text file
_books_cache = {}
_cache_loaded = False


def _get_books_file_path():
    """Get the path to the book summaries text file"""
    # Find the project root
    project_root = Path(__file__).parent.parent.parent
    return project_root / "data" / "book_summaries.txt"


def _load_books_from_file():
    """Load all books from data/book_summaries.txt into cache"""
    global _books_cache, _cache_loaded

    if _cache_loaded:
        return _books_cache

    try:
        books_file = _get_books_file_path()

        if not books_file.exists():
            print(f"Books file not found at {books_file}")
            _cache_loaded = True
            return _books_cache

        with open(books_file, 'r', encoding='utf-8') as file:
            content = file.read()

        # Parse the text file
        books = content.split('## Title:')[1:]  # Skip empty first element

        for book in books:
            lines = book.strip().split('\n')
            if lines:
                title = lines[0].strip()
                summary = '\n'.join(lines[1:]).strip()
                _books_cache[title] = summary

        print(f"Loaded {len(_books_cache)} books from {books_file}")
        _cache_loaded = True

    except Exception as e:
        print(f"Error loading books from file: {e}")
        _cache_loaded = True

    return _books_cache


def get_summary_by_title(title: str) -> str:
    """
    Get the full detailed summary for a book by its exact title.

    Args:
        title (str): The exact title of the book

    Returns:
        str: The detailed summary of the book, or a message if not found
    """
    books = _load_books_from_file()

    if title in books:
        return books[title]
    else:
        available_titles = list(books.keys())[:5]  # Show first 5 titles as suggestions
        suggestion_text = f" Available books include: {', '.join(available_titles)}..." if available_titles else ""
        return f"Sorry, I don't have a detailed summary for '{title}'. Please check the title spelling or ask for a different book.{suggestion_text}"


def get_all_book_titles() -> list:
    """
    Get a list of all available book titles.

    Returns:
        list: List of all book titles in the database
    """
    books = _load_books_from_file()
    return list(books.keys())


def reload_books_cache():
    """
    Reload the books cache
    """
    global _cache_loaded, _books_cache
    _cache_loaded = False
    _books_cache.clear()
    _load_books_from_file()
    print(f"Reloaded cache: {len(_books_cache)} books available")


def get_books_count() -> int:
    """
    Get the total number of books in the database

    Returns:
        int: Number of books available
    """
    books = _load_books_from_file()
    return len(books)


def get_books_file_info() -> dict:
    """
    Get information about the books file

    Returns:
        dict: File information including path, size, and book count
    """
    books_file = _get_books_file_path()
    books = _load_books_from_file()

    info = {
        'file_path': str(books_file.absolute()),
        'file_exists': books_file.exists(),
        'book_count': len(books),
        'file_size_bytes': books_file.stat().st_size if books_file.exists() else 0
    }

    return info


def add_book_to_file(title: str, summary: str):
    """
    Add a new book to the text file

    Args:
        title (str): Book title
        summary (str): Book summary
    """
    books_file = _get_books_file_path()

    # Ensure the summary ends with themes if not already present
    if "Main themes:" not in summary:
        summary += "\nMain themes: [Add themes here]"

    # Append to file
    with open(books_file, 'a', encoding='utf-8') as f:
        f.write(f"\n## Title: {title}\n{summary}\n")

    # Reload cache
    reload_books_cache()

    print(f"Added '{title}' to the database")


# Function to load book summaries from the text file for vector storage
def load_book_summaries_for_vectorization(file_path: str) -> list:
    """
    Load book summaries from text file and parse them for vector storage.

    Args:
        file_path (str): Path to the book summaries text file

    Returns:
        list: List of dictionaries containing title and summary
    """
    summaries = []

    try:
        # Handle both relative and absolute paths
        file_path_obj = Path(file_path)

        # If it's a relative path, make it relative to the project root
        if not file_path_obj.is_absolute():
            # Find the project root
            project_root = Path(__file__).parent.parent.parent
            file_path_obj = project_root / file_path

        # Debug: Print the resolved path
        print(f"Loading book summaries from: {file_path_obj.absolute()}")
        print(f"File exists: {file_path_obj.exists()}")

        if not file_path_obj.exists():
            print(f"Error: File not found at {file_path_obj}")
            print("Run 'python migrate_to_single_source.py' to create the file")
            return summaries

        with open(file_path_obj, 'r', encoding='utf-8') as file:
            content = file.read()

        # Split by "## Title:" to separate books
        books = content.split('## Title:')[1:]  # Skip empty first element

        for book in books:
            lines = book.strip().split('\n')
            if lines:
                title = lines[0].strip()
                summary = '\n'.join(lines[1:]).strip()

                summaries.append({
                    'title': title,
                    'summary': summary,
                    'content': f"Title: {title}\n{summary}"  # Combined content for embedding
                })

        print(f"Successfully loaded {len(summaries)} books from file")

    except FileNotFoundError:
        print(f"Error: Could not find the file {file_path}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Attempted path: {file_path_obj if 'file_path_obj' in locals() else file_path}")
        print("Run 'python migrate_to_single_source.py' to create the file")
    except Exception as e:
        print(f"Error loading book summaries: {e}")

    return summaries