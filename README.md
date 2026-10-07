# HealthMate AI

**Asistenti personal i shëndetit, i ndërtuar për njerëzit që nuk duan të merren me teknologji.**

HealthMate është një aplikacion web që e ruan historikun tënd shëndetësor (analizat, terapinë, simptomat) dhe të lejon të bisedosh me një asistent inteligjent që i njeh të gjitha këto. Kur shton një analizë, të tregon menjëherë nëse vlera është normale. Kur fillon një bar të ri, mund ta pyesësh asistentin nëse shkon mirë me barnat e tjera. Kur ndihesh keq, e shënon dhe e pyet çfarë të bësh.

Projekti është shkruar në **Python** (backend) dhe **HTML/CSS/JavaScript** (frontend), dhe përdor vetëm shërbime **falas**.

---

## Përmbajtja

1. [Si ta nisim](#1-si-ta-nisim)
2. [Problemi që zgjidhim](#2-problemi-që-zgjidhim)
3. [Çfarë bën aplikacioni](#3-çfarë-bën-aplikacioni)
4. [Si është ndërtuar (arkitektura)](#4-si-është-ndërtuar-arkitektura)
5. [Struktura e dosjeve](#5-struktura-e-dosjeve)
6. [Shpjegimi i çdo pjese](#6-shpjegimi-i-çdo-pjese)
7. [API-të e jashtme që përdorim](#7-api-të-e-jashtme-që-përdorim)
8. [Dizajni për të moshuarit](#8-dizajni-për-të-moshuarit)
9. [Siguria dhe privatësia](#9-siguria-dhe-privatësia)
10. [Udhëzues për prezantimin](#10-udhëzues-për-prezantimin)
11. [Pyetje që mund t'ju bëjnë](#11-pyetje-që-mund-tju-bëjnë)
12. [Ide për zgjerim](#12-ide-për-zgjerim)

---

## 1. Si ta nisim

### Çfarë ju duhet

- **Python 3.10 ose më i ri** — shkarkohet nga [python.org](https://www.python.org/downloads/). Në Windows, gjatë instalimit shënoni **"Add Python to PATH"**.
- **Lidhje me internet** (për asistentin dhe të dhënat e OBSH-së).
- *(Opsionale)* **Git**, për ta shkarkuar projektin me komandë.

Kontrolloni versionin e Python-it:

```bash
python --version      # Windows
python3 --version     # macOS / Linux
```

### Hapi 1 - Shkarkoni projektin

Me Git:

```bash
git clone https://github.com/Albion-Hajzeraj/healthmate-ai.git
cd healthmate-ai
```

Ose pa Git: në faqen e projektit në GitHub klikoni **Code → Download ZIP**, pastaj hapeni (extract) dosjen.

### Hapi 2a - Nisja me një klik (Windows)

Klikoni dy herë mbi **`start.bat`**. Herën e parë instalohet gjithçka vetë (zgjat 1-2 minuta), pastaj hapet shfletuesi në `http://localhost:8000`.

### Hapi 2b - Nisja manuale (Windows, macOS, Linux)

**Windows (PowerShell ose CMD):**

```bash
python -m venv .venv                  # 1. krijo ambientin virtual (vetëm herën e parë)
.venv\Scripts\activate                # 2. aktivizoje
pip install -r requirements.txt       # 3. instalo libraritë (vetëm herën e parë)
python run.py                         # 4. nise
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Shfletuesi hapet vetë; nëse jo, hapni **http://localhost:8000**. Për ta ndalur aplikacionin shtypni `Ctrl + C` në terminal.

Herët e tjera mjafton vetëm hapi 2 (aktivizimi) dhe hapi 4 (`python run.py`), ose `start.bat` në Windows.

Baza e të dhënave (`data/healthmate.db`) krijohet vetë herën e parë që niset aplikacioni, bosh. Të dhënat tuaja mbeten vetëm në kompjuterin tuaj dhe **nuk** ngarkohen në GitHub (dosja `data/` është në `.gitignore`).

### Probleme të zakonshme

| Problemi | Zgjidhja |
|---|---|
| `python` nuk njihet si komandë | Riinstaloni Python-in duke shënuar "Add Python to PATH", ose provoni `py` në vend të `python` (Windows) / `python3` (macOS, Linux). |
| PowerShell nuk lejon `activate` ("running scripts is disabled") | Ekzekutoni një herë `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ose përdorni CMD. |
| Porti 8000 është i zënë | Në `.env` vendosni p.sh. `PORT=8080` dhe hapni `http://localhost:8080`. |
| Asistenti përgjigjet ngadalë ose thotë që s'ka lidhje | Shërbimi falas pa çelës ka kufi; shtoni një çelës falas (shih më poshtë). |
| "Dërgo foto të fletës" nuk punon | Leximi i fotove kërkon çelës **Groq** ose **Gemini** në `.env`. |

### Asistenti: a duhet çelës (API key)?

**Jo.** Aplikacioni punon menjëherë pa asnjë çelës, sepse përdor **Pollinations.ai**, një shërbim AI falas që nuk kërkon regjistrim.

Shërbimi pa çelës ka një kufi: nëse bëni shumë pyetje njëra pas tjetrës, mund t'ju duhet të prisni pak sekonda (aplikacioni pret dhe provon vetë përsëri). Për një përvojë **më të shpejtë dhe më të qëndrueshme** (rekomandohet për prezantimin), merrni një çelës falas te njëri nga këta:

| Shërbimi | Ku merret çelësi | Pse |
|---|---|---|
| **Groq** (rekomandohet) | https://console.groq.com/keys | Shumë i shpejtë, plan falas bujar |
| **Google Gemini** | https://aistudio.google.com/apikey | Model i fortë, plan falas |
| **OpenRouter** | https://openrouter.ai/keys | Shumë modele `:free` |

Pastaj:
1. Kopjoni skedarin `.env.example` si `.env`:
   ```bash
   copy .env.example .env     # Windows
   cp .env.example .env       # macOS / Linux
   ```
2. Hapeni `.env` me një redaktor teksti dhe ngjitni çelësin, p.sh. `GROQ_API_KEY=gsk_...`
3. Rinisni aplikacionin

> **Mos e ndani kurrë skedarin `.env` dhe mos e ngarkoni në GitHub.** Ai përmban çelësat tuaj personalë dhe është tashmë i përjashtuar në `.gitignore`.

Në faqen **Profili im** shkruhet cili shërbim po përdoret.

---

## 2. Problemi që zgjidhim

Mendoni për një gjysh ose gjyshe që:

- ka bërë analiza disa herë në vit, por fletët i ka nëpër sirtarë dhe nuk e di nëse sheqeri është rritur apo ulur;
- merr 3-4 barna dhe nuk mban mend gjithmonë nëse e ka pirë atë të mëngjesit;
- kur mjeku i jep një bar të ri, nuk e di nëse shkon mirë me të tjerët;
- ka një dhimbje të re dhe nuk di nëse duhet të shqetësohet;
- kur shkon te mjeku, nuk mban mend të gjitha barnat dhe vlerat.

Aplikacionet ekzistuese janë shpesh në anglisht, me shkronja të vogla, me shumë butona dhe me një pamje "teknologjike" që i frikëson.

**HealthMate e zgjidh këtë me:** një vend të vetëm për të gjithë historikun, gjuhë shqipe të thjeshtë, shkronja të mëdha, dhe një asistent që e njeh personin.

---

## 3. Çfarë bën aplikacioni

Aplikacioni ka 7 faqe, të gjitha të arritshme nga menyja anash (ose poshtë në celular).

### Kreu
- Përshëndetje me emër dhe data e sotme.
- **Barnat e sotme:** lista e barnave sipas orarit (mëngjes, mesditë, mbrëmje, para gjumit). Me një klik shënohet "E mora".
- **Analizat që duan vëmendje:** vetëm ato që janë jashtë normës.
- **Simptomat e fundit.**
- **Printo përmbledhjen:** një faqe e pastër me terapinë, analizat dhe simptomat, gati për mjekun.

### Analizat
- **Dërgo foto të fletës:** bëni një foto të fletës së laboratorit (me telefon ose nga kompjuteri). Programi:
  1. lexon të gjitha vlerat, njësitë, kufijtë normalë të laboratorit dhe datën;
  2. i shfaq në një tabelë ku përdoruesi **i kontrollon dhe i ndryshon** para se t'i ruajë;
  3. i ruan në historik, bashkë me **foton origjinale**;
  4. shkruan një **raport** në shqip: përmbledhje, çfarë është në rregull, çfarë kërkon vëmendje, krahasim me analizat e mëparshme, këshilla dhe pyetje për mjekun.

  Raportet ruhen te **"Raportet e mia"** dhe mund të printohen për mjekun. Nëse e njëjta fletë dërgohet dy herë, vlerat nuk dyfishohen.
- Shtimi i një analize: zgjedhim nga lista (23 analiza të zakonshme: glukoza, kolesteroli, hemoglobina, vitamina D, TSH, tensioni...) dhe shkruajmë vlerën. Njësia plotësohet vetë.
- **Ngjit tekstin e fletës:** kopjon tekstin nga PDF-ja e laboratorit, dhe programi i gjen vetë vlerat. Nëse vlerat janë në njësi tjetër (p.sh. glukoza në mmol/L), i konverton automatikisht.
- Çdo analizë merr një shenjë: **Në rregull**, **Më e lartë se normalja** ose **Më e ulët se normalja**, me shpjegim në shqip.
- Kufijtë normalë ndryshojnë sipas gjinisë (p.sh. hemoglobina te femrat dhe meshkujt).
- Kur ka disa matje, shfaqet një **grafik** që tregon si ka ndryshuar vlera me kohë, me zonën normale të ngjyrosur.
- **Më shpjego analizat:** asistenti i lexon dhe i shpjegon me fjalë të thjeshta.

### Terapia
- Shtimi i barnave: emri, doza, kur merret, për çfarë.
- Pas shtimit të një bari të ri, aplikacioni pyet: *"Dëshironi të kontrolloni nëse shkon mirë me barnat e tjera?"*
- Butoni **E përfundova** e kalon barin në historik (nuk fshihet), kështu ruhet historiku i plotë i terapisë.

### Si ndihem (simptomat)
- Butona të gatshëm për simptomat më të shpeshta (dhimbje koke, marramendje, lodhje...).
- Rëndësia nga 1 deri në 10 me butona të mëdhenj.
- Pas ruajtjes: *"Dëshironi ta pyesni asistentin?"*

### Bisedë (asistenti)
- Bisedë e lirë në shqip. Asistenti **i sheh** profilin, analizat, terapinë dhe simptomat, kështu që përgjigjet janë personale.
- **Mbrojtje urgjence:** nëse shkruani p.sh. "dhimbje gjoksi" ose "nuk marr frymë", del menjëherë një paralajmërim i kuq "Telefononi 112", edhe pa internet.
- Nëse asnjë shërbim AI nuk përgjigjet, aplikacioni jep një përgjigje rezervë nga të dhënat e ruajtura (p.sh. cilat analiza janë jashtë normës).

### Shëndeti në botë (OBSH)
- Statistika zyrtare nga **Organizata Botërore e Shëndetësisë** për shtetin e zgjedhur: jetëgjatësia, tensioni i lartë, diabeti, mbipesha, duhani, alkooli, të krahasuara me mesataren e Evropës.
- Lajmet e fundit të OBSH-së dhe njoftimet për shpërthime sëmundjesh në botë.

### Profili im
- Emri, viti i lindjes, gjinia, gjatësia, pesha, alergjitë, sëmundjet kronike, mjeku dhe personi për urgjencë.

---

## 4. Si është ndërtuar (arkitektura)

Aplikacioni ka tri shtresa që flasin me njëra-tjetrën:

```
 ┌──────────────────────────────────────────────┐
 │  FRONTENDI  (ajo që sheh përdoruesi)         │
 │  HTML + CSS + JavaScript, në shfletues       │
 └───────────────────────┬──────────────────────┘
                         │  kërkesa HTTP (JSON)
                         │  p.sh. GET /api/labs
 ┌───────────────────────▼──────────────────────┐
 │  BACKENDI  (truri)                           │
 │  Python + FastAPI                            │
 │  - vlerëson analizat                         │
 │  - ndërton kontekstin për asistentin         │
 │  - flet me shërbimet e jashtme               │
 └───────┬──────────────────┬───────────────┬───┘
         │                  │               │
 ┌───────▼───────┐  ┌───────▼───────┐  ┌────▼─────────────┐
 │ SQLite        │  │ Shërbimet AI  │  │ API-të e OBSH-së │
 │ (baza lokale) │  │ Groq / Gemini │  │ statistika +     │
 │ healthmate.db │  │ / Pollinations│  │ lajme            │
 └───────────────┘  └───────────────┘  └──────────────────┘
```

**Shembull i një rrugëtimi të plotë:** përdoruesi shkruan *"A janë analizat e mia në rregull?"*

1. JavaScript-i e dërgon pyetjen te `POST /api/chat`.
2. Backendi kontrollon nëse ka fjalë urgjence.
3. Backendi lexon nga baza profilin, analizat, terapinë dhe simptomat, dhe i përmbledh në tekst.
4. I dërgon AI-së: udhëzimet + përmbledhjen + bisedën e fundit + pyetjen.
5. AI-ja kthen përgjigjen; backendi e ruan në bazë dhe ia kthen frontendit.
6. Frontendi e shfaq si mesazh.

### Teknologjitë

| Pjesa | Teknologjia | Pse e zgjodhëm |
|---|---|---|
| Backend | **Python 3 + FastAPI** | E thjeshtë për t'u lexuar, shumë e shpejtë, krijon vetë dokumentimin e API-së |
| Serveri | **Uvicorn** | Serveri që e ekzekuton FastAPI-në |
| Baza e të dhënave | **SQLite** | Një skedar i vetëm, pa instalim, ideale për aplikacion personal |
| Kërkesat në internet | **httpx** | Librari moderne për të thirrur API të jashtme (asinkrone) |
| Frontend | **HTML, CSS, JavaScript** (pa framework) | Pa hapa ndërtimi, çdo nxënës mund ta lexojë kodin |
| Shkronjat | **Atkinson Hyperlegible** + **Source Serif 4** | E para është krijuar nga Braille Institute për njerëz me shikim të dobët |

Gjithsej përdorim vetëm **4 librari Python** (`requirements.txt`).

---

## 5. Struktura e dosjeve

```
HealthMate AI/
│
├── run.py                  ← Nis aplikacionin (python run.py)
├── start.bat               ← Nisja me një klik në Windows
├── requirements.txt        ← Libraritë Python që duhen
├── .env.example            ← Shembull i konfigurimit (çelësat e AI-së)
├── README.md               ← Ky dokument
│
├── backend/                ← PYTHON: logjika dhe të dhënat
│   ├── main.py             ← Krijon aplikacionin dhe lidh të gjitha pjesët
│   ├── database.py         ← Tabelat e bazës SQLite
│   ├── lab_reference.py    ← Katalogu i analizave, vlerat normale, leximi i tekstit
│   ├── routers/            ← "Adresat" e API-së, një skedar për çdo faqe
│   │   ├── profile.py      ←   /api/profile
│   │   ├── labs.py         ←   /api/labs
│   │   ├── therapies.py    ←   /api/therapies
│   │   ├── symptoms.py     ←   /api/symptoms
│   │   ├── chat.py         ←   /api/chat
│   │   └── who.py          ←   /api/who
│   └── services/           ← Lidhja me shërbimet e jashtme
│       ├── ai_service.py   ←   Asistenti (AI)
│       └── who_service.py  ←   Organizata Botërore e Shëndetësisë
│
├── frontend/               ← Ajo që shihet në shfletues
│   ├── index.html          ← Struktura e të gjitha faqeve
│   ├── css/style.css       ← Pamja (ngjyrat, madhësitë, rregullimi)
│   └── js/app.js           ← Sjellja (klikimet, formularët, biseda, grafikët)
│
└── data/
    └── healthmate.db       ← Krijohet vetë: këtu ruhen të gjitha të dhënat
```

---

## 6. Shpjegimi i çdo pjese

### 6.1 `run.py` - pika e nisjes
Lexon konfigurimin nga `.env`, nis serverin në portin 8000 dhe hap shfletuesin automatikisht.

### 6.2 `backend/main.py` - zemra e backendit
- Krijon aplikacionin FastAPI.
- Krijon bazën e të dhënave nëse nuk ekziston (`init_db()`).
- Lidh 6 "routers" (secili merret me një pjesë: profilin, analizat, etj.).
- Shërben frontendin: kur hap `http://localhost:8000`, kthen `index.html`.

> **Këshillë për prezantim:** hapni **http://localhost:8000/docs**. FastAPI krijon vetë një faqe ku shihen dhe provohen të gjitha adresat e API-së. Kjo është shumë mbresëlënëse për t'u treguar.

### 6.3 `backend/database.py` - baza e të dhënave
Përcakton 7 tabela:

| Tabela | Çfarë ruan |
|---|---|
| `profile` | Të dhënat personale (vetëm një rresht, sepse aplikacioni është personal) |
| `lab_results` | Çdo matje: analiza, vlera, njësia, data |
| `therapies` | Barnat: emri, doza, oraret, data e fillimit dhe e mbarimit |
| `dose_log` | Cilat doza janë shënuar "E mora" çdo ditë |
| `symptoms` | Simptomat me rëndësinë 1-10 |
| `lab_reports` | Raportet e shkruara nga asistenti për çdo fletë analizash, me emrin e fotos |
| `chat_messages` | E gjithë biseda me asistentin |

Fotot e fletëve ruhen si skedarë në `data/uploads/`.

Funksioni `get_conn()` hap lidhjen, e ruan çdo ndryshim dhe e mbyll vetë në fund.

### 6.4 `backend/lab_reference.py` - "mjeku i vogël" i analizave
Kjo është pjesa më interesante e logjikës. Përmban:

- **`CATALOG`**: 23 analiza me emrin shqip, njësinë, kufijtë normalë, kufij të veçantë për femra/meshkuj, dhe shpjegime të thjeshta ("çfarë është", "nëse është e lartë", "nëse është e ulët").
- **`evaluate()`**: krahason vlerën me kufijtë dhe kthen `normal`, `high` ose `low`.
- **`parse_lab_text()`**: lexon tekstin e ngjitur nga fleta e laboratorit. Për çdo rresht:
  1. kërkon emrin e analizës (njeh edhe variante si "glukoza", "glicemia", "GLU");
  2. merr numrin pas emrit (duke anashkaluar gjëra si "(10^9/L)");
  3. nëse numri duket në njësi tjetër, e konverton (p.sh. glukoza 6.2 mmol/L → 111.7 mg/dL);
  4. tensioni "145/92" ndahet në dy vlera.

  Analizat specifike kërkohen para të përgjithshmeve (p.sh. **HbA1c** para **Hemoglobinës**, **LDL** para **Kolesterolit**) që të mos ngatërrohen.
- **`normalize_item()`**: merr një rresht të lexuar nga fotoja (emri, vlera, njësia, kufijtë) dhe:
  1. gjen analizën në katalog (`match_test()`: "Hemoglobina (HGB)" → `hemoglobin`);
  2. krahason njësinë: nëse fleta e ka në mmol/L ose µmol/L, konverton **vlerën dhe kufijtë** (glukoza 6.8 mmol/L → 122.5 mg/dL);
  3. analizat që nuk janë në katalog (p.sh. kalciumi, sedimentacioni) ruhen gjithsesi, me kufijtë e laboratorit.

> **Kush bën çfarë te fotoja?** AI-ja vetëm **kopjon** numrat nga fotoja, si një sekretare. Vendimin "normal / i lartë / i ulët" e merr **kodi ynë**, me rregulla të sakta. Dhe para ruajtjes, njeriu i kontrollon numrat. Kështu, edhe nëse AI-ja lexon gabim një numër, gabimi kapet para se të hyjë në historik.

### 6.5 `backend/routers/` - adresat e API-së
Çdo skedar përcakton disa adresa. Shembuj:

| Metoda | Adresa | Çfarë bën |
|---|---|---|
| `GET` | `/api/labs` | Kthen të gjitha analizat me statusin (normal/lartë/ulët) |
| `POST` | `/api/labs` | Ruan një analizë të re |
| `POST` | `/api/labs/parse` | Gjen analizat në një tekst të ngjitur |
| `POST` | `/api/labs/photo/read` | Lexon vlerat nga fotoja e fletës (pa ruajtur) |
| `POST` | `/api/labs/photo/save` | Ruan vlerat e kontrolluara + foton, dhe shkruan raportin |
| `GET` | `/api/labs/reports` | Lista e raporteve të ruajtura |
| `GET` | `/api/therapies/today` | Barnat që duhen marrë sot |
| `POST` | `/api/therapies/{id}/stop` | E kalon një bar në historik |
| `POST` | `/api/chat` | Dërgon një pyetje te asistenti |
| `POST` | `/api/chat/explain-labs` | Kërkon shpjegimin e analizave |
| `GET` | `/api/who/indicators?country=ALB` | Statistikat e OBSH-së |

Të dhënat që vijnë nga frontendi kontrollohen me **Pydantic** (p.sh. rëndësia e simptomës duhet të jetë 1-10; përndryshe kthehet gabim).

### 6.6 `backend/services/ai_service.py` - asistenti
- **Zinxhiri i ofruesve:** provon me radhë Groq → Gemini → OpenRouter → Pollinations. Përdoren vetëm ata që kanë çelës, përveç Pollinations që s'ka nevojë. Nëse njëri dështon, kalon te tjetri.
- Të gjithë ofruesit përdorin të njëjtin format ("OpenAI-compatible"), prandaj mjafton **një funksion** (`ask()`) për të gjithë.
- **`SYSTEM_PROMPT`**: udhëzimet për asistentin: fol shqip të thjeshtë, mos jep diagnoza, mos ndrysho kurrë dozat, thuaj "112" në urgjencë.
- **`build_context()`**: e kthen historikun e pacientit në tekst që AI-ja ta lexojë.
- **`is_emergency()`**: kontrollon fjalë si "dhimbje gjoksi", "nuk marr frymë" para se të pyetet AI-ja.
- **`offline_answer()`**: përgjigje rezervë pa AI, nga të dhënat e ruajtura.
- **`read_lab_image()`**: i dërgon foton një modeli që "sheh" (Groq `qwen/qwen3.8-27b`, ose Gemini) dhe i kërkon vetëm JSON: emrin, vlerën, njësinë dhe kufijtë e çdo rreshti. Fotoja zvogëlohet më parë në shfletues (max 2000 px), që të dërgohet shpejt.
- **`REPORT_PROMPT`**: udhëzimet për raportin (seksionet, pa tabela, pa diagnoza).

### 6.7 `backend/services/who_service.py` - OBSH
- Merr 7 tregues nga **WHO GHO API** për shtetin e zgjedhur dhe për rajonin e Evropës.
- Kërkesat dërgohen **paralelisht** (`asyncio.gather`), kështu 14 kërkesa zgjasin sa një.
- Nga të gjitha vlerat zgjedh vitin më të fundit të matur (OBSH publikon edhe parashikime për vitet e ardhshme, të cilat i anashkalojmë).
- Përgjigjet ruhen në memorie (**cache**) për 6 orë.
- Merr edhe lajmet dhe njoftimet për shpërthime sëmundjesh nga **WHO News API**.

### 6.8 `frontend/index.html` - struktura
Të 7 faqet janë në një skedar të vetëm. JavaScript-i shfaq vetëm atë që i përket adresës (`#kreu`, `#analizat`...). Kjo quhet **Single Page Application**: faqja nuk ringarkohet kur kalon nga një seksion te tjetri.

### 6.9 `frontend/css/style.css` - pamja
- Ngjyrat janë të përcaktuara si **variabla** (`--primary`, `--ok`, `--high`...) në krye, kështu ndryshohen lehtë.
- Tre madhësi shkrimi (18px, 20px, 23px); i gjithë dizajni përdor `rem`, kështu zmadhohet çdo gjë njëherësh.
- Në kompjuter menyja është lart; në celular dhe tablet kalon në një **shirit poshtë me 5 butona** (si te aplikacionet e telefonit), me hapësirë për "home bar"-in e iPhone-it.
- Në celular: grafikët vizatohen me gjerësinë reale të ekranit (që numrat të mos dalin të vegjël), lista e kontrollit të fotos bëhet kartela në vend të tabelës, fushat kanë shkrim 16px+ që telefoni të mos zmadhojë faqen vetë.
- Rregulla të veçanta për printim (`@media print`).

### 6.10 `frontend/js/app.js` - sjellja
- **`api()`**: funksioni i vetëm që flet me backendin.
- **`route()`**: shfaq faqen e duhur kur ndryshon adresa.
- **`loadHome()`, `loadLabs()`, ...**: një funksion për çdo faqe; marrin të dhënat dhe i vizatojnë.
- **`lineChart()`**: vizaton grafikun e analizave si SVG, pa asnjë librari: brezi i gjelbër = zona normale, pikat = matjet, me tooltip kur kalon miu sipër.
- **`renderText()`**: e kthen tekstin e asistentit në HTML të sigurt (lista, tekst i theksuar).
- **`askAssistant()`**: hap bisedën dhe dërgon një pyetje të gatshme (përdoret nga butonat "Pyet asistentin").
- **`esc()`**: mbron nga futja e kodit të dëmshëm (XSS) duke "pastruar" çdo tekst para se ta shfaqë.

---

## 7. API-të e jashtme që përdorim

Të gjitha janë **falas**.

| API | Adresa | Çelës? | Për çfarë |
|---|---|---|---|
| WHO Global Health Observatory | `ghoapi.azureedge.net/api` | Jo | Statistika shëndetësore sipas shtetit |
| WHO News | `who.int/api/news` | Jo | Lajme dhe njoftime për sëmundje |
| Pollinations.ai | `text.pollinations.ai/openai` | Jo | Asistenti (parazgjedhje) |
| Groq | `api.groq.com` | Po, falas | Asistenti (më i shpejtë) dhe leximi i fotove |
| Google Gemini | `generativelanguage.googleapis.com` | Po, falas | Asistenti dhe leximi i fotove (rezervë) |
| OpenRouter | `openrouter.ai` | Po, falas | Asistenti |

**Shembull kërkese te OBSH-ja** (mund ta hapni direkt në shfletues):

```
https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'ALB'
```
Kthen jetëgjatësinë mesatare në Shqipëri për çdo vit.

---

## 8. Dizajni për të moshuarit

Synimi ishte një aplikacion që duket **si një kartelë mjekësore e kujdesshme**: i qetë, i besueshëm dhe i hijshëm, jo si një "dashboard" teknologjik.

| Vendimi | Arsyeja |
|---|---|
| Shkrim bazë 18px, deri në 23px me një klik | Shikimi dobësohet me moshën |
| Shkronja **Atkinson Hyperlegible** | E krijuar për lexim të lehtë; shkronjat e ngjashme (I, l, 1, 0, O) dallohen qartë |
| Butona të paktën 48px të lartë | Më lehtë për t'u shtypur me gishta që dridhen |
| Çdo ikonë ka edhe tekst | Ikonat vetëm nuk kuptohen nga të gjithë |
| Ngjyrë "teal" klinike, sfond i bardhë i butë, tituj me shkronja serif si në letrat e një klinike | Të kujton spitalin/klinikën dhe ngjall besim; pa gradientë neoni apo efekte "AI" |
| **Kartela e pacientit** në Kreu: emri, mosha, alergjitë me të kuqe, mjeku me buton "Telefono" | Si kartela që mjeku ka në sirtar; informacioni më i rëndësishëm gjendet menjëherë |
| Barnat e sotme sipas kohës së ditës, me ikona dielli/hëne dhe shirit progresi | Kuptohet pa lexuar shumë: "çfarë më mbetet për sot?" |
| Çdo analizë ka një vijë ngjyre anash (jeshile / e kuqe / e verdhë) | Shihet me një sy cilat vlera duan vëmendje |
| Në celular: shirit poshtë me 5 butona, butoni "Bëj foto me kamerë" hap direkt kamerën | Si aplikacionet që njerëzit i njohin tashmë |
| Statusi i analizës = ngjyrë + shigjetë + fjalë | Edhe një person që nuk dallon ngjyrat e kupton |
| Butoni i kuq "Urgjenca 112" gjithmonë i dukshëm | Në urgjencë nuk ka kohë për të kërkuar |
| Pyetje të gatshme dhe simptoma me një klik | Shkrimi në tastierë është i vështirë për shumë të moshuar |
| Pak gjëra në ekran njëherësh, formularët hapen vetëm kur duhen | Më pak konfuzion |
| Gjuha: "Si ndiheni?", "E mora", "E përfundova" | Fjalë të përditshme, jo terma teknikë |
| Asistenti quhet thjesht "Asistenti" | Pa fjalë si "AI", "bot" apo ikona robotësh |

---

## 9. Siguria dhe privatësia

- **Të dhënat ruhen vetëm lokalisht**, në `data/healthmate.db` në kompjuterin tuaj. Nuk ka llogari në internet.
- Shërbimit AI i dërgohet vetëm përmbledhja e nevojshme për përgjigjen, dhe fotoja e fletës kur përdorni "Dërgo foto të fletës".
- Serveri dëgjon vetëm në `127.0.0.1` (vetë kompjuteri), jo në rrjet.
- Çdo tekst "pastrohet" para se të shfaqet (mbrojtje nga XSS).
- Çelësat e AI-së ruhen në `.env`, jo në kod.
- Asistenti është udhëzuar të mos japë diagnoza dhe të mos ndryshojë kurrë terapinë.

> **Kujdes:** HealthMate është projekt edukativ. Nuk e zëvendëson mjekun dhe nuk është pajisje mjekësore e certifikuar.

---

## 10. Udhëzues për prezantimin

Një prezantim rreth **10-12 minutash**, i ndarë për 3-4 nxënës.

### Pjesa 1 - Problemi (2 min) · *Nxënësi 1*
- Filloni me një histori: *"Gjyshja ime merr 4 barna dhe ka analiza nga 3 laboratorë të ndryshëm..."*
- Tregoni problemet nga [seksioni 2](#2-problemi-që-zgjidhim).
- Mesazhi kryesor: *"Teknologjia shëndetësore ekziston, por nuk është bërë për ta."*

### Pjesa 2 - Demonstrimi live (5 min) · *Nxënësi 2*
Përgatitni paraprakisht një profil me disa të dhëna. Pastaj tregoni:

1. **Kreu:** përshëndetja, barnat e sotme (klikoni "E mora").
2. **Madhësia e shkrimit:** klikoni A-të lart. *"Për gjyshin që nuk sheh mirë."*
3. **Analizat → Dërgo foto të fletës:** fotografoni një fletë analizash të vërtetë (ose të printuar). Tregoni:
   - si i lexon të gjitha vlerat dhe datën;
   - që mund të ndryshoni një numër dhe shenja ndryshon menjëherë;
   - raportin që shkruhet pas ruajtjes dhe ku ruhet ("Raportet e mia").
4. **Ngjit tekstin e fletës** (alternativë pa foto): ngjitni këtë tekst:
   ```
   Glukoza 6.2 mmol/L
   HbA1c 6.1 %
   Kolesteroli total 245
   Hemoglobina 118 g/L
   Vitamina D 18
   TA 145/92
   ```
   Tregoni si i gjen vetë vlerat dhe i konverton njësitë.
5. **Grafiku:** tregoni si ka ndryshuar glukoza me kohë.
6. **Terapia:** shtoni një bar të ri (p.sh. "Aspirinë 100 mg") dhe klikoni "Pyet asistentin" për ndërveprimet.
7. **Bisedë:** pyesni *"A janë analizat e mia në rregull?"*. Theksoni që asistenti i përmend vlerat **tuaja**.
8. **Urgjenca:** shkruani *"kam dhimbje gjoksi"* dhe tregoni paralajmërimin e kuq.
9. **Shëndeti në botë:** ndërroni shtetin dhe krahasoni.
10. **Printo përmbledhjen** për mjekun.

### Pjesa 3 - Si funksionon (3 min) · *Nxënësi 3*
- Tregoni diagramin e [arkitekturës](#4-si-është-ndërtuar-arkitektura).
- Hapni **http://localhost:8000/docs** dhe provoni live një adresë (p.sh. `GET /api/labs`).
- Shpjegoni **zinxhirin e AI-së**: nëse një shërbim bie, kalon te tjetri; nëse bien të gjithë, aplikacioni prapë jep përgjigje.
- Shpjegoni ndarjen e punës te fotoja: AI-ja **lexon**, kodi **vlerëson**, njeriu **kontrollon**.

### Pjesa 4 - Dizajni dhe përfundimi (2 min) · *Nxënësi 4*
- Zgjidhni 3-4 vendime nga [seksioni 8](#8-dizajni-për-të-moshuarit).
- Privatësia: gjithçka mbetet në kompjuter.
- Përfundoni me idetë për të ardhmen ([seksioni 12](#12-ide-për-zgjerim)).

### Këshilla për ditën e prezantimit
- Vendosni një çelës **Groq** në `.env` që përgjigjet të jenë të shpejta (2-3 sekonda).
- Nisni aplikacionin **para** se të fillojë prezantimi.
- Mbani gati screenshot-e për rast se nuk ka internet. (Edhe pa internet, analizat, terapia, simptomat dhe paralajmërimi i urgjencës funksionojnë.)

---

## 11. Pyetje që mund t'ju bëjnë

**A është AI-ja e sigurt për këshilla mjekësore?**
Jo plotësisht, prandaj kemi vendosur kufij: asistenti udhëzohet të mos japë diagnoza dhe të mos ndryshojë terapinë; urgjencat kapen me rregulla të thjeshta para AI-së; vlerat e analizave vlerësohen me tabela të sakta, jo nga AI-ja.

**Ku ruhen të dhënat?**
Në skedarin `data/healthmate.db` në kompjuterin tuaj. Mund ta kopjoni si kopje rezervë.

**Pse SQLite dhe jo MySQL?**
Sepse aplikacioni është për një person. SQLite nuk kërkon instalim apo server; e gjithë baza është një skedar.

**Pse nuk përdorët React apo ndonjë framework?**
Për thjeshtësi: pa hapa ndërtimi dhe pa qindra paketa. Kodi lexohet direkt dhe është më i lehtë për t'u kuptuar e shpjeguar.

**Çfarë ndodh nëse bie interneti?**
Gjithçka e ruajtur funksionon normalisht. Asistenti jep përgjigje rezervë nga të dhënat lokale, dhe paralajmërimi i urgjencës punon gjithmonë.

**Pse nuk ka të dhëna të OBSH-së për Kosovën?**
OBSH-ja nuk publikon të dhëna të veçanta për Kosovën në këtë bazë. Prandaj ofrojmë Shqipërinë dhe shtetet e rajonit.

**Po nëse AI-ja e lexon gabim një numër nga fotoja?**
Prandaj vlerat nuk ruhen direkt: shfaqen në një tabelë ku përdoruesi i krahason me fletën dhe i ndryshon nëse duhet. Fotoja origjinale ruhet gjithashtu, që të kontrollohet më vonë.

**A dërgohet fotoja diku?**
Po, vetëm te shërbimi që e lexon (Groq ose Gemini). HealthMate e ruan kopjen e vet vetëm në kompjuterin tuaj, në `data/uploads/`. Si i trajton shërbimi i jashtëm të dhënat, varet nga politika e privatësisë së tij, prandaj mund të prisni ose mbuloni emrin në foto para se ta dërgoni.

**Si e di programi që glukoza 6.2 është në mmol/L?**
Glukoza në mg/dL nuk është kurrë nën 35 te një njeri i gjallë; nëse vlera është nën 35, është në mmol/L dhe e shumëzojmë me 18.

---

## 12. Ide për zgjerim

- Kujtues me zë ose njoftim në telefon për orën e barit.
- Leximi i fletëve PDF direkt (pa foto).
- Disa profile (p.sh. një fëmijë që kujdeset për të dy prindërit).
- Ndarja e përmbledhjes me mjekun me email.
- Leximi me zë i përgjigjeve të asistentit.
- Lidhje me matës tensioni ose glukometër me Bluetooth.

---

*HealthMate AI - projekt shkollor. Informacioni nuk e zëvendëson këshillën e mjekut.*
