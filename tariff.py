from datetime import datetime, time, timedelta
from decimal import Decimal

WINDOWS = [
    (time(0, 0), Decimal("0.18")),  # off-peak
    (time(6, 0), Decimal("0.28")),  # mid-peak
    (time(16, 0), Decimal("0.42")), # peak
    (time(21, 0), Decimal("0.28")), # mid-peak
    (time(22, 0), Decimal("0.18")), # off-peak
]


RATE_CHANGE_TIMES = [
    start for i, (start, rate) in enumerate(WINDOWS)
    if rate != WINDOWS[i - 1][1] 
]

def rate_at(at: datetime) -> Decimal:
    """Return the tariff in effect at the given local datetime."""
    for start, rate in reversed(WINDOWS):
        if at.time() >= start:
            return rate
    return WINDOWS[-1][1]


def split_at_rate_changes(start: datetime, end: datetime):
    """Split [start, end) at every rate-change boundary it crosses."""
    points = {start, end}
    day = start.date()
    while day <= end.date():
        for t in RATE_CHANGE_TIMES:
            boundary = datetime.combine(day, t)
            if start <= boundary < end:
                points.add(boundary)
        day += timedelta(days=1)
        ordered = sorted(points)        
    return list(zip(ordered, ordered[1:]))