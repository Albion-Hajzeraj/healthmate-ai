"""
Shërbimi i Organizatës Botërore të Shëndetësisë (OBSH / WHO).

Përdorim dy API publike dhe FALAS të OBSH-së (pa çelës):
  1. GHO OData API  -> statistika shëndetësore për çdo shtet
     https://ghoapi.azureedge.net/api/
  2. WHO News API   -> lajmet dhe njoftimet për shpërthime sëmundjesh
     https://www.who.int/api/news/

Përgjigjet ruhen përkohësisht (cache) për 6 orë, që aplikacioni të jetë
i shpejtë dhe të mos e ngarkojë serverin e OBSH-së.
"""
import asyncio
import time

import httpx

GHO_URL = "https://ghoapi.azureedge.net/api"
NEWS_URL = "https://www.who.int/api/news"
CACHE_SECONDS = 6 * 60 * 60

# Treguesit (indikatorët) që shfaqim, me shpjegim në shqip.
INDICATORS = [
    {"code": "WHOSIS_000001", "title": "Jetëgjatësia mesatare", "unit": "vjet",
     "info": "Sa vjet jeton mesatarisht një person i lindur në këtë shtet."},
    {"code": "WHOSIS_000002", "title": "Jetëgjatësia e shëndetshme", "unit": "vjet",
     "info": "Sa vjet jeton mesatarisht një person pa sëmundje serioze."},
    {"code": "NCD_HYP_PREVALENCE_A", "title": "Tensioni i lartë", "unit": "%",
     "info": "Përqindja e të rriturve (30-79 vjeç) me hipertension."},
    {"code": "NCD_DIABETES_PREVALENCE_AGESTD", "title": "Diabeti", "unit": "%",
     "info": "Përqindja e të rriturve (30+ vjeç) që kanë diabet."},
    {"code": "NCD_BMI_30A", "title": "Mbipesha (obeziteti)", "unit": "%",
     "info": "Përqindja e të rriturve me indeks të masës trupore 30 ose më shumë."},
    {"code": "M_Est_tob_curr_std", "title": "Përdorimi i duhanit", "unit": "%",
     "info": "Përqindja e të rriturve që përdorin duhan."},
    {"code": "SA_0000001688", "title": "Konsumi i alkoolit", "unit": "litra/vit",
     "info": "Litra alkool të pastër për person (15+ vjeç) në vit."},
]

# Shtetet që mund të zgjidhen (kodi ISO3 -> emri në shqip).
# Shënim: OBSH nuk publikon të dhëna të veçanta për Kosovën.
COUNTRIES = {
    "ALB": "Shqipëria", "MKD": "Maqedonia e Veriut", "MNE": "Mali i Zi",
    "SRB": "Serbia", "GRC": "Greqia", "ITA": "Italia", "DEU": "Gjermania",
    "CHE": "Zvicra", "AUT": "Austria", "FRA": "Franca", "GBR": "Mbretëria e Bashkuar",
    "SWE": "Suedia", "BEL": "Belgjika", "NLD": "Holanda", "TUR": "Turqia",
    "HRV": "Kroacia", "SVN": "Sllovenia", "BGR": "Bullgaria", "USA": "SHBA", "CAN": "Kanadaja",
}

_cache: dict[str, tuple[float, object]] = {}


def _cached(key: str):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    return None


def _store(key: str, value):
    _cache[key] = (time.time(), value)
    return value


def _pick_latest(values: list[dict]) -> dict | None:
    """Nga të gjitha rreshtat, zgjedh vitin më të fundit, për të dy gjinitë bashkë."""
    if not values:
        return None
    both = [v for v in values if v.get("Dim1") == "SEX_BTSX"]
    pool = both or values
    # Nëse ka ndarje sipas moshës, preferojmë grupin e të rriturve të përgjithshëm
    adult = [v for v in pool if (v.get("Dim2") or "").startswith("AGEGROUP_YEARS18") or
             (v.get("Dim2") or "").startswith("AGEGROUP_YEARS30")]
    # Vetëm vlera të matura (OBSH publikon edhe parashikime për vitet e ardhshme)
    this_year = time.localtime().tm_year
    pool = [v for v in (adult or pool) if v.get("NumericValue") is not None and v["TimeDim"] <= this_year]
    if not pool:
        return None
    latest_year = max(v["TimeDim"] for v in pool)
    same_year = [v for v in pool if v["TimeDim"] == latest_year and v.get("NumericValue") is not None]
    if not same_year:
        return None
    avg = sum(v["NumericValue"] for v in same_year) / len(same_year)
    return {"year": latest_year, "value": round(avg, 1),
            "estimated_both_sexes": not both and len(same_year) > 1}


async def get_indicators(country: str) -> dict:
    country = country.upper()
    cache_key = f"ind:{country}"
    if (c := _cached(cache_key)) is not None:
        return c

    async def fetch(client, code: str, place: str):
        try:
            r = await client.get(f"{GHO_URL}/{code}", params={"$filter": f"SpatialDim eq '{place}'"})
            r.raise_for_status()
            return _pick_latest(r.json().get("value", []))
        except Exception:
            return None

    # Të gjitha kërkesat dërgohen njëherësh (paralelisht) që të jetë më shpejt.
    # Për çdo tregues marrim shtetin e zgjedhur dhe mesataren e rajonit të Evropës.
    async with httpx.AsyncClient(timeout=25) as client:
        tasks = []
        for ind in INDICATORS:
            tasks.append(fetch(client, ind["code"], country))
            tasks.append(fetch(client, ind["code"], "EUR"))
        values = await asyncio.gather(*tasks)

    results = [{**ind, "country": values[2 * i], "europe": values[2 * i + 1]}
               for i, ind in enumerate(INDICATORS)]

    data = {"country": country, "country_name": COUNTRIES.get(country, country), "indicators": results}
    if any(i["country"] for i in results):
        _store(cache_key, data)
    return data


async def get_news(limit: int = 6) -> dict:
    if (c := _cached("news")) is not None:
        return c
    params = {"sf_culture": "en", "$orderby": "PublicationDateAndTime desc", "$top": str(limit),
              "$select": "Title,PublicationDateAndTime,ItemDefaultUrl"}
    news, outbreaks = [], []
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.get(f"{NEWS_URL}/newsitems", params=params)
            r.raise_for_status()
            news = [{"title": n["Title"], "date": n["PublicationDateAndTime"][:10],
                     "url": "https://www.who.int/news/item" + n["ItemDefaultUrl"]}
                    for n in r.json().get("value", [])]
        except Exception:
            pass
        try:
            r = await client.get(f"{NEWS_URL}/diseaseoutbreaknews", params={**params, "$top": "4"})
            r.raise_for_status()
            outbreaks = [{"title": n["Title"], "date": n["PublicationDateAndTime"][:10],
                          "url": "https://www.who.int/emergencies/disease-outbreak-news/item" + n["ItemDefaultUrl"]}
                         for n in r.json().get("value", [])]
        except Exception:
            pass
    data = {"news": news, "outbreaks": outbreaks}
    if news or outbreaks:
        _store("news", data)
    return data
