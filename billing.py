from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from models import BillingInterval, ChargingSession, Invoice, MeterReading
from tariff import rate_at, split_at_rate_changes

ENERGY_QUANT = Decimal("0.001")
MONEY_QUANT = Decimal("0.01")
SESSION_FEE = Decimal("1.00")
_MICROSECOND = timedelta(microseconds=1)

def clean_readings(readings: list[MeterReading]):
    """Dedupe by timestamp, sort, then drop rollbacks.

    Returns the kept readings and the number of readings replaced.
    """
    latest = {}
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

def build_invoice(session: ChargingSession) -> Invoice:
    kept, replaced = clean_readings(session.meter_readings)
    lines = []
    for prev, nxt in zip(kept, kept[1:]):
        total_us = (nxt.at - prev.at) // _MICROSECOND
        delta_kwh = nxt.cumlative_kwh - prev.cumlative_kwh
        for seg_start, seg_end in split_at_rate_changes(prev.at, nxt.at):
            seg_us = (seg_end - seg_start) // _MICROSECOND
            kwh = (delta_kwh * Decimal(seg_us) / Decimal(total_us)).quantize(
                ENERGY_QUANT, rounding=ROUND_HALF_UP
            )
            rate = rate_at(seg_start)
            amount = (kwh * rate).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
            lines.append(BillingInterval(seg_start, seg_end, kwh, rate, amount))

    total = SESSION_FEE + sum((line.amount for line in lines), Decimal("0"))
    return Invoice(session.session_id, lines, SESSION_FEE, replaced, total)