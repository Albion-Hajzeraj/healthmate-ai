"""Simptomat: shënimi i simptomave të reja me rëndësinë (1-10) dhe datën."""
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..database import get_conn, rows

router = APIRouter(prefix="/api/symptoms", tags=["Simptomat"])


class SymptomIn(BaseModel):
    description: str
    severity: int = Field(default=5, ge=1, le=10)
    started_on: str = Field(default_factory=lambda: date.today().isoformat())
    notes: str = ""


def list_symptoms() -> list[dict]:
    with get_conn() as conn:
        return rows(conn.execute("SELECT * FROM symptoms ORDER BY started_on DESC, id DESC"))


@router.get("")
def get_symptoms():
    return list_symptoms()


@router.post("")
def add_symptom(s: SymptomIn):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO symptoms (description, severity, started_on, notes) VALUES (?, ?, ?, ?)",
            (s.description, s.severity, s.started_on, s.notes),
        )
    return {"id": cur.lastrowid}


@router.delete("/{sid}")
def delete_symptom(sid: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM symptoms WHERE id = ?", (sid,))
    return {"ok": True}
