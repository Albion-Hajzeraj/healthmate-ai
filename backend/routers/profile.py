"""Profili i përdoruesit: të dhënat personale, alergjitë, mjeku, kontakti i urgjencës."""
from fastapi import APIRouter
from pydantic import BaseModel

from ..database import get_conn

router = APIRouter(prefix="/api/profile", tags=["Profili"])


class Profile(BaseModel):
    name: str = ""
    birth_year: int | None = None
    sex: str = ""
    country: str = "ALB"
    height_cm: float | None = None
    weight_kg: float | None = None
    allergies: str = ""
    conditions: str = ""
    doctor_name: str = ""
    doctor_phone: str = ""
    emergency_name: str = ""
    emergency_phone: str = ""


def load_profile() -> dict:
    with get_conn() as conn:
        return dict(conn.execute("SELECT * FROM profile WHERE id = 1").fetchone())


@router.get("")
def get_profile():
    return load_profile()


@router.put("")
def save_profile(p: Profile):
    data = p.model_dump()
    cols = ", ".join(f"{k} = ?" for k in data)
    with get_conn() as conn:
        conn.execute(f"UPDATE profile SET {cols} WHERE id = 1", list(data.values()))
    return load_profile()
