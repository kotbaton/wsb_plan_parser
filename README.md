# Parser planu WSB

## Generator planu zajęć (CSV / ICS / HTML)

Program służy do przetwarzania pliku `plan.json` (wyeksportowanego z Merito/WSB) i automatycznego wygenerowania:

- 📄 `plan.csv` – plan w formacie do Excela
- 📅 `plan.ics` – kalendarz do importu (Google Calendar, Outlook itp.)
- 📊 `grupy.html` – raport godzin dla Moodle (z podsumowaniem godzin)

---

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/kotbaton/wsb_plan_parser.git
````

2. Przejdź do katalogu projektu:
```bash
cd nazwa_repozytorium
```

## Jak użyć programu

1. Umieść plik `plan.json` w tym samym folderze co skrypt. Na końcu pliku README znajdziesz instrukcję, jak wyeksportować plan z Merito/WSB.
2. Uruchom program:
    ```bash
    python main.py
    ```
   lub, jeżeli masz plik o innej nazwie:
    ```bash
    python main.py sciezka/do/plik.json
    ```
3. Po zakończeniu działania w folderze `output/` w katalogu projektu pojawią się pliki:
- `plan.csv`
- `plan.ics`
- `grupy.html`

Skrypt sprawdza, czy katalog `output` istnieje i w razie potrzeby go tworzy.

---

## Opis programu

Krótki opis głównych plików w repozytorium:

- `main.py` — główny skrypt uruchamiający program: parsuje argument CLI (opcjonalna ścieżka do pliku JSON), tworzy katalog `output` jeśli trzeba i wywołuje kolejne kroki (wczytanie planu, zapis CSV, zapis ICS, generowanie raportu HTML).
- `event.py` — definicja klasy `Event`: reprezentuje pojedyncze zajęcia, oblicza długość w godzinach akademickich, przechowuje informacje pomocnicze oraz potrafi wygenerować wpisy CSV i ICS.
- `schedule.py` — klasa `Schedule`: parsuje plik JSON z planem, tworzy listę obiektów `Event`, grupuje zajęcia według przedmiotu/grupy i udostępnia metody zapisu do plików (`save_to_csv`, `save_to_ics`, `groups_to_html`).
- `plan_example.json` — przykładowy plik JSON (wzorzec) pokazujący oczekiwaną strukturę `plan.json` używaną przez skrypt.

---

## Opis generowanych plików

### 📄 plan.csv
Zawiera:
- datę
- dzień tygodnia
- godzinę rozpoczęcia i zakończenia
- długość zajęć (w godzinach akademickich)
- salę
- nazwę przedmiotu
- grupę

Można otworzyć w Excelu lub LibreOffice.

---

### 📅 plan.ics
Plik do importu do kalendarza.
Zawiera:
- poprawną strefę czasową Europe/Warsaw
- opis z informacją o:
- grupie
- liczbie zrealizowanych godzin
- opisie zajęć
- prowadzącym

Można zaimportować do:
- Google Calendar
- Outlook
- Apple Calendar

---

### 📊 grupy.html
Raport godzin do wklejenia do Moodle.

Dla każdej grupy generowana jest tabela zawierająca:
- datę
- godzinę rozpoczęcia i zakończenia
- dzień tygodnia
- długość zajęć
- postęp godzin (np. 6/30)

Każda grupa oddzielona jest linią:
```html
=================================
```

Plik można:
- otworzyć w przeglądarce
- skopiować i wkleić do Moodle (tryb HTML)

---

# Eksport planu z WSB (Merito)

Poniżej znajduje się instrukcja krok po kroku, jak wyeksportować plan zajęć w formacie JSON z serwisu https://meritogo.pl.

---

## 🔵 Wersja dla Firefox

### 1. Wejście na stronę
- Otwórz stronę: https://meritogo.pl  
- **Nie loguj się jeszcze**

### 2. Otwórz narzędzia deweloperskie
- Naciśnij `F12`
- Przejdź do zakładki **Network**

Zakładka Network pozwala śledzić zapytania (requesty) wysyłane do serwera.

### 3. Zaloguj się
- Zaloguj się normalnie do systemu
- Po zalogowaniu pojawi się dużo requestów w zakładce Network

### 4. Znajdź zapytanie z planem
- Wyszukaj request typu **GET**
- Szukaj adresu zawierającego:

  lecturer?dateFrom=

- Kliknij w ten request
- Sprawdź zakładkę **Response**

Jeżeli w Response widzisz dane planu w formacie JSON — to jest właściwe zapytanie.  
Jeżeli nie — szukaj dalej.

