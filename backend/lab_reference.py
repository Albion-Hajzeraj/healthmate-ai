"""
Katalogu i analizave dhe vlerat e referencës.

Këtu ruhen analizat më të zakonshme të gjakut, njësia e tyre, kufijtë
"normalë" për të rriturit dhe një shpjegim i thjeshtë në shqip.

KUJDES: Vlerat e referencës ndryshojnë pak nga laboratori në laborator.
Kur fleta e analizës ka kufijtë e vet, ato kanë përparësi.
"""
import re

# Çdo analizë: emri, njësia, kufiri i poshtëm/sipërm (low/high),
# kufij të veçantë për femra (F) ose meshkuj (M) nëse ka,
# fjalë kyçe (aliases) për ta gjetur në tekstin e fletës së analizave,
# dhe shpjegimet "what" (çfarë është), "if_high" (nëse është e lartë), "if_low" (nëse është e ulët).
CATALOG: dict[str, dict] = {
    "glucose": {
        "name": "Glukoza në gjak (esëll)",
        "unit": "mg/dL", "low": 70, "high": 99,
        "aliases": ["glukoza", "glukozë", "glukoze", "glicemia", "glucose", "glu", "sheqeri"],
        "convert": {"unit": "mmol/L", "below": 35, "factor": 18.016},
        "what": "Sasia e sheqerit në gjak, e matur pa ngrënë (në mëngjes, esëll).",
        "if_high": "Sheqeri i lartë mund të tregojë rrezik për diabet ose diabet të pakontrolluar.",
        "if_low": "Sheqeri i ulët (hipoglicemia) mund të shkaktojë dridhje, djersitje dhe marramendje.",
    },
    "hba1c": {
        "name": "HbA1c (hemoglobina e glikuar)",
        "unit": "%", "low": 4.0, "high": 5.6,
        "aliases": ["hba1c", "hb a1c", "a1c", "hemoglobina e glikuar", "glikuar", "glikozil"],
        "what": "Tregon mesataren e sheqerit në gjak për 2-3 muajt e fundit.",
        "if_high": "5.7-6.4% konsiderohet paradiabet, 6.5% e lart sugjeron diabet.",
        "if_low": "Vlera të ulëta janë të rralla; mund të lidhen me anemi ose humbje gjaku.",
    },
    "chol_total": {
        "name": "Kolesteroli total",
        "unit": "mg/dL", "low": None, "high": 200,
        "aliases": ["kolesteroli total", "kolesterol total", "kolesteroli", "kolesterol", "cholesterol", "chol"],
        "convert": {"unit": "mmol/L", "below": 20, "factor": 38.67},
        "what": "Sasia e përgjithshme e yndyrës (kolesterolit) në gjak.",
        "if_high": "Kolesteroli i lartë rrit rrezikun për sëmundje të zemrës dhe enëve të gjakut.",
        "if_low": "",
    },
    "ldl": {
        "name": "LDL (kolesteroli 'i keq')",
        "unit": "mg/dL", "low": None, "high": 130,
        "aliases": ["ldl-c", "ldl"],
        "convert": {"unit": "mmol/L", "below": 15, "factor": 38.67},
        "what": "Kolesteroli që grumbullohet në muret e enëve të gjakut.",
        "if_high": "LDL i lartë është faktori kryesor i rrezikut për infarkt dhe goditje në tru.",
        "if_low": "",
    },
    "hdl": {
        "name": "HDL (kolesteroli 'i mirë')",
        "unit": "mg/dL", "low": 40, "high": None,
        "aliases": ["hdl-c", "hdl"],
        "convert": {"unit": "mmol/L", "below": 5, "factor": 38.67},
        "what": "Kolesteroli që ndihmon pastrimin e enëve të gjakut. Sa më i lartë, aq më mirë.",
        "if_high": "",
        "if_low": "HDL i ulët rrit rrezikun për sëmundje të zemrës. Lëvizja fizike ndihmon ta rrisë.",
    },
    "triglycerides": {
        "name": "Trigliceridet",
        "unit": "mg/dL", "low": None, "high": 150,
        "aliases": ["trigliceridet", "triglicerid", "triglycerides", "tg"],
        "convert": {"unit": "mmol/L", "below": 20, "factor": 88.57},
        "what": "Një lloj yndyre në gjak që vjen kryesisht nga ushqimi.",
        "if_high": "Trigliceridet e larta lidhen me ushqim të yndyrshëm/ëmbël, alkool dhe diabet.",
        "if_low": "",
    },
    "hemoglobin": {
        "name": "Hemoglobina",
        "unit": "g/dL", "low": 12.0, "high": 17.5,
        "F": (12.0, 15.5), "M": (13.5, 17.5),
        "aliases": ["hemoglobina", "hemoglobin", "hgb", "hb"],
        "convert": {"unit": "g/L", "above": 40, "factor": 0.1},
        "what": "Proteina në rruazat e kuqe që mbart oksigjenin në trup.",
        "if_high": "Mund të ndodhë te duhanpirësit, në dehidratim ose në disa sëmundje të gjakut.",
        "if_low": "Hemoglobina e ulët quhet anemi; shkakton lodhje, zbehje dhe mungesë fryme.",
    },
    "wbc": {
        "name": "Leukocitet (rruazat e bardha)",
        "unit": "x10⁹/L", "low": 4.0, "high": 11.0,
        "aliases": ["leukocitet", "leukocite", "leukociti", "wbc", "leu"],
        "what": "Qelizat që e mbrojnë trupin nga infeksionet.",
        "if_high": "Shpesh tregon infeksion ose inflamacion në trup.",
        "if_low": "Mund të tregojë imunitet të dobësuar ose efekt të disa barnave.",
    },
    "platelets": {
        "name": "Trombocitet",
        "unit": "x10⁹/L", "low": 150, "high": 450,
        "aliases": ["trombocitet", "trombocite", "trombociti", "platelets", "plt"],
        "what": "Qelizat që ndihmojnë mpiksjen e gjakut kur pritemi.",
        "if_high": "Mund të ndodhë pas infeksioneve, inflamacionit ose mungesës së hekurit.",
        "if_low": "Rrit rrezikun për gjakderdhje dhe mavijosje të lehta.",
    },
    "creatinine": {
        "name": "Kreatinina",
        "unit": "mg/dL", "low": 0.6, "high": 1.2,
        "F": (0.5, 1.1), "M": (0.7, 1.3),
        "aliases": ["kreatinina", "kreatinin", "creatinine", "crea", "krea"],
        "convert": {"unit": "µmol/L", "above": 20, "factor": 1 / 88.4},
        "what": "Mbetje e muskujve që e largojnë veshkat. Tregon si punojnë veshkat.",
        "if_high": "Mund të tregojë që veshkat nuk po filtrojnë mirë, ose dehidratim.",
        "if_low": "Zakonisht nuk është shqetësuese; mund të lidhet me masë të ulët muskulore.",
    },
    "urea": {
        "name": "Urea",
        "unit": "mg/dL", "low": 15, "high": 45,
        "aliases": ["urea", "ure", "urë"],
        "convert": {"unit": "mmol/L", "below": 12, "factor": 6.006},
        "what": "Mbetje nga zbërthimi i proteinave, e larguar nga veshkat.",
        "if_high": "Mund të tregojë dehidratim, ushqim shumë proteinik ose punë të dobët të veshkave.",
        "if_low": "Rrallë shqetësuese; mund të lidhet me ushqim të varfër në proteina.",
    },
    "uric_acid": {
        "name": "Acidi urik",
        "unit": "mg/dL", "low": 3.5, "high": 7.2,
        "F": (2.6, 6.0), "M": (3.5, 7.2),
        "aliases": ["acidi urik", "acid urik", "uric acid", "urat"],
        "what": "Mbetje që krijohet nga zbërthimi i disa ushqimeve (mish, alkool).",
        "if_high": "Acidi urik i lartë mund të shkaktojë gut (dhimbje e fortë në nyje).",
        "if_low": "Rrallë shqetësues.",
    },
    "alt": {
        "name": "ALT (GPT) - enzimë e mëlçisë",
        "unit": "U/L", "low": 7, "high": 56,
        "aliases": ["alt", "gpt", "sgpt", "alat"],
        "what": "Enzimë që gjendet kryesisht në mëlçi.",
        "if_high": "Mund të tregojë dëmtim ose lodhje të mëlçisë (yndyrë, alkool, barna, hepatit).",
        "if_low": "Zakonisht nuk ka rëndësi klinike.",
    },
    "ast": {
        "name": "AST (GOT) - enzimë e mëlçisë",
        "unit": "U/L", "low": 10, "high": 40,
        "aliases": ["ast", "got", "sgot", "asat"],
        "what": "Enzimë që gjendet në mëlçi, zemër dhe muskuj.",
        "if_high": "Mund të tregojë problem në mëlçi ose dëmtim muskulor.",
        "if_low": "Zakonisht nuk ka rëndësi klinike.",
    },
    "tsh": {
        "name": "TSH (tiroidja)",
        "unit": "mIU/L", "low": 0.4, "high": 4.0,
        "aliases": ["tsh", "tirotropina"],
        "what": "Hormon që tregon si punon gjëndra tiroide.",
        "if_high": "TSH i lartë zakonisht tregon tiroide që punon pak (hipotiroidizëm): lodhje, shtim peshe.",
        "if_low": "TSH i ulët zakonisht tregon tiroide tepër aktive: rrahje zemre, humbje peshe.",
    },
    "vitamin_d": {
        "name": "Vitamina D",
        "unit": "ng/mL", "low": 30, "high": 100,
        "aliases": ["25-oh vitamina d", "vitamina d3", "vitamina d", "vitamin d", "25-oh", "vit d", "vit. d"],
        "what": "Vitaminë e nevojshme për kocka të forta dhe imunitet.",
        "if_high": "Vlera shumë të larta ndodhin zakonisht nga marrja e tepërt e suplementeve.",
        "if_low": "Mungesa e vitaminës D është shumë e zakonshme; mund të shkaktojë kocka të dobëta dhe lodhje.",
    },
    "b12": {
        "name": "Vitamina B12",
        "unit": "pg/mL", "low": 200, "high": 900,
        "aliases": ["vitamina b12", "vitamin b12", "b12", "kobalamina"],
        "what": "Vitaminë e rëndësishme për nervat dhe prodhimin e gjakut.",
        "if_high": "Rrallë shqetësuese, zakonisht nga suplementet.",
        "if_low": "Mungesa mund të shkaktojë anemi, mpirje të duarve/këmbëve dhe harresë.",
    },
    "iron": {
        "name": "Hekuri (Fe)",
        "unit": "µg/dL", "low": 60, "high": 170,
        "aliases": ["hekuri", "hekur", "iron", "fe"],
        "what": "Mineral i nevojshëm për të prodhuar hemoglobinë.",
        "if_high": "Mund të ndodhë nga suplementet ose sëmundje që grumbullojnë hekur.",
        "if_low": "Hekuri i ulët është shkaku më i shpeshtë i anemisë.",
    },
    "ferritin": {
        "name": "Feritina",
        "unit": "ng/mL", "low": 30, "high": 400,
        "F": (15, 150), "M": (30, 400),
        "aliases": ["feritina", "ferritin", "feritin"],
        "what": "Tregon sa hekur ka të rezervuar trupi.",
        "if_high": "Mund të tregojë inflamacion, sëmundje të mëlçisë ose tepricë hekuri.",
        "if_low": "Rezervat e hekurit janë të ulëta - shpesh para se të shfaqet anemia.",
    },
    "crp": {
        "name": "CRP (proteina C-reaktive)",
        "unit": "mg/L", "low": None, "high": 5,
        "aliases": ["crp", "proteina c reaktive", "proteina c-reaktive", "pcr"],
        "what": "Shenjë e inflamacionit ose infeksionit në trup.",
        "if_high": "Tregon se në trup ka inflamacion ose infeksion; mjeku e lidh me simptomat.",
        "if_low": "",
    },
    "systolic": {
        "name": "Tensioni i sipërm (sistolik)",
        "unit": "mmHg", "low": 90, "high": 130,
        "aliases": ["sistolik", "systolic"],
        "what": "Presioni i gjakut kur zemra rrah (numri i parë, p.sh. 120 në 120/80).",
        "if_high": "Tensioni i lartë (hipertensioni) rrit rrezikun për infarkt dhe goditje në tru.",
        "if_low": "Tensioni i ulët mund të shkaktojë marramendje, sidomos kur ngriheni shpejt.",
    },
    "diastolic": {
        "name": "Tensioni i poshtëm (diastolik)",
        "unit": "mmHg", "low": 60, "high": 85,
        "aliases": ["diastolik", "diastolic"],
        "what": "Presioni i gjakut kur zemra pushon (numri i dytë, p.sh. 80 në 120/80).",
        "if_high": "Vlerë e lartë tregon tension të lartë; duhet ndjekur rregullisht.",
        "if_low": "Vlerë e ulët mund të shkaktojë lodhje dhe marramendje.",
    },
    "pulse": {
        "name": "Pulsi (rrahjet e zemrës)",
        "unit": "rrahje/min", "low": 60, "high": 100,
        "aliases": ["pulsi", "puls", "pulse", "frekuenca kardiake"],
        "what": "Sa herë rreh zemra në një minutë, në qetësi.",
        "if_high": "Puls i shpejtë mund të vijë nga stresi, kafeja, ethet ose probleme të zemrës/tiroides.",
        "if_low": "Puls i ngadaltë është normal te sportistët, por mund të shkaktohet edhe nga disa barna.",
    },
}

