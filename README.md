# Parser planu WSB

Narzędzie do:

- przetwarzania lokalnego pliku JSON z planem,
- pobierania planów prowadzących z API Meritogo,
- eksportu planu do `CSV`, `ICS` i `HTML`,
- sprawdzania planu grupy w wybranym dniu,
- sprawdzania zajętości sali w wybranym dniu.

## Instalacja

```bash
pip install -r requirements.txt
```

## Konfiguracja `.env`

Aplikacja potrzebuje dwóch tokenów, żeby utworzyć obiekt `API`.

Utwórz plik `.env` w katalogu projektu:

```dotenv
CONTEXT_ID=twoj_context_id
BEARER_TOKEN="Bearer twoj_token"
```

### Jak pozyskać tokeny

Po zalogowaniu na `https://meritogo.pl`:

1. otwórz narzędzia developerskie przeglądarki,
2. przejdź do zakładki **Network**,
3. wybierz dowolny request do `api.meritogo.pl`,
4. w zakładce **Headers** odczytaj:
   - `context-id` → wpisz do `CONTEXT_ID`,
   - `authorization` → wpisz całą wartość do `BEARER_TOKEN` razem z prefiksem `Bearer`.

Uwaga: token `authorization` może wygasnąć. W takim przypadku trzeba pobrać go ponownie.

## Uruchomienie

Uruchomienie bez argumentów pokazuje pomoc:

```bash
python main.py
```

Pomoc można też wyświetlić jawnie:

```bash
python main.py --help
```

## Tryby działania CLI

### 1. Przetwarzanie lokalnego pliku JSON

```bash
python main.py --file plan.json
```

Generowane pliki trafiają do katalogu `output/`:

- `*.csv`
- `*.ics`
- `*.html`

### 2. Lista prowadzących

```bash
python main.py --list-lecturers
```

### 3. Pobranie planu jednego prowadzącego

```bash
python main.py --lecturer "Imię Nazwisko"
```

Z opcjonalnym zakresem dat:

```bash
python main.py --lecturer "Imię Nazwisko" --dstart 2026-05-01 --dend 2026-05-31
```

### 4. Pobranie planu wielu prowadzących z pliku

```bash
python main.py --lecturers file.txt
```

Plik `file.txt` powinien zawierać po jednym prowadzącym w każdej linii, np.:

```text
Jan Kowalski
Anna Nowak
```

### 5. Sprawdzenie planu grupy

```bash
python main.py --group "Nazwa Grupy"
```

Domyślnie używana jest dzisiejsza data.

Z podaniem konkretnego dnia:

```bash
python main.py --group "Nazwa Grupy" --date 2026-05-23
```

Z przygotowaniem cache na szerszy zakres dat:

```bash
python main.py --group "Nazwa Grupy" --date 2026-05-23 --dstart 2026-05-20 --dend 2026-05-31
```

Wynik jest wypisywany w formie tabeli w terminalu.

### 6. Sprawdzenie zajętości sali

```bash
python main.py --room "ŚN 7"
```

Domyślnie używana jest dzisiejsza data.

Z podaniem konkretnego dnia:

```bash
python main.py --room "ŚN 7" --date 2026-05-23
```

Z przygotowaniem cache na szerszy zakres dat:

```bash
python main.py --room "ŚN 7" --date 2026-05-23 --dstart 2026-05-20 --dend 2026-05-31
```

Jeżeli w danym dniu nie ma żadnych zajęć w tej sali, program wypisze informację, że sala jest wolna.

## Cache i `--refresh`

Odpowiedzi API są zapisywane w katalogu `json/`.

### Lista prowadzących

- lista prowadzących jest cache’owana w `json/lecturers.json`,
- jeśli plik istnieje, program użyje go ponownie,
- przy pobraniu z cache pojawia się komunikat informujący o użyciu lokalnego pliku.

### Tryby `--group` i `--room`

W tych trybach program sprawdza plany wszystkich prowadzących po kolei.

Zachowanie cache:

- jeśli istnieje cache pokrywający wybraną datę lub żądany zakres, program użyje go bez pobierania danych ponownie,
- jeśli cache nie pokrywa potrzebnego zakresu, program pobierze brakujące dane z API,
- jeśli podasz `--refresh`, dane zostaną pobrane ponownie niezależnie od istniejącego cache.

Przykład:

- istnieje cache od `2026-05-01` do `2026-07-31`,
- uruchamiasz `--group` albo `--room` dla daty `2026-06-15`,
- program użyje istniejącego cache i nie pobierze danych od nowa.

### Wymuszenie ponownego pobrania

```bash
python main.py --group "Nazwa Grupy" --date 2026-05-23 --refresh
python main.py --room "ŚN 7" --date 2026-05-23 --refresh
python main.py --lecturer "Imię Nazwisko" --refresh
```

## Najważniejsze przełączniki

- `--file PATH` – przetworzenie lokalnego pliku JSON,
- `--list-lecturers` – wypisanie wszystkich prowadzących,
- `--lecturer "Imię Nazwisko"` – pobranie planu jednego prowadzącego,
- `--lecturers file.txt` – pobranie planów prowadzących z pliku,
- `--group "Nazwa Grupy"` – sprawdzenie planu grupy na wybrany dzień,
- `--room "ŚN 7"` – sprawdzenie zajętości sali na wybrany dzień,
- `--date YYYY-MM-DD` – dzień używany z `--group` albo `--room`,
- `--dstart YYYY-MM-DD` – początek zakresu pobierania/cache,
- `--dend YYYY-MM-DD` – koniec zakresu pobierania/cache,
- `--refresh` – wymuszenie ponownego pobrania danych z API.

## Struktura projektu

- `main.py` — główne CLI oparte o `argparse`,
- `wsbparser/api.py` — komunikacja z API Meritogo i obsługa cache,
- `wsbparser/schedule.py` — parsowanie planu i eksport do `CSV` / `ICS` / `HTML`,
- `wsbparser/event.py` — model pojedynczych zajęć,
- `wsbparser/group_schedule.py` — logika sprawdzania planu grupy,
- `wsbparser/room_schedule.py` — logika sprawdzania zajętości sal,
- `json/` — lokalny cache danych z API,
- `output/` — wygenerowane pliki wynikowe.
