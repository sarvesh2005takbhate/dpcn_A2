"""
DPCN 2026 - Group 10 - Shared analysis functions
=================================================
One implementation of every statistic, used by part3 (report charts),
part4 (static HTML dashboard) and app.py (Streamlit dashboard), so the
three outputs always agree.
"""

import json
import os

import numpy as np
import pandas as pd

import group10_common as C

QUARTILES = ["Q1", "Q2", "Q3", "Q4"]
CORE_RANKS = ["A*", "A", "B", "C"]


# ─────────────────────────────────────────────
# LOADING
# ─────────────────────────────────────────────

def _read_csv(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False, low_memory=False)


def _read_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _bool(s):
    return s.astype(str).str.upper().eq("TRUE")


def load_outputs():
    df = _read_csv(C.DATA_CSV)
    if not df.empty:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df["citations"] = pd.to_numeric(df["citations"], errors="coerce").fillna(0).astype(int)
        for col in ("cites_indian_inst", "cited_by_indian_inst", "is_hyperauthored",
                    "is_international", "is_open_access", "partial_year"):
            if col in df:
                df[col] = _bool(df[col])
        df["n_authors"] = pd.to_numeric(df["n_authors"], errors="coerce").fillna(0).astype(int)
    fac = _read_csv(C.FACULTY_CSV)
    if not fac.empty:
        for col in ("papers", "citations", "h_index", "journal_papers", "conference_papers",
                    "q1_papers", "astar_a_papers", "active_years"):
            fac[col] = pd.to_numeric(fac[col], errors="coerce").fillna(0).astype(int)
        fac["h_index_lifetime_openalex"] = pd.to_numeric(fac["h_index_lifetime_openalex"], errors="coerce")
        fac["is_core_faculty"] = _bool(fac["is_core_faculty"])
    adf = _read_csv(C.AUTHORSHIPS_CSV)
    if not adf.empty:
        adf["year"] = pd.to_numeric(adf["year"], errors="coerce").astype("Int64")
    return {
        "df": df, "fac": fac, "adf": adf,
        "jaccard": _read_csv(C.JACCARD_CSV),
        "indian": _read_csv(C.INDIAN_CSV),
        "cite_edges": _read_csv(C.CITATION_CSV),
        "auth_edges": _read_csv(C.AUTHORSHIP_CSV),
        "cite_metrics": _read_json(C.CITE_METRICS),
        "auth_metrics": _read_json(C.AUTH_METRICS),
        "flow": _read_json(C.FLOW_JSON),
        "insights": _read_json(C.INSIGHTS_JSON),
        "structure": _read_json(C.STRUCTURE_JSON),
    }


def unique_papers(df):
    """One row per paper (a paper shared by two assigned institutes counts once)."""
    return df.drop_duplicates("openalex_id")


# ─────────────────────────────────────────────
# INSTITUTION-LEVEL STATISTICS
# ─────────────────────────────────────────────

def institution_summary(df, fac):
    rows = []
    groups = [(i, df[df["institution"] == i]) for i in C.INST_NAMES] + [("All (unique papers)", unique_papers(df))]
    for inst, s in groups:
        j = s[s["type"] == "journal"]
        c = s[s["type"] == "conference"]
        fac_i = fac[fac["is_core_faculty"]] if inst.startswith("All") else \
            fac[(fac["institution"] == inst) & fac["is_core_faculty"]]
        authors = fac if inst.startswith("All") else fac[fac["institution"] == inst]
        no_mega = s[~s["is_hyperauthored"]]
        rows.append({
            "institution": inst,
            "papers": len(s),
            "journal_papers": len(j),
            "conference_papers": len(c),
            "q1_journal_pct": round((j["quartile"] == "Q1").mean() * 100, 1) if len(j) else 0.0,
            "q1_q2_journal_pct": round(j["quartile"].isin(["Q1", "Q2"]).mean() * 100, 1) if len(j) else 0.0,
            "unranked_journal_pct": round((j["quartile"] == "").mean() * 100, 1) if len(j) else 0.0,
            "q1_papers": int((j["quartile"] == "Q1").sum()),
            "core_astar_a": int(c["quartile"].isin(["A*", "A"]).sum()),
            "core_ranked_pct": round((c["quartile"] != "").mean() * 100, 1) if len(c) else 0.0,
            "citations": int(s["citations"].sum()),
            "citations_excl_mega": int(no_mega["citations"].sum()),
            "mean_citations": round(s["citations"].mean(), 2) if len(s) else 0,
            "median_citations": float(s["citations"].median()) if len(s) else 0,
            "zero_cited_pct": round((s["citations"] == 0).mean() * 100, 1) if len(s) else 0,
            "h_index": C.hindex(s["citations"]),
            "affiliated_authors": int(authors["author_id"].nunique()) if len(authors) else 0,
            "core_faculty": int(fac_i["author_id"].nunique()) if len(fac_i) else 0,
            "median_faculty_h": float(fac_i["h_index"].median()) if len(fac_i) else 0,
            "international_pct": round(s["is_international"].mean() * 100, 1) if len(s) else 0,
            "indian_collab_pct": round((s["coauthor_institutes"] != "").mean() * 100, 1) if len(s) else 0,
            "cites_indian_pct": round(s["cites_indian_inst"].mean() * 100, 1) if len(s) else 0,
            "cited_by_indian_pct": round(s["cited_by_indian_inst"].mean() * 100, 1) if len(s) else 0,
            "open_access_pct": round(s["is_open_access"].mean() * 100, 1) if len(s) else 0,
            "hyperauthored_papers": int(s["is_hyperauthored"].sum()),
        })
    return pd.DataFrame(rows)


