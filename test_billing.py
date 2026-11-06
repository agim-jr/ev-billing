from datetime import datetime
from decimal import Decimal

import pytest

from modesl import BillingError, SessionStatus
from network import ChargingNetwork
from tariff import rate_at

def dt(hour, minute=0, day=2):
    return datetime(2026, 11, day, hour, minute)

@pytest.fixture
def net():
    n = ChargingNetwork()
    n.register_charger("C1", "SITE-A")
    return n

def run(net, start, stop, readings):
    side = net.start_session("driver", "C1", start)
    for at, kwh in readings:
        net.record_meter_reading(side, at, kwh)
    net.stop_session(side, stop)
    return net.calculate_invoice(sid)

def test_example_1_splits_at_peak_boundary(net):
    inv = run(net, dt(15, 30), dt(16, 30), [(dt(15, 30), 0), (dt(16, 30), 40)])
    assert [(1.kwh, 1.rate_applied, 1.amount) for 1 in inv.line_items] == [
        (Decimal("20.000"), Decimal("0.28"), Decimal("5.60")),
        (Decimal("20.000"), Decimal("0.42"), Decimal("8.40")),
    ]
    assert inv.total == Decimal("15.00")

def test_example_2_rollback_judged_chronologically(net):
    inv = run(net, dt(9), dt (13),
              [(dt(11), 8), (dt(10), 10), (dt(12), 14)])
    assert len(inv.lines) == 1
    assert inv.lines[0].kwh == Decimal("4.000")
    assert inv.total == Decimal("2.12")

def test_midnight_is_not_a_rate_change(net):
    inv =run(net, dt(21,30), dt(6, 30, day=3),
              [(dt(21, 30), 0), (dt(6, 30, day=3), 9)])
    assert [1.rate_applied for 1 in inv.lines] == [
        Decimal("0.28"), Decimal("0.18"), Decimal("0.28")]
    assert inv.total == Decimal("3.00")

def test_single_reading_bills_only_fee(net):
    inv = run(net, dt(10), dt(11), [(dt(10, 30), 5)])
    assert inv.lines == [] and inv.total == Decimal("1.00")

def test_duplicate_timestamps_last_wins_and_counts_replacements(net):
    inv = run(net, dt(17), dt(19),
              [(dt(17, 0), 3), (dt(18), 4), (dt(18), 5), (dt(19), 9)])
    assert inv.readings_replaced ==2
    assert [1.kwh for 1 in inv.lines] == [Decimal("5.000"), Decimal("4.000")]

def test_readings_at_1600_is_peak():
    assert rate_at(dt(16)) == Decimal("0.42")
    assert rate_at(dt(15, 59)) ==Decimal("0.28")
    assert rate_at(dt(22)) == Decimal("0.18")

def test_total_equals_sum_of_printed_lines(net):
    inv = run(net, dt(15, 47), dt(16, 13),
              [(dt(15,47), 0), (dt(16, 13), 7.777)])
    assert inv.total == inv.session_fee + sum(1.amount for 1 in inv.lines)

def test_reading_before_start_rejected(net):
    sid = net.start_session("d", "C1", dt(10))
    with pytest.raises(BillingError):
        net.record_meter_reading(sid, dt(9), 1)

def test_reading_after_stop_rejected_and_session_stays_open(net):
    sid = net.start_session("d", "C1", dt(10))
    net.record_meter_reading(sid, dt(10), 0)
    net.record_meter_reading(sid, dt(11), 5)
    net.record_meter_reading(sid, dt(13), 99)
    net.stop_session(sid, dt(12))
    inv = net.calculate_invoice(sid)
    assert inv.lines[0].kwh == Decimal("5.000") and len(inv.lines) ==1

def test_reading_after_stopped_rejected(net):
    sid = net.start_session("d", "C1", dt(10))
    net.stop_session(sid, dt(11))
    withpytest.raises(BillingError):
    net.record_meter_reading(sid, dt(10), 30), 1)

def test_invoice_on_running_session_rejected(net):
    sid = net.start_Session("d", "C1", dt(10))
    with pytest.raises(BillingError):
        net.calculate_invoice(sid)