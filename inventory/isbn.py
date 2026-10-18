"""ISBN validation and book lookup (FR-02, NFR-13).

"""

import requests


HEADERS = {"User-Agent": "BookLoop/0.1 (student project, African Leadership University)"}
TIMEOUT_SECONDS = 5


def clean_isbn(raw):
    """Remove spaces and hyphens: '978-0-14-032872-1' -> '9780140328721'."""
    return raw.replace("-", "").replace(" ", "").strip().upper()


def is_valid_isbn13(isbn):
    if len(isbn) != 13 or not isbn.isdigit():
        return False
    if not isbn.startswith(("978", "979")):
        return False

    total = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(isbn))
    return total % 10 == 0


def is_valid_isbn10(isbn):
    if len(isbn) != 10:
        return False
    if not isbn[:9].isdigit() or not (isbn[9].isdigit() or isbn[9] == "X"):
        return False
        
    total = 0
    for i, char in enumerate(isbn):
        value = 10 if char == "X" else int(char)
        total += value * (10 - i)
    return total % 11 == 0


def isbn10_to_isbn13(isbn10):
    """Convert an old 10-digit ISBN to the modern 13-digit form."""
    core = "978" + isbn10[:9]
    total = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(core))
    check_digit = (10 - total % 10) % 10
    return core + str(check_digit)


def normalise_isbn(raw):
    """Return a valid 13-digit ISBN, or None if the input isn't a valid ISBN."""
    isbn = clean_isbn(raw)
    if is_valid_isbn13(isbn):
        return isbn
    if is_valid_isbn10(isbn):
        return isbn10_to_isbn13(isbn)
    return None


def lookup_open_library(isbn):
    url = "https://openlibrary.org/api/books"
    params = {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"}
    response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json().get(f"ISBN:{isbn}")
    if not data:
        return None
    return {
        "title": data.get("title", ""),
        "author": ", ".join(a["name"] for a in data.get("authors", [])),
        "publisher": ", ".join(p["name"] for p in data.get("publishers", [])),
        "source": "Open Library",
    }


def lookup_google_books(isbn):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"isbn:{isbn}"}
    response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    items = response.json().get("items")
    if not items:
        return None
    info = items[0].get("volumeInfo", {})
    return {
        "title": info.get("title", ""),
        "author": ", ".join(info.get("authors", [])),
        "publisher": info.get("publisher", ""),
        "source": "Google Books",
    }


def lookup_isbn(raw):
    """Look up a book by ISBN.

    Returns a dictionary with isbn, title, author, publisher and source,
    or None if the ISBN is invalid or no service recognises it.
    """
    isbn = normalise_isbn(raw)
    if isbn is None:
        return None

    for lookup in (lookup_open_library, lookup_google_books):
        try:
            result = lookup(isbn)
        except requests.RequestException:
            # Service down or slow: try the next one.
            continue
        if result:
            result["isbn"] = isbn
            return result
    return None