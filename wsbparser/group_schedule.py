from datetime import date
import sys

from .api import API
from .daterange import DateRange


TABLE_HEADERS = ("Od", "Do", "Forma", "Przedmiot", "Sala", "Prowadzący")
TABLE_MAX_WIDTHS = (5, 5, 8, 40, 18, 35)


def build_group_fetch_range(selected_date: date, dstart: date | None, dend: date | None) -> DateRange:
    start = dstart if dstart is not None else selected_date
    end = dend if dend is not None else selected_date
    return DateRange(start, end)


def _event_matches_group(event, group_name: str) -> bool:
    wanted = group_name.strip().casefold()
    return any(group.casefold() == wanted for group in event.groups)


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


def _table_row(event) -> tuple[str, str, str, str, str, str]:
    return (
        event.dtstart.strftime("%H:%M"),
        event.dtend.strftime("%H:%M"),
        event.form or "-",
        event.name,
        _event_room_label(event),
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
    force_refresh: bool = False,
) -> int:
    print("Zakres dat do pobrania/analizy planu:", fetch_range)
    print(f"Data wyświetlanego planu grupy: {selected_date}")

    lecturers = api.get_lecturers(force_refresh=force_refresh)
    matched_events = []
    seen_events = set()
    skipped_lecturers = []

    n_lecturers = len(lecturers)
    for i, lecturer in enumerate(lecturers, 1):
        print(f"({i} / {n_lecturers}) Sprawdzanie planu dla {lecturer.full_name()}...")
        try:
            schedule = api.get_schedule(
                lecturer,
                fetch_range,
                force_refresh=force_refresh,
                allow_covering_cache=True,
            )
        except Exception as e:
            skipped_lecturers.append(lecturer.full_name())
            print(
                f"Pomijam prowadzącego {lecturer.full_name()}, bo nie udało się pobrać lub wczytać planu: {e}",
                file=sys.stderr,
            )
            continue

        for event in schedule.events:
            if event.dtstart.date() != selected_date:
                continue
            if not _event_matches_group(event, group_name):
                continue

            dedupe_key = _event_dedupe_key(event)
            if dedupe_key in seen_events:
                continue

            seen_events.add(dedupe_key)
            matched_events.append(event)

    matched_events.sort(key=lambda e: (e.dtstart, e.dtend, e.name))

    if skipped_lecturers:
        print(
            f"Pominięto {len(skipped_lecturers)} prowadzących z powodu błędów pobierania lub odczytu planu.",
            file=sys.stderr,
        )

    if not matched_events:
        print(f"Nie znaleziono zajęć dla grupy '{group_name}' w dniu {selected_date}.")
        return 0

    print(f"Plan grupy '{group_name}' dla dnia {selected_date}:")
    _print_events_table(matched_events)
    return 0

