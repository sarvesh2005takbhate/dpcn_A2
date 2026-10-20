"""
DPCN 2026 - Group 10 - Part 1b: Build the dataset + enrichment
================================================================
Runs AFTER part1_collect_data.py (uses ./cache/). Produces:

  group10_data.csv              main dataset - one row per (paper, assigned institution)
                                with all 14 required columns + extra analysis columns
  group10_authorships.csv       one row per (paper, author affiliated with our institution)
  group10_faculty.csv           faculty list: name, department, papers, citations, h-index ...
  group10_jaccard_similarity.csv research-topic similarity (OpenAlex subfields) between
                                our institutions and their top Indian partner institutions

Key definitions
---------------
* type          journal | conference (preprints, book chapters, errata, datasets,
                peer reviews, retracted papers and duplicate versions are excluded)
* quartile      journals: Scimago SJR best quartile of the journal in the publication
                year (2026 uses SJR 2025); conferences: CORE rank (ICORE2026, A*/A/B/C)
* citations     OpenAlex cited_by_count (max over versions of the same paper)
* author        authors of the paper affiliated with THIS institution
* coauthor_institutes   other Indian institutions on the paper (OpenAlex country_code IN)
* cites_indian_inst     paper cites a work authored at another Indian institution
* cited_by_indian_inst  paper is cited by a work authored at another Indian institution
* department    parsed from the raw affiliation strings ("Department of ..."); if the
                author never states one, inferred from their dominant OpenAlex field
* core faculty  heuristic for permanent faculty (PI pattern): >=5 papers at the
                institution in >=3 distinct years, last author on >=30% of them and
                first author on <=50% (excludes most PhD students)

Usage:
    python part1b_enrich_data.py
"""

import sys
from collections import Counter, defaultdict
from itertools import combinations

import pandas as pd

import group10_common as C

MIN_SUBFIELD_SHARE = 0.01     # subfields below 1% of an entity's output are noise
TOP_PARTNERS = 10


# ─────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────

def load_inputs():
    works = C.load_json_gz(C.WORKS_CACHE, {}).get("works", {})
    if not works:
        print("ERROR: cache/works.json.gz missing - run part1_collect_data.py first.")
        sys.exit(1)
    inflow = C.load_json_gz(C.INFLOW_CACHE, {}).get("works", {})
    outflow = C.load_json_gz(C.OUTFLOW_CACHE, {}).get("works", {})
    if not inflow or not outflow:
        print("WARNING: citation-flow caches incomplete - cites/cited_by flags will be partial.")
    return works, inflow, outflow


# ─────────────────────────────────────────────
# AUTHORS
# ─────────────────────────────────────────────

def affiliated_authorships(work, inst_id, inst_name):
    """Authorships of `work` that are affiliated with our institution."""
    out = []
    for a in work["authorships"]:
        if any(i["id"] == inst_id for i in a["insts"]):
            raw = [af["s"] for af in a["affs"] if inst_id in af["i"]] or [af["s"] for af in a["affs"]]
            dept = C.most_common_nonempty(C.department_from_affiliation(s) for s in raw)
            # authorships without an OpenAlex author ID get a name-based pseudo ID
            aid = a["aid"] or "noid:" + C.norm_person(a["name"])
            out.append({"aid": aid, "name": a["name"], "pos": a["pos"],
                        "corr": a["corr"], "dept": dept})
    return out


def canonical_author_map(records):
    """Merge OpenAlex author IDs that are the same person (identical normalised
    name at our institutions). Returns raw id -> (canonical id, display name)."""
    by_name = defaultdict(Counter)
    names = defaultdict(Counter)
    for r in records:
        key = C.norm_person(r["name"])
        by_name[key][r["aid"]] += 1
        names[key][r["name"]] += 1
    mapping = {}
    for key, ids in by_name.items():
        canon = ids.most_common(1)[0][0]
        disp = names[key].most_common(1)[0][0]
        for aid in ids:
            mapping[aid] = (canon, disp)
    return mapping


