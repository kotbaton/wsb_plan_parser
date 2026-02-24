import requests
import json
from pathlib import Path
import os
from dotenv import load_dotenv

from . import Schedule
from .lecturer import Lecturer
from .daterange import DateRange

class API:
    def __init__(self, json_dir="json"):
        context_id, bearer_token = self._load_tokens_from_env()
        self.context_id = context_id
        self.bearer_token = bearer_token
        self.json_dir = Path(json_dir)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pl_PL",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://meritogo.pl/",
            "X-Timezone": "Europe/Warsaw",
            "context-id": self.context_id,
            "Origin": "https://meritogo.pl",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Authorization": self.bearer_token,
            "impersonification-id": "",
            "Connection": "keep-alive",
            "TE": "trailers",
        }

    def _load_tokens_from_env(self) -> tuple[str, str]:
        """Wczytuje tokeny do API z .env (lub zmiennych środowiskowych).

        Wymagane klucze:
          - CONTEXT_ID
          - BEARER_TOKEN (zwykle w formie: 'Bearer ...')
        """
        env_path = Path(".env")

        # Jeżeli plik .env nie istnieje, i tak próbujemy z env systemowego.
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()

        context_id = (os.getenv("CONTEXT_ID") or os.getenv("context_id") or "").strip()
        bearer_token = (os.getenv("BEARER_TOKEN") or os.getenv("bearer_token") or "").strip()

        missing: list[str] = []
        if not context_id:
            missing.append("CONTEXT_ID")
        if not bearer_token:
            missing.append("BEARER_TOKEN")
        if missing:
            raise RuntimeError(
                "Brakuje tokenów do API. Uzupełnij .env albo zmienne środowiskowe: " + ", ".join(missing)
            )

        return context_id, bearer_token

    @staticmethod
    def _check_and_write(response, filename):
        # Sprawdzenie czy request się powiódł
        response.raise_for_status()
        # Parsowanie JSON
        data = response.json()
        # Zapis do pliku
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def fetch_lecturers(self):
        """Fetch lecturers from remote API and save to json_dir/lecturers.json.

        Ensure the json_dir exists before writing.
        """
        # ensure directory exists
        self.json_dir.mkdir(parents=True, exist_ok=True)

        url = "https://api.meritogo.pl/v2/office-hours/v2/lecturers"
        response = requests.get(url, headers=self.headers)
        self._check_and_write(response, self.json_dir / "lecturers.json")

    def fetch_schedule(self, lecturer: Lecturer, dr: DateRange, cache_file: Path):
        # ensure directory exists
        self.json_dir.mkdir(parents=True, exist_ok=True)

        dfrom = dr.start.strftime("%Y-%m-%d")
        dto = dr.end.strftime("%Y-%m-%d")
        url = (f"https://api.meritogo.pl/v2/class_schedule/v3/schedule/lecturer/{lecturer.lecturerId}"
               f"?dateFrom={dfrom}&dateTo={dto}&categoryNames=CLASS_SCHEDULE,STUDY,OFFICE_HOURS,EVENTS")
        response = requests.get(url, headers=self.headers)
        self._check_and_write(response, cache_file)


    def get_schedule(self, lecturer: Lecturer, dr: DateRange, force_refresh: bool = False):
        login = lecturer.login()
        cache_file = self.json_dir / f"{login}_schedule_{dr}.json"

        if not cache_file.exists() and not force_refresh:
            try:
                print("Pobieranie danych o planie z API...")
                # ensure directory exists
                self.json_dir.mkdir(parents=True, exist_ok=True)
                self.fetch_schedule(lecturer, dr, cache_file)
            except Exception as e:
                print(f"Pobieranie danych nie powiodło się: {e}")
                exit(1)
        else:
            print(f"Używanie danych o planie z cache: {cache_file}")

        return Schedule(lecturer, cache_file)


    def get_lecturers(self, force_refresh: bool = False):
        cache_file = self.json_dir / "lecturers.json"

        if not cache_file.exists() and not force_refresh:
            try:
                print("Pobieranie danych o wykładowcach z API... (może potrwać kilka sekund)")
                # ensure directory exists
                self.json_dir.mkdir(parents=True, exist_ok=True)
                self.fetch_lecturers()
            except Exception as e:
                print(f"Pobieranie danych nie powiodło się: {e}")
                exit(1)
        else:
            print(f"Używanie danych o wykładowcach z cache: {cache_file}")

        # after fetch, read and return
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        res = []
        for item in data["data"]:
            res.append(Lecturer(item))
        return res

