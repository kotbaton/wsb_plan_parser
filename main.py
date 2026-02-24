import sys
import traceback
from datetime import date, datetime, time
from pathlib import Path
import argparse

from wsbparser import Schedule, API, DateRange

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
        "--dstart",
        metavar="YYYY-MM-DD",
        type=_parse_iso_date,
        help="Data od kiedy pobierać/analizować plan (opcjonalne).",
        default=None,
    )
    parser.add_argument(
        "--dend",
        metavar="YYYY-MM-DD",
        type=_parse_iso_date,
        help="Data do kiedy pobierać/analizować plan (opcjonalne).",
        default=None,
    )

    return parser


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    # If you provide date range, you must also choose a mode that uses it.
    if (args.dstart is not None or args.dend is not None) and not (
        args.list_lecturers or args.lecturer or args.lecturers
    ):
        parser.error("--dstart/--dend ma sens tylko razem z --lecturer, --lecturers albo --list-lecturers")

    if args.dstart is not None and args.dend is not None and args.dstart > args.dend:
        parser.error("Niepoprawny zakres dat: --dstart nie może być później niż --dend")

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

    api = API()
    dr = DateRange(args.dstart, args.dend)
    print('Zakres dat do pobrania/analizy planu:', dr)

    # Mode: list lecturers
    if args.list_lecturers:
        lecturers = api.get_lecturers()
        for l in lecturers:
            print(l)
        return 0

    # Get schedule for lecturer / lecturers
    if args.lecturer is not None or args.lecturers is not None:
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
            schedule = api.get_schedule(lecturer, dr)
            out_dir = _ensure_output_dir()
            schedule.export_schedule(out_dir)

        return 0

    # Parse schedule from file
    if args.file is not None:
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
