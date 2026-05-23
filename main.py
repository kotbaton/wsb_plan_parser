import sys
import traceback
from datetime import date
from pathlib import Path
import argparse

from wsbparser import Schedule, API, DateRange
from wsbparser.group_schedule import build_group_fetch_range, print_group_schedule
from wsbparser.room_schedule import build_room_fetch_range, print_room_schedule

OUTPUT_DIR = "output"


def _parse_iso_date(value: str) -> date:
    """Parse date in YYYY-MM-DD format (argparse helper)."""
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Niepoprawny format daty '{value}'. Oczekiwany format: YYYY-MM-DD."
        ) from e


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Parser planu WSB: generuje CSV/ICS/HTML z pliku JSON.",
        add_help=True,
    )

    # Template switches (to be extended later)
    mx = parser.add_mutually_exclusive_group()
    mx.add_argument(
        "--list-lecturers",
        action="store_true",
        help="Wyświetla wszystkich dostępnych prowadzących i kończy działanie.",
    )
    mx.add_argument(
        "--lecturer",
        metavar='"NAME SURNAME"',
        type=str,
        help="Pobiera i rozparsowuje plan dla konkretnego prowadzącego.",
    )
    mx.add_argument(
        "--group",
        metavar='"GROUP NAME"',
        type=str,
        help="Pokazuje plan konkretnej grupy dla dnia podanego w --date.",
    )
    mx.add_argument(
        "--room",
        metavar='"ROOM NAME"',
        type=str,
        help="Pokazuje zajętość konkretnej sali dla dnia podanego w --date.",
    )
    mx.add_argument(
        "--lecturers",
        metavar="FILE.txt",
        type=str,
        help="Pobiera i rozparsowuje plan dla prowadzących z pliku.",
    )
    mx.add_argument(
        "--file",
        dest="file",
        metavar="PATH",
        help="Ścieżka do pliku JSON z planem (np. plan.json).",
        default=None,
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        type=_parse_iso_date,
        help="Data dla planu grupy lub zajętości sali (działa tylko razem z --group albo --room, domyślnie: dzisiaj).",
        default=None,
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Wymusza ponowne pobranie danych z API zamiast użycia lokalnego cache JSON.",
    )

    parser.add_argument(
        "--dstart",
        metavar="YYYY-MM-DD",
        type=_parse_iso_date,
        help="Data od kiedy pobierać/analizować plan (opcjonalne; dla --group/--room określa początek zakresu cache).",
        default=None,
    )
    parser.add_argument(
        "--dend",
        metavar="YYYY-MM-DD",
        type=_parse_iso_date,
        help="Data do kiedy pobierać/analizować plan (opcjonalne; dla --group/--room określa koniec zakresu cache).",
        default=None,
    )

    return parser


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.date is not None and args.group is None and args.room is None:
        parser.error("--date można używać tylko razem z --group albo --room")

    if args.group is not None and not args.group.strip():
        parser.error("Wartość podana w --group nie może być pusta")

    if args.room is not None and not args.room.strip():
        parser.error("Wartość podana w --room nie może być pusta")

    # If you provide date range, you must also choose a mode that uses it.
    if (args.dstart is not None or args.dend is not None) and not (
        args.list_lecturers or args.lecturer or args.lecturers or args.group or args.room
    ):
        parser.error("--dstart/--dend ma sens tylko razem z --lecturer, --lecturers, --list-lecturers, --group albo --room")

    if args.refresh and not (args.list_lecturers or args.lecturer or args.lecturers or args.group or args.room):
        parser.error("--refresh ma sens tylko razem z --list-lecturers, --lecturer, --lecturers, --group albo --room")

    if args.dstart is not None and args.dend is not None and args.dstart > args.dend:
        parser.error("Niepoprawny zakres dat: --dstart nie może być później niż --dend")

    if args.group is not None or args.room is not None:
        selected_date = args.date if args.date is not None else date.today()
        effective_start = args.dstart if args.dstart is not None else selected_date
        effective_end = args.dend if args.dend is not None else selected_date
        if effective_start > effective_end:
            parser.error("Niepoprawny zakres dat dla --group/--room: --dstart nie może być później niż --dend")
        if not (effective_start <= selected_date <= effective_end):
            parser.error("Data z --date musi mieścić się w zakresie wyznaczonym przez --dstart/--dend")

    if args.file is not None:
        p = Path(args.file)
        if not p.is_file():
            parser.error(f"Plik podany w --file nie istnieje lub nie jest plikiem: {p}")

    if args.lecturers is not None:
        p = Path(args.lecturers)
        if not p.is_file():
            parser.error(f"Plik z listą prowadzących nie istnieje: {p}")


