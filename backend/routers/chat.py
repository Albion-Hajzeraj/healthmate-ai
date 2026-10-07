"""
Biseda me asistentin.

Sa herë që përdoruesi shkruan, i dërgojmë AI-së:
  1. udhëzimet (si të sillet),
  2. historikun e pacientit (profili, analizat, terapia, simptomat),
  3. 10 mesazhet e fundit të bisedës,
  4. pyetjen e re.
Kështu asistenti "e mban mend" pacientin.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from ..database import get_conn, rows
from ..services import ai_service
from .labs import list_labs
from .profile import load_profile
from .symptoms import list_symptoms
from .therapies import list_therapies

router = APIRouter(prefix="/api/chat", tags=["Asistenti"])

EMERGENCY_TEXT = ("KUJDES: Ajo që përshkruani mund të jetë urgjente. "
                  "Telefononi menjëherë 112 ose kërkoni ndihmë nga dikush pranë jush.")

class ChatIn(BaseModel):
    message: str


def _save(role: str, content: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO chat_messages (role, content) VALUES (?, ?)", (role, content))
        return dict(conn.execute("SELECT * FROM chat_messages WHERE id = ?", (cur.lastrowid,)).fetchone())


def _context_messages() -> list[dict]:
    context = ai_service.build_context(load_profile(), list_labs(), list_therapies(), list_symptoms())
    return [{"role": "system", "content": ai_service.SYSTEM_PROMPT + "\n\n" + context}]


@router.get("/history")
def history():
    with get_conn() as conn:
        return rows(conn.execute("SELECT * FROM chat_messages ORDER BY id"))


@router.delete("/history")
def clear_history():
    with get_conn() as conn:
        conn.execute("DELETE FROM chat_messages")
    return {"ok": True}


@router.post("")
async def send(body: ChatIn):
    text = body.message.strip()
    user_msg = _save("user", text)
    emergency = ai_service.is_emergency(text)

    with get_conn() as conn:
        recent = rows(conn.execute(
            "SELECT role, content FROM chat_messages ORDER BY id DESC LIMIT 11"))[::-1]
    messages = _context_messages() + [{"role": r["role"], "content": r["content"]} for r in recent]

    try:
        answer, provider = await ai_service.ask(messages)
    except RuntimeError:
        # Asnjë shërbim AI nuk u përgjigj: jepim përgjigjen lokale nga të dhënat
        answer, provider = ai_service.offline_answer(text, list_labs(), list_therapies()), None

    # Paralajmërimi i urgjencës del gjithmonë i pari, edhe pa AI
    if emergency and (provider is None or "112" not in answer):
        answer = EMERGENCY_TEXT + "\n\n" + answer

    reply = _save("assistant", answer)
    return {"user": user_msg, "reply": reply, "emergency": emergency, "provider": provider}


@router.post("/explain-labs")
async def explain_labs():
    """Kërkon nga asistenti një shpjegim të thjeshtë të analizave të fundit."""
    labs = list_labs()
    if not labs:
        return {"text": "Nuk keni ende analiza të ruajtura."}
    latest_date = labs[0]["taken_on"]
    question = (f"Më shpjego me fjalë të thjeshta analizat e mia të datës {latest_date}. "
                "Thuaj cilat janë në rregull, cilat jo, çfarë mund të bëj vetë (ushqim, lëvizje), "
                "dhe çfarë duhet të pyes mjekun. Krahaso me analizat e mëparshme nëse ka.")
    _save("user", question)
    try:
        answer, _ = await ai_service.ask(_context_messages() + [{"role": "user", "content": question}])
    except RuntimeError:
        answer = ai_service.offline_answer("analizat", labs, list_therapies())
    _save("assistant", answer)
    return {"text": answer}


@router.get("/status")
def ai_status():
    return ai_service.status()