# Rendi në të cilin kërkohen analizat në tekst. Analizat më specifike
# vijnë para atyre të përgjithshme (p.sh. HbA1c para Hemoglobinës,
# LDL/HDL para Kolesterolit) që të mos ngatërrohen.
PARSE_ORDER = [
    "hba1c", "ldl", "hdl", "chol_total", "triglycerides", "glucose",
    "hemoglobin", "wbc", "platelets", "creatinine", "uric_acid", "urea",
    "alt", "ast", "tsh", "vitamin_d", "b12", "ferritin", "iron", "crp",
    "systolic", "diastolic", "pulse",
]


def reference_range(test_key: str, sex: str = "") -> tuple[float | None, float | None]:
    """Kthen kufijtë normalë (low, high) për një analizë, sipas gjinisë nëse ka."""
    item = CATALOG.get(test_key)
    if not item:
        return None, None
    if sex in ("F", "M") and sex in item:
        return item[sex]
    return item["low"], item["high"]


def evaluate(value: float, low: float | None, high: float | None) -> str:
    """Krahason vlerën me kufijtë: 'high', 'low', 'normal' ose 'unknown'."""
    if low is None and high is None:
        return "unknown"
    if high is not None and value > high:
        return "high"
    if low is not None and value < low:
        return "low"
    return "normal"