def publication_trend(df, by_type=False):
    keys = ["year", "institution"] + (["type"] if by_type else [])
    t = df.groupby(keys).size().rename("papers").reset_index()
    return t


def quartile_table(df):
    j = df[df["type"] == "journal"]
    t = (j.assign(q=j["quartile"].replace("", "Unranked"))
         .groupby(["institution", "q"]).size().unstack(fill_value=0))
    return t.reindex(columns=QUARTILES + ["Unranked"], fill_value=0).reindex(C.INST_NAMES, fill_value=0)


def core_table(df):
    c = df[df["type"] == "conference"]
    t = (c.assign(r=c["quartile"].replace("", "Unranked"))
         .groupby(["institution", "r"]).size().unstack(fill_value=0))
    return t.reindex(columns=CORE_RANKS + ["Unranked"], fill_value=0).reindex(C.INST_NAMES, fill_value=0)


def top_venues(df, inst, kind="journal", n=5):
    s = df[(df["institution"] == inst) & (df["type"] == kind) & (df["journal_name"] != "")]
    return (s.groupby("journal_name")
            .agg(papers=("openalex_id", "count"), citations=("citations", "sum"),
                 quartile=("quartile", lambda q: q.mode().iloc[0] if len(q.mode()) else ""))
            .sort_values(["papers", "citations"], ascending=False).head(n).reset_index())


def most_cited(df, n=10, inst=None):
    s = df if inst is None else df[df["institution"] == inst]
    s = s.sort_values("citations", ascending=False)
    if inst is None:
        s = (s.groupby("openalex_id", sort=False)
             .agg(title=("title", "first"), institution=("institution", lambda x: " & ".join(x)),
                  journal_name=("journal_name", "first"), year=("year", "first"),
                  citations=("citations", "first"), doi=("doi", "first"),
                  n_authors=("n_authors", "first"), type=("type", "first"))
             .reset_index())
    return s.head(n)[["title", "institution", "journal_name", "year", "citations", "doi",
                      "n_authors", "type"]].reset_index(drop=True)


def research_areas(df, level="field", n=10):
    """Share of each institution's papers per OpenAlex field/subfield (%)."""
    s = df[df[level] != ""]
    t = s.groupby(["institution", level]).size().unstack(fill_value=0)
    share = t.div(t.sum(axis=1), axis=0) * 100
    top = share.mean(axis=0).sort_values(ascending=False).head(n).index
    return share[top].reindex(C.INST_NAMES).fillna(0).round(1)


def department_breakdown(adf, fac):
    """Papers per (institution, department) - a paper counts once per department."""
    if adf.empty or fac.empty:
        return pd.DataFrame()
    dept = fac.drop_duplicates(["institution", "author_id"]).set_index(["institution", "author_id"])["department"]
    a = adf.join(dept, on=["institution", "author_id"])
    t = (a.drop_duplicates(["institution", "department", "openalex_id"])
         .groupby(["institution", "department"]).agg(papers=("openalex_id", "nunique"),
                                                       citations=("citations", "sum"))
         .reset_index())
    f = (fac[fac["is_core_faculty"]].groupby(["institution", "department"])
         .agg(core_faculty=("author_id", "nunique"), median_h=("h_index", "median")).reset_index())
    return t.merge(f, on=["institution", "department"], how="left").fillna({"core_faculty": 0})


def citation_age(df):
    return (df.groupby(["year", "institution"])["citations"]
            .agg(["mean", "median", "count"]).round(2).reset_index())


def h_hist(fac, inst, core_only=True, cap=30):
    f = fac[(fac["institution"] == inst) & (fac["is_core_faculty"] | (not core_only))]
    h = f["h_index"].clip(upper=cap)
    return np.bincount(h, minlength=cap + 1).tolist()


def faculty_list(fac, inst=None, core_only=True):
    f = fac if inst is None else fac[fac["institution"] == inst]
    if core_only:
        f = f[f["is_core_faculty"]]
    cols = ["name", "institution", "department", "department_source", "papers", "journal_papers",
            "conference_papers", "q1_papers", "citations", "h_index", "h_index_lifetime_openalex",
            "top_journal", "first_year", "last_year"]
    return f[cols].sort_values(["h_index", "citations"], ascending=False).reset_index(drop=True)


def top_partners(indian, inst=None, n=15, by="shared_papers"):
    if indian.empty:
        return indian
    s = indian if inst is None else indian[indian["your_inst"] == inst]
    s = s[s[by].astype(int) > 0]
    return s.sort_values(by, ascending=False).head(n)


def cluster_links(indian):
    """Shared papers per (our institution, partner cluster)."""
    if indian.empty:
        return indian
    s = indian.copy()
    s["shared_papers"] = s["shared_papers"].astype(int)
    return (s[s["shared_papers"] > 0].groupby(["your_inst", "partner_cluster"])["shared_papers"]
            .sum().unstack(fill_value=0))
