"""
DPCN 2026 - Group 10 - Shared configuration and helpers
========================================================
Imported by every part*_*.py script and by both dashboards so that the
institution list, file names, OpenAlex access, classification rules and
metric definitions live in exactly one place.
"""

import gzip
import json
import os
import re
import time
from collections import Counter

import requests

# ─────────────────────────────────────────────
# INSTITUTIONS (verified against the OpenAlex institutions endpoint)
# ─────────────────────────────────────────────
GROUP = 10
START_YEAR = 2016
END_YEAR = 2026
PARTIAL_YEAR = 2026          # collection happened during 2026 -> incomplete year

INSTITUTIONS = {
    # short name          OpenAlex ID     ROR
    "IIIT Allahabad":    ("I26072440",  "03rgjt374"),
    "ABV-IIITM Gwalior": ("I9747756",   "008b3ap06"),
    "IIIT Bangalore":    ("I181514455", "05h9eqy10"),
}
INST_NAMES = list(INSTITUTIONS)
INST_ID_TO_NAME = {v[0]: k for k, v in INSTITUTIONS.items()}
INST_FULL_NAMES = {
    "IIIT Allahabad":    "Indian Institute of Information Technology Allahabad",
    "ABV-IIITM Gwalior": "Atal Bihari Vajpayee Indian Institute of Information Technology and Management Gwalior",
    "IIIT Bangalore":    "International Institute of Information Technology Bangalore",
}
# categorical slots 1-3 of the validated reference palette (CVD-safe all-pairs)
INST_COLORS = {
    "IIIT Allahabad":    "#2a78d6",
    "ABV-IIITM Gwalior": "#eb6834",
    "IIIT Bangalore":    "#1baf7a",
}
INST_COLORS_DARK = {
    "IIIT Allahabad":    "#3987e5",
    "ABV-IIITM Gwalior": "#d95926",
    "IIIT Bangalore":    "#199e70",
}
# ordinal blue ramp for ranked tiers (Q1 / A* darkest), grey = unranked
TIER_COLORS = ["#184f95", "#2a78d6", "#5598e7", "#86b6ef", "#c9c8c2"]
OUR_CLUSTER = "IIIT"
TEAM_NAME = "Titan Mandal"
TEAM_MEMBERS = ["Hrishikesh", "Sarvesh", "Shourya"]
REPO_URL = "https://github.com/sarvesh2005takbhate/dpcn_A2"
DASHBOARD_FILE_URL = REPO_URL + "/blob/main/dashboard.html"
DASHBOARD_LIVE_URL = "https://htmlpreview.github.io/?" + DASHBOARD_FILE_URL
REPORT_URL = REPO_URL + "/blob/main/10_IIIT.pdf"

# ─────────────────────────────────────────────
# FILES
# ─────────────────────────────────────────────
CACHE_DIR        = "cache"
WORKS_CACHE      = os.path.join(CACHE_DIR, "works.json.gz")
INFLOW_CACHE     = os.path.join(CACHE_DIR, "inflow_citing_works.json.gz")
OUTFLOW_CACHE    = os.path.join(CACHE_DIR, "outflow_cited_works.json.gz")
AUTHORS_CACHE    = os.path.join(CACHE_DIR, "authors.json.gz")
TOPICS_CACHE     = os.path.join(CACHE_DIR, "subfield_profiles.json.gz")

REFERENCE_DIR    = "reference"
OUT_DIR          = "outputs"
SCIMAGO_FILE     = os.path.join(REFERENCE_DIR, "scimago_sjr_2016_2025.csv.gz")
CORE_FILE        = os.path.join(REFERENCE_DIR, "core_conference_rankings.csv")

DATA_CSV         = "group10_data.csv"
AUTHORSHIPS_CSV  = os.path.join(OUT_DIR, "group10_authorships.csv")
FACULTY_CSV      = os.path.join(OUT_DIR, "group10_faculty.csv")
JACCARD_CSV      = os.path.join(OUT_DIR, "group10_jaccard_similarity.csv")
CITATION_CSV     = "citation_network.csv"
AUTHORSHIP_CSV   = "authorship_network.csv"
INDIAN_CSV       = "indian_connections.csv"
CITE_METRICS     = os.path.join(OUT_DIR, "group10_citation_metrics.json")
AUTH_METRICS     = os.path.join(OUT_DIR, "group10_author_metrics.json")
FLOW_JSON        = os.path.join(OUT_DIR, "group10_citation_flow.json")
INSIGHTS_JSON    = os.path.join(OUT_DIR, "group10_insights.json")
CHARTS_DIR       = os.path.join(OUT_DIR, "charts")
SUMMARY_MD       = os.path.join(OUT_DIR, "group10_statistics_summary.md")
os.makedirs(CHARTS_DIR, exist_ok=True)

