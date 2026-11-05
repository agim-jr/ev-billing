from dataclasses import dataclasses, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional 

class BillingError(Exception):
    """Raised when an operation is rejected."""

class SessionStatus(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"

@dataclass(frozen=True)
class Charger:
    charger_id: str
    site_id: str

@dataclass(frozen=True)
class MeterReading:
    at: datetime
    cumlative_kwh: Decimal

@dataclass
class ChargingSession:
    session_id: str
    charger_id: str
    driver_id: str
    started_at: datetime
    stopped_at: Optional[datetime] = None
    meter_readings: list [MeterReading] = field(default_factory=list)
    status: SessionStatus = SessionStatus.RUNNING


@dataclass(frozen=True)
class BillingInterval:
    from_time: datetime
    to_time: datetime
    kwh: Decimal
    rate_applied: Decimal
    amount: Decimal

@dataclass(frozen=True)
class Invoice:
    session_id: str
    lines: list[BillingInterval]
    session_fee: Decimal
    readings_replaced: int
    total: Decimal
