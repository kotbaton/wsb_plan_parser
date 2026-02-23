import json
import csv
from datetime import datetime
from collections import defaultdict
from html import escape

from event import Event, DAY_MAP

class Schedule:
    def __init__(self, file_path):
        self.file_path = file_path
        try:
            with open(file_path) as f:
                schedule_text = f.read()
                plan_json = json.loads(schedule_text)
        except (FileNotFoundError, json.JSONDecodeError):
            print('Plik plan.json nie został odnaleziony lub nie jest to plik JSON. Kończę pracę.')
            exit(1)
        self.events, self.groups = Schedule.json_to_events(plan_json)

    def to_str(self, n=3):
        lines = [f"Plan wczytany z {self.file_path}",
                 f'Wyświetlam pierwsze {n} zajęć z {len(self.events)}:\n',
                 "\n\n".join(str(e) for e in self.events[:n])]
        return '\n'.join(lines)

    @staticmethod
    def json_to_events(plan):
        events = []
        for entry in plan["events"]:
            event = Event(entry)
            events.append(event)
        events.sort(key=lambda e: e.dtstart)  # sortowanie po dtstart
        groups = Schedule.update_with_cumulative_hours(events)
        return events, groups

    @staticmethod
    def update_with_cumulative_hours(events):
        # Jako że działamy na referencjach do obiektów, możemy bezpośrednio aktualizować ich atrybuty w miejscu,
        # bez konieczności tworzenia nowych obiektów i zwracania nowej listy.

        # Grupujemy zajęcia po formie, nazwie i grupach, aby obliczyć łączną liczbę godzin dla każdej unikalnej kombinacji
        groups = defaultdict(list)
        for event in events:
            groups[(event.form, event.name, event.groups)].append(event)

        # Obliczamy łączną liczbę godzin dla każdej grupy zajęć i zapisujemy do osobnego słownika
        total_group_hours = {}
        for key, group_events in groups.items():
            total_hours = sum(e.duration for e in group_events)
            total_group_hours[key] = total_hours

        # Aktualizujemy każde zajęcia o skumulowaną i łączną liczbę godzin dla jego grupy
        for key, group_events in groups.items():
            cumulative_hours = 0
            for event in group_events:
                cumulative_hours += event.duration
                event.cumulative_hours = cumulative_hours
                event.total_hours = total_group_hours[key]

        return groups

    def save_to_csv(self, filename="plan.csv"):
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(Event.csv_headers())
            writer.writerows([e.to_csv_entry() for e in self.events])

    def save_to_ics(self, filename="plan.ics"):
        def format_dt(date_str, time_str):
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            return dt.strftime("%Y%m%dT%H%M%S")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("BEGIN:VCALENDAR\n")
            f.write("VERSION:2.0\n")
            f.write("PRODID:-//Plan zajęć//EN\n")
            f.write("CALSCALE:GREGORIAN\n")
            f.write("""BEGIN:VTIMEZONE
TZID:Europe/Warsaw
X-LIC-LOCATION:Europe/Warsaw
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE
""")
            for event in self.events:
                f.write(event.to_ics_entry())

            f.write("END:VCALENDAR\n")

    def groups_to_html(self, filename="groups.html"):
        html_blocks = []
        # Sortujemy grupy po formie i nazwach grup
        for (form, name, group), group_events in self.groups.items():
            if not form:  # Pomijamy egzaminy
                continue
            rows = []
            for event in group_events:
                rows.append(f"""<tr>
<td>{event.dtstart.strftime('%d.%m.%Y')}</td>
<td>{event.dtstart.strftime('%H:%M')}</td>
<td>{DAY_MAP[event.dtstart.weekday()]}</td>
<td>{event.dtend.strftime('%H:%M')}</td>
<td>{event.duration}</td>
<td>{event.cumulative_hours}/{event.total_hours}</td>
</tr>""")
            table = f"""<strong>{escape(form)} - {escape(name)} - {escape(group)}</strong>
<table border="1" cellpadding="5" cellspacing="0">
<thead>
<tr>
<th>Data</th>
<th>Początek</th>
<th>Koniec</th>
<th>Dzień</th>
<th>Długość</th>
<th>Godziny</th>
</tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>"""
            html_blocks.append('\n=================================\n')
            html_blocks.append(table)

        res = "\n".join(html_blocks)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(res)
