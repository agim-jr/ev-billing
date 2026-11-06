from datetime import datetime

from network import ChargingNetwork

def dt(hour, minute=0, day=2):
    return datetime(2026, 11, day, hour, minute)

SCENARIO = [
    # (label, charger, start, stop, readings)
    ("S1 crosses 16:00 (peak)", "C1", dt(15, 30), dt(16, 30), [(dt(15, 30), 0), (dt(16, 30), 40)]),
    ("S2 crosses midnight + 3 intervals", "C2", dt(21, 30), dt(6, 30, 3), [(dt(21, 30), 0), (dt(6, 30, 3), 9)]),
    ("S3 rollback reading", "C3", dt(9), dt(13), [(dt(11), 8), (dt(10), 10), (dt(12), 14)]),
    ("S4 crosses 21:00 and 22:00", "C1", dt(20, 30), dt(22, 30), [(dt(20, 30), 0), (dt(21, 30), 3), (dt(22, 30), 6)]),
    ("S5 single reading", "C2", dt(13), dt(14), [(dt(13, 30), 5)]),
    ("S6 off-peak only", "C3", dt(2), dt(4), [(dt(2, 0),  (dt(4), 14)]),
    ("S7 mid-peak only", "C1", dt(10), dt(12), [(dt(10, 0),  (dt(12), 22)])
    ("S8 duplicate timestamps", "C2" , dt(17), dt(19), [(dt(17, 0), (dt(18), 3), (dt(18), 4), (dt(18), 5), (dt(19), 9)]),
]

def main():
    net = ChargingNetwork()
    for cid, site in [("C1", "SITE-A"), ("C2", "SITE-A"), ("C3", "SITE-B")]:
        net.register_charger(cid, site)

    for label, charger, start, stop, readings in SCENARIO:
        sid = net.start_session("driver-" + label[:2], charger, start)
        for at, kwh in readings:
            net.record_meter_reading(sid, at, kwh)
        net.stop_session(sid, stop)
        inv = net.calculate_invoice(sid)
        print(f"\n=={label} {{sid} on {charger}} == 
        for line in inv.line:
            print(f" {line.from_time:%d %H:%M} -> {line.to_time:%d %H:%M} "
            f"{line.kwh:>8} kWh @ ${line.rate_applied} =${line.amount}")")
        print(f" session fee ${inv.session_fee} | replaced{inv.readings_replaced}"
        f" | TOTAL ${inv.total}")

    if__name__==__main__":
        main()