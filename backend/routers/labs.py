"""
Analizat: ruajtja, vlerësimi (normal / i lartë / i ulët), leximi automatik i tekstit
dhe leximi i fotos së fletës së analizave me raport nga asistenti.
"""
import base64
import re
import uuid
from datetime import date

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .. import lab_reference as ref
from ..database import UPLOADS_DIR, get_conn, rows
from ..services import ai_service
from .profile import load_profile
from .symptoms import list_symptoms
from .therapies import list_therapies

router = APIRouter(prefix="/api/labs", tags=["Analizat"])


class LabIn(BaseModel):
    test_key: str = "custom"
    test_name: str = ""
    value: float
    unit: str = ""
    ref_low: float | None = None
    ref_high: float | None = None
    taken_on: str = Field(default_factory=lambda: date.today().isoformat())
    note: str = ""


class ParseIn(BaseModel):
    text: str


def enrich(lab: dict, sex: str) -> dict:
    """Shton statusin (normal/i lartë/i ulët) dhe shpjegimin për një rezultat."""
    low, high = lab.get("ref_low"), lab.get("ref_high")
    if low is None and high is None:
        low, high = ref.reference_range(lab["test_key"], sex)
    lab["ref_low"], lab["ref_high"] = low, high
    lab["status"] = ref.evaluate(lab["value"], low, high)
    lab["explanation"] = ref.explain(lab["test_key"], lab["status"])
    return lab


def list_labs() -> list[dict]:
    sex = load_profile().get("sex", "")
    with get_conn() as conn:
        data = rows(conn.execute("SELECT * FROM lab_results ORDER BY taken_on DESC, id DESC"))
    return [enrich(l, sex) for l in data]


@router.get("/catalog")
def catalog():
    return ref.public_catalog()


@router.get("")
def get_labs():
    return list_labs()


def _insert(conn, lab: LabIn) -> int:
    item = ref.CATALOG.get(lab.test_key)
    name = lab.test_name or (item["name"] if item else "Analizë")
    unit = lab.unit or (item["unit"] if item else "")
    if not item:
        lab.test_key = "custom"
    cur = conn.execute(
        "INSERT INTO lab_results (test_key, test_name, value, unit, ref_low, ref_high, taken_on, note) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (lab.test_key, name, lab.value, unit, lab.ref_low, lab.ref_high, lab.taken_on, lab.note),
    )
    return cur.lastrowid


@router.post("")
def add_lab(lab: LabIn):
    with get_conn() as conn:
        new_id = _insert(conn, lab)
    return next(l for l in list_labs() if l["id"] == new_id)


@router.post("/bulk")
def add_many(labs: list[LabIn]):
    with get_conn() as conn:
        for lab in labs:
            _insert(conn, lab)
    return {"saved": len(labs)}


@router.post("/parse")
def parse_text(body: ParseIn):
    """Merr tekstin e ngjitur nga fleta e analizave dhe gjen vlerat e njohura."""
    sex = load_profile().get("sex", "")
    found = ref.parse_lab_text(body.text)
    for f in found:
        low, high = ref.reference_range(f["test_key"], sex)
        f["status"] = ref.evaluate(f["value"], low, high)
    return found


# --------------------------------------------------------------------------
# Foto e fletës së analizave -> vlerat -> raport
# --------------------------------------------------------------------------
MAX_IMAGE_BYTES = 8 * 1024 * 1024
STATUS_TXT = {"high": "MË E LARTË se normalja", "low": "MË E ULËT se normalja",
              "normal": "në rregull", "unknown": "pa kufij reference"}


class PhotoIn(BaseModel):
    image: str                      # foto si "data URL" (data:image/jpeg;base64,...)


class PhotoSaveIn(BaseModel):
    image: str | None = None
    taken_on: str
    items: list[LabIn]


def _decode_image(data_url: str) -> tuple[bytes, str]:
    """Kontrollon që është vërtet foto dhe jo shumë e madhe; kthen (bajtet, prapashtesa)."""
    m = re.match(r"data:image/(jpeg|jpg|png|webp);base64,(.+)", data_url, re.S)
    if not m:
        raise HTTPException(400, "Skedari nuk është foto (JPG, PNG ose WEBP).")
    try:
        raw = base64.b64decode(m.group(2), validate=True)
    except ValueError:
        raise HTTPException(400, "Fotoja është e dëmtuar.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Fotoja është shumë e madhe.")
    return raw, "jpg" if m.group(1) in ("jpeg", "jpg") else m.group(1)


@router.post("/photo/read")
async def read_photo(body: PhotoIn):
    """Hapi 1: lexon vlerat nga fotoja. Nuk ruan asgjë - përdoruesi i kontrollon së pari."""
    if not ai_service.vision_available():
        raise HTTPException(503, "Për leximin e fotove duhet një çelës Groq ose Gemini në skedarin .env.")
    _decode_image(body.image)
    try:
        data, provider = await ai_service.read_lab_image(body.image)
    except RuntimeError:
        raise HTTPException(502, "Fotoja nuk u lexua dot. Provoni përsëri, ose me një foto më të qartë.")

    sex = load_profile().get("sex", "")
    items = []
    for raw in data["items"]:
        item = ref.normalize_item(**raw)
        low, high = item["ref_low"], item["ref_high"]
        if low is None and high is None:
            low, high = ref.reference_range(item["test_key"], sex)
        item["range_low"], item["range_high"] = low, high   # kufijtë që shfaqen
        item["status"] = ref.evaluate(item["value"], low, high)
        items.append(item)
    return {"date": data["date"], "items": items, "provider": provider}


def _fmt(v: float) -> str:
    return f"{v:g}"


