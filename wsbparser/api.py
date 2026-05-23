import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from . import Schedule
from .daterange import DateRange
from .lecturer import Lecturer

logger = logging.getLogger(__name__)

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
        logger.debug("Zapisano odpowiedź API do %s", filename)

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

    def _schedule_cache_file(self, lecturer: Lecturer, dr: DateRange) -> Path:
        login = lecturer.login()
        return self.json_dir / f"{login}_schedule_{dr}.json"

    def _parse_schedule_cache_range(self, lecturer: Lecturer, cache_file: Path) -> DateRange | None:
        prefix = f"{lecturer.login()}_schedule_"
        suffix = ".json"
        filename = cache_file.name

        if not filename.startswith(prefix) or not filename.endswith(suffix):
            return None

        range_part = filename[len(prefix):-len(suffix)]
        if "_" not in range_part:
            return None

        start_text, end_text = range_part.split("_", 1)
        try:
            return DateRange(start_text, end_text)
        except (TypeError, ValueError):
            return None

    def find_schedule_cache_covering_range(self, lecturer: Lecturer, dr: DateRange) -> Path | None:
        pattern = f"{lecturer.login()}_schedule_*.json"
        matching_cache_files = []

        for cache_file in self.json_dir.glob(pattern):
            cache_range = self._parse_schedule_cache_range(lecturer, cache_file)
            if cache_range is None:
                continue
            if cache_range.start <= dr.start and cache_range.end >= dr.end:
                cache_span_days = (cache_range.end - cache_range.start).days
                matching_cache_files.append((cache_span_days, cache_range.start, cache_file))

        if not matching_cache_files:
            return None

        matching_cache_files.sort(key=lambda item: (item[0], item[1], item[2].name))
        return matching_cache_files[0][2]


    def get_schedule(
        self,
        lecturer: Lecturer,
        dr: DateRange,
        force_refresh: bool = False,
        allow_covering_cache: bool = False,
    ):
        requested_cache_file = self._schedule_cache_file(lecturer, dr)
        cache_file = requested_cache_file
        used_covering_cache = False

        if not force_refresh and allow_covering_cache:
            covering_cache_file = self.find_schedule_cache_covering_range(lecturer, dr)
            if covering_cache_file is not None:
                cache_file = covering_cache_file
                used_covering_cache = cache_file != requested_cache_file
                logger.info("Używanie danych o planie z cache pokrywającego zakres %s: %s", dr, cache_file)

        should_fetch = force_refresh or not cache_file.exists()

        if should_fetch:
            try:
                logger.info("Pobieranie danych o planie z API...")
                # ensure directory exists
                self.json_dir.mkdir(parents=True, exist_ok=True)
                cache_file = requested_cache_file
                self.fetch_schedule(lecturer, dr, cache_file)
            except Exception as e:
                raise RuntimeError(
                    f"Pobieranie planu dla {lecturer.full_name()} nie powiodło się: {e}"
                ) from e
        elif not used_covering_cache:
            logger.info("Używanie danych o planie z cache: %s", cache_file)

        try:
            return Schedule(lecturer, cache_file)
        except RuntimeError as e:
            raise RuntimeError(
                f"Nie udało się wczytać planu dla {lecturer.full_name()} z pliku {cache_file}"
            ) from e


    def get_lecturers(self, force_refresh: bool = False):
        cache_file = self.json_dir / "lecturers.json"
        should_fetch = force_refresh or not cache_file.exists()

        if should_fetch:
            try:
                logger.info("Pobieranie danych o wykładowcach z API... (może potrwać kilka sekund)")
                # ensure directory exists
                self.json_dir.mkdir(parents=True, exist_ok=True)
                self.fetch_lecturers()
            except Exception as e:
                raise RuntimeError(f"Pobieranie danych o wykładowcach nie powiodło się: {e}") from e
        else:
            logger.info("Używanie danych o wykładowcach z cache: %s", cache_file)

        # after fetch, read and return
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        res = []
        for item in data["data"]:
            res.append(Lecturer(item))
        return res

