"""
DPCN 2026 - Group 10 - Faculty / student classification
=========================================================
OpenAlex does not say whether an author is a faculty member or a student, so
author names are matched against the people lists published on the institute
websites (reference/faculty_rosters/<slug>_faculty.csv and, where an institute
publishes one, <slug>_students.csv). Authors that appear on no list get a
heuristic label from their authorship pattern.

role values
  Faculty                      on the official faculty list (regular post)
  Adjunct / visiting faculty   on the list as adjunct, visiting, emeritus, guest
  PhD scholar                  on the institute's published PhD list (current or graduated)
  Student (MS / M.Tech / B.Tech) on a published MS-by-research, M.Tech or B.Tech list
  Likely faculty (not listed)  not on the current list, but PI pattern (>=5 papers
                               in >=3 years, last author >=30%) - mostly former
                               faculty or people who moved
  Likely student / researcher  >=2 papers, not a PI pattern
  Occasional author            one paper (UG/MTech students, staff, visitors)

Name matching is conservative: same surname, compatible first name (equal, or an
initial matching the other's first letter - not accepted for very common surnames
such as Kumar or Singh) and no contradicting middle names. An author whose name
matches two different listed people is left unmatched.
"""

import glob
import os
import re

import pandas as pd

import group10_common as C

ROSTER_DIR = os.path.join(C.REFERENCE_DIR, "faculty_rosters")
SLUG = {"IIIT Allahabad": "iiit_allahabad", "ABV-IIITM Gwalior": "abv_iiitm_gwalior",
        "IIIT Bangalore": "iiit_bangalore", "IIIT Hyderabad": "iiit_hyderabad", "IIIT Delhi": "iiit_delhi"}

ROLE_ORDER = ["Faculty", "Adjunct / visiting faculty", "PhD scholar", "Student (MS / M.Tech / B.Tech)",
              "Likely faculty (not listed)", "Likely student / researcher", "Occasional author"]
VERIFIED = ROLE_ORDER[:4]
STUDENT_LIKE = {"PhD scholar", "Student (MS / M.Tech / B.Tech)", "Likely student / researcher"}
FACULTY_LIKE = {"Faculty", "Adjunct / visiting faculty", "Likely faculty (not listed)"}
_TITLES = {"dr", "prof", "professor", "mr", "mrs", "ms", "shri", "smt", "sri", "er", "phd"}


def name_tokens(name):
    n = re.sub(r"\(.*?\)", " ", str(name or "")).lower()
    n = re.sub(r"[.\-‐_,']", " ", n)
    toks = [t for t in n.split() if t and t not in _TITLES]
    return toks


def _first_ok(a, b):
    if a == b:
        return True
    if len(a) == 1 or len(b) == 1:
        return a[0] == b[0]
    return False


# surnames shared by very many people: an initial is not enough evidence
COMMON_SURNAMES = {"kumar", "singh", "sharma", "gupta", "yadav", "verma", "mishra", "agarwal", "agrawal", "patel",
                   "jain", "das", "reddy", "rao", "shukla", "pandey", "tiwari", "srivastava", "kaur", "khan", "sahu",
                   "dubey", "tripathi", "joshi", "mehta", "shah", "saxena", "chaudhary", "chauhan", "rai", "ghosh",
                   "roy", "sinha", "jha", "pal", "nair", "iyer", "krishnan", "babu", "raj", "prasad", "goyal",
                   "garg", "bansal", "mittal", "dutta", "banerjee", "chatterjee", "mukherjee", "bhat", "naik"}


def _tok_ok(a, b):
    return a == b or ((len(a) == 1 or len(b) == 1) and a[0] == b[0])


def _compatible_middles(at, rt):
    """Middle names must not contradict: aligned by position when both names
    have the same length (initials match full tokens); otherwise every middle
    token of the shorter name must fit one of the longer name's, and a name
    written with initials only must have the same number of parts."""
    if len(at) == len(rt):
        return all(_tok_ok(x, y) for x, y in zip(at[1:-1], rt[1:-1]))
    short, long_ = (at, rt) if len(at) < len(rt) else (rt, at)
    if len(short[0]) == 1:
        return False
    return all(any(_tok_ok(t, x) for x in long_[1:-1]) for t in short[1:-1])


def _match_score(at, rt):
    """3 = identical, 2 = full first name + surname, 1 = initial-compatible, 0 = none."""
    if len(at) < 2 or len(rt) < 2:
        return 0
    if at == rt:
        return 3
    if at[-1] == rt[-1] and _first_ok(at[0], rt[0]) and _compatible_middles(at, rt):
        if at[-1] in COMMON_SURNAMES and ({t for t in at[1:-1] if len(t) > 1} != {t for t in rt[1:-1] if len(t) > 1}):
            return 0
        if at[0] == rt[0]:
            return 2
        return 0 if at[-1] in COMMON_SURNAMES else 1
    # surname-first order ("Varadwaj Pritish Kumar"), full names only
    if len(at[0]) > 1 and len(rt[0]) > 1 and at[0] == rt[-1] and at[-1] == rt[0]:
        return 1
    return 0