HYPERAUTHOR_THRESHOLD = 50   # papers with more authors are mega-collaborations

# ─────────────────────────────────────────────
# OPENALEX CLIENT (budget aware)
# ─────────────────────────────────────────────
BASE_URL = "https://api.openalex.org"
API_KEY = os.environ.get("OPENALEX_API_KEY", "").strip()
MAILTO = os.environ.get("OPENALEX_MAILTO", "").strip()
BUDGET_RESERVE = int(os.environ.get("OPENALEX_BUDGET_RESERVE", "5"))


class BudgetExhausted(RuntimeError):
    """Raised when the OpenAlex daily request budget is used up."""


class OpenAlex:
    """Thin wrapper: retries, rate-limit handling and daily-budget tracking.

    Without an API key OpenAlex allows ~1000 list requests per day per IP.
    Set OPENALEX_API_KEY (free at https://openalex.org/settings/api) for more.
    """

    def __init__(self, delay=0.12, max_retries=6):
        self.delay = delay
        self.max_retries = max_retries
        self.calls = 0
        self.remaining = None
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "DPCN2026-Group10/2.0"

    def get(self, endpoint, params):
        params = dict(params)
        if API_KEY:
            params["api_key"] = API_KEY
        if MAILTO:
            params["mailto"] = MAILTO
        if self.remaining is not None and self.remaining <= BUDGET_RESERVE:
            raise BudgetExhausted(f"only {self.remaining} OpenAlex requests left today")
        url = f"{BASE_URL}/{endpoint}"
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=60)
            except requests.RequestException as e:
                print(f"    [network] {e} (retry {attempt + 1})")
                time.sleep(3 * (attempt + 1))
                continue
            self.calls += 1
            rem = resp.headers.get("X-RateLimit-Remaining")
            if rem is not None and rem.lstrip("-").isdigit():
                self.remaining = int(rem)
            if resp.status_code == 200:
                time.sleep(self.delay)
                return resp.json()
            if resp.status_code == 429:
                if self.remaining is not None and self.remaining <= 0:
                    raise BudgetExhausted("OpenAlex daily budget exhausted (HTTP 429)")
                time.sleep(5 * (attempt + 1))
                continue
            if resp.status_code >= 500:
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError(f"OpenAlex HTTP {resp.status_code}: {resp.text[:300]}")
        raise RuntimeError(f"OpenAlex request failed after retries: {url}")

    def paginate(self, endpoint, params, per_page=200):
        """Yield results across all pages.

        Cursor paging needs an API key; without one we fall back to basic
        page= paging, which OpenAlex serves for the first 10,000 results.
        """
        if API_KEY:
            cursor = "*"
            while cursor:
                data = self.get(endpoint, dict(params, per_page=per_page, cursor=cursor))
                yield from data.get("results", [])
                nxt = data.get("meta", {}).get("next_cursor")
                cursor = nxt if nxt and data.get("results") else None
            return
        page = 1
        while True:
            data = self.get(endpoint, dict(params, per_page=per_page, page=page))
            results = data.get("results", [])
            yield from results
            count = data.get("meta", {}).get("count") or 0
            if not results or page * per_page >= count:
                break
            if page * per_page >= 10000:
                print(f"    [warn] {count} results exceed the 10,000 basic-paging limit; "
                      "set OPENALEX_API_KEY to fetch the rest")
                break
            page += 1


# ─────────────────────────────────────────────
# CACHE I/O
# ─────────────────────────────────────────────