# ─────────────────────────────────────────────
# MAIN DATASET
# ─────────────────────────────────────────────

def build_dataset(works, inflow, outflow):
    scimago = C.Scimago()
    core = C.CoreRanks()
    print(f"  Scimago SJR loaded (up to {scimago.max_year}); CORE edition: {core.edition}")

    corpus, excluded, aliases = C.select_corpus(works, scimago)
    aliases_of = defaultdict(list)
    for a, canon in aliases.items():
        aliases_of[canon].append(a)
    print(f"  Corpus: {len(corpus)} papers")
    for reason, n in excluded.most_common():
        print(f"    excluded {n:5d}  {reason}")

    # Indian works that cite each corpus paper (credit aliases to canonical)
    citing_by_paper = defaultdict(list)
    for cw in inflow.values():
        for t in cw.get("cites", []):
            citing_by_paper[aliases.get(t, t)].append(cw)
    # Indian works cited by each corpus paper
    cited_by_paper = defaultdict(list)
    for wid in corpus:
        for r in works[wid]["refs"]:
            if r in outflow:
                cited_by_paper[wid].append(outflow[r])

    rows, auth_rows = [], []
    for wid, (ptype, venue) in corpus.items():
        w = works[wid]
        cites = C.effective_citations(wid, works, aliases_of)
        sjr_q = scimago.quartile(venue, w["year"]) if venue["name"] else ""
        core_rank = core.rank(venue["name"]) if ptype == "conference" else ""
        quartile = sjr_q if ptype == "journal" else core_rank
        all_names = [a["name"] for a in w["authorships"]]
        n_auth = len(all_names)
        our_insts = C.our_institutions_on(w)
        foreign = sorted({i["name"] for a in w["authorships"] for i in a["insts"]
                          if i["cc"] and i["cc"] != "IN"})
        countries = sorted({i["cc"] for a in w["authorships"] for i in a["insts"]
                            if i["cc"] and i["cc"] != "IN"})
        for inst in our_insts:
            inst_id = C.INSTITUTIONS[inst][0]
            mine = affiliated_authorships(w, inst_id, inst)
            indian = C.indian_institutions(w["authorships"], exclude_ids={inst_id})
            ind_sorted = sorted(indian.values(), key=lambda i: i["name"])   # names & ids aligned
            out_partners = {iid for cw in cited_by_paper[wid] for iid in cw["insts"] if iid != inst_id}
            in_partners = {iid for cw in citing_by_paper[wid] for iid in cw["insts"] if iid != inst_id}
            n_in_works = sum(1 for cw in citing_by_paper[wid] if set(cw["insts"]) - {inst_id})
            n_out_works = sum(1 for cw in cited_by_paper[wid] if set(cw["insts"]) - {inst_id})
            rows.append({
                "group": C.GROUP,
                "institution": inst,
                "author": "; ".join(a["name"] for a in mine),
                "title": w["title"],
                "year": w["year"],
                "type": ptype,
                "journal_name": venue["name"],
                "issn": venue["issn_l"] or (venue["issn"][0] if venue["issn"] else ""),
                "doi": f"https://doi.org/{w['doi']}" if w["doi"] else "",
                "citations": cites,
                "quartile": quartile,
                "coauthor_institutes": ";".join(i["name"] for i in ind_sorted),
                "cites_indian_inst": "TRUE" if n_out_works else "FALSE",
                "cited_by_indian_inst": "TRUE" if n_in_works else "FALSE",
                # ── extra analysis columns ──
                "openalex_id": wid,
                "sjr_quartile": sjr_q,
                "core_rank": core_rank,
                "venue_source_type": venue["stype"],
                "field": w["field"],
                "subfield": w["subfield"],
                "topic": w["topic"],
                "n_authors": n_auth,
                "is_hyperauthored": n_auth > C.HYPERAUTHOR_THRESHOLD,
                "all_authors": "; ".join(all_names),
                "group_coinstitutions": ";".join(i for i in our_insts if i != inst),
                "coauthor_institute_ids": ";".join(i["id"] for i in ind_sorted),
                "foreign_coauthor_institutes": ";".join(foreign),
                "coauthor_countries": ";".join(countries),
                "is_international": bool(countries),
                "n_references": len(w["refs"]),
                "indian_works_cited": n_out_works,
                "indian_citing_works": n_in_works,
                "indian_institutes_cited": len(out_partners),
                "indian_institutes_citing": len(in_partners),
                "is_open_access": w["is_oa"],
                "partial_year": w["year"] == C.PARTIAL_YEAR,
            })
            for a in mine:
                auth_rows.append({
                    "openalex_id": wid, "doi": w["doi"], "year": w["year"],
                    "institution": inst, "raw_author_id": a["aid"], "author_name": a["name"],
                    "author_position": a["pos"], "is_corresponding": a["corr"],
                    "department_affiliation": a["dept"], "citations": cites,
                    "type": ptype, "journal_name": venue["name"], "quartile": quartile,
                    "field": w["field"],
                })

    df = pd.DataFrame(rows).sort_values(["institution", "year", "citations"],
                                        ascending=[True, True, False])
    adf = pd.DataFrame(auth_rows)
    amap = canonical_author_map(adf.rename(columns={"raw_author_id": "aid",
                                                    "author_name": "name"}).to_dict("records"))
    adf["author_id"] = adf["raw_author_id"].map(lambda a: amap[a][0])
    adf["author_name"] = adf["raw_author_id"].map(lambda a: amap[a][1])
    return df, adf


