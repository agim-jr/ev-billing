from datetime import datetime
from decimal import Decimal, InvalidOperation

from billing import build_invoice
from models import (BillingError, Charger, ChargingSession, Invoice, MeterReading, )

class ChargingNetwork:
    def __init__(self):
        self.chargers: dict[str, Charger] = {}
        self.sessions: dict[str, ChargingSession] = {}
        self._next_id = 1

    def register_charger(self, charger_id: str, site_id: str) -> Charger:
        if charger_id in self.chargers:
            raise BillingError(f"Charger {charger_id} already registered")
        charger = Charger(charger_id=charger_id, site_id=site_id)
        self.chargers[charger_id] = charger
        return charger

    def start_session(self, driver_id: str, charger_id: str, started_at: datetime) -> ChargingSession:
        if charger_id not in self.chargers:
            raise BillingError(f"Unknown charger {charger_id}")
        if any(s.charger_id == charger_id and s.status == SessionStatus.RUNNING for s in self.sessions.values()):
            raise BillingError(f"Charger {charger_id} already has a running session")
        session_id = f"S-{self._next_id:04d}"
        self._next_id += 1
        session = ChargingSession(session_id=session_id, driver_id=driver_id, charger_id=charger_id, started_at=started_at)
        self.sessions[session_id] = session
        return session_id

    def record_meter_reading(self, session_id: str, at: datetime, cumlative_kwh) -> bool:
      session =self.sessions.get(session_id)
      if session.status == SessionStatus.STOPPED:
        raise BillingError("Session is stopped; readinfs rejected")
      if at < session.started_at:
        raise BillingError("Reading percedes session start time")
      try:
        value = Decimal(str(cumlative_kwh))
      except InvalidOperation:
        raise BillingError("Invalid kWh value")
      if not value.is_finite() or value < 0:
        raise BillingError("kWh must be a non-negative finite number")
      session.meter_readings.append(MeterReading(at, value))
      return True

    def stop_session(self, session_id: str, 
                     stopped_at: datetime) -> ChargingSession:
        session = self._get(session_id)
        if session.status == SessionStatus.STOPPED:
            raise BillingError("Session already stopped")
        if stopped_at < session.started_at:
            raise BillingError("stoppedAt precedes startedAt; session remiains open")
        session.meter_readings = [r for r in session.meter_readings 
                                  if r.at <= stopped_at]
        session.stopped_at = stopped_at
        session.status = SessionStatus.STOPPED
        return session
        
    def calculate_invoice(self, session_id: str) -> Invoice:
        session = self._get(session_id)
        if session.status != SessionStatus.STOPPED:
            raise BillingError("Cannot invoice a running session")
        return build_invoice(session)

    def _get(self, session_id: str) -> ChargingSession:
        try:
            return self.sessions[session_id]
        except KeyError:
            raise BillingError(f"Unknown session {session_id}") from None
from models import SessionStatus
