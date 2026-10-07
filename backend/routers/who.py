"""Të dhënat nga Organizata Botërore e Shëndetësisë (OBSH / WHO)."""
from fastapi import APIRouter

from ..services import who_service
from .profile import load_profile

router = APIRouter(prefix="/api/who", tags=["OBSH"])


@router.get("/countries")
def countries():
    return [{"code": k, "name": v} for k, v in who_service.COUNTRIES.items()]


@router.get("/indicators")
async def indicators(country: str | None = None):
    return await who_service.get_indicators(country or load_profile().get("country") or "ALB")


@router.get("/news")
async def news():
    return await who_service.get_news()
