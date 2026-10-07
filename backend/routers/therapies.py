"""Terapia: barnat aktuale dhe të mëparshme, si dhe shënimi i dozave të marra sot."""
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_conn, rows

router = APIRouter(prefix="/api/therapies", tags=["Terapia"])

SLOTS = ["morning", "noon", "evening", "night"]


class TherapyIn(BaseModel):
    medication: str
    dose: str = ""
    times: list[str] = []          # p.sh. ["morning", "evening"]
    reason: str = ""
    start_date: str | None = None
    end_date: str | None = None
    notes: str = ""


class DoseIn(BaseModel):
    slot: str
    taken: bool


def _row_out(t: dict) -> dict:
    t["times"] = [x for x in (t.get("times") or "").split(",") if x]
    t["active"] = not t.get("end_date")
    return t


def list_therapies() -> list[dict]:
    with get_conn() as conn:
        data = rows(conn.execute(
            "SELECT * FROM therapies ORDER BY (end_date IS NOT NULL), start_date DESC, id DESC"))
    return [_row_out(t) for t in data]


@router.get("")
def get_therapies():
    return list_therapies()


@router.post("")
def add_therapy(t: TherapyIn):
    times = ",".join(s for s in t.times if s in SLOTS)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO therapies (medication, dose, times, reason, start_date, end_date, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (t.medication, t.dose, times, t.reason, t.start_date or date.today().isoformat(),
             t.end_date or None, t.notes),
        )
    return {"id": cur.lastrowid}


@router.put("/{tid}")
def update_therapy(tid: int, t: TherapyIn):
    times = ",".join(s for s in t.times if s in SLOTS)
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE therapies SET medication=?, dose=?, times=?, reason=?, start_date=?, end_date=?, notes=? "
            "WHERE id=?",
            (t.medication, t.dose, times, t.reason, t.start_date, t.end_date or None, t.notes, tid),
        )
    if cur.rowcount == 0:
        raise HTTPException(404, "Terapia nuk u gjet")
    return {"ok": True}


@router.post("/{tid}/stop")
def stop_therapy(tid: int):
    """Shënon terapinë si të përfunduar sot (ruhet në historik)."""
    with get_conn() as conn:
        conn.execute("UPDATE therapies SET end_date = ? WHERE id = ?", (date.today().isoformat(), tid))
    return {"ok": True}


@router.delete("/{tid}")
def delete_therapy(tid: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM therapies WHERE id = ?", (tid,))
    return {"ok": True}


@router.get("/today")
def today_doses():
    """Lista e dozave që duhen marrë sot dhe cilat janë shënuar si të marra."""
    today = date.today().isoformat()
    active = [t for t in list_therapies() if t["active"]]
    with get_conn() as conn:
        taken = {(r["therapy_id"], r["slot"]) for r in
                 conn.execute("SELECT therapy_id, slot FROM dose_log WHERE day = ?", (today,))}
    out = []
    for slot in SLOTS:
        for t in active:
            if slot in t["times"]:
                out.append({"therapy_id": t["id"], "medication": t["medication"], "dose": t["dose"],
                            "slot": slot, "taken": (t["id"], slot) in taken})
    return out


@router.post("/{tid}/dose")
def mark_dose(tid: int, body: DoseIn):
    today = date.today().isoformat()
    with get_conn() as conn:
        if body.taken:
            conn.execute("INSERT OR IGNORE INTO dose_log (therapy_id, day, slot) VALUES (?, ?, ?)",
                         (tid, today, body.slot))
        else:
            conn.execute("DELETE FROM dose_log WHERE therapy_id=? AND day=? AND slot=?",
                         (tid, today, body.slot))
    return {"ok": True}
