from zoneinfo import ZoneInfo
import uuid
import math
from datetime import datetime, UTC


DAY_MAP = ["Pn", "Wt", "Śr", "Cz", "Pt", "Sb", "Nd"]
WARSAW = ZoneInfo("Europe/Warsaw")


def academic_hours(dtstart, dtend):
    diff_minutes = (dtend - dtstart).seconds / 60
    return math.floor(diff_minutes / 45)


class Event:
    def __init__(self, event: dict):
        self.name = event["name"]
        self.description = event["description"]
        self.dtstart = datetime.fromisoformat(event["start"]).astimezone(WARSAW)
        self.dtend = datetime.fromisoformat(event["end"]).astimezone(WARSAW)
        self.duration = academic_hours(self.dtstart, self.dtend)
        self.cumulative_hours = 0  # To be calculated later
        self.total_hours = 0  # To be calculated later
        self.online = event["isOnline"]
        if event["localization"]:
            self.location = event["localization"]["address"]
            if 'Śniadeckich' in self.location:
                self.location = 'ŚN'
            self.rooms = ' '.join(event["rooms"])  # Empty or rooms
        else:
            self.location = 'Zd'
            self.rooms = 'Zd'
        self.form = event["classFormShortName"]  # Empty or form
        self.groups = ' '.join(event["groups"])  # Empty or groups
        self.lecturers = ' '.join(l["fullName"] for l in event["lecturers"])

    def __str__(self):
        return f"""Name: ({self.form}) {self.name}
Time: {self.dtstart} to {self.dtend}
Duration: {self.duration} academic hours
Cumulative Hours: {self.cumulative_hours} / {self.total_hours}
Location: {self.rooms} {self.location}
Groups: {self.groups}
Lecturers: {self.lecturers}"""

    @staticmethod
    def csv_headers():
        return ["Date", "Day", "Start Time", "End Time", "Duration", "Location", "Subject", "Groups"]

    def to_csv_entry(self):
        date = self.dtstart.date()
        day = DAY_MAP[self.dtstart.weekday()]
        start_time = self.dtstart.strftime("%H:%M")
        end_time = self.dtend.strftime("%H:%M")
        location = f'{self.rooms}'
        subject = f'({self.form}) {self.name}' if self.form else self.name
        return date, day, start_time, end_time, self.duration, location, subject, self.groups

    def to_ics_entry(self):
        summary = f'({self.form}) {self.name} {self.rooms}' if self.form else self.name
        description = f"""Grupa: {self.groups}
 \\nGodziny: {self.cumulative_hours}/{self.total_hours}
 \\nOpis: {self.description if self.description else 'brak'}
 \\nProwadzący: {self.lecturers}"""
        return f"""BEGIN:VEVENT
UID:{uuid.uuid4()}
DTSTAMP:{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}
DTSTART;TZID=Europe/Warsaw:{self.dtstart.strftime("%Y%m%dT%H%M%S")}
DTEND;TZID=Europe/Warsaw:{self.dtend.strftime("%Y%m%dT%H%M%S")}
SUMMARY:{summary}
DESCRIPTION:{description}
LOCATION:{self.rooms} {self.location}
END:VEVENT
"""