def _range_txt(low, high) -> str:
    if low is not None and high is not None:
        return f"{_fmt(low)}-{_fmt(high)}"
    if high is not None:
        return f"nën {_fmt(high)}"
    if low is not None:
        return f"mbi {_fmt(low)}"
    return "pa kufij"


def _offline_report(labs: list[dict]) -> str:
    """Raport i thjeshtë pa AI, kur asnjë shërbim nuk përgjigjet."""
    flagged = [l for l in labs if l["status"] in ("high", "low")]
    ok = [l for l in labs if l["status"] == "normal"]
    out = ["### Përmbledhje",
           f"Nga {len(labs)} analiza, {len(ok)} janë brenda normës dhe {len(flagged)} kërkojnë vëmendje. "
           "(Ky raport u bë pa asistentin, sepse shërbimi nuk ishte i arritshëm.)"]
    if ok:
        out += ["### Çfarë është në rregull"] + [f"- {l['test_name']}: {_fmt(l['value'])} {l['unit']}" for l in ok]
    if flagged:
        out.append("### Çfarë kërkon vëmendje")
        for l in flagged:
            out.append(f"- **{l['test_name']}**: {_fmt(l['value'])} {l['unit']} - {STATUS_TXT[l['status']]} "
                       f"(normale: {_range_txt(l['ref_low'], l['ref_high'])}). {l.get('explanation', '')}")
    out += ["### Pyetje për mjekun", "- Tregojini mjekut këtë raport dhe vlerat që kërkojnë vëmendje."]
    return "\n".join(out)


async def _write_report(labs: list[dict], taken_on: str) -> str:
    lines = "\n".join(
        f"- {l['test_name']}: {_fmt(l['value'])} {l['unit']} (normale: {_range_txt(l['ref_low'], l['ref_high'])})"
        f" -> {STATUS_TXT[l['status']]}" for l in labs)
    context = ai_service.build_context(load_profile(), list_labs(), list_therapies(), list_symptoms())
    messages = [
        {"role": "system", "content": ai_service.SYSTEM_PROMPT + "\n\n" + context},
        {"role": "user", "content": ai_service.REPORT_PROMPT.format(date=taken_on, lines=lines)},
    ]
    try:
        text, _ = await ai_service.ask(messages, temperature=0.3)
        return text
    except RuntimeError:
        return _offline_report(labs)


@router.post("/photo/save")
async def save_photo(body: PhotoSaveIn):
    """Hapi 2: ruan vlerat e kontrolluara + foton, dhe shkruan raportin."""
    if not body.items:
        raise HTTPException(400, "Nuk ka asnjë vlerë për të ruajtur.")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", body.taken_on):
        raise HTTPException(400, "Data nuk është e saktë.")

    image_file = None
    if body.image:
        raw, ext = _decode_image(body.image)
        image_file = f"fleta_{body.taken_on}_{uuid.uuid4().hex[:8]}.{ext}"
        (UPLOADS_DIR / image_file).write_bytes(raw)

    # Nëse e njëjta fletë dërgohet dy herë, vlerat që ekzistojnë nuk ruhen përsëri
    skipped = 0
    with get_conn() as conn:
        for lab in body.items:
            lab.taken_on = body.taken_on
            exists = conn.execute(
                "SELECT 1 FROM lab_results WHERE test_key = ? AND lower(test_name) = lower(?) "
                "AND taken_on = ? AND value = ?",
                (lab.test_key if lab.test_key in ref.CATALOG else "custom",
                 lab.test_name or ref.CATALOG.get(lab.test_key, {}).get("name", ""), lab.taken_on, lab.value),
            ).fetchone()
            if exists:
                skipped += 1
                continue
            _insert(conn, lab)

    sex = load_profile().get("sex", "")
    saved = [enrich(lab.model_dump(), sex) for lab in body.items]
    content = await _write_report(saved, body.taken_on)

    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO lab_reports (taken_on, content, image_file, item_count) VALUES (?, ?, ?, ?)",
            (body.taken_on, content, image_file, len(saved)))
        report = dict(conn.execute("SELECT * FROM lab_reports WHERE id = ?", (cur.lastrowid,)).fetchone())
    report["saved"], report["skipped"] = len(saved) - skipped, skipped
    return report


@router.get("/reports")
def get_reports():
    with get_conn() as conn:
        return rows(conn.execute("SELECT * FROM lab_reports ORDER BY taken_on DESC, id DESC"))


@router.get("/reports/{rid}/image")
def report_image(rid: int):
    with get_conn() as conn:
        row = conn.execute("SELECT image_file FROM lab_reports WHERE id = ?", (rid,)).fetchone()
    if not row or not row["image_file"] or not (UPLOADS_DIR / row["image_file"]).exists():
        raise HTTPException(404, "Fotoja nuk u gjet")
    return FileResponse(UPLOADS_DIR / row["image_file"])


@router.delete("/reports/{rid}")
def delete_report(rid: int):
    """Fshin raportin dhe foton. Vlerat e analizave mbeten në historik."""
    with get_conn() as conn:
        row = conn.execute("SELECT image_file FROM lab_reports WHERE id = ?", (rid,)).fetchone()
        conn.execute("DELETE FROM lab_reports WHERE id = ?", (rid,))
    if row and row["image_file"]:
        (UPLOADS_DIR / row["image_file"]).unlink(missing_ok=True)
    return {"ok": True}


@router.delete("/{lab_id}")
def delete_lab(lab_id: int):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM lab_results WHERE id = ?", (lab_id,))
    if cur.rowcount == 0:
        raise HTTPException(404, "Analiza nuk u gjet")
    return {"ok": True}
