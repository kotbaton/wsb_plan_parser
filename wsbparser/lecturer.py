import unicodedata
import re


def sanitize_to_ascii(text: str, allow_basic_punctuation: bool = True) -> str:
    # normalizacja (np. ą → a + ogonek)
    normalized = unicodedata.normalize("NFKD", text)

    # usunięcie znaków diakrytycznych
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    # opcjonalne czyszczenie z dziwnych znaków
    if allow_basic_punctuation:
        ascii_text = re.sub(r"[^a-zA-Z0-9\-_. ]", "", ascii_text)
    else:
        ascii_text = re.sub(r"[^a-zA-Z0-9]", "", ascii_text)

    # redukcja wielu spacji
    ascii_text = re.sub(r"\s+", " ", ascii_text).strip()

    return ascii_text


class Lecturer:
    def __init__(self, data: dict):
        self.name = data["name"]
        self.surname = data["surname"]
        self.userId = data["userId"]
        self.lecturerId = data["lecturerId"]
        self.personId = data["personId"]

    def __str__(self):
        return f"{self.lecturerId} {self.name} {self.surname}"

    def login(self):
        base_login = f"{self.name}_{self.surname}".lower()
        sanitized_login = sanitize_to_ascii(base_login)
        return sanitized_login

    def full_name(self):
        return f"{self.name} {self.surname}"