def load_json_gz(path, default=None):
    if os.path.exists(path):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def save_json_gz(obj, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"))
    os.replace(tmp, path)


# ─────────────────────────────────────────────
# SMALL HELPERS
# ─────────────────────────────────────────────

def short_id(oa_id):
    """'https://openalex.org/W123' -> 'W123'."""
    return (oa_id or "").rstrip("/").split("/")[-1]


def normalize_doi(doi):
    if not doi or (isinstance(doi, float)):
        return ""
    return (str(doi).replace("https://doi.org/", "")
            .replace("http://doi.org/", "").lower().strip())


def doi_or_id(doi, wid):
    """Node key used in edge lists: DOI when present, otherwise openalex:W..."""
    d = normalize_doi(doi)
    return d if d else f"openalex:{wid}"


def hindex(citations):
    s = sorted((int(c) for c in citations), reverse=True)
    h = 0
    for i, c in enumerate(s, 1):
        if c >= i:
            h = i
        else:
            break
    return h


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def norm_person(name):
    n = re.sub(r"[.\-‐_]", " ", (name or "").lower())
    return re.sub(r"\s+", " ", n).strip()


# ─────────────────────────────────────────────
# WORK COMPACTION (keeps caches small)
# ─────────────────────────────────────────────

def compact_institution(inst):
    return {
        "id": short_id(inst.get("id")),
        "name": inst.get("display_name") or "",
        "cc": inst.get("country_code") or "",
        "type": inst.get("type") or "",
    }


def compact_work(w):
    authorships = []
    for a in w.get("authorships") or []:
        affs = []
        for af in a.get("affiliations") or []:
            affs.append({"s": af.get("raw_affiliation_string") or "",
                         "i": [short_id(x) for x in af.get("institution_ids") or []]})
        authorships.append({
            "aid": short_id((a.get("author") or {}).get("id")),
            "name": (a.get("author") or {}).get("display_name") or a.get("raw_author_name") or "",
            "pos": a.get("author_position") or "",
            "corr": bool(a.get("is_corresponding")),
            "insts": [compact_institution(i) for i in a.get("institutions") or []],
            "affs": affs,
        })
    locations = []
    seen = set()
    for loc in ([w.get("primary_location")] + (w.get("locations") or [])):
        if not loc:
            continue
        src = loc.get("source") or {}
        key = (short_id(src.get("id")), loc.get("version"))
        if key in seen:
            continue
        seen.add(key)
        locations.append({
            "sid": short_id(src.get("id")),
            "name": src.get("display_name") or "",
            "stype": src.get("type") or "",
            "issn_l": src.get("issn_l") or "",
            "issn": src.get("issn") or [],
            "version": loc.get("version") or "",
        })
    pt = w.get("primary_topic") or {}
    return {
        "id": short_id(w.get("id")),
        "doi": normalize_doi(w.get("doi")),
        "title": w.get("display_name") or w.get("title") or "",
        "year": w.get("publication_year"),
        "type": w.get("type") or "",
        "cited_by_count": w.get("cited_by_count") or 0,
        "counts_by_year": {str(c["year"]): c["cited_by_count"] for c in w.get("counts_by_year") or []},
        "is_retracted": bool(w.get("is_retracted")),
        "is_oa": bool((w.get("open_access") or {}).get("is_oa")),
        "refs": [short_id(r) for r in w.get("referenced_works") or []],
        "authorships": authorships,
        "authors_truncated": bool(w.get("is_authors_truncated")),
        "locations": locations,
        "topic": (pt.get("display_name") or ""),
        "subfield": ((pt.get("subfield") or {}).get("display_name") or ""),
        "field": ((pt.get("field") or {}).get("display_name") or ""),
        "domain": ((pt.get("domain") or {}).get("display_name") or ""),
    }


def indian_institutions(authorships, exclude_ids=()):
    """Distinct Indian institutions on a work (compact authorships)."""
    out = {}
    for a in authorships:
        for i in a.get("insts", []):
            if i.get("cc") == "IN" and i["id"] not in exclude_ids:
                out[i["id"]] = i
    return out


# ─────────────────────────────────────────────
# PUBLICATION TYPE / VENUE CLASSIFICATION
# ─────────────────────────────────────────────
EXCLUDED_TYPES = {
    "preprint", "dataset", "paratext", "peer-review", "erratum", "retraction",
    "editorial", "supplementary-materials", "software", "report", "dissertation",
    "standard", "reference-entry", "grant", "other", "book", "libguides",
    "conference-abstract",
}
NO_VENUE = {"sid": "", "name": "", "stype": "", "issn_l": "", "issn": [], "version": ""}
ERRATA_TITLE = re.compile(
    r"^\s*(author correction|publisher correction|correction|erratum|corrigendum|"
    r"retraction|retracted|expression of concern|withdrawn|editorial|preface|foreword|"
    r"front matter|back matter|table of contents|index)\b|correction to\s*:", re.I)
PROCEEDINGS_SERIES = re.compile(
    r"lecture notes|communications in computer|advances in intelligent systems|"
    r"smart innovation|algorithms for intelligent systems|ifip advances|"
    r"proceedings|conference|symposium|workshop|congress|"
    r"learning and analytics in intelligent|advances in computer science research|"
    r"atlantis highlights|springer proceedings", re.I)
CONFERENCE_NAME = re.compile(r"\b(conference|proceedings|symposium|workshop|congress|"
                             r"colloquium|summit)\b", re.I)
VENUE_SOURCE_TYPES = ("journal", "conference", "book series")


def choose_venue(work):
    """Pick the publication venue: prefer a journal/conference/series location
    over repositories (fixes e.g. Astropy listed under a library repository)."""
    locs = work.get("locations") or []
    for loc in locs:
        if loc["stype"] in VENUE_SOURCE_TYPES and loc["name"]:
            return loc
    for loc in locs:
        if loc["stype"] in ("ebook platform",) and loc["name"]:
            return loc
    return None


def classify_work(work, scimago_type_for):
    """Return ('journal'|'conference', venue) or (None, reason)."""
    otype = work.get("type") or ""
    if work.get("is_retracted"):
        return None, "retracted"
    if otype in EXCLUDED_TYPES:
        return None, f"type:{otype}"
    if ERRATA_TITLE.search(work.get("title") or ""):
        return None, "erratum/front-matter"
    venue = choose_venue(work)
    if venue is None:
        # OpenAlex often has no source record for proceedings papers
        if otype == "conference-paper":
            return "conference", NO_VENUE
        return None, "no peer-reviewed venue"
    stype, name = venue["stype"], venue["name"]
    sj_type = scimago_type_for(venue) or ""
    if otype == "conference-paper":
        return "conference", venue
    if stype == "conference" or sj_type == "conference and proceedings":
        return "conference", venue
    if stype == "book series":
        if PROCEEDINGS_SERIES.search(name):
            return "conference", venue
        return (None, "book-series chapter") if otype == "book-chapter" else ("conference", venue)
    if stype == "journal":
        if otype == "book-chapter":
            return None, "book-chapter"
        if CONFERENCE_NAME.search(name) and sj_type != "journal":
            return "conference", venue
        return "journal", venue
    # ebook platform etc.
    if otype != "book-chapter" and CONFERENCE_NAME.search(name):
        return "conference", venue
    return None, f"venue:{stype or 'unknown'}"


# ─────────────────────────────────────────────
# SCIMAGO QUARTILES (year-matched)
# ─────────────────────────────────────────────

class Scimago:
    def __init__(self, path=SCIMAGO_FILE):
        import pandas as pd
        df = pd.read_csv(path, dtype=str)
        self.q = {}        # issn -> {year: quartile}
        self.type = {}     # issn -> scimago source type
        for year, issns, typ, q in zip(df["year"], df["issn"], df["type"], df["quartile"]):
            y = int(year)
            for raw in re.split(r"[,\s]+", str(issns)):
                issn = raw.strip().upper().replace("-", "")
                if len(issn) != 8:
                    continue
                self.type[issn] = typ
                if q in ("Q1", "Q2", "Q3", "Q4"):
                    self.q.setdefault(issn, {})[y] = q
        self.max_year = int(df["year"].astype(int).max())

    @staticmethod
    def _issns(venue):
        out = []
        for i in [venue.get("issn_l")] + list(venue.get("issn") or []):
            i = (i or "").upper().replace("-", "").strip()
            if len(i) == 8 and i not in out:
                out.append(i)
        return out

    def source_type(self, venue):
        for i in self._issns(venue):
            if i in self.type:
                return self.type[i]
        return None

    def quartile(self, venue, year):
        """Quartile of the venue in the publication year (2026 -> latest).
        Falls back to the nearest ranked year within +/-2 years."""
        y = min(int(year), self.max_year)
        for i in self._issns(venue):
            yq = self.q.get(i)
            if not yq:
                continue
            if y in yq:
                return yq[y]
            for d in (1, -1, 2, -2):
                if y + d in yq:
                    return yq[y + d]
        return ""


# ─────────────────────────────────────────────
# CORE CONFERENCE RANKS (ICORE2026 portal export)
# ─────────────────────────────────────────────
_CORE_STOP = {"of", "the", "on", "in", "and", "for", "ieee", "acm", "international",
              "annual", "proceedings", "conference", "symposium", "joint", "to", "a",
              "an", "at", "with", "by", "&", "usenix", "aaai", "siam", "ifip", "cvf",
              "sigplan", "sigkdd", "sigmod", "ieee/cvf", "ieee/acm"}
_CORE_EXCLUDE = re.compile(r"workshop|extended abstract|companion|adjunct|doctoral|"
                           r"poster|demo|tutorial|student research|wkshps", re.I)
VALID_CORE = ("A*", "A", "B", "C")


def _core_tokens(s):
    s = re.sub(r"\(.*?\)", " ", s or "")
    s = re.sub(r"\b(19|20)\d{2}\b|\b\d+(st|nd|rd|th)\b", " ", s.lower())
    toks = re.findall(r"[a-z][a-z0-9\-]+", s)
    return {t for t in toks if t not in _CORE_STOP}


class CoreRanks:
    def __init__(self, path=CORE_FILE):
        import pandas as pd
        df = pd.read_csv(path, dtype=str).fillna("")
        df = df[df["rank"].isin(VALID_CORE)]
        self.by_acr = {}
        self.entries = []
        for title, acr, rank in zip(df["title"], df["acronym"], df["rank"]):
            toks = _core_tokens(title)
            self.entries.append((toks, rank, title))
            if acr.strip():
                self.by_acr.setdefault(acr.strip().upper(), []).append((toks, rank, title))
        self.edition = df["source"].iloc[0] if len(df) else ""

    @staticmethod
    def _sim(a, b):
        return len(a & b) / len(a | b) if a and b else 0.0

    def rank(self, venue_name):
        """Strict matching: acronym in parentheses AND title overlap, or a
        near-identical title. Workshops/extended abstracts never inherit."""
        name = venue_name or ""
        if not name or _CORE_EXCLUDE.search(name):
            return ""
        toks = _core_tokens(name)
        for acr in re.findall(r"\(([A-Za-z][A-Za-z0-9\-&+]{1,15})\)", name):
            for etoks, rank, _ in self.by_acr.get(acr.upper(), []):
                if self._sim(toks, etoks) >= 0.4 or etoks <= toks:
                    return rank
        best, best_rank = 0.0, ""
        for etoks, rank, _ in self.entries:
            s = self._sim(toks, etoks)
            if s > best:
                best, best_rank = s, rank
        return best_rank if best >= 0.85 else ""


# ─────────────────────────────────────────────
# INSTITUTION CLUSTERS (for cross-cluster flags)
# ─────────────────────────────────────────────
_CLUSTER_RULES = [
    ("IIIT", r"institute of information technology|iiit|information technology design and manufacturing"),
    ("IIT", r"indian institute of technology|\biit\b"),
    ("NIT", r"national institute of technology|\bnit\b|\bmnnit\b|\bmanit\b"),
    ("IISER/IISc/NISER", r"indian institute of science|national institute of science education"),
    ("IIM", r"indian institute of management"),
    ("CSIR", r"\bcsir\b|council of scientific|academy of scientific and innovative|national physical laboratory|national chemical laboratory|"
             r"central electronics engineering|central scientific instruments|central mechanical engineering|"
             r"institute of genomics|centre for cellular|central drug research|institute of microbial|"
             r"central road research|central building research|central glass|national metallurgical|"
             r"indian institute of chemical technology|central electrochemical|central food technological|"
             r"national institute for interdisciplinary|advanced materials and processes|structural engineering research|"
             r"central institute of mining|national botanical|national environmental engineering|indian institute of toxicology"),
    ("DAE", r"bhabha|indira gandhi centre for atomic|raja ramanna|tata institute of fundamental|"
            r"saha institute|homi bhabha|variable energy cyclotron|institute of physics, bhubaneswar|"
            r"harish-chandra|institute of mathematical sciences|atomic energy|nuclear"),
    ("DRDO/ISRO", r"defence research|\bdrdo\b|indian space research|\bisro\b|space applications centre|"
                  r"vikram sarabhai|defence|aeronautical development"),
    ("ISI/Premier Science", r"indian statistical institute|chennai mathematical|s\.? ?n\.? bose|bose institute|"
                            r"national centre for biological|raman research|jawaharlal nehru centre"),
    ("Central University", r"jawaharlal nehru university|university of delhi|banaras hindu|university of hyderabad|"
                           r"jamia millia|aligarh muslim|university of allahabad|central university|"
                           r"pondicherry university|visva-bharati|tezpur university|assam university|"
                           r"guru ghasidas|hemvati nandan|babasaheb bhimrao|mizoram university|"
                           r"north[- ]eastern hill|sikkim university|manipur university|tripura university|"
                           r"dr\. harisingh gour|rajiv gandhi university|nagaland university"),
    ("Medical", r"all india institute of medical|aiims|medical college|institute of medical sciences|"
                r"postgraduate institute of medical|\bpgimer\b|hospital|tata memorial"),
]


def institution_cluster(name, oa_type=""):
    n = (name or "").lower()
    for label, pat in _CLUSTER_RULES:
        if re.search(pat, n):
            return label
    if oa_type == "company":
        return "Industry"
    if oa_type in ("government", "facility", "nonprofit", "archive"):
        return "Govt/Other Research"
    if oa_type == "healthcare":
        return "Medical"
    if oa_type == "education":
        return "State/Private University"
    return "Other"


# ─────────────────────────────────────────────
# DEPARTMENTS (from raw affiliation strings)
# ─────────────────────────────────────────────
DEPARTMENTS = [
    ("Information Technology",              r"\binformation technology\b|\bdept\.? of it\b|\bit department\b|\bdepartment of it\b"),
    ("Computer Science & Engineering",      r"computer science|computer engineering|\bcse\b|computing|artificial intelligence|"
                                            r"data science|machine learning|computer vision|software|cyber ?security|"
                                            r"information security|robotics|intelligent systems|\bnlp\b|language technolog|"
                                            r"data mining|computational intelligence|multimedia|soft computing|"
                                            r"high performance computing|cloud|database"),
    ("Electronics & Electrical Engineering", r"electronics|electrical|communication engineering|\bece\b|\beee\b|vlsi|"
                                            r"signal processing|wireless|microwave|embedded|telecommunication|networking and communication"),
    ("Applied Sciences & Mathematics",     r"applied science|mathemat|physics|chemistry|engineering science|basic science|"
                                            r"statistics|nanotechnolog|material"),
    ("Biosciences & Bioinformatics",        r"bio|medical|health|life science|genom|pharma"),
    ("Management & Humanities",             r"management|business|humanities|social science|economics|entrepreneur|"
                                            r"liberal arts|digital society|public policy|psychology"),
]
_DEPT_MARKERS = re.compile(r"department|dept|division|school|centre|center|faculty|laboratory|\blab\b|group|"
                           r"\bunit\b|program", re.I)
_INSTITUTE_SEGMENT = re.compile(r"institute of information technology|iiit|indian institute|"
                                r"atal bihari|abv|international institute", re.I)
FIELD_TO_DEPT = {
    "Computer Science": "Computer Science & Engineering",
    "Engineering": "Electronics & Electrical Engineering",
    "Mathematics": "Applied Sciences & Mathematics",
    "Physics and Astronomy": "Applied Sciences & Mathematics",
    "Chemistry": "Applied Sciences & Mathematics",
    "Materials Science": "Applied Sciences & Mathematics",
    "Chemical Engineering": "Applied Sciences & Mathematics",
    "Earth and Planetary Sciences": "Applied Sciences & Mathematics",
    "Energy": "Electronics & Electrical Engineering",
    "Biochemistry, Genetics and Molecular Biology": "Biosciences & Bioinformatics",
    "Medicine": "Biosciences & Bioinformatics",
    "Immunology and Microbiology": "Biosciences & Bioinformatics",
    "Neuroscience": "Biosciences & Bioinformatics",
    "Pharmacology, Toxicology and Pharmaceutics": "Biosciences & Bioinformatics",
    "Agricultural and Biological Sciences": "Biosciences & Bioinformatics",
    "Health Professions": "Biosciences & Bioinformatics",
    "Environmental Science": "Applied Sciences & Mathematics",
    "Business, Management and Accounting": "Management & Humanities",
    "Economics, Econometrics and Finance": "Management & Humanities",
    "Social Sciences": "Management & Humanities",
    "Decision Sciences": "Management & Humanities",
    "Psychology": "Management & Humanities",
    "Arts and Humanities": "Management & Humanities",
}


def department_from_affiliation(raw):
    """Canonical department from one raw affiliation string, or ''."""
    if not raw:
        return ""
    segments = [s.strip() for s in re.split(r"[,;]", raw) if s.strip()]
    for seg in segments:
        if not _DEPT_MARKERS.search(seg):
            continue
        if _INSTITUTE_SEGMENT.search(seg) and not re.search(r"department|dept|school|division", seg, re.I):
            continue
        seg_l = seg.lower()
        # strip the institute name from segments like "Dept of IT, IIIT Allahabad"
        seg_l = re.sub(r"(indian|international) institute of information technology.*", "", seg_l)
        for dept, pat in DEPARTMENTS:
            if re.search(pat, seg_l):
                return dept
    return ""


def our_institutions_on(work):
    """Short names of our institutions that appear in a work's authorships."""
    found = []
    for a in work.get("authorships", []):
        for i in a.get("insts", []):
            name = INST_ID_TO_NAME.get(i["id"])
            if name and name not in found:
                found.append(name)
    # authorships are capped at 100 in the API, so a mega-collaboration may
    # hide our author -> fall back to the institution query that returned it
    for inst_id in work.get("found_via", []):
        name = INST_ID_TO_NAME.get(inst_id)
        if name and name not in found:
            found.append(name)
    return found


def select_corpus(works, scimago):
    """Apply the inclusion rules and collapse duplicate versions of a paper.

    Returns (corpus, excluded, aliases):
      corpus   work id -> (pub_type, venue) for the kept (canonical) records
      excluded Counter of exclusion reasons
      aliases  other-version work id -> canonical work id (published/preprint/
               repository copies of the same paper); citations made to an alias
               are credited to the canonical record.
    """
    kept, excluded, rejected = {}, Counter(), {}
    for wid, w in works.items():
        y = w.get("year") or 0
        if not (START_YEAR <= y <= END_YEAR):
            excluded["outside 2016-2026"] += 1
            continue
        if not our_institutions_on(w):
            excluded["no assigned-institution author"] += 1
            continue
        ptype, venue = classify_work(w, scimago.source_type)
        if ptype is None:
            excluded[venue] += 1
            rejected[wid] = venue
            continue
        kept[wid] = (ptype, venue)

    def rank(wid):
        w = works[wid]
        return (kept[wid][0] == "journal", bool(kept[wid][1]["name"]),
                w.get("cited_by_count") or 0, -int(wid[1:]))

    def same_people(a, b):
        pa = {norm_person(x["name"]) for x in works[a]["authorships"]}
        pb = {norm_person(x["name"]) for x in works[b]["authorships"]}
        return bool(pa & pb) or not pa or not pb

    by_title = {}
    for wid in list(kept) + list(rejected):
        t = norm_title(works[wid]["title"])
        if len(t) >= 25:
            by_title.setdefault(t, []).append(wid)

    aliases = {}
    for wids in by_title.values():
        if len(wids) < 2:
            continue
        canon = sorted((w for w in wids if w in kept), key=rank, reverse=True)
        if not canon:
            continue
        best = canon[0]
        for other in wids:
            if other != best and same_people(best, other):
                aliases[other] = best
    seen_doi = {}
    for wid in sorted(kept, key=rank, reverse=True):
        if wid in aliases:
            continue
        d = works[wid]["doi"]
        if d and d in seen_doi:
            aliases[wid] = seen_doi[d]
        elif d:
            seen_doi[d] = wid
    dup = [w for w in aliases if w in kept]
    for wid in dup:
        kept.pop(wid)
    excluded["duplicate version"] += len(dup)
    return kept, excluded, aliases


def effective_citations(wid, works, aliases_of):
    """Citation count of a paper = max over its versions (OpenAlex sometimes
    credits the citations to a repository/preprint copy)."""
    return max([works[wid].get("cited_by_count") or 0] +
               [works[a].get("cited_by_count") or 0 for a in aliases_of.get(wid, [])])


def most_common_nonempty(values):
    c = Counter(v for v in values if v)
    return c.most_common(1)[0][0] if c else ""