def explain(test_key: str, status: str) -> str:
    """Shpjegim i shkurtër në shqip për një analizë dhe statusin e saj."""
    item = CATALOG.get(test_key)
    if not item:
        return ""
    text = item["what"]
    extra = item.get(f"if_{status}", "") if status in ("high", "low") else ""
    return f"{text} {extra}".strip()


def public_catalog() -> list[dict]:
    """Katalogu pa fushat e brendshme - për t'u dërguar te frontendi."""
    out = []
    for key, item in CATALOG.items():
        out.append({
            "key": key, "name": item["name"], "unit": item["unit"],
            "low": item["low"], "high": item["high"],
            "F": item.get("F"), "M": item.get("M"), "what": item["what"],
        })
    return out


# --------------------------------------------------------------------------
# Leximi automatik i tekstit të fletës së analizave
# --------------------------------------------------------------------------
_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?)")


def _clean_rest(rest: str) -> str:
    """Heq pjesët që ngatërrojnë numrat: (kllapat) dhe shprehje si 10^9."""
    rest = re.sub(r"\([^)]*\)", " ", rest)
    rest = re.sub(r"\d+\s*[\^eE]\s*\d+", " ", rest)
    return rest


def parse_lab_text(text: str) -> list[dict]:
    """
    Gjen analizat e njohura në një tekst të ngjitur (copy/paste nga fleta e laboratorit).
    Për çdo rresht kërkon emrin e analizës dhe numrin e parë pas tij.
    Nëse vlera duket në njësi tjetër (p.sh. mmol/L), e konverton automatikisht.
    """
    found: list[dict] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip().lower()
        if not line:
            continue

        # Tensioni i shkruar si "130/85"
        bp = re.search(r"(tension|presion|ta\b|bp\b)[^\d]*(\d{2,3})\s*/\s*(\d{2,3})", line)
        if bp:
            for key, val in (("systolic", bp.group(2)), ("diastolic", bp.group(3))):
                if key not in seen:
                    seen.add(key)
                    found.append(_make_item(key, float(val), raw_line))
            continue

        for key in PARSE_ORDER:
            if key in seen:
                continue
            best_end = _alias_end(line, key)
            if best_end < 0:
                continue
            num = _NUMBER.search(_clean_rest(line[best_end:]))
            if not num:
                continue
            value = float(num.group(1).replace(",", "."))
            seen.add(key)
            found.append(_make_item(key, value, raw_line))
            break  # një analizë për rresht

    return found