def load_rosters():
    """{institution: (faculty_df, students_df)} for every list found on disk."""
    out = {}
    for inst, slug in SLUG.items():
        f = os.path.join(ROSTER_DIR, f"{slug}_faculty.csv")
        s = os.path.join(ROSTER_DIR, f"{slug}_students.csv")
        fac = pd.read_csv(f, dtype=str).fillna("") if os.path.exists(f) else pd.DataFrame()
        stu = pd.read_csv(s, dtype=str).fillna("") if os.path.exists(s) else pd.DataFrame()
        out[inst] = (fac, stu)
    return out


def _best(at, people):
    """people: list of (tokens, payload). Unique best match or None."""
    scored = [(_match_score(at, rt), i) for i, (rt, _) in enumerate(people)]
    scored = [x for x in scored if x[0] > 0]
    if not scored:
        return None
    top = max(x[0] for x in scored)
    hits = [i for sc, i in scored if sc == top]
    # same normalised name listed twice (e.g. two departments) is one person
    keys = {" ".join(people[i][0]) for i in hits}
    return people[hits[0]][1] if len(keys) == 1 else None


def heuristic_role(r):
    if bool(r.get("is_core_faculty")):
        return "Likely faculty (not listed)"
    if int(r.get("papers", 0)) >= 2:
        return "Likely student / researcher"
    return "Occasional author"


def assign_roles(fac):
    """Add role, role_source, roster_designation, roster_department columns."""
    rosters = load_rosters()
    fac = fac.copy()
    roles, src, desig, dept = [], [], [], []
    prepared = {}
    for inst, (fr, sr) in rosters.items():
        fl = [(name_tokens(r["name"]), r) for r in fr.to_dict("records")] if len(fr) else []
        sl = [(name_tokens(r["name"]), r) for r in sr.to_dict("records")] if len(sr) else []
        phd = [x for x in sl if x[1].get("program", "") == "phd"]
        other = [x for x in sl if x[1].get("program", "") != "phd"]
        prepared[inst] = (fl, (phd, other))
    for r in fac.to_dict("records"):
        fl, (phd, other) = prepared.get(r["institution"], ([], ([], [])))
        at = name_tokens(r["name"])
        hit = _best(at, fl)
        if hit is not None:
            role = "Adjunct / visiting faculty" if hit.get("role") == "adjunct_visiting" else (
                "Faculty" if hit.get("role", "faculty") == "faculty" else None)
            if role:
                roles.append(role)
                src.append("institute faculty list")
                desig.append(hit.get("designation", ""))
                dept.append(hit.get("department", ""))
                continue
        hit, role = _best(at, phd), "PhD scholar"
        if hit is None:
            hit, role = _best(at, other), "Student (MS / M.Tech / B.Tech)"
        if hit is not None:
            roles.append(role)
            src.append("institute student list")
            desig.append(hit.get("program", ""))
            dept.append(hit.get("department", ""))
            continue
        roles.append(heuristic_role(r))
        src.append("heuristic (authorship pattern)")
        desig.append("")
        dept.append("")
    fac["role"] = roles
    fac["role_source"] = src
    fac["roster_designation"] = desig
    fac["roster_department"] = dept
    return fac


def roster_coverage(fac):
    """Per institute: listed people, how many were found among the authors,
    and how well the old core-faculty heuristic agrees with the lists."""
    rosters = load_rosters()
    out = {}
    for inst in C.INST_NAMES:
        fr, sr = rosters.get(inst, (pd.DataFrame(), pd.DataFrame()))
        f = fac[fac["institution"] == inst]
        listed_fac = int((fr.get("role", pd.Series(dtype=str)) == "faculty").sum()) if len(fr) else 0
        matched = f[f["role"] == "Faculty"]
        core = f[f["is_core_faculty"]]
        tp = int((core["role"].isin(["Faculty", "Adjunct / visiting faculty"])).sum())
        out[inst] = {
            "faculty_listed": listed_fac,
            "adjunct_listed": int((fr.get("role", pd.Series(dtype=str)) == "adjunct_visiting").sum()) if len(fr) else 0,
            "scholars_listed": int((sr["program"] == "phd").sum()) if len(sr) else 0,
            "students_listed": int((sr["program"] != "phd").sum()) if len(sr) else 0,
            "faculty_matched_authors": int(len(matched)),
            "faculty_listed_with_papers": int(matched["name"].map(lambda n: " ".join(name_tokens(n))).nunique()),
            "scholars_matched_authors": int((f["role"] == "PhD scholar").sum()),
            "students_matched_authors": int((f["role"] == "Student (MS / M.Tech / B.Tech)").sum()),
            "has_roster": bool(len(fr)), "has_scholar_list": bool(len(sr)),
            "heuristic_core": int(len(core)),
            "heuristic_core_on_list_pct": round(tp / len(core) * 100, 1) if len(core) else None,
            "listed_faculty_flagged_core_pct": round(int(matched["is_core_faculty"].sum()) / len(matched) * 100, 1)
            if len(matched) else None,
            "roles": {k: int((f["role"] == k).sum()) for k in ROLE_ORDER},
        }
    return out


def roster_sources():
    """Source URLs per institute (shown on the dashboard's methods page)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(ROSTER_DIR, "*.csv"))):
        d = pd.read_csv(path, dtype=str).fillna("")
        if "source_url" in d:
            out[os.path.basename(path)] = sorted(set(u for u in d["source_url"] if u))[:12]
    return out
