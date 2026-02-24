# Parser planu WSB

Program służy do przetwarzania pliku JSON z planem zajęć oraz (w kolejnych krokach) do pobierania danych z API Meritogo.

Aktualnie narzędzie potrafi wygenerować:

- `output/plan.csv` – plan w formacie do Excela
- `output/plan.ics` – kalendarz do importu (Google Calendar, Outlook itp.)
- `output/groups.html` – raport godzin dla Moodle (z podsumowaniem godzin)

## Instalacja

1. Sklonuj repozytorium:

```bash
git clone https://github.com/kotbaton/wsb_plan_parser.git
```

2. Wejdź do katalogu projektu i zainstaluj zależności:

```bash
pip install -r requirements.txt
```

## Konfiguracja tokenów API (.env)

Aplikacja wymaga tokenów, żeby utworzyć obiekt `API`.

1. Utwórz plik `.env` w katalogu projektu:

```dotenv
CONTEXT_ID=twoj_context_id
BEARER_TOKEN="Bearer twoj_token"
```

2. Jak zdobyć tokeny z `meritogo.pl` (po zalogowaniu):

- Otwórz `https://meritogo.pl` i zaloguj się.
- Otwórz narzędzia developerskie (DevTools) → zakładka **Network**.
- Znajdź zapytanie (request) do API (zwykle `GET`) – praktycznie dowolne, które idzie do `api.meritogo.pl`.
- Kliknij request i wejdź w **Headers**.
- Skopiuj wartości:
  - `context-id: ...` → wklej do `CONTEXT_ID`
  - `authorization: Bearer ...` → wklej CAŁĄ wartość (razem z `Bearer`) do `BEARER_TOKEN`

Uwaga: token `authorization` jest tymczasowy i może wygasnąć – wtedy trzeba pobrać nowy.

## Jak użyć programu (CLI)

Program używa `argparse`.

- Uruchomienie bez argumentów wyświetla pomoc:

```bash
python main.py
```

- Przetworzenie lokalnego pliku JSON (działa jak dawniej, ale teraz przez `--file`):

```bash
python main.py --file plan.json
```

### Przełączniki

- `--list-lecturers` – wyświetla dostępnych prowadzących i kończy działanie
- `--lecturer "Imię Nazwisko"` – plan dla konkretnego prowadzącego
- `--lecturers file.txt` – plan dla prowadzących z pliku
- `--dstart YYYY-MM-DD` / `--dend YYYY-MM-DD` – opcjonalny zakres dat (używany z opcjami powyżej)

## Struktura projektu

- `main.py` — CLI (argparse), wczytanie `.env`, utworzenie `API`, eksport plików.
- `wsbparser/schedule.py` — parsowanie pliku JSON i eksport do CSV/ICS/HTML.
- `wsbparser/event.py` — model pojedynczych zajęć i generowanie wpisów CSV/ICS.
- `wsbparser/api.py` — komunikacja z API Meritogo + cache odpowiedzi (np. `json/lecturers.json`).