# ─────────────────────────────────────────────
# FACULTY TABLE
# ─────────────────────────────────────────────

def build_faculty(adf, oa):
    rows = []
    for (inst, aid), g in adf.groupby(["institution", "author_id"]):
        papers = g.drop_duplicates("openalex_id")
        n = len(papers)
        years = papers["year"].nunique()
        last_share = (papers["author_position"] == "last").mean()
        first_share = (papers["author_position"] == "first").mean()
        dept = C.most_common_nonempty(g["department_affiliation"].fillna(""))
        dept_src = "affiliation"
        if not dept:
            dept = C.FIELD_TO_DEPT.get(C.most_common_nonempty(papers["field"].fillna("")), "Other")
            dept_src = "inferred (OpenAlex field)"
        venues = papers[papers["journal_name"].fillna("") != ""]
        top_venue = venues["journal_name"].value_counts().index[0] if len(venues) else ""
        best = papers.sort_values("citations", ascending=False).iloc[0]
        rows.append({
            "author_id": aid,
            "name": g["author_name"].iloc[0],
            "institution": inst,
            "department": dept,
            "department_source": dept_src,
            "papers": n,
            "journal_papers": int((papers["type"] == "journal").sum()),
            "conference_papers": int((papers["type"] == "conference").sum()),
            "q1_papers": int((papers["quartile"] == "Q1").sum()),
            "astar_a_papers": int(papers["quartile"].isin(["A*", "A"]).sum()),
            "citations": int(papers["citations"].sum()),
            "h_index": C.hindex(papers["citations"]),
            "top_journal": top_venue,
            "most_cited_paper_venue": best["journal_name"],
            "first_year": int(papers["year"].min()),
            "last_year": int(papers["year"].max()),
            "active_years": int(years),
            "last_author_share": round(float(last_share), 3),
            "first_author_share": round(float(first_share), 3),
            "is_core_faculty": bool(n >= 5 and years >= 3 and last_share >= 0.3 and first_share <= 0.5),
            "openalex_author_ids": ";".join(sorted(g["raw_author_id"].unique())),
        })
    fac = pd.DataFrame(rows)

    # lifetime h-index from OpenAlex author profiles (core faculty only)
    cache = C.load_json_gz(C.AUTHORS_CACHE, {})
    want = []
    for ids in fac.loc[fac["is_core_faculty"], "openalex_author_ids"]:
        want.extend(ids.split(";"))
    missing = [a for a in dict.fromkeys(want) if a.startswith("A") and a not in cache]
    if missing:
        print(f"  Fetching {len(missing)} OpenAlex author profiles ...")
        try:
            for i in range(0, len(missing), 100):
                data = oa.get("authors", {"filter": "openalex:" + "|".join(missing[i:i + 100]),
                                          "per_page": 100,
                                          "select": "id,display_name,works_count,cited_by_count,summary_stats"})
                for r in data.get("results", []):
                    s = r.get("summary_stats") or {}
                    cache[C.short_id(r["id"])] = {"h": s.get("h_index"), "works": r.get("works_count"),
                                                  "cites": r.get("cited_by_count")}
        except C.BudgetExhausted as e:
            print(f"  [budget] {e} - lifetime h-index left partly empty")
        C.save_json_gz(cache, C.AUTHORS_CACHE)

    def lifetime(ids, key):
        vals = [cache[a][key] for a in ids.split(";") if a in cache and cache[a].get(key) is not None]
        return max(vals) if vals else None

    fac["h_index_lifetime_openalex"] = fac["openalex_author_ids"].map(lambda s: lifetime(s, "h"))
    fac["works_lifetime_openalex"] = fac["openalex_author_ids"].map(lambda s: lifetime(s, "works"))
    return fac.sort_values(["institution", "is_core_faculty", "citations"], ascending=[True, False, False])


# ─────────────────────────────────────────────
# JACCARD SIMILARITY OF RESEARCH TOPICS
# ─────────────────────────────────────────────

def subfield_profile(oa, inst_id, cache):
    if inst_id in cache:
        return cache[inst_id]
    flt = (f"authorships.institutions.id:{inst_id},publication_year:{C.START_YEAR}-{C.END_YEAR},"
           "type:article|review|conference-paper")
    # OpenAlex returns at most the 200 largest groups; the remaining subfields
    # are far below the 1% threshold and negligible for the weighted index
    data = oa.get("works", {"filter": flt, "group_by": "primary_topic.subfield.id", "per_page": 200})
    prof = {g["key_display_name"]: g["count"] for g in data.get("group_by", [])
            if g.get("key_display_name") and g["key_display_name"] != "unknown"}
    cache[inst_id] = prof
    return prof


def compare(pa, pb):
    ta, tb = sum(pa.values()) or 1, sum(pb.values()) or 1
    sa = {k: v / ta for k, v in pa.items()}
    sb = {k: v / tb for k, v in pb.items()}
    keys = set(sa) | set(sb)
    weighted = sum(min(sa.get(k, 0), sb.get(k, 0)) for k in keys) / \
        (sum(max(sa.get(k, 0), sb.get(k, 0)) for k in keys) or 1)
    A = {k for k, v in sa.items() if v >= MIN_SUBFIELD_SHARE}
    B = {k for k, v in sb.items() if v >= MIN_SUBFIELD_SHARE}
    binary = len(A & B) / len(A | B) if A | B else 0.0
    shared = sorted(A & B, key=lambda k: -min(sa[k], sb[k]))
    return round(binary, 4), round(weighted, 4), A, B, shared


