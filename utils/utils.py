from datetime import datetime, timezone

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def seconds_between(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds())