from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from models import BillingInterval, ChargingSession, Invoice, MeterReading
from tariff import rate_at, split_at_rate_changes

ENERGY_QUANT = Decimal("0.001")
MONEY_QUANT = Decimal("0.01")
SESSION_FEE = Decimal("1.00")
_MICROSECOND = timedelta(microseconds=1)

def clean_readings(readings: list[MeterReading]):
    """Dedupe by timestamp, sort, then drop rollbacks."""

    Returns (kept_readings, number_of_readings_replaced).
    """
    latest ={}
    replaced = 0
    for reading in readings:
        if reading.at in latest:
            replaced += 1
        latest[reading.at] = reading

    kept = []
    for reading in sorted(latest.values(), key=lambda r: r.at):
        if kept and reading.cumlative_kwh < kept[-1].cumlative_kwh:
            continue
        kept.append(reading)

    return kept, replaced

    def build_invoice()