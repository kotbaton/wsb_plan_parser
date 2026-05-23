from datetime import date
import logging
import re

from .api import API
from .daterange import DateRange


TABLE_HEADERS = ("Od", "Do", "Sala", "Forma", "Przedmiot", "Grupy", "Prowadzący")
TABLE_MAX_WIDTHS = (5, 5, 18, 8, 36, 50, 30)
logger = logging.getLogger(__name__)


def build_group_fetch_range(selected_date: date, dstart: date | None, dend: date | None) -> DateRange:
    start = dstart if dstart is not None else selected_date
    end = dend if dend is not None else selected_date
    return DateRange(start, end)


def _event_matches_group(event, group_name: str) -> bool:
    wanted = group_name.strip().casefold()
    return any(group.casefold() == wanted for group in event.groups)


def _event_matches_group_regex(event, pattern) -> bool:
    return any(pattern.fullmatch(group) for group in event.groups)


def _event_dedupe_key(event) -> tuple:
    return (
        event.dtstart,
        event.dtend,
        event.name,
        event.form,
        event.groups,
        event.rooms,
        event.location,
        event.lecturers,
    )


def _clip(value: object, max_width: int) -> str:
    text = str(value)
    if len(text) <= max_width:
        return text
    if max_width <= 3:
        return text[:max_width]
    return text[: max_width - 3] + "..."


def _event_room_label(event) -> str:
    if event.rooms and event.location and event.location not in event.rooms:
        return f"{event.rooms} {event.location}"
    return event.rooms or event.location or "-"


def _table_row(event) -> tuple[str, str, str, str, str, str, str]:
    return (
        event.dtstart.strftime("%H:%M"),
        event.dtend.strftime("%H:%M"),
        _event_room_label(event),
        event.form or "-",
        event.name,
        ", ".join(event.groups) if event.groups else "-",
        event.lecturers or "-",
    )


def _print_events_table(events) -> None:
    rows = [tuple(_clip(value, TABLE_MAX_WIDTHS[i]) for i, value in enumerate(_table_row(event))) for event in events]
    widths = [len(header) for header in TABLE_HEADERS]

    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))

    divider = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    header = "| " + " | ".join(TABLE_HEADERS[i].ljust(widths[i]) for i in range(len(TABLE_HEADERS))) + " |"

    print(divider)
    print(header)
    print(divider)
    for row in rows:
        print("| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(row))) + " |")
    print(divider)


def print_group_schedule(
    api: API,
    group_name: str,
    selected_date: date,
    fetch_range: DateRange,
    regex: bool = False,
    force_refresh: bool = False,
) -> int:
    logger.info("Zakres dat do pobrania/analizy planu: %s", fetch_range)
    logger.info("Data wyświetlanego planu grupy: %s", selected_date)

    lecturers = api.get_lecturers(force_refresh=force_refresh)
    matched_events = []
    seen_events = set()
    skipped_lecturers = []

    n_lecturers = len(lecturers)
    for i, lecturer in enumerate(lecturers, 1):
        logger.debug("(%s / %s) Sprawdzanie planu dla %s...", i, n_lecturers, lecturer.full_name())
        try:
            schedule = api.get_schedule(
                lecturer,
                fetch_range,
                force_refresh=force_refresh,
                allow_covering_cache=True,
            )
        except Exception as e:
            skipped_lecturers.append(lecturer.full_name())
            logger.warning(
                "Pomijam prowadzącego %s, bo nie udało się pobrać lub wczytać planu: %s",
                lecturer.full_name(),
                e,
            )
            logger.debug("Szczegóły błędu podczas analizy planu grupy.", exc_info=True)
            continue

        pattern = re.compile(group_name, re.IGNORECASE) if regex else None
        for event in schedule.events:
            if event.dtstart.date() != selected_date:
                continue
            if ((not _event_matches_group(event, group_name))
                    and (regex and not _event_matches_group_regex(event, pattern))):
                continue

            dedupe_key = _event_dedupe_key(event)
            if dedupe_key in seen_events:
                continue

            seen_events.add(dedupe_key)
            matched_events.append(event)

    matched_events.sort(key=lambda e: (e.dtstart, e.dtend, e.name))

    if skipped_lecturers:
        logger.warning(
            "Pominięto %s prowadzących z powodu błędów pobierania lub odczytu planu.",
            len(skipped_lecturers),
        )

    if not matched_events:
        print(f"Nie znaleziono zajęć dla grupy '{group_name}' w dniu {selected_date}.")
        return 0

    print(f"Plan grupy '{group_name}' dla dnia {selected_date}:")
    _print_events_table(matched_events)
    return 0