def _alias_end(line: str, key: str) -> int:
    """Ku mbaron emri i analizës `key` brenda rreshtit (-1 nëse nuk gjendet)."""
    best_end = -1
    for alias in CATALOG[key]["aliases"]:
        m = re.search(r"(?<![a-zë0-9])" + re.escape(alias) + r"(?![a-zë])", line)
        if m and m.end() > best_end:
            best_end = m.end()
    return best_end


def match_test(name: str) -> str | None:
    """Gjen cilës analizë të katalogut i përket një emër, p.sh. 'Hemoglobina (HGB)' -> 'hemoglobin'."""
    line = name.strip().lower()
    for key in PARSE_ORDER:
        if _alias_end(line, key) >= 0:
            return key
    return None


def _unit_key(unit: str) -> str:
    """Njësi në formë të njëtrajtshme për krahasim: 'µmol/L' dhe 'umol/l' -> 'umol/l'."""
    return (unit or "").lower().replace(" ", "").replace("µ", "u").replace("μ", "u")


def _round(x: float) -> float:
    """Rrumbullakim i lexueshëm: 1.04 mbetet 1.04, 201.08 bëhet 201.1."""
    return round(x, 2) if abs(x) < 10 else round(x, 1)


def normalize_item(name: str, value: float, unit: str = "",
                   ref_low: float | None = None, ref_high: float | None = None) -> dict:
    """
    Merr një rresht të lexuar nga fleta (emri, vlera, njësia, kufijtë e laboratorit)
    dhe e përshtat me katalogun tonë:
      - njeh analizën (p.sh. 'Glukoza' -> 'glucose');
      - nëse njësia është tjetër (p.sh. mmol/L), konverton vlerën DHE kufijtë;
      - analizat që nuk janë në katalog ruhen si 'custom' me kufijtë e fletës.
    Kufijtë e fletës kanë përparësi, sepse janë të atij laboratori.
    """
    key = match_test(name)
    if not key:
        return {"test_key": "custom", "test_name": name.strip(), "value": value, "unit": unit.strip(),
                "ref_low": ref_low, "ref_high": ref_high, "note": ""}

    item = CATALOG[key]
    conv = item.get("convert")
    u = _unit_key(unit)
    factor = None
    if conv:
        if u and u == _unit_key(conv["unit"]):
            factor = conv["factor"]
        elif not u or u != _unit_key(item["unit"]):
            # Njësia mungon ose nuk e njohim: vendosim sipas madhësisë së numrit
            if ("below" in conv and value < conv["below"]) or ("above" in conv and value > conv["above"]):
                factor = conv["factor"]

    note = ""
    if factor:
        note = f"Në fletë: {value} {unit or conv['unit']}"
        value = _round(value * factor)
        ref_low = _round(ref_low * factor) if ref_low is not None else None
        ref_high = _round(ref_high * factor) if ref_high is not None else None

    return {"test_key": key, "test_name": item["name"], "value": value, "unit": item["unit"],
            "ref_low": ref_low, "ref_high": ref_high, "note": note}


def _make_item(key: str, value: float, source_line: str) -> dict:
    item = CATALOG[key]
    note = ""
    conv = item.get("convert")
    if conv:
        if ("below" in conv and value < conv["below"]) or ("above" in conv and value > conv["above"]):
            original = value
            value = round(value * conv["factor"], 2)
            note = f"Konvertuar nga {original} {conv['unit']}"
    return {
        "test_key": key, "test_name": item["name"], "value": value,
        "unit": item["unit"], "note": note, "source": source_line.strip(),
    }
