from datetime import date, datetime, time, timedelta, timezone


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def compute_day_bucket(utc_date: datetime) -> str:
    if utc_date.tzinfo is None:
        kickoff_date = utc_date.date()
    else:
        kickoff_date = utc_date.astimezone(timezone.utc).date()

    today = utc_today()
    if kickoff_date == today:
        return "today"
    if kickoff_date == today + timedelta(days=1):
        return "tomorrow"
    if kickoff_date == today - timedelta(days=1):
        return "yesterday"
    return "other"


def utc_day_range(start: date, end: date) -> tuple[datetime, datetime]:
    range_start = datetime.combine(start, time.min, tzinfo=timezone.utc)
    range_end = datetime.combine(end, time.max, tzinfo=timezone.utc)
    return range_start, range_end


def today_tomorrow_utc_range() -> tuple[datetime, datetime]:
    today = utc_today()
    return utc_day_range(today, today + timedelta(days=1))


def yesterday_tomorrow_utc_range() -> tuple[datetime, datetime]:
    today = utc_today()
    return utc_day_range(today - timedelta(days=1), today + timedelta(days=1))
