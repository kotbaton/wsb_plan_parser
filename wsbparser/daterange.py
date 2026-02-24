from datetime import date, datetime


class DateRange:
    def __init__(self, start=None, end=None):
        self.start = self._parse_date(start)
        self.end = self._parse_date(end)

        if self.start is None and self.end is None:
            self.start, self.end = self._current_semester()

        if self.start and self.end and self.start > self.end:
            raise ValueError("Start date cannot be after end date")

    def _parse_date(self, value):
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()
        raise TypeError("Date must be date, 'YYYY-MM-DD' string, or None")

    def _current_semester(self):
        today = date.today()
        year = today.year

        march_1 = date(year, 3, 1)
        oct_1 = date(year, 10, 1)

        # Semestr 1: 1 marca – 1 października
        if march_1 <= today < oct_1:
            return march_1, oct_1

        # Semestr 2: 1 października – 1 marca następnego roku
        if today >= oct_1:
            return oct_1, date(year + 1, 3, 1)

        # Jeśli jesteśmy między 1 stycznia a 1 marca
        return date(year - 1, 10, 1), march_1

    def __str__(self):
        return f"{self.start}_{self.end}"

    def __repr__(self):
        return f"DateRange(start={self.start}, end={self.end})"
