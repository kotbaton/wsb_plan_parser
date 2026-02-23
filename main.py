from schedule import Schedule
import sys
import traceback
from pathlib import Path

OUTPUT_DIR = 'output'

if __name__=='__main__':
    # wybór pliku: najpierw argument CLI, jeśli istnieje; w przeciwnym razie 'plan.json'
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if Path(arg_path).exists():
            file_path = arg_path
            print(f"Używam pliku: {file_path}")
        else:
            print(f"Plik podany jako argument ({arg_path}) nie istnieje — przełączam się na 'plan.json'.")
            file_path = 'plan.json'
    else:
        file_path = 'plan.json'

    # Wczytanie harmonogramu (Schedule może wypisać własne błędy)
    try:
        schedule = Schedule(file_path)
        print('='*50, schedule.to_str(), '='*50, sep='\n\n')
    except Exception as e:
        print(f"Coś poszło nie tak podczas wczytywania harmonogramu z '{file_path}':", str(e))
        traceback.print_exc()
        sys.exit(1)

    # Informujemy o katalogu wyników i tworzymy go, jeśli nie istnieje
    out_dir = Path(OUTPUT_DIR)
    print(f"Folder dla wyników to: {out_dir}")
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Katalog '{out_dir}' nie istniał — utworzono.")
    else:
        print(f"Katalog '{out_dir}' istnieje — wyniki zostaną tam zapisane.")

    # Zapis CSV
    try:
        csv_path = out_dir / 'plan.csv'
        schedule.save_to_csv(str(csv_path))
        if csv_path.exists():
            print(f"Gotowe! Zapisano plik {csv_path}")
        else:
            print(f"Coś poszło nie tak: plik '{csv_path}' nie został utworzony.")
            sys.exit(1)
    except Exception as e:
        print("Coś poszło nie tak podczas zapisu CSV:", str(e))
        traceback.print_exc()
        sys.exit(1)

    # Zapis ICS
    try:
        ics_path = out_dir / 'plan.ics'
        schedule.save_to_ics(str(ics_path))
        if ics_path.exists():
            print(f"Gotowe! Zapisano plik {ics_path}")
        else:
            print(f"Coś poszło nie tak: plik '{ics_path}' nie został utworzony.")
            sys.exit(1)
    except Exception as e:
        print("Coś poszło nie tak podczas zapisu ICS:", str(e))
        traceback.print_exc()
        sys.exit(1)

    # Generowanie raportu grup (generuje 'groups.html' w bieżącym katalogu) -> przenosimy do OUTPUT_DIR
    try:
        html_path = out_dir / 'groups.html'
        schedule.groups_to_html(html_path)
        if html_path.exists():
            print(f"Gotowe! Raport z liczby zajęć zapisano do {html_path}")
        else:
            print("Coś poszło nie tak: plik 'groups.html' nie został utworzony przez schedule.groups_to_html().")
            sys.exit(1)
    except Exception as e:
        print("Coś poszło nie tak podczas generowania raportu grup:", str(e))
        traceback.print_exc()
        sys.exit(1)