### 5. Wyślij zapytanie ponownie z inną datą
- Po znalezieniu właściwego requestu:
  - Przejdź do zakładki **Headers**
  - Znajdź przycisk **Resend**

- W oknie, które się otworzy:
  - Zmień zakres dat (`dateFrom`, `dateTo`) na interesujący Cię
  - Kliknij **Send**

### 6. Pobierz wynik
- Nowy request pojawi się na końcu listy
- W zakładce **Response** znajdziesz pełny plan w formacie JSON
- Skopiuj dane do pliku i zapisz jako `plan.json` w folderze ze skryptem

---

## 🟢 Wersja dla Chromium / Chrome

### 1. Wejście na stronę
- Otwórz: https://meritogo.pl  
- Nie loguj się jeszcze

### 2. Otwórz DevTools
- Naciśnij `F12`
- Przejdź do zakładki **Network**

### 3. Zaloguj się
- Zaloguj się normalnie
- W Network pojawi się wiele requestów

### 4. Znajdź właściwy request
- Szukaj zapytania **GET**
- Adres powinien zawierać:

  lecturer?dateFrom=

- Sprawdź w zakładce **Response**, czy zawiera plan (JSON)

Jeżeli nie — znajdź inne zapytanie.

### 5. Skopiuj request jako cURL
- Kliknij prawym przyciskiem myszy na właściwy request
- Wybierz:

  Copy → Copy as cURL

### 6. Uruchom w terminalu
- Wklej skopiowane polecenie do:
  - PowerShell
  - Terminala
  - CMD (jeśli masz curl)

- Zmodyfikuj parametry:
  dateFrom=
  dateTo=

### 7. Pobierz plan jako plik

Możesz od razu zapisać wynik do pliku:

curl (tu całe polecenie) > plan.json

Po wykonaniu polecenia otrzymasz plik `plan.json` zawierający cały plan zajęć.

## Wersja Uniwersalna (curl – niezależna od przeglądarki)

Ta metoda pozwala pobrać plan bez używania funkcji „Resend” w przeglądarce.  
Wymaga jednak ręcznego znalezienia **dwóch wartości** w zakładce Network:

- `authorization` (Bearer token)
- `context-id`

Działa w większości przypadków, ale token może wygasać (np. po wylogowaniu).

---

### Krok 1 – Zaloguj się i znajdź request

1. Wejdź na https://meritogo.pl  
2. Otwórz DevTools (`F12`)  
3. Przejdź do zakładki **Network**  
4. Zaloguj się normalnie  
5. Znajdź request typu **GET**, którego adres zawiera `lecturer?dateFrom=`

6. Kliknij ten request i przejdź do zakładki **Headers**

---

### Krok 2 – Skopiuj wymagane wartości

W sekcji **Request Headers** znajdź:

- `authorization: Bearer ......`
- `context-id: ......`

Skopiuj:

- cały token po słowie `Bearer`
- wartość `context-id`

---

### Krok 3 – Wstaw dane do polecenia curl

W poniższym poleceniu:

- wstaw swój token w miejsce `TUTAJ_WPISZ_SWÓJ_TOKEN`
- wstaw swój `context-id` w miejsce `TUTAJ_WPISZ_SWOJE_CONTEXT_ID`
- opcjonalnie zmień zakres dat (`dateFrom`, `dateTo`)

```bash
curl 'https://api.meritogo.pl/v2/class_schedule/v3/schedule/lecturer?dateFrom=2026-02-28&dateTo=2026-10-31&categoryNames=CLASS_SCHEDULE,STUDY,OFFICE_HOURS,EVENTS' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: pl_PL' \
  -H 'authorization: Bearer TUTAJ_WPISZ_SWÓJ_TOKEN' \
  -H 'context-id: TUTAJ_WPISZ_SWOJE_CONTEXT_ID' \
  -H 'impersonification-id;' \
  -H 'origin: https://meritogo.pl' \
  -H 'priority: u=1, i' \
  -H 'referer: https://meritogo.pl/' \
  -H 'sec-ch-ua: "Chromium";v="145", "Not:A-Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Linux"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  -H 'x-timezone: Europe/Warsaw' > plan.json
```

---

### Krok 4 – Uruchom polecenie

Wklej komendę do:
- PowerShell (Windows 10/11 ma curl domyślnie)
- Terminal (Linux/macOS)
- Git Bash

Po wykonaniu polecenia powstanie plik:
```bash
plan.json
```
Zawiera on pełny plan zajęć w formacie JSON.

### Ważne informacje

- Token `authorization` jest tymczasowy – po wylogowaniu lub po czasie może przestać działać.
- Jeśli otrzymasz błąd 401/403 – pobierz nowy token z Network.
- Nie udostępniaj swojego tokena innym osobom.