def _ensure_output_dir() -> Path:
    out_dir = Path(OUTPUT_DIR)
    print(f"Folder dla wyników to: {out_dir}")
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Katalog '{out_dir}' nie istniał — utworzono.")
    else:
        print(f"Katalog '{out_dir}' istnieje — wyniki zostaną tam zapisane.")
    return out_dir


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    argv = sys.argv[1:] if argv is None else argv

    # Requirement: when run without arguments, show help.
    if not argv:
        parser.print_help(sys.stdout)
        return 0

    args = parser.parse_args(argv)
    _validate_args(parser, args)

    # Mode: list lecturers
    if args.list_lecturers:
        api = API()
        dr = DateRange(args.dstart, args.dend)
        print('Zakres dat do pobrania/analizy planu:', dr)
        lecturers = api.get_lecturers(force_refresh=args.refresh)
        for l in lecturers:
            print(l)
        return 0

    # Get schedule for group and day
    if args.group is not None:
        api = API()
        selected_date = args.date if args.date is not None else date.today()
        fetch_range = build_group_fetch_range(selected_date, args.dstart, args.dend)
        return print_group_schedule(
            api,
            args.group.strip(),
            selected_date,
            fetch_range,
            force_refresh=args.refresh,
        )

    # Get room occupancy for day
    if args.room is not None:
        api = API()
        selected_date = args.date if args.date is not None else date.today()
        fetch_range = build_room_fetch_range(selected_date, args.dstart, args.dend)
        return print_room_schedule(
            api,
            args.room.strip(),
            selected_date,
            fetch_range,
            force_refresh=args.refresh,
        )

    # Get schedule for lecturer / lecturers
    if args.lecturer is not None or args.lecturers is not None:
        api = API()
        dr = DateRange(args.dstart, args.dend)
        print('Zakres dat do pobrania/analizy planu:', dr)
        lecturer_names = []
        if args.lecturer is not None:
            lecturer_names.append(args.lecturer.strip())
        else:
            with open(args.lecturers) as f:
                for line in f:
                    name = line.strip()
                    if name:
                        lecturer_names.append(name)

        lecturers = api.get_lecturers()
        selected = [l for l in lecturers if l.full_name() in lecturer_names]
        not_found = set(lecturer_names) - set(l.full_name() for l in selected)
        if not_found:
            print("Nie znaleziono prowadzących o podanych nazwiskach:", ", ".join(not_found), file=sys.stderr)
            return 1

        for lecturer in selected:
            print(f"Pobieranie planu dla {lecturer.full_name()}...")
            try:
                schedule = api.get_schedule(lecturer, dr, force_refresh=args.refresh)
            except Exception as e:
                print(f"Nie udało się pobrać lub wczytać planu dla {lecturer.full_name()}: {e}", file=sys.stderr)
                return 1
            out_dir = _ensure_output_dir()
            schedule.export_schedule(out_dir)

        return 0

    # Parse schedule from file
    if args.file is not None:
        dr = DateRange(args.dstart, args.dend)
        print('Zakres dat do pobrania/analizy planu:', dr)
        try:
            schedule = Schedule(None, args.file)
            out_dir = _ensure_output_dir()
            schedule.export_schedule(out_dir)
            return 0
        except Exception as e:
            print("Coś poszło nie tak podczas przetwarzania pliku:", str(e))
            traceback.print_exc()
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