def build_jaccard(df, oa, works):
    cache = C.load_json_gz(C.TOPICS_CACHE, {})
    inst_type = {i["id"]: i["type"] for w in works.values() for a in w["authorships"] for i in a["insts"]}
    # top Indian co-author partners per institution (by shared papers)
    our_ids = {v[0] for v in C.INSTITUTIONS.values()}
    partners = {}
    names = {}
    for inst in C.INST_NAMES:
        sub = df[df["institution"] == inst]
        cnt = Counter()
        for ids, nm in zip(sub["coauthor_institute_ids"].fillna(""), sub["coauthor_institutes"].fillna("")):
            for iid, n in zip(ids.split(";"), nm.split(";")):
                if iid and iid not in our_ids:
                    cnt[iid] += 1
                    names[iid] = n
        partners[inst] = cnt.most_common(TOP_PARTNERS)

    profiles = {}
    try:
        for inst, (iid, _) in C.INSTITUTIONS.items():
            profiles[iid] = subfield_profile(oa, iid, cache)
        for plist in partners.values():
            for iid, _ in plist:
                profiles[iid] = subfield_profile(oa, iid, cache)
    except C.BudgetExhausted as e:
        print(f"  [budget] {e} - Jaccard computed for the profiles fetched so far")
    finally:
        C.save_json_gz(cache, C.TOPICS_CACHE)

    rows = []

    def add(a_name, b_name, a_id, b_id, kind, shared_papers=None):
        if a_id not in profiles or b_id not in profiles:
            return
        binary, weighted, A, B, shared = compare(profiles[a_id], profiles[b_id])
        rows.append({
            "entity_a": a_name, "entity_b": b_name, "comparison_type": kind,
            "partner_cluster": (C.institution_cluster(b_name, inst_type.get(b_id, ""))
                                if kind != "intra_group" else C.OUR_CLUSTER),
            "shared_papers": shared_papers,
            "jaccard_similarity": binary, "weighted_jaccard": weighted,
            "entity_a_subfields": len(A), "entity_b_subfields": len(B),
            "shared_subfields_count": len(shared),
            "top_shared_subfields": "; ".join(shared[:8]),
        })

    for a, b in combinations(C.INST_NAMES, 2):
        add(a, b, C.INSTITUTIONS[a][0], C.INSTITUTIONS[b][0], "intra_group")
    for inst, plist in partners.items():
        for iid, n in plist:
            add(inst, names[iid], C.INSTITUTIONS[inst][0], iid, "cross_institution", n)
    out = pd.DataFrame(rows)
    out["shared_papers"] = out["shared_papers"].astype("Int64")
    return out.sort_values(["comparison_type", "jaccard_similarity"], ascending=[False, False])


def main():
    print("=" * 65)
    print(" DPCN 2026 - Group 10 - Part 1b: Dataset build + enrichment")
    print("=" * 65)
    works, inflow, outflow = load_inputs()
    oa = C.OpenAlex()

    print("\n[1/3] Building main dataset ...")
    df, adf = build_dataset(works, inflow, outflow)
    df.to_csv(C.DATA_CSV, index=False, encoding="utf-8-sig")
    adf.to_csv(C.AUTHORSHIPS_CSV, index=False, encoding="utf-8-sig")
    print(f"  Saved {C.DATA_CSV} ({len(df)} rows) and {C.AUTHORSHIPS_CSV} ({len(adf)} rows)")
    for inst in C.INST_NAMES:
        s = df[df["institution"] == inst]
        j = s[s["type"] == "journal"]
        print(f"    {inst:18s} papers={len(s):5d} journal={len(j):5d} "
              f"Q1={(j['quartile'] == 'Q1').mean() * 100:5.1f}% of journal | "
              f"CORE-ranked conf={(s['core_rank'] != '').sum()}")

    print("\n[2/3] Faculty table ...")
    fac = build_faculty(adf, oa)
    fac.to_csv(C.FACULTY_CSV, index=False, encoding="utf-8-sig")
    core = fac[fac["is_core_faculty"]]
    print(f"  Saved {C.FACULTY_CSV}: {len(fac)} affiliated authors, {len(core)} core faculty")
    print(core.groupby("institution").size().to_string())

    print("\n[3/3] Jaccard similarity of research topics (OpenAlex subfields) ...")
    jac = build_jaccard(df, oa, works)
    jac.to_csv(C.JACCARD_CSV, index=False, encoding="utf-8-sig")
    print(f"  Saved {C.JACCARD_CSV} ({len(jac)} rows)")
    print(jac.head(8)[["entity_a", "entity_b", "jaccard_similarity", "weighted_jaccard"]].to_string(index=False))

    print(f"\n  OpenAlex requests: {oa.calls} | budget left: {oa.remaining}")
    print("=" * 65)
    print(" Part 1b complete. Next: python part2_networks.py")
    print("=" * 65)


if __name__ == "__main__":
    main()
