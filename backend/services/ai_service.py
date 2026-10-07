"""
Shërbimi i asistentit (Inteligjenca Artificiale).

Të gjithë ofruesit e mëposhtëm përdorin të njëjtin format ("OpenAI-compatible"):
dërgojmë një listë mesazhesh dhe marrim përgjigjen. Kështu një funksion i
vetëm mjafton për të gjithë.

Radha e provimit:
  1. Groq        (falas, kërkon çelës GROQ_API_KEY)
  2. Gemini      (falas, kërkon çelës GEMINI_API_KEY)
  3. OpenRouter  (modele falas, kërkon çelës OPENROUTER_API_KEY)
  4. Pollinations(falas, PA çelës - punon menjëherë)
Nëse një ofrues dështon, provohet i radhës.
"""
import asyncio
import json
import os
import re

import httpx


def _providers() -> list[dict]:
    """Lista e ofruesve që mund të përdoren tani, sipas çelësave në .env."""
    providers = []
    if os.getenv("GROQ_API_KEY"):
        providers.append({
            "name": "Groq",
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "key": os.getenv("GROQ_API_KEY"),
            "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        })
    if os.getenv("GEMINI_API_KEY"):
        providers.append({
            "name": "Google Gemini",
            "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "key": os.getenv("GEMINI_API_KEY"),
            "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        })
    if os.getenv("OPENROUTER_API_KEY"):
        providers.append({
            "name": "OpenRouter",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "key": os.getenv("OPENROUTER_API_KEY"),
            "model": os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
        })
    # Gjithmonë në fund: Pollinations, që nuk kërkon çelës
    providers.append({
        "name": "Pollinations",
        "url": "https://text.pollinations.ai/openai",
        "key": None,
        "model": os.getenv("POLLINATIONS_MODEL", "openai"),
    })
    return providers


def status() -> dict:
    """Cili ofrues do të përdoret i pari (për faqen e Profilit)."""
    p = _providers()
    v = _vision_providers()
    return {"active": p[0]["name"], "model": p[0]["model"], "chain": [x["name"] for x in p],
            "vision": v[0]["name"] if v else None, "vision_model": v[0]["model"] if v else None}


async def ask(messages: list[dict], temperature: float = 0.4) -> tuple[str, str]:
    """
    Dërgon mesazhet te ofruesi i parë që punon.
    Kthen (teksti_i_përgjigjes, emri_i_ofruesit).
    """
    errors = []
    async with httpx.AsyncClient(timeout=90) as client:
        for p in _providers():
            headers = {"Content-Type": "application/json"}
            if p["key"]:
                headers["Authorization"] = f"Bearer {p['key']}"
            body = {"model": p["model"], "messages": messages, "temperature": temperature}
            # Shërbimi pa çelës (Pollinations) ka kufi përdorimi: kur thotë
            # "prit pak" (kodet 402/429), presim dhe provojmë përsëri.
            waits = [0, 8, 15] if p["key"] is None else [0]
            for wait in waits:
                await asyncio.sleep(wait)
                try:
                    r = await client.post(p["url"], json=body, headers=headers)
                    if r.status_code in (402, 429, 503) and wait != waits[-1]:
                        continue
                    r.raise_for_status()
                    content = r.json()["choices"][0]["message"]["content"]
                    if content and content.strip():
                        return content.strip(), p["name"]
                    errors.append(f"{p['name']}: përgjigje bosh")
                except Exception as e:  # provo ofruesin tjetër
                    errors.append(f"{p['name']}: {type(e).__name__}")
                break
    raise RuntimeError("; ".join(errors))


# --------------------------------------------------------------------------
# Leximi i fotos së fletës së analizave (modele që "shohin" foto)
# --------------------------------------------------------------------------
def _vision_providers() -> list[dict]:
    """Ofruesit që mund të lexojnë foto. Të dy kanë plan falas, por kërkojnë çelës."""
    providers = []
    if os.getenv("GROQ_API_KEY"):
        providers.append({
            "name": "Groq",
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "key": os.getenv("GROQ_API_KEY"),
            "model": os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b"),
            # JSON i pastër dhe pa "mendimet" e modelit në përgjigje
            "extra": {"response_format": {"type": "json_object"}, "reasoning_format": "hidden"},
        })
    if os.getenv("GEMINI_API_KEY"):
        providers.append({
            "name": "Google Gemini",
            "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "key": os.getenv("GEMINI_API_KEY"),
            "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            "extra": {"response_format": {"type": "json_object"}},
        })
    return providers


def vision_available() -> bool:
    return bool(_vision_providers())


READ_SHEET_PROMPT = """You are reading a photo of a medical laboratory results sheet.
Return ONLY a JSON object in this exact shape:
{"date": "YYYY-MM-DD or null",
 "items": [{"name": "test name exactly as written", "value": number,
            "unit": "unit as written", "ref_low": number or null, "ref_high": number or null}]}
Rules:
- Copy every test result row. Copy numbers EXACTLY as printed; never guess or calculate.
- Use "." as the decimal separator.
- Reference range "3.9 - 6.1" -> ref_low 3.9, ref_high 6.1. "< 5.2" -> ref_low null, ref_high 5.2.
  "> 1.0" -> ref_low 1.0, ref_high null. No range -> both null.
- If a value is not a number (e.g. "negativ"), skip that row.
- "date" is the sample/collection date on the sheet, if present.
- If the image is not a lab results sheet, return {"date": null, "items": []}."""


def _extract_json(text: str) -> dict:
    """Nxjerr objektin JSON nga përgjigja, edhe nëse modeli shtoi tekst rreth tij."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("Përgjigja nuk ka JSON")
    return json.loads(text[start:end + 1])


def _to_number(v) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return float(str(v).replace(",", ".").strip())
    except ValueError:
        return None


async def read_lab_image(data_url: str) -> tuple[dict, str]:
    """
    Dërgon foton te një model që lexon foto dhe kthen (të_dhënat, ofruesi).
    Modeli vetëm KOPJON numrat; vlerësimin (normal / i lartë / i ulët)
    e bën më pas kodi ynë me rregulla të sakta.
    """
    messages = [{"role": "user", "content": [
        {"type": "text", "text": READ_SHEET_PROMPT},
        {"type": "image_url", "image_url": {"url": data_url}},
    ]}]
    errors = []
    async with httpx.AsyncClient(timeout=120) as client:
        for p in _vision_providers():
            body = {"model": p["model"], "messages": messages, "temperature": 0, **p["extra"]}
            try:
                r = await client.post(p["url"], json=body, headers={"Authorization": f"Bearer {p['key']}"})
                r.raise_for_status()
                data = _extract_json(r.json()["choices"][0]["message"]["content"])
            except Exception as e:
                errors.append(f"{p['name']}: {type(e).__name__}")
                continue
            items = []
            for it in data.get("items") or []:
                value = _to_number(it.get("value"))
                name = str(it.get("name") or "").strip()
                if value is None or not name:
                    continue
                items.append({"name": name, "value": value, "unit": str(it.get("unit") or "").strip(),
                              "ref_low": _to_number(it.get("ref_low")), "ref_high": _to_number(it.get("ref_high"))})
            date = data.get("date")
            if not (isinstance(date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)):
                date = None
            return {"date": date, "items": items}, p["name"]
    raise RuntimeError("; ".join(errors) or "Nuk ka asnjë shërbim për leximin e fotove")


REPORT_PROMPT = """Më poshtë janë analizat e mia të reja të datës {date}:
{lines}

Shkruaj një RAPORT të qartë për mua, në shqip të thjeshtë, me këto pjesë
(secila me titull që fillon me ###):
### Përmbledhje
2-3 fjali: si janë analizat në përgjithësi.
### Çfarë është në rregull
### Çfarë kërkon vëmendje
Për çdo vlerë jashtë normës: vlera ime, kufiri normal, çfarë mund të nënkuptojë.
### Krahasimi me analizat e mëparshme
Vetëm nëse kam analiza më të vjetra për të njëjtat teste; përndryshe shkruaj se kjo është matja e parë.
### Çfarë mund të bëj vetë
Këshilla praktike për ushqimin, lëvizjen, gjumin.
### Pyetje për mjekun
2-4 pyetje konkrete që t'ia bëj mjekut.

Mos përdor tabela - vetëm tekst dhe lista me "-".
Mos shpik vlera që nuk janë në listë. Mos jep diagnozë dhe mos ndrysho terapinë."""


# --------------------------------------------------------------------------
# Udhëzimet për asistentin (system prompt)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """Ti je "Asistenti" i aplikacionit HealthMate - një ndihmës i sjellshëm
shëndetësor për të moshuarit dhe familjet e tyre. Flet GJITHMONË në shqip të thjeshtë.

Rregullat e tua:
- Shkruaj shkurt dhe qartë: fjali të shkurtra, pa terma të ndërlikuar mjekësorë.
  Nëse përdor një term, shpjegoje me fjalë të thjeshta.
- Mos përdor emoji. Mos përdor tabela. Përdor lista të shkurtra kur ndihmon.
- Ti NUK je mjek dhe nuk vendos diagnoza. Jep informacion, shpjegime dhe këshilla
  të përgjithshme, dhe kur duhet, sugjero që të flasin me mjekun e tyre.
- MOS sugjero kurrë ndalimin, ndryshimin e dozës ose fillimin e një bari pa mjekun.
- Nëse simptomat tingëllojnë urgjente (dhimbje gjoksi, vështirësi në frymëmarrje,
  dobësi në njërën anë të trupit, të folur i ngatërruar, gjakderdhje e madhe,
  humbje vetëdijeje), thuaj qartë në fillim: "Telefononi menjëherë 112.", pastaj
  jep 2-3 hapa të thjeshtë çfarë të bëjë derisa të vijë ndihma.
- Përdor të dhënat e pacientit më poshtë (analizat, terapitë, simptomat)
  për të dhënë përgjigje personale. P.sh. kontrollo nëse një bar i ri mund të
  ndikojë te barnat ekzistuese ose te alergjitë.
- Ji i ngrohtë dhe inkurajues, si një infermier i durueshëm.
"""


def build_context(profile: dict, labs: list[dict], therapies: list[dict], symptoms: list[dict]) -> str:
    """Përmbledh historikun e pacientit në tekst, që asistenti ta njohë."""
    lines = ["TË DHËNAT E PACIENTIT:"]
    if profile.get("name"):
        lines.append(f"- Emri: {profile['name']}")
    if profile.get("birth_year"):
        lines.append(f"- Viti i lindjes: {profile['birth_year']}")
    if profile.get("sex"):
        lines.append(f"- Gjinia: {'femër' if profile['sex'] == 'F' else 'mashkull'}")
    if profile.get("height_cm") and profile.get("weight_kg"):
        lines.append(f"- Gjatësia {profile['height_cm']} cm, pesha {profile['weight_kg']} kg")
    lines.append(f"- Alergji: {profile.get('allergies') or 'nuk janë shënuar'}")
    lines.append(f"- Sëmundje kronike: {profile.get('conditions') or 'nuk janë shënuar'}")

    active = [t for t in therapies if not t.get("end_date")]
    past = [t for t in therapies if t.get("end_date")]
    lines.append("\nTERAPIA AKTUALE:")
    lines += [f"- {t['medication']} {t.get('dose') or ''} ({t.get('reason') or 'pa arsye të shënuar'}), "
              f"që nga {t.get('start_date') or '?'}" for t in active] or ["- asnjë"]
    if past:
        lines.append("\nTERAPI TË MËPARSHME:")
        lines += [f"- {t['medication']} {t.get('dose') or ''}, {t.get('start_date') or '?'} deri {t['end_date']}"
                  for t in past[:10]]

    lines.append("\nANALIZAT E FUNDIT:")
    status_txt = {"high": "E LARTË", "low": "E ULËT", "normal": "normale", "unknown": ""}
    lines += [f"- {l['taken_on']}: {l['test_name']} = {l['value']} {l.get('unit') or ''} "
              f"{status_txt.get(l.get('status', ''), '')}" for l in labs[:40]] or ["- asnjë"]

    lines.append("\nSIMPTOMAT E FUNDIT:")
    lines += [f"- {s.get('started_on') or s['created_at'][:10]}: {s['description']} "
              f"(rëndësia {s.get('severity')}/10)" for s in symptoms[:10]] or ["- asnjë"]
    return "\n".join(lines)


# Fjalë që tregojnë urgjencë - kontrollohen PARA se të pyetet AI-ja,
# që paralajmërimi të dalë edhe pa internet.
EMERGENCY_WORDS = [
    "dhimbje gjoksi", "dhimbje në gjoks", "dhimbje ne gjoks", "më dhemb gjoksi", "me dhemb gjoksi",
    "shtrëngim në gjoks", "shtrengim ne gjoks",
    "nuk marr frymë", "nuk marr fryme", "s'marr frymë", "vështirësi në frymëmarrje",
    "veshtiresi ne frymemarrje", "po mbytem",
    "humba vetëdijen", "humba vetedijen", "rashë pa ndjenja", "rashe pa ndjenja",
    "nuk e lëviz dorën", "nuk e leviz doren", "fytyra më është shtrembëruar", "goja e shtrembër",
    "nuk mund të flas", "paralizë", "paralize",
    "gjakderdhje", "po më rrjedh gjak", "vjella gjak", "vjell gjak",
    "vetëvras", "vetevras", "dua të vdes", "dua te vdes",
    "helmim", "piva shumë tableta", "piva shume tableta",
]


def is_emergency(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in EMERGENCY_WORDS)


def offline_answer(question: str, labs: list[dict], therapies: list[dict]) -> str:
    """
    Përgjigje rezervë kur asnjë shërbim AI nuk është i arritshëm.
    Nuk "mendon" si AI, por përdor të dhënat e ruajtura që përdoruesi
    të marrë të paktën një përmbledhje të dobishme.
    """
    q = question.lower()
    parts = ["Asistenti nuk është i lidhur tani (mungon interneti ose shërbimi është i zënë). "
             "Ja çfarë mund t'ju them nga të dhënat tuaja:"]

    if any(w in q for w in ("analiz", "rezultat", "vlera", "glukoz", "kolesterol", "sheqer", "hemoglobin")):
        seen, flagged = set(), []
        for l in labs:  # labs janë të renditura nga më e reja
            key = l["test_key"] if l["test_key"] != "custom" else l["test_name"]
            if key in seen:
                continue
            seen.add(key)
            if l.get("status") in ("high", "low"):
                flagged.append(l)
        if not labs:
            parts.append("- Nuk keni ende analiza të ruajtura.")
        elif not flagged:
            parts.append("- Të gjitha analizat tuaja të fundit janë brenda kufijve normalë.")
        else:
            for l in flagged:
                word = "më e lartë" if l["status"] == "high" else "më e ulët"
                parts.append(f"- **{l['test_name']}**: {l['value']} {l.get('unit', '')} - {word} se normalja. "
                             f"{l.get('explanation', '')}")
    elif any(w in q for w in ("bar", "terapi", "tablet", "ilaç")):
        active = [t for t in therapies if not t.get("end_date")]
        if active:
            parts.append("Barnat që merrni tani:")
            parts += [f"- {t['medication']} {t.get('dose') or ''}" for t in active]
        else:
            parts.append("- Nuk keni barna aktive të shënuara.")
        parts.append("Për pyetje mbi ndërveprimin e barnave, pyesni farmacistin ose mjekun.")
    else:
        parts.append("- Ruani pyetjen dhe provoni përsëri pas një minute.")

    parts.append("\nNëse ndiheni keq, mos prisni: kontaktoni mjekun tuaj ose telefononi 112.")
    return "\n".join(parts)
