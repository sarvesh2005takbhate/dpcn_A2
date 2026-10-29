"""
DPCN 2026 - Group 10 - Part 4: Interactive HTML dashboard
==========================================================
Builds dashboard.html - a single self-contained file (Chart.js + D3 inlined)
that opens in any browser, offline. Panels (instruction note section 4):

  Overview      publication trend, Q1/Q2/Q3/Q4 share, CORE A*/A/B/C breakdown,
                research areas, top-10 most-cited papers, citation age
  Institution   per-institute KPIs, trend (journal vs conference), quartile and
  pages (x3)    CORE breakdown, top-5 journals / conferences, research areas,
                departments, faculty h-index histogram, faculty list + sortable
                faculty performance table, top-10 cited papers
  Citation      internal directed citation graph (D3), PageRank top-10,
  network       in-degree distribution
  Authorship    co-authorship graph coloured by Louvain community (D3), degree /
  network       betweenness top-10, communities, hub authors
  Indian        citation in-/out-flow per year, impact ratio, top-10 citing
  connectivity  institutes, top citing papers, partner ranking with cross-cluster
                flags, cluster links, Jaccard topic similarity

Usage:
    python part4_dashboard.py
"""

import json
import os
from collections import Counter
from datetime import date

import pandas as pd
import requests

import group10_analysis as A
import group10_common as C

OUTPUT_HTML = "dashboard.html"
LIBS = {
    "assets/d3.min.js": "https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js",
    "assets/chart.umd.min.js": "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js",
}
KEYS = {"IIIT Allahabad": "iiita", "ABV-IIITM Gwalior": "abv", "IIIT Bangalore": "iiitb"}
CITE_GRAPH_NODES = 220
EXPLORER_PER_INST = 110
SITE_DIR = "site"           # deploy folder (gitignored: the page embeds node-level data)


def lib(local):
    if not os.path.exists(local):
        print(f"  Downloading {local} ...")
        os.makedirs(os.path.dirname(local), exist_ok=True)
        r = requests.get(LIBS[local], timeout=60)
        r.raise_for_status()
        with open(local, "w", encoding="utf-8") as f:
            f.write(r.text)
    with open(local, encoding="utf-8") as f:
        return f.read()


def records(df):
    return json.loads(df.to_json(orient="records", force_ascii=False))


def explorer_graph(o, nd):
    """Co-authorship subgraph for the Network Explorer: the most connected
    authors of each institute plus EVERY author with a co-author at another
    institute, so the inter-institution structure is shown completely."""
    ae = o["auth_edges"]
    ae = ae[ae["edge_scope"].isin(["same_institution", "inter_group"])]
    w = ae.groupby(["author_a_id", "author_b_id"])["paper_doi"].nunique().reset_index(name="w")
    inst = nd["institution"].to_dict()
    cross = Counter()
    for a, b in zip(w["author_a_id"], w["author_b_id"]):
        if inst[a] != inst[b]:
            cross[a] += 1
            cross[b] += 1
    moved = set(o["adf"].groupby("author_id")["institution"].nunique().loc[lambda s: s > 1].index)
    keep = set(cross) | (moved & set(nd.index))
    for i in C.INST_NAMES:
        keep |= set(nd[nd["institution"] == i].sort_values("strength", ascending=False).head(EXPLORER_PER_INST).index)
    sub = nd.loc[sorted(keep)]
    w = w[w["author_a_id"].isin(keep) & w["author_b_id"].isin(keep)]
    return {"nodes": [{"id": k, "n": r["name"], "i": r["institution"], "dep": r["department"],
                       "cm": int(r["community"]), "dg": int(r["degree"]), "b": r["betweenness_centrality"],
                       "core": bool(r["is_core_faculty"]), "x": int(cross.get(k, 0)), "mv": k in moved,
                       "p": int(r["papers"])} for k, r in sub.iterrows()],
            "links": [{"source": a, "target": b, "w": int(n), "x": inst[a] != inst[b]}
                      for a, b, n in w.itertuples(index=False)],
            "per_inst": EXPLORER_PER_INST}


# ─────────────────────────────────────────────
# DATA FOR THE PAGE
# ─────────────────────────────────────────────

def build_data(o):
    df, fac, adf = o["df"], o["fac"], o["adf"]
    years = list(range(C.START_YEAR, C.END_YEAR + 1))
    D = {"meta": {"institutions": C.INST_NAMES, "keys": KEYS, "colors": C.INST_COLORS,
                  "colors_dark": C.INST_COLORS_DARK, "years": years, "partial_year": C.PARTIAL_YEAR,
                  "generated": date.today().isoformat(), "full_names": C.INST_FULL_NAMES,
                  "ror": {k: v[1] for k, v in C.INSTITUTIONS.items()},
                  "openalex": {k: v[0] for k, v in C.INSTITUTIONS.items()}}}
    D["summary"] = records(A.institution_summary(df, fac))

    tr = A.publication_trend(df, by_type=True)
    D["trend"] = {inst: {t: [int(tr[(tr.institution == inst) & (tr.type == t) & (tr.year == y)]["papers"].sum())
                             for y in years] for t in ("journal", "conference")} for inst in C.INST_NAMES}
    D["quartile"] = A.quartile_table(df).to_dict(orient="index")
    D["core"] = A.core_table(df).to_dict(orient="index")
    fields = A.research_areas(df, "field", 8)
    D["fields"] = {"labels": list(fields.columns), "values": {i: fields.loc[i].tolist() for i in C.INST_NAMES}}
    D["subfields"] = {i: records(df[(df.institution == i) & (df.subfield != "")]["subfield"]
                                 .value_counts().head(10).rename_axis("name").reset_index(name="papers"))
                      for i in C.INST_NAMES}
    D["top_journals"] = {i: records(A.top_venues(df, i, "journal", 5)) for i in C.INST_NAMES}
    D["top_conferences"] = {i: records(A.top_venues(df, i, "conference", 5)) for i in C.INST_NAMES}
    D["most_cited"] = records(A.most_cited(df, 10))
    D["most_cited_inst"] = {i: records(A.most_cited(df, 10, i)) for i in C.INST_NAMES}
    age = A.citation_age(df)
    D["citation_age"] = {i: [float(age[(age.institution == i) & (age.year == y)]["median"].sum()) for y in years]
                         for i in C.INST_NAMES}
    D["hhist"] = {i: A.h_hist(fac, i) for i in C.INST_NAMES}

    f = fac[fac["papers"] >= 2].copy()
    D["faculty"] = {i: [[r.name, r.department, r.department_source.startswith("inferred"), int(r.papers),
                         int(r.journal_papers), int(r.conference_papers), int(r.q1_papers), int(r.citations),
                         int(r.h_index), None if pd.isna(r.h_index_lifetime_openalex) else int(r.h_index_lifetime_openalex),
                         r.top_journal, int(r.first_year), int(r.last_year), bool(r.is_core_faculty)]
                        for r in f[f.institution == i].itertuples()] for i in C.INST_NAMES}
    dep = A.department_breakdown(adf, fac)
    D["departments"] = {i: records(dep[dep.institution == i].sort_values("papers", ascending=False))
                        for i in C.INST_NAMES} if not dep.empty else {}

    # citation network
    cm = o["cite_metrics"]
    D["cite"] = {"summary": cm.get("summary", {}), "top10": cm.get("pagerank_top10", [])}
    papers = df.drop_duplicates("openalex_id").set_index("openalex_id")
    edges = o["cite_edges"]
    internal = edges[edges["edge_type"] == "internal"] if not edges.empty else edges
    pr, indeg = cm.get("pagerank", {}), cm.get("in_degree", {})
    connected = set(internal["source_openalex_id"]) | set(internal["target_openalex_id"]) if len(internal) else set()
    # highest-PageRank papers, keeping only those linked to another shown paper
    # (an isolated dot says nothing about citation structure)
    ranked = sorted(connected, key=lambda w: -pr.get(w, 0))[:CITE_GRAPH_NODES * 3]
    rs = set(ranked)
    linked = {w for s_, t_ in zip(internal["source_openalex_id"], internal["target_openalex_id"])
              if s_ in rs and t_ in rs for w in (s_, t_)}
    chosen = [w for w in ranked if w in linked][:CITE_GRAPH_NODES]
    cs = set(chosen)
    insts_of = df.groupby("openalex_id")["institution"].apply(list).to_dict()
    D["cite"]["graph"] = {
        "nodes": [{"id": w, "t": papers.loc[w, "title"][:110], "i": insts_of[w], "y": int(papers.loc[w, "year"]),
                   "pr": pr.get(w, 0), "d": indeg.get(w, 0), "c": int(papers.loc[w, "citations"]),
                   "doi": C.normalize_doi(papers.loc[w, "doi"])} for w in chosen],
        "links": [{"source": s, "target": t} for s, t in
                  zip(internal["source_openalex_id"], internal["target_openalex_id"]) if s in cs and t in cs]}

    # authorship network
    am = o["auth_metrics"]
    nodes = am.get("nodes", {})
    nd = pd.DataFrame.from_dict(nodes, orient="index") if nodes else pd.DataFrame()
    D["auth"] = {"summary": am.get("summary", {}), "communities": am.get("communities", [])[:12],
                 "hubs": am.get("hub_authors", [])[:12]}
    if not nd.empty:
        D["auth"]["top_degree"] = records(nd.sort_values("degree_centrality", ascending=False).head(10)
                                          [["name", "institution", "department", "degree", "degree_centrality"]])
        D["auth"]["top_between"] = records(nd.sort_values("betweenness_centrality", ascending=False).head(10)
                                           [["name", "institution", "department", "betweenness_centrality"]])

    # Indian connectivity
    flow = o["flow"]
    D["flow"] = {i: {k: v for k, v in flow[i].items()
                     if k not in ("partner_in", "partner_out", "partner_names", "partner_clusters")}
                 for i in flow}
    ind = o["indian"]
    if not ind.empty:
        D["partners"] = {i: records(A.top_partners(ind, i, 15)[
            ["partner_inst", "partner_cluster", "shared_papers", "total_citations",
             "citations_received_from_partner", "citations_given_to_partner", "cross_cluster", "intra_group"]])
            for i in C.INST_NAMES}
        cl = A.cluster_links(ind)
        D["cluster_links"] = {"clusters": list(cl.columns),
                              "values": {i: [int(cl.loc[i, c]) if i in cl.index else 0 for c in cl.columns]
                                         for i in C.INST_NAMES}}
    D["jaccard"] = records(o["jaccard"]) if not o["jaccard"].empty else []
    D["insights"] = o["insights"]
    S = o["structure"]
    D["structure"] = S
    if nodes and S:
        D["explorer"] = explorer_graph(o, nd)
    D["links"] = {"repo": C.REPO_URL, "report": C.REPORT_URL, "dashboard": C.DASHBOARD_LIVE_URL,
                  "team": C.TEAM_NAME, "members": C.TEAM_MEMBERS}
    return D


# ─────────────────────────────────────────────
# PAGE TEMPLATE
# ─────────────────────────────────────────────

CSS = r"""
:root{
  color-scheme: light;
  --bg:#f4f3ef; --surface:#fcfcfb; --surface-2:#f1f0ec; --border:#e4e3df;
  --text:#0b0b0b; --text-2:#52514e; --muted:#8a8984; --accent:#2a78d6;
  --grid:#e4e3df;
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#eda100; --s5:#e87ba4; --s6:#008300; --s7:#6250d6;
  --other:#b5b4ae;
  --t1:#184f95; --t2:#2a78d6; --t3:#5598e7; --t4:#86b6ef; --t5:#c9c8c2;
}
@media (prefers-color-scheme: dark){
  :root:where(:not([data-theme="light"])){
    color-scheme: dark;
    --bg:#121211; --surface:#1a1a19; --surface-2:#232321; --border:#33332f;
    --text:#f0efec; --text-2:#c3c2b7; --muted:#8f8e86; --accent:#3987e5; --grid:#2c2c29;
    --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#c98500; --s5:#d55181; --s6:#008300; --s7:#9085e9;
    --other:#5d5c57;
    --t1:#86b6ef; --t2:#5598e7; --t3:#2a78d6; --t4:#1c5cab; --t5:#4a4a46;
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --bg:#121211; --surface:#1a1a19; --surface-2:#232321; --border:#33332f;
  --text:#f0efec; --text-2:#c3c2b7; --muted:#8f8e86; --accent:#3987e5; --grid:#2c2c29;
  --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#c98500; --s5:#d55181; --s6:#008300; --s7:#9085e9;
  --other:#5d5c57;
  --t1:#86b6ef; --t2:#5598e7; --t3:#2a78d6; --t4:#1c5cab; --t5:#4a4a46;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);
  display:flex;min-height:100vh;font-size:14px;line-height:1.45}
#side{width:240px;flex-shrink:0;background:var(--surface);border-right:1px solid var(--border);
  position:sticky;top:0;height:100vh;overflow-y:auto;padding:18px 0}
.logo{padding:0 18px 14px;border-bottom:1px solid var(--border)}
.logo b{display:block;font-size:15px}.logo span{color:var(--muted);font-size:12px}
.navh{padding:14px 18px 4px;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.nav{display:flex;align-items:center;gap:8px;width:calc(100% - 16px);margin:1px 8px;padding:8px 10px;
  border:0;border-radius:8px;background:none;color:var(--text);font:inherit;cursor:pointer;text-align:left}
.nav:hover{background:var(--surface-2)}.nav.on{background:var(--surface-2);font-weight:600}
.dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.themebtn{margin:16px 18px 0;padding:6px 10px;border:1px solid var(--border);border-radius:8px;
  background:var(--surface);color:var(--text-2);font:inherit;font-size:12px;cursor:pointer}
#main{flex:1;min-width:0;padding:24px 28px 60px}
.page{display:none}.page.on{display:block}
h1{font-size:22px;margin-bottom:2px}.sub{color:var(--text-2);margin-bottom:18px}
.grid{display:grid;gap:16px;margin-bottom:16px}
.g2{grid-template-columns:repeat(2,minmax(0,1fr))}.g3{grid-template-columns:repeat(3,minmax(0,1fr))}
.g4{grid-template-columns:repeat(4,minmax(0,1fr))}.g6{grid-template-columns:repeat(6,minmax(0,1fr))}
@media(max-width:1200px){.g4,.g6{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:860px){body{flex-direction:column}
  #side{width:100%;height:auto;position:sticky;top:0;z-index:20;display:flex;align-items:center;overflow-x:auto;
    padding:6px 4px;border-right:0;border-bottom:1px solid var(--border)}
  #side .logo,#side .navh,#side .sidelinks{display:none}
  #side .nav{width:auto;flex-shrink:0;margin:0 2px;padding:6px 10px;white-space:nowrap}
  #side .themebtn{margin:0 6px;flex-shrink:0}
  .g2,.g3,.g4,.g6{grid-template-columns:minmax(0,1fr)}#main{padding:16px}}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;min-width:0}
.card h3{font-size:13px;font-weight:600;margin-bottom:2px}
.card .note{font-size:12px;color:var(--muted);margin-bottom:10px}
.tile .lab{font-size:12px;color:var(--text-2)}.tile .val{font-size:26px;font-weight:650;margin-top:2px}
.tile .foot{font-size:12px;color:var(--muted)}
.cw{position:relative;height:280px}.cw.tall{height:360px}
.tw{overflow-x:auto;max-height:520px;overflow-y:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{position:sticky;top:0;background:var(--surface-2);color:var(--text-2);text-align:left;font-weight:600;
  padding:7px 9px;border-bottom:1px solid var(--border);cursor:pointer;white-space:nowrap}
td{padding:6px 9px;border-bottom:1px solid var(--border);vertical-align:top}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.pill{display:inline-block;padding:1px 7px;border-radius:99px;font-size:11px;background:var(--surface-2);
  color:var(--text-2);border:1px solid var(--border)}
.swatch{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px;font-size:12.5px;color:var(--text-2)}
.controls input[type=search]{padding:6px 9px;border:1px solid var(--border);border-radius:8px;background:var(--surface);
  color:var(--text);font:inherit;min-width:220px}
.net{position:relative;height:560px;border:1px solid var(--border);border-radius:10px;overflow:hidden;background:var(--surface)}
.tip{position:fixed;pointer-events:none;background:var(--surface);border:1px solid var(--border);border-radius:8px;
  padding:8px 10px;font-size:12px;max-width:320px;box-shadow:0 4px 18px rgba(0,0,0,.18);display:none;z-index:50}
.tip b{display:block;margin-bottom:2px}
.legend{display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;font-size:12px;color:var(--text-2)}
.warn{font-size:12px;color:var(--text-2);background:var(--surface-2);border:1px solid var(--border);
  border-radius:8px;padding:8px 10px;margin-bottom:14px}
ul.defs{margin:6px 0 0 18px;color:var(--text-2);font-size:13px}ul.defs li{margin-bottom:5px}
.sidelinks{margin:14px 18px 0;font-size:12px;line-height:1.9}.sidelinks a{display:block}
.finding h3{font-size:13.5px;margin-bottom:6px}.finding p{font-size:12.5px;color:var(--text-2)}
.lead p{font-size:14px;max-width:900px}
h2.sec{font-size:15px;margin:6px 0 10px;color:var(--text)}
ol.flist{margin:4px 0 0 20px;font-size:13px}ol.flist li{margin-bottom:6px}ol.flist li span{color:var(--text-2)}
.sfind dl{display:grid;grid-template-columns:96px 1fr;gap:4px 10px;font-size:12.5px;margin-top:6px}
.sfind dt{color:var(--muted);font-weight:600}.sfind dd{color:var(--text-2)}
table.mat td,table.mat th{text-align:center}table.mat td.diag{font-weight:600}
.exwrap{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:12px}
.detail{border:1px solid var(--border);border-radius:10px;padding:12px;font-size:12.5px;max-height:620px;overflow:auto;background:var(--surface)}
.detail h4{font-size:14px;margin-bottom:4px}.detail ul{margin:6px 0 0 16px}.detail li{margin-bottom:2px}
#net-ex{height:620px}
@media(max-width:860px){.exwrap{grid-template-columns:minmax(0,1fr)}#net-ex{height:460px}}
.muted{color:var(--muted)}
.btn{padding:5px 10px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--text-2);font:inherit;font-size:12px;cursor:pointer}
select{padding:4px 6px;border:1px solid var(--border);border-radius:6px;background:var(--surface);color:var(--text);font:inherit}
.pill.used{background:var(--t1);color:#fff;border-color:transparent}.pill.cmp{background:var(--surface-2)}
.cc p{font-size:13px;color:var(--text-2);margin:6px 0;max-width:980px}.cc h3{font-size:14px;margin-top:8px}
.cut{margin-bottom:10px;font-size:12.5px}.cut b{display:block}
.errbar{position:fixed;bottom:12px;right:12px;max-width:420px;background:#b3261e;color:#fff;padding:10px 12px;border-radius:8px;font-size:12.5px;z-index:99;display:none}
.finding .num{display:inline-block;width:22px;height:22px;border-radius:50%;background:var(--surface-2);
  border:1px solid var(--border);text-align:center;line-height:20px;font-size:11px;margin-right:6px;color:var(--text)}
"""

BODY = r"""
<nav id="side">
  <div class="logo"><b>Research Map · Group 10</b><span>DPCN 2026 · 2016–2026</span></div>
  <div class="navh">Start here</div>
  <button class="nav on" data-p="overview"><span class="dot" style="background:var(--muted)"></span>Overview</button>
  <button class="nav" data-p="findings"><span class="dot" style="background:var(--s5)"></span>Findings &amp; modelling</button>
  <div class="navh">Three institutes</div>
  <button class="nav" data-p="compare"><span class="dot" style="background:var(--s7)"></span>Institution comparison</button>
  %INSTNAV%
  <div class="navh">Networks</div>
  <button class="nav" data-p="explorer"><span class="dot" style="background:var(--t2)"></span>Network explorer</button>
  <button class="nav" data-p="authorship"><span class="dot" style="background:var(--t3)"></span>Network analysis</button>
  <button class="nav" data-p="citation"><span class="dot" style="background:var(--t1)"></span>Citation network</button>
  <button class="nav" data-p="india"><span class="dot" style="background:var(--s4)"></span>Indian connectivity</button>
  <div class="navh">About</div>
  <button class="nav" data-p="course"><span class="dot" style="background:var(--s6)"></span>Course connections</button>
  <button class="nav" data-p="method"><span class="dot" style="background:var(--other)"></span>Data &amp; methods</button>
  <button class="themebtn" id="themebtn">Toggle dark / light</button>
  <div class="sidelinks" id="sidelinks"></div>
</nav>
<main id="main">
<section class="page on" id="p-overview">
  <h1>Research output of three IIITs</h1>
  <div class="sub">IIIT Allahabad · ABV-IIITM Gwalior · IIIT Bangalore — journal and conference papers 2016–2026 (OpenAlex)</div>
  <div class="card lead" style="margin-bottom:16px">
    <h3>Research question</h3>
    <p>How do the research networks of IIIT Allahabad, ABV-IIITM Gwalior and IIIT Bangalore compare, and how — and through whom — are the three institutes connected to each other?</p>
    <p class="note" style="margin-top:6px">A node in the co-authorship network is an author affiliated with one of the institutes on at least one paper; an edge means two such authors co-wrote at least one paper (undirected, weighted by joint papers). A node in the citation network is a paper; an edge A → B means A lists B in its references (directed, unweighted). Edges do not measure friendship, funding or influence beyond these definitions.</p>
  </div>
  <div class="grid g4" id="ov-net"></div>
  <div class="card" style="margin-bottom:16px"><h3>Main structural findings</h3><div class="note">Full evidence, interpretation and caveats on the Findings &amp; modelling page</div><ol class="flist" id="ov-find"></ol></div>
  <div class="warn">2026 is a partial year (data collected during 2026); recent papers have had little time to be cited.</div>
  <div class="grid g3" id="ov-tiles"></div>
  <div class="grid g2">
    <div class="card"><h3>Publication trend</h3><div class="note">Papers per year; dotted segment = partial 2026</div><div class="cw"><canvas id="c-trend"></canvas></div></div>
    <div class="card"><h3>Median citations by publication year</h3><div class="note">Citation counts depend strongly on paper age</div><div class="cw"><canvas id="c-age"></canvas></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Journal quartile distribution</h3><div class="note">Scimago SJR quartile in the publication year, % of journal papers</div><div class="cw"><canvas id="c-q"></canvas></div></div>
    <div class="card"><h3>Conference rank (CORE)</h3><div class="note">ICORE2026 rank, % of conference papers</div><div class="cw"><canvas id="c-core"></canvas></div></div>
  </div>
  <div class="card" style="margin-bottom:16px"><h3>Research area breakdown</h3><div class="note">% of each institution's papers per OpenAlex field</div><div class="cw tall"><canvas id="c-fields"></canvas></div></div>
  <div class="card"><h3>Top 10 most-cited papers</h3><div class="note">OpenAlex citation count at collection date</div><div class="tw"><table id="t-cited"></table></div></div>
</section>
<section class="page" id="p-findings">
  <h1>Findings &amp; modelling</h1>
  <div class="sub">Every claim is tested against a baseline (null model, control variables or confidence interval). Observation → evidence → meaning → caveats.</div>
  <h2 class="sec">How the three institutes connect</h2>
  <div class="grid g2" id="sfind-cards"></div>
  <h2 class="sec">Output, impact and citation flow</h2>
  <div class="grid g3" id="find-cards"></div>
  <div class="card" style="margin-bottom:16px"><h3>Methods: what was run, why, and what it can and cannot show</h3><div class="tw"><table id="t-methods"></table></div></div>
  <div class="card" style="margin-bottom:16px"><h3>Limitations</h3><ul class="defs" id="limits"></ul></div>
  <div class="grid g2">
    <div class="card"><h3>Venue quality over time</h3><div class="note">Share of journal papers in Q1 venues, per year</div><div class="cw"><canvas id="c-q1year"></canvas></div></div>
    <div class="card"><h3>Citations received / given with other Indian institutes</h3><div class="note">Per year; above 1 = the institute is cited more than it cites</div><div class="cw"><canvas id="c-ratio"></canvas></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Normalised citation impact by collaboration type</h3><div class="note">Mean citation score normalised by year, field and paper type (1 = average); hover for 95% CI</div><div class="cw"><canvas id="c-ncs"></canvas></div></div>
    <div class="card"><h3>What predicts citations?</h3><div class="note">OLS on log(1 + citations) with year and field fixed effects; % change with 95% CI</div><div class="tw"><table id="t-reg"></table></div></div>
  </div>
  <div class="card"><h3>Network tests</h3><div class="note">Observed value vs the random-graph baseline</div><div class="tw"><table id="t-nettest"></table></div></div>
</section>
<section class="page" id="p-compare">
  <h1>Institution comparison</h1>
  <div class="sub">Each institute's own co-authorship subgraph, and every measurable tie between the three</div>
  <div class="card" style="margin-bottom:16px"><h3>Structure of each institute's co-authorship network</h3><div class="note">Authors are assigned to the institute where they have most papers. Path length and diameter on each subgraph's giant component; communities = Louvain (seed 42) on the subgraph.</div><div class="tw"><table id="t-inst"></table></div></div>
  <div class="grid g2">
    <div class="card"><h3>Co-author links within and between institutes</h3><div class="note">Observed links (configuration-model expectation in brackets). Off-diagonal = links between authors of two institutes.</div><div class="tw"><table class="mat" id="t-mix"></table></div></div>
    <div class="card"><h3>Mean shortest-path distance (steps)</h3><div class="note">Average co-authorship distance between authors of two institutes, giant component</div><div class="tw"><table class="mat" id="t-dist"></table></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Pairwise ties</h3><div class="tw"><table id="t-pairs"></table></div></div>
    <div class="card"><h3>Internal citations between institutes</h3><div class="note">Rows cite columns. Left number: all internal citations; right: after removing author self-citations</div><div class="tw"><table class="mat" id="t-citmat"></table></div></div>
  </div>
  <div class="card" style="margin-bottom:16px"><h3>Bridge authors</h3><div class="note">Authors with a co-author at another of the three institutes, or whom OpenAlex places at two of them. Ranked by betweenness in the full co-authorship network.</div><div class="tw"><table id="t-bridges"></table></div></div>
  <div class="grid g2">
    <div class="card"><h3>Bottlenecks: minimum node cuts</h3><div class="note">Smallest set of authors whose removal leaves no co-authorship path between two institutes</div><div id="cuts"></div></div>
    <div class="card"><h3>Shared Indian partners</h3><div class="note">Indian institutions that co-author with all three IIITs, ranked by the smallest of the three counts</div><div class="tw"><table id="t-common"></table></div></div>
  </div>
  <div class="card"><h3>Output and impact beyond counts</h3><div class="tw"><table id="t-cmp"></table></div></div>
</section>
<section class="page" id="p-explorer">
  <h1>Network explorer</h1>
  <div class="sub">Co-authorship network: the %EXPN% most connected authors of each institute plus every author with ties to another institute. Bridge authors are deliberately over-represented here; all mixing statistics use the full network.</div>
  <div class="card" style="margin-bottom:16px">
    <div class="controls" id="ex-ctl">
      <span id="ex-inst"></span>
      <label>Colour <select id="ex-col"><option value="i">institution</option><option value="c">Louvain community</option></select></label>
      <label><input type="checkbox" id="ex-br"> bridges and their co-authors only</label>
      <input type="search" id="ex-q" placeholder="Find an author">
      <span id="ex-n" class="muted"></span>
    </div>
    <div class="exwrap">
      <div class="net" id="net-ex"></div>
      <aside class="detail" id="ex-detail"><p class="muted">Click an author to see their position in the network.</p></aside>
    </div>
    <div class="legend" id="leg-ex"></div>
  </div>
</section>
<section class="page" id="p-course">
  <h1>Course connections</h1>
  <div class="sub">Topics from the network-science course that this project uses directly, or uses only as a reference for comparison</div>
  <div class="warn">Included after review: degree &amp; paths, log scales &amp; log-binning, Erdős–Rényi graphs, path lengths of closed chains and star networks. Not included because the data have no corresponding dynamics: Eulerian paths, SI/SIS and diffusion, 1-D/2-D stability, Lorenz, logistic map, Kuramoto.</div>
  <div class="card cc" style="margin-bottom:16px"><span class="pill used">used in the analysis</span>
    <h3>1 · Degree and paths</h3>
    <p>Degree k<sub>i</sub> = number of co-authors of author i; mean degree ⟨k⟩ = 2m / n. A path is a sequence of co-authorship links; the shortest-path distance d<sub>ij</sub> is its minimum length, the average path length ⟨d⟩ is the mean over all connected pairs and the diameter is the largest d<sub>ij</sub>.</p>
    <div class="grid g4" id="cc-deg"></div>
    <p class="note">In this project: paths decide whether two institutes are connected at all (minimum node cut), and how far apart they are (distance matrix). IIITA–IIITB authors are on average <b id="cc-d1"></b> steps apart, versus <b id="cc-d2"></b> inside IIITB.</p>
  </div>
  <div class="card cc" style="margin-bottom:16px"><span class="pill used">used in the analysis</span>
    <h3>2 · Log scales and log-binning</h3>
    <p>A heavy-tailed degree distribution looks like an L on linear axes and is noisy on log axes because high-degree bins hold 0 or 1 authors. Log-binning uses bins of width growing geometrically (b<sub>j+1</sub> = c·b<sub>j</sub>) and divides each count by the bin width and by n, giving a smooth density p(k).</p>
    <div class="controls"><label><input type="radio" name="lb" value="lin" checked> linear histogram</label><label><input type="radio" name="lb" value="log"> log–log, unit bins</label><label><input type="radio" name="lb" value="bin"> log–log, log-binned</label><label><input type="radio" name="lb" value="ccdf"> CCDF P(K ≥ k)</label></div>
    <div class="cw"><canvas id="c-lb"></canvas></div>
    <p class="note" id="cc-lb-note"></p>
  </div>
  <div class="card cc" style="margin-bottom:16px"><span class="pill used">used as null model</span>
    <h3>3 · Erdős–Rényi random graphs</h3>
    <p>G(n, p): each pair linked independently with p. Mean degree ⟨k⟩ = p(n−1); degrees are Poisson; clustering C = p ≈ ⟨k⟩/n; average path length ⟨d⟩ ≈ ln n / ln ⟨k⟩; a giant component appears when ⟨k⟩ &gt; 1, and its share S solves S = 1 − e<sup>−⟨k⟩S</sup>.</p>
    <div class="controls"><label>n <input type="range" id="er-n" min="100" max="20000" step="1"></label><span id="er-nv"></span><label>⟨k⟩ <input type="range" id="er-k" min="0.2" max="12" step="0.1"></label><span id="er-kv"></span><button class="btn" id="er-reset">use this network</button></div>
    <div class="tw"><table id="t-er"></table></div>
    <p class="note">Simulated rows are 5 ER graphs G(n, m) with the same n and m as the real network (part5b). <span id="er-ratio"></span></p>
  </div>
  <div class="card cc"><span class="pill cmp">comparison only</span>
    <h3>4 · Path lengths of closed chains and stars</h3>
    <p>Closed chain (ring) of n nodes: ⟨d⟩ = n² / (4(n−1)) ≈ n/4 for even n — grows linearly. Star: every leaf is 2 steps from every other leaf, ⟨d⟩ = 2(n−1)/n → 2. ER sits in between with ⟨d⟩ ∝ ln n. These bracket the observed value: the co-authorship network is far closer to the star (hub faculty) than to the chain.</p>
    <div class="controls"><label>n <input type="range" id="rs-n" min="10" max="20000" step="1"></label><span id="rs-nv"></span></div>
    <div class="cw"><canvas id="c-rs"></canvas></div>
    <p class="note">These are idealised graphs, not models of this data: no co-authorship network is a ring or a pure star. They only show how strongly topology controls path length.</p>
  </div>
</section>
%INSTPAGES%
<section class="page" id="p-citation">
  <h1>Citation network</h1>
  <div class="sub">Directed graph within the three institutes: nodes = papers, edge A → B = A cites B</div>
  <div class="grid g4" id="cit-tiles"></div>
  <div class="card" style="margin-bottom:16px"><h3>Internal citation graph</h3>
    <div class="note">The %CITEN% highest-PageRank papers that cite or are cited by another paper in this view (chosen from the top 660). Node size ∝ PageRank, colour = institution. Drag, scroll to zoom.</div>
    <div class="net" id="net-cit"></div><div class="legend" id="leg-cit"></div></div>
  <div class="grid g2">
    <div class="card"><h3>PageRank top 10</h3><div class="note">Most influential papers inside the cluster</div><div class="tw"><table id="t-pr"></table></div></div>
    <div class="card"><h3>In-degree distribution</h3><div class="note">Times a paper is cited by other papers of the three institutes (log scale)</div><div class="cw"><canvas id="c-indeg"></canvas></div></div>
  </div>
</section>
<section class="page" id="p-authorship">
  <h1>Network analysis</h1>
  <div class="sub">Co-authorship network of the three institutes — undirected, weighted by joint papers (metrics unweighted unless stated), not connected. The interactive graph is on the Network explorer page.</div>
  <div class="grid g4" id="auth-tiles"></div>
  <div class="card" style="margin-bottom:16px"><h3>Network properties</h3><div class="note">Path length and diameter are computed on the giant component (the graph is disconnected). Citation-network values are on the Citation network page.</div><div class="tw"><table id="t-props"></table></div></div>
  <div class="grid g2">
    <div class="card"><h3>Degree distribution (log-binned)</h3><div class="note">Density p(k) in geometrically growing bins, log–log axes; line = Poisson distribution of an ER graph with the same ⟨k⟩</div><div class="cw"><canvas id="c-degdist"></canvas></div></div>
    <div class="card"><h3>Robustness to author removal</h3><div class="note">Removing authors in order of betweenness vs at random (mean of 10 runs). Cross-institute reach = share of author pairs from different institutes still joined by a path.</div><div class="cw"><canvas id="c-robust"></canvas></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Observed network vs random baselines</h3><div class="tw"><table id="t-null"></table></div></div>
    <div class="card"><h3>Do the centralities agree?</h3><div class="note">Spearman rank correlation between centrality measures, giant component</div><div class="tw"><table id="t-cagree"></table></div><p class="note" id="eig-note" style="margin-top:8px"></p></div>
  </div>
  <div class="card" style="margin-bottom:16px"><h3>Top authors by centrality</h3>
    <div class="controls" id="cent-ctl"><label><input type="radio" name="cent" value="degree" checked> degree</label><label><input type="radio" name="cent" value="betweenness"> betweenness</label><label><input type="radio" name="cent" value="closeness"> closeness</label><label><input type="radio" name="cent" value="eigenvector"> eigenvector</label></div>
    <div class="note" id="cent-note"></div><div class="tw"><table id="t-cent"></table></div></div>
  <div class="grid g2">
    <div class="card"><h3>Degree centrality — most collaborative</h3><div class="tw"><table id="t-deg"></table></div></div>
    <div class="card"><h3>Betweenness centrality — bridges between groups</h3><div class="tw"><table id="t-bet"></table></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Largest communities</h3><div class="note" id="comm-note"></div><div class="tw"><table id="t-comm"></table></div></div>
    <div class="card"><h3>Hub authors</h3><div class="note">Authors linking the most other Indian institutes through co-authorship</div><div class="tw"><table id="t-hub"></table></div></div>
  </div>
</section>
<section class="page" id="p-india">
  <h1>Indian connectivity</h1>
  <div class="sub">Citation flow and co-authorship between our institutes and every other Indian institution (OpenAlex country code IN)</div>
  <div class="grid g3" id="flow-tiles"></div>
  <div class="card" style="margin-bottom:16px"><h3>Year-wise citation flow</h3>
    <div class="controls" id="flow-ctl"></div>
    <div class="note">In-flow = citations our papers receive from works of other Indian institutes (by citing year); out-flow = citations our papers give to them (by our paper's year)</div>
    <div class="cw"><canvas id="c-flow"></canvas></div></div>
  <div class="grid g2">
    <div class="card"><h3>Top 10 Indian institutes citing us</h3><div class="controls" id="cit-ctl"></div><div class="tw"><table id="t-citing"></table></div></div>
    <div class="card"><h3>Top 10 most-cited papers citing us</h3><div class="note">Indian-affiliated papers that cite the selected institute</div><div class="tw"><table id="t-citpap"></table></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Co-authorship partners</h3><div class="controls" id="par-ctl"></div><div class="note">Ranked by shared papers; cross-cluster = partner is not an IIIT</div><div class="tw"><table id="t-part"></table></div></div>
    <div class="card"><h3>Co-authorship by partner cluster</h3><div class="note">Shared papers with each type of Indian institution</div><div class="cw tall"><canvas id="c-cluster"></canvas></div></div>
  </div>
  <div class="card"><h3>Research-topic similarity (Jaccard)</h3><div class="note">Jaccard over OpenAlex subfields that hold ≥1% of each entity's 2016–2026 output; weighted = overlap of the full subfield distributions</div><div class="tw"><table id="t-jac"></table></div></div>
</section>
<section class="page" id="p-method">
  <h1>Data &amp; definitions</h1>
  <div class="sub">How every number on this dashboard is produced</div>
  <div class="card"><ul class="defs" id="defs"></ul></div>
</section>
</main>
<div class="tip" id="tip"></div>
<div class="errbar" id="errbar" role="alert"></div>
"""

INST_PAGE = r"""
<section class="page" id="p-%KEY%">
  <h1><span class="swatch" style="background:var(--%SV%)"></span>%NAME%</h1>
  <div class="sub">%FULL% · OpenAlex %OA% · ROR %ROR%</div>
  <div class="grid g6" id="tiles-%KEY%"></div>
  <div class="grid g2">
    <div class="card"><h3>Publication trend</h3><div class="note">Journal vs conference papers per year</div><div class="cw"><canvas id="c-trend-%KEY%"></canvas></div></div>
    <div class="card"><h3>h-index distribution of core faculty</h3><div class="note">h-index from 2016–2026 papers; bin 30 = 30+</div><div class="cw"><canvas id="c-h-%KEY%"></canvas></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Journal quartiles</h3><div class="note">Share of journal papers</div><div class="cw"><canvas id="c-q-%KEY%"></canvas></div></div>
    <div class="card"><h3>Conference ranks (CORE)</h3><div class="note">Share of conference papers</div><div class="cw"><canvas id="c-core-%KEY%"></canvas></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Top 5 journals</h3><div class="tw"><table id="t-j-%KEY%"></table></div></div>
    <div class="card"><h3>Top 5 conferences / proceedings</h3><div class="tw"><table id="t-cf-%KEY%"></table></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Research areas</h3><div class="note">Top 10 OpenAlex subfields by papers</div><div class="cw tall"><canvas id="c-sub-%KEY%"></canvas></div></div>
    <div class="card"><h3>Departments</h3><div class="note">Papers with ≥1 author from the department; dept. from affiliation strings (else inferred from research field)</div><div class="tw"><table id="t-dep-%KEY%"></table></div></div>
  </div>
  <div class="card" style="margin-bottom:16px"><h3>Faculty list &amp; performance</h3>
    <div class="controls"><input type="search" placeholder="Search name, department, journal" id="q-%KEY%">
      <label><input type="checkbox" id="core-%KEY%" checked> core faculty only</label><span id="n-%KEY%"></span></div>
    <div class="note">Click a column to sort. h-index uses 2016–2026 papers; lifetime h-index from the OpenAlex author profile. * = department inferred.</div>
    <div class="tw"><table id="t-fac-%KEY%"></table></div></div>
  <div class="card"><h3>Top 10 most-cited papers</h3><div class="tw"><table id="t-cited-%KEY%"></table></div></div>
</section>
"""

JS = r"""
const D = %DATA%;
const INST = D.meta.institutions, KEYS = D.meta.keys, YEARS = D.meta.years;
const KEY2INST = Object.fromEntries(Object.entries(KEYS).map(([a,b])=>[b,a]));
const SLOT = {}; INST.forEach((n,i)=>SLOT[n]="--s"+(i+1));
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const col = inst => css(SLOT[inst]||"--other");
const TIER = ["--t1","--t2","--t3","--t4","--t5"];
const esc = s => String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt = n => (n==null||n==="")?"–":(typeof n==="number"?n.toLocaleString():n);
const doiLink = d => d ? `<a href="${d.startsWith("http")?d:"https://doi.org/"+d}" target="_blank" rel="noopener">DOI ↗</a>` : "–";
const charts = {};
const SUP={"-":"⁻","0":"⁰","1":"¹","2":"²","3":"³","4":"⁴","5":"⁵","6":"⁶","7":"⁷","8":"⁸","9":"⁹"};
const LOGT={callback:v=>{ const l=Math.log10(v); if(Math.abs(l-Math.round(l))>1e-9) return ""; return v>=1?v.toLocaleString():"10"+String(Math.round(l)).split("").map(c=>SUP[c]).join(""); }};

function baseOpts(extra={}){
  const g = css("--grid"), t = css("--text-2");
  const o = {responsive:true, maintainAspectRatio:false, animation:false,
    interaction:{mode:"nearest", intersect:false},
    plugins:{legend:{labels:{color:t, boxWidth:12, boxHeight:12, usePointStyle:true}},
             tooltip:{backgroundColor:css("--surface"), titleColor:css("--text"), bodyColor:t,
                      borderColor:css("--border"), borderWidth:1}},
    scales:{x:{grid:{color:g, drawTicks:false}, border:{color:g}, ticks:{color:t}},
            y:{grid:{color:g, drawTicks:false}, border:{color:g}, ticks:{color:t}, beginAtZero:true}}};
  return merge(o, extra);
}
function merge(a,b){ for(const k in b){ if(b[k]&&typeof b[k]==="object"&&!Array.isArray(b[k])&&a[k]) merge(a[k],b[k]); else a[k]=b[k]; } return a; }
function chart(id, cfg){ if(charts[id]) charts[id].destroy(); const el=document.getElementById(id); if(!el) return; charts[id]=new Chart(el,cfg); }

function table(id, cols, rows, opts={}){
  const el = document.getElementById(id); if(!el) return;
  let sortI = opts.sort ?? -1, asc = false;
  function render(){
    let r = rows.slice();
    if(sortI>=0){ const k=cols[sortI].v; r.sort((a,b)=>{const x=k(a),y=k(b); return (x>y?1:x<y?-1:0)*(asc?1:-1);}); }
    if(opts.limit) r = r.slice(0, opts.limit);
    if(!r.length){ el.innerHTML = `<tbody><tr><td class="muted">${opts.empty||"No data for this selection."}</td></tr></tbody>`; return; }
    el.innerHTML ="<thead><tr>"+cols.map((c,i)=>`<th class="${c.num?"num":""}" data-i="${i}">${c.h}${i===sortI?(asc?" ▲":" ▼"):""}</th>`).join("")+
      "</tr></thead><tbody>"+r.map(x=>"<tr>"+cols.map(c=>`<td class="${c.num?"num":""}">${c.f?c.f(x):esc(c.v(x))}</td>`).join("")+"</tr>").join("")+"</tbody>";
    el.querySelectorAll("th").forEach(th=>th.onclick=()=>{const i=+th.dataset.i; if(i===sortI) asc=!asc; else {sortI=i; asc=false;} render();});
  }
  render();
}

function tile(lab,val,foot){ return `<div class="card tile"><div class="lab">${lab}</div><div class="val">${val}</div><div class="foot">${foot||""}</div></div>`; }

// ── Overview ───────────────────────────────────────────
const ST = D.structure||{};
const AB = {"IIIT Allahabad":"IIITA","ABV-IIITM Gwalior":"ABV","IIIT Bangalore":"IIITB"};
const pct = x => (x*100).toFixed(x<0.01?1:0)+"%";
function renderOverview(){
  const S = Object.fromEntries(D.summary.map(s=>[s.institution,s]));
  const co=ST.coauthorship||{}, mx=ST.mixing||{}, cs=ST.communities||{};
  const uniq=D.summary.find(s=>s.institution.startsWith("All"))||{};
  document.getElementById("ov-net").innerHTML=[
    tile("Papers (unique)",fmt(uniq.papers),`${fmt(mx.inter_papers)} papers link authors of two IIITs`),
    tile("Authors · co-author links",`${fmt(co.nodes)} · ${fmt(co.edges)}`,`giant component ${co.giant_share_pct}% · ${fmt(co.components)} components`),
    tile("Links between institutes",`${fmt(mx.inter_links_total)} <span class="muted" style="font-size:13px">(${mx.inter_share_pct}%)</span>`,`${fmt(Math.round(mx.inter_links_expected_total))} expected under random mixing with the same degrees`),
    tile("Single-institute communities",(cs.single_institute_communities_pct??"–")+"%",`of ${cs.communities_10plus} Louvain communities with ≥10 authors`)].join("");
  document.getElementById("ov-find").innerHTML=(ST.findings||[]).map(f=>`<li><b>${esc(f.title)}.</b> <span>${esc(f.observation)}</span></li>`).join("")||"<li class='muted'>Run part5b_network_structure.py.</li>";
  document.getElementById("ov-tiles").innerHTML = INST.map(i=>{
    const s=S[i]; return `<div class="card tile"><div class="lab"><span class="swatch" style="background:${col(i)}"></span>${i}</div>
      <div class="val">${fmt(s.papers)} papers</div>
      <div class="foot">${fmt(s.journal_papers)} journal · ${fmt(s.conference_papers)} conference · ${s.q1_journal_pct}% of journal papers in Q1</div>
      <div class="foot">${fmt(s.citations)} citations (median ${s.median_citations}) · institutional h-index ${s.h_index} · ${s.core_faculty} core faculty</div></div>`;}).join("");
  chart("c-trend",{type:"line",data:{labels:YEARS,datasets:INST.map(i=>({label:i,
      data:YEARS.map((y,k)=>D.trend[i].journal[k]+D.trend[i].conference[k]),
      borderColor:col(i),backgroundColor:col(i),borderWidth:2,pointRadius:3,pointHoverRadius:5,tension:0,
      segment:{borderDash:c=>YEARS[c.p1DataIndex]===D.meta.partial_year?[4,4]:undefined}}))},options:baseOpts()});
  chart("c-age",{type:"line",data:{labels:YEARS,datasets:INST.map(i=>({label:i,data:D.citation_age[i],
      borderColor:col(i),backgroundColor:col(i),borderWidth:2,pointRadius:3}))},options:baseOpts()});
  stackedShare("c-q", D.quartile, ["Q1","Q2","Q3","Q4","Unranked"]);
  stackedShare("c-core", D.core, ["A*","A","B","C","Unranked"]);
  chart("c-fields",{type:"bar",data:{labels:D.fields.labels,datasets:INST.map(i=>({label:i,data:D.fields.values[i],
      backgroundColor:col(i),borderRadius:4,borderSkipped:"start",categoryPercentage:.75,barPercentage:.9}))},
      options:baseOpts({scales:{y:{title:{display:true,text:"% of papers",color:css("--text-2")}}}})});
  citedTable("t-cited", D.most_cited, true);
}
function stackedShare(id, tab, cats, onlyInst){
  const insts = onlyInst?[onlyInst]:INST;
  const tot = i => cats.reduce((s,c)=>s+(tab[i][c]||0),0)||1;
  chart(id,{type:"bar",data:{labels:insts,datasets:cats.map((c,k)=>({label:c,
      data:insts.map(i=>+(100*(tab[i][c]||0)/tot(i)).toFixed(1)),
      counts:insts.map(i=>tab[i][c]||0),
      backgroundColor:css(TIER[k]),borderColor:css("--surface"),borderWidth:{left:0,right:2,top:0,bottom:0}}))},
    options:baseOpts({indexAxis:"y",scales:{x:{stacked:true,max:100,title:{display:true,text:"%",color:css("--text-2")}},y:{stacked:true}},
      plugins:{tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw}% (${c.dataset.counts[c.dataIndex]} papers)`}}}})});
}
function citedTable(id, rows, withInst){
  const cols=[{h:"#",v:r=>rows.indexOf(r)+1,num:true},{h:"Title",v:r=>r.title},
    ...(withInst?[{h:"Institution",v:r=>r.institution}]:[]),
    {h:"Venue",v:r=>r.journal_name||"–"},{h:"Year",v:r=>r.year,num:true},
    {h:"Citations",v:r=>r.citations,num:true,f:r=>fmt(r.citations)+(r.n_authors>50?' <span class="pill">'+r.n_authors+' authors</span>':"")},
    {h:"DOI",v:r=>r.doi,f:r=>doiLink(r.doi)}];
  table(id, cols, rows);
}

// ── Institution page ───────────────────────────────────
function renderInst(key){
  const inst = KEY2INST[key], s = D.summary.find(x=>x.institution===inst), c = col(inst);
  document.getElementById("tiles-"+key).innerHTML = [
    tile("Papers",fmt(s.papers),`${fmt(s.journal_papers)} J · ${fmt(s.conference_papers)} C`),
    tile("Q1 journal share",s.q1_journal_pct+"%",`${fmt(s.q1_papers)} Q1 papers · ${s.unranked_journal_pct}% unranked`),
    tile("CORE A*/A papers",fmt(s.core_astar_a),`${s.core_ranked_pct}% of conf. papers CORE-ranked`),
    tile("Citations",fmt(s.citations),`median ${s.median_citations} · ${s.zero_cited_pct}% uncited`),
    tile("Institutional h-index",s.h_index,"papers 2016–2026"),
    tile("Core faculty",fmt(s.core_faculty),`${fmt(s.affiliated_authors)} affiliated authors · median h ${s.median_faculty_h}`)].join("");
  chart("c-trend-"+key,{type:"bar",data:{labels:YEARS,datasets:[
      {label:"Journal",data:D.trend[inst].journal,backgroundColor:css("--t1"),borderColor:css("--surface"),borderWidth:{top:2},borderRadius:0},
      {label:"Conference",data:D.trend[inst].conference,backgroundColor:css("--t4"),borderRadius:{topLeft:4,topRight:4},borderSkipped:"start"}]},
    options:baseOpts({scales:{x:{stacked:true},y:{stacked:true}}})});
  const hh = D.hhist[inst];
  chart("c-h-"+key,{type:"bar",data:{labels:hh.map((_,i)=>i===hh.length-1?i+"+":i),datasets:[{label:"Core faculty",data:hh,
      backgroundColor:c,borderRadius:3,categoryPercentage:.95,barPercentage:.92}]},
    options:baseOpts({plugins:{legend:{display:false}},scales:{x:{title:{display:true,text:"h-index",color:css("--text-2")}}}})});
  stackedShare("c-q-"+key, D.quartile, ["Q1","Q2","Q3","Q4","Unranked"], inst);
  stackedShare("c-core-"+key, D.core, ["A*","A","B","C","Unranked"], inst);
  const vcols=[{h:"Venue",v:r=>r.journal_name},{h:"Papers",v:r=>r.papers,num:true},{h:"Citations",v:r=>r.citations,num:true,f:r=>fmt(r.citations)},{h:"Rank",v:r=>r.quartile||"–"}];
  table("t-j-"+key, vcols, D.top_journals[inst]);
  table("t-cf-"+key, vcols, D.top_conferences[inst]);
  const sf = D.subfields[inst];
  chart("c-sub-"+key,{type:"bar",data:{labels:sf.map(x=>x.name),datasets:[{label:"Papers",data:sf.map(x=>x.papers),backgroundColor:c,borderRadius:4,borderSkipped:"start"}]},
    options:baseOpts({indexAxis:"y",plugins:{legend:{display:false}}})});
  table("t-dep-"+key,[{h:"Department",v:r=>r.department},{h:"Papers",v:r=>r.papers,num:true},{h:"Citations",v:r=>r.citations,num:true,f:r=>fmt(r.citations)},
    {h:"Core faculty",v:r=>r.core_faculty,num:true},{h:"Median h",v:r=>r.median_h??"–",num:true}], (D.departments||{})[inst]||[], {sort:1});
  const F = D.faculty[inst];
  const fcols=[{h:"Name",v:r=>r[0]},{h:"Department",v:r=>r[1],f:r=>esc(r[1])+(r[2]?" *":"")},
    {h:"Papers",v:r=>r[3],num:true},{h:"Journal",v:r=>r[4],num:true},{h:"Conf.",v:r=>r[5],num:true},{h:"Q1",v:r=>r[6],num:true},
    {h:"Citations",v:r=>r[7],num:true,f:r=>fmt(r[7])},{h:"h-index",v:r=>r[8],num:true},{h:"Lifetime h",v:r=>r[9]??-1,num:true,f:r=>r[9]??"–"},
    {h:"Top journal / venue",v:r=>r[10]},{h:"Active",v:r=>r[11],f:r=>r[11]+"–"+r[12]}];
  const q=document.getElementById("q-"+key), cb=document.getElementById("core-"+key);
  const upd=()=>{ const s=q.value.toLowerCase(); const rows=F.filter(r=>(!cb.checked||r[13])&&(!s||(r[0]+" "+r[1]+" "+r[10]).toLowerCase().includes(s)));
    document.getElementById("n-"+key).textContent=rows.length+" authors"; table("t-fac-"+key,fcols,rows,{sort:7}); };
  q.oninput=upd; cb.onchange=upd; upd();
  citedTable("t-cited-"+key, D.most_cited_inst[inst], false);
}

// ── Force graph helper ─────────────────────────────────
const tip = document.getElementById("tip");
function showTip(e, html){ tip.innerHTML=html; tip.style.display="block"; tip.style.left=(e.clientX+14)+"px"; tip.style.top=(e.clientY+10)+"px"; }
function hideTip(){ tip.style.display="none"; }
function forceGraph(elId, nodes, links, o){
  const el=document.getElementById(elId); el.innerHTML="";
  if(!nodes.length){ el.innerHTML="<p style='padding:16px;color:var(--muted)'>No network data.</p>"; return; }
  const W=el.clientWidth, H=el.clientHeight;
  const svg=d3.select(el).append("svg").attr("width",W).attr("height",H).attr("role","img").attr("aria-label",o.label);
  const g=svg.append("g");
  const zoom=d3.zoom().scaleExtent([.2,8]).on("zoom",e=>g.attr("transform",e.transform)); svg.call(zoom);
  if(o.directed){ svg.append("defs").append("marker").attr("id",elId+"-arr").attr("viewBox","0 -4 8 8").attr("refX",8).attr("markerWidth",5).attr("markerHeight",5).attr("orient","auto")
      .append("path").attr("d","M0,-4L8,0L0,4").attr("fill",css("--muted")); }
  const sim=d3.forceSimulation(nodes).force("link",d3.forceLink(links).id(d=>d.id).distance(o.dist||40).strength(.25))
    .force("charge",d3.forceManyBody().strength(-38)).force("center",d3.forceCenter(W/2,H/2))
    .force("x",d3.forceX(W/2).strength(.04)).force("y",d3.forceY(H/2).strength(.05))
    .force("col",d3.forceCollide(d=>o.r(d)+1.5));
  const link=g.append("g").selectAll("line").data(links).join("line").attr("stroke",d=>(o.lc&&o.lc(d))||css("--muted")).attr("stroke-opacity",d=>(o.lc&&o.lc(d))?.9:.35)
    .attr("stroke-width",d=>o.lw?o.lw(d):1).attr("marker-end",o.directed?`url(#${elId}-arr)`:null);
  const node=g.append("g").selectAll("circle").data(nodes).join("circle").attr("r",o.r).attr("fill",o.fill)
    .attr("stroke",o.stroke||css("--surface")).attr("stroke-width",o.sw||2).style("cursor","pointer")
    .on("mousemove",(e,d)=>showTip(e,o.tip(d))).on("mouseleave",hideTip)
    .call(d3.drag().on("start",(e,d)=>{if(!e.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y;})
      .on("drag",(e,d)=>{d.fx=e.x;d.fy=e.y;}).on("end",(e,d)=>{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}));
  if(o.click) node.on("click",(e,d)=>o.click(d));
  const paint=()=>{
    link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>{ if(!o.directed) return d.target.x; const dx=d.target.x-d.source.x, dy=d.target.y-d.source.y, L=Math.hypot(dx,dy)||1; return d.target.x-dx/L*(o.r(d.target)+2);})
        .attr("y2",d=>{ if(!o.directed) return d.target.y; const dx=d.target.x-d.source.x, dy=d.target.y-d.source.y, L=Math.hypot(dx,dy)||1; return d.target.y-dy/L*(o.r(d.target)+2);});
    node.attr("cx",d=>d.x).attr("cy",d=>d.y);
  };
  // settle the layout before drawing: a half-finished layout misrepresents structure
  sim.stop(); for(let i=0;i<Math.ceil(Math.log(sim.alphaMin())/Math.log(1-sim.alphaDecay()));i++) sim.tick();
  paint(); sim.on("tick",paint);
  const xs=nodes.map(d=>d.x), ys=nodes.map(d=>d.y), pad=20;
  const x0=Math.min(...xs)-pad, x1=Math.max(...xs)+pad, y0=Math.min(...ys)-pad, y1=Math.max(...ys)+pad;
  const k=Math.min(1.5, W/(x1-x0), H/(y1-y0));
  svg.call(zoom.transform, d3.zoomIdentity.translate(W/2-k*(x0+x1)/2, H/2-k*(y0+y1)/2).scale(k));
}

// ── Citation network ───────────────────────────────────
function renderCitation(){
  const s=D.cite.summary||{};
  document.getElementById("cit-tiles").innerHTML=[
    tile("Papers (nodes)",fmt(s.nodes),"journal + conference, 3 institutes"),
    tile("Internal citation edges",fmt(s.internal_edges),`${fmt(s.cross_institution_internal_edges)} between different institutes`),
    tile("Papers cited internally",fmt(s.papers_cited_internally),`max in-degree ${fmt(s.max_in_degree)}`),
    tile("Largest weak component",fmt(s.largest_weak_component),`directed, unweighted · ${fmt((ST.citation||{}).weak_components)} weak components · reciprocity ${(ST.citation||{}).reciprocity}`)].join("");
  const G=D.cite.graph||{nodes:[],links:[]};
  const maxPR=Math.max(...G.nodes.map(n=>n.pr),1e-9);
  const r=d3.scaleSqrt().domain([0,maxPR]).range([3,16]);
  forceGraph("net-cit",G.nodes.map(n=>({...n})),G.links.map(l=>({...l})),{directed:true,label:"Citation network",dist:45,
    r:d=>r(d.pr), fill:d=>col(d.i[0]), sw:d=>d.i.length>1?3:1.5, stroke:d=>d.i.length>1?col(d.i[1]):css("--surface"),
    tip:d=>`<b>${esc(d.t)}</b>${esc(d.i.join(" & "))} · ${d.y}<br>PageRank ${d.pr.toFixed(5)} · in-degree ${d.d} · ${fmt(d.c)} citations`,
    click:d=>{ if(d.doi) window.open("https://doi.org/"+d.doi,"_blank"); }});
  document.getElementById("leg-cit").innerHTML=INST.map(i=>`<span><span class="swatch" style="background:${col(i)}"></span>${i}</span>`).join("")+
    "<span>ring in a second colour = co-published by two of the institutes · click a node to open its DOI</span>";
  table("t-pr",[{h:"#",v:r=>D.cite.top10.indexOf(r)+1,num:true},{h:"Title",v:r=>r.title},{h:"Institution",v:r=>r.institutions.join(" & ")},
    {h:"Year",v:r=>r.year,num:true},{h:"In-degree",v:r=>r.in_degree,num:true},{h:"PageRank",v:r=>r.pagerank,num:true,f:r=>r.pagerank.toFixed(5)},
    {h:"DOI",v:r=>r.doi,f:r=>doiLink(r.doi)}],D.cite.top10);
  const dist=Object.entries(s.in_degree_distribution||{}).map(([k,v])=>({x:+k,y:v})).filter(p=>p.x>0);
  chart("c-indeg",{type:"scatter",data:{datasets:[{label:"Papers",data:dist,backgroundColor:css("--t2"),pointRadius:5}]},
    options:baseOpts({plugins:{legend:{display:false}},scales:{x:{type:"logarithmic",ticks:LOGT,title:{display:true,text:"in-degree",color:css("--text-2")}},
      y:{type:"logarithmic",beginAtZero:false,ticks:LOGT,title:{display:true,text:"papers",color:css("--text-2")}}}})});
}

// ── Authorship network ─────────────────────────────────
function renderAuthorship(){
  const s=D.auth.summary||{};
  document.getElementById("auth-tiles").innerHTML=[
    tile("Authors (nodes)",fmt(s.nodes),`${fmt(s.isolated_authors)} without co-authors at the 3 institutes`),
    tile("Co-author links",fmt(s.edges),`${fmt((ST.mixing||{}).inter_links_total)} join authors of different institutes`),
    tile("Louvain communities",fmt(s.communities),`modularity ${s.modularity}`),
    tile("Giant component",fmt(s.giant_component),`avg clustering ${s.avg_clustering}`)].join("");
  const co=ST.coauthorship||{}, ci=ST.citation||{}, er=ST.er_baseline||{}, eg=ST.er_baseline_giant||{}, an=(D.insights||{}).authorship_network||{};
  table("t-props",[{h:"Property",v:r=>r[0]},{h:"Co-authorship",v:r=>r[1],num:true},{h:"Reading",v:r=>r[2]}],[
    ["Type","undirected · weighted","edge weight = number of joint papers"],
    ["Nodes / edges",`${fmt(co.nodes)} / ${fmt(co.edges)}`,"authors / distinct co-author pairs"],
    ["Density",co.density,"0.1% of all possible pairs are linked"],
    ["Connected components",fmt(co.components),`${fmt(co.isolated_nodes)} isolated authors (no co-author at the 3 institutes); second-largest component ${co.second_component}`],
    ["Giant component",`${fmt(co.giant_nodes)} (${co.giant_share_pct}%)`,"contains authors of all three institutes"],
    ["Degree: mean / median / max",`${co.degree?.mean} / ${co.degree?.median} / ${co.degree?.max}`,`top 5% of authors hold ${co.degree?.share_of_degree_top5pct}% of degree`],
    ["Average clustering / transitivity",`${co.avg_clustering} / ${co.transitivity}`,"local clustering is high because each paper creates a clique; transitivity is lower because hubs have many unconnected co-authors"],
    ["Average path length (giant)",co.giant_avg_path_length,"exact, all pairs"],
    ["Diameter (giant)",co.giant_diameter,"longest shortest path"],
    ["Degree assortativity",co.degree_assortativity,"negative: hubs (faculty) link to low-degree authors (students)"],
    ["Institute assortativity",an.institution_assortativity,"1 = links only inside institutes"]]);
  const dd=(ST.degree_distribution||{}).coauthorship;
  if(dd){ const k=co.degree.mean; const fact=n=>{let f=0;for(let i=2;i<=n;i++)f+=Math.log(i);return f;};
    const pois=[]; for(let x=1;x<=30;x++) pois.push({x,y:Math.exp(-k+x*Math.log(k)-fact(x))});
    chart("c-degdist",{type:"scatter",data:{datasets:[
      {label:"co-authorship p(k), log-binned",data:dd.bin_centers.map((x,i)=>({x,y:dd.pdf[i],n:dd.counts[i]})),backgroundColor:css("--t1"),pointRadius:5},
      {label:`ER / Poisson, ⟨k⟩ = ${k}`,data:pois.filter(p=>p.y>1e-6),showLine:true,borderColor:css("--muted"),pointRadius:0,borderWidth:1.5}]},
      options:baseOpts({scales:{x:{type:"logarithmic",ticks:LOGT,title:{display:true,text:"degree k",color:css("--text-2")}},
        y:{type:"logarithmic",beginAtZero:false,min:1e-6,ticks:LOGT,title:{display:true,text:"p(k)",color:css("--text-2")}}},
        plugins:{tooltip:{callbacks:{label:c=>c.raw.n!=null?`k ≈ ${c.raw.x.toFixed(1)}: p = ${c.raw.y.toExponential(2)} (${c.raw.n} authors)`:`Poisson p(${c.raw.x}) = ${c.raw.y.toExponential(2)}`}}}})}); }
  const rb=ST.robustness;
  if(rb){ const xs=rb.fraction_removed.map(f=>+(f*100).toFixed(1));
    const ds=(lab,arr,c,dash)=>({label:lab,data:xs.map((x,i)=>({x,y:arr[i]})),borderColor:c,backgroundColor:c,borderDash:dash,borderWidth:2,pointRadius:3,showLine:true});
    chart("c-robust",{type:"scatter",data:{datasets:[
      ds("cross-institute reach · by betweenness",rb.targeted.cross_reach,css("--t1")),
      ds("cross-institute reach · random",rb.random.cross_reach,css("--t3"),[5,4]),
      ds("giant component · by betweenness",rb.targeted.giant,css("--s2")),
      ds("giant component · random",rb.random.giant,css("--s4"),[5,4])]},
      options:baseOpts({scales:{x:{type:"linear",title:{display:true,text:"% of authors removed",color:css("--text-2")}},
        y:{max:1,title:{display:true,text:"fraction remaining",color:css("--text-2")}}},
        plugins:{tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${(c.raw.y*100).toFixed(1)}% after removing ${c.raw.x}%`}}}})}); }
  table("t-null",[{h:"Metric",v:r=>r[0]},{h:"Observed",v:r=>r[1],num:true},{h:"ER G(n,m)",v:r=>r[2],num:true},{h:"Degree-preserving",v:r=>r[3],num:true}],[
    ["Mean degree ⟨k⟩",co.degree?.mean,er.mean_degree,"same by construction"],
    ["Average clustering",co.avg_clustering,er.clustering_sim,"–"],
    ["Giant component share",co.giant_share_pct+"%",er.giant_share_sim_pct+"%","–"],
    ["Path length (giant)",co.giant_avg_path_length,`${eg.path_length_sim} (theory ln n/ln⟨k⟩ = ${eg.path_length_theory_lnN_lnk})`,"–"],
    ["Max degree",co.degree?.max,er.max_degree_sim,"same by construction"],
    ["Louvain modularity",an.modularity,"–",`${an.modularity_null} ± ${an.modularity_null_sd}`],
    ["Links between institutes",fmt((ST.mixing||{}).inter_links_total),"–",fmt(Math.round((ST.mixing||{}).inter_links_expected_total))]]);
  const ce=ST.centrality||{};
  table("t-cagree",[{h:"Pair",v:r=>r[0]},{h:"Spearman ρ",v:r=>r[1],num:true}],Object.entries(ce.spearman||{}).map(([k,v])=>[k.replace("~"," ~ "),v]));
  const em=ce.eigenvector_mass_pct||{};
  document.getElementById("eig-note").innerHTML=`Eigenvector centrality is <b>not</b> used to compare institutes: ${INST.map(i=>AB[i]+" "+em[i]+"%").join(", ")} of its squared mass sits in one institute — it localises on IIITA's densest cluster, a known failure on modular networks. Degree and betweenness are the informative measures here.`;
  const cn={degree:"normalised degree — share of all other authors who are co-authors",betweenness:"share of shortest paths passing through the author (exact, full network)",closeness:"inverse mean distance to everyone in the giant component",eigenvector:"localised on one cluster (see note above)"};
  const rc=m=>{ document.getElementById("cent-note").textContent=cn[m];
    table("t-cent",[{h:"#",v:r=>ce.top10[m].indexOf(r)+1,num:true},{h:"Author",v:r=>r.name},{h:"Institution",v:r=>r.institution,f:r=>`<span class="swatch" style="background:${col(r.institution)}"></span>${esc(r.institution)}`},
      {h:m,v:r=>r.value,num:true,f:r=>r.value.toFixed(4)}],(ce.top10||{})[m]||[]); };
  document.getElementById("cent-ctl").onchange=e=>rc(e.target.value); rc("degree");
  const cs=ST.communities||{};
  document.getElementById("comm-note").textContent=cs.seeds?`Stable across ${cs.seeds} random seeds: modularity ${cs.modularity_mean} ± ${cs.modularity_sd}, mean pairwise NMI ${cs.pairwise_nmi_mean} (min ${cs.pairwise_nmi_min}). ${cs.single_institute_communities_pct}% of communities with ≥10 authors are ≥90% one institute.`:"";
  table("t-deg",[{h:"Author",v:r=>r.name},{h:"Institution",v:r=>r.institution},{h:"Department",v:r=>r.department},
    {h:"Co-authors",v:r=>r.degree,num:true},{h:"Degree centr.",v:r=>r.degree_centrality,num:true,f:r=>r.degree_centrality.toFixed(4)}],D.auth.top_degree||[]);
  table("t-bet",[{h:"Author",v:r=>r.name},{h:"Institution",v:r=>r.institution},{h:"Department",v:r=>r.department},
    {h:"Betweenness",v:r=>r.betweenness_centrality,num:true,f:r=>r.betweenness_centrality.toFixed(4)}],D.auth.top_between||[]);
  table("t-comm",[{h:"Community",v:r=>"C"+r.id},{h:"Authors",v:r=>r.size,num:true},
    {h:"Institutions",v:r=>Object.entries(r.institutions).map(([k,v])=>k+" "+v).join(", ")},
    {h:"Main department",v:r=>r.dominant_department},{h:"Lead authors",v:r=>r.top_authors.join(", ")}],D.auth.communities||[]);
  table("t-hub",[{h:"Author",v:r=>r.name},{h:"Institution",v:r=>r.institution},
    {h:"Indian partner institutes",v:r=>r.external_indian_partner_institutes,num:true},
    {h:"Betweenness",v:r=>r.betweenness_centrality,num:true,f:r=>r.betweenness_centrality.toFixed(4)}],D.auth.hubs||[]);
}

// ── Indian connectivity ────────────────────────────────
function selector(id, cb){
  const el=document.getElementById(id);
  el.innerHTML=INST.map((i,k)=>`<label><input type="radio" name="${id}" value="${i}" ${k===0?"checked":""}> ${i}</label>`).join(" ");
  el.onchange=()=>cb(el.querySelector("input:checked").value); cb(INST[0]);
}
function renderIndia(){
  document.getElementById("flow-tiles").innerHTML=INST.map(i=>{const f=D.flow[i]||{};
    return `<div class="card tile"><div class="lab"><span class="swatch" style="background:${col(i)}"></span>${i}</div>
      <div class="val">${f.impact_ratio??"–"} <span style="font-size:13px;font-weight:400;color:var(--text-2)">in / out ratio</span></div>
      <div class="foot">${fmt(f.in_citations)} citations received from ${fmt(f.in_citing_works)} Indian papers · ${fmt(f.out_citations)} given to ${fmt(f.out_cited_works)} Indian papers</div></div>`;}).join("");
  selector("flow-ctl", inst=>{ const by=D.flow[inst].by_year;
    chart("c-flow",{type:"line",data:{labels:YEARS,datasets:[
      {label:"In-flow (citations received)",data:YEARS.map(y=>by[y].in),borderColor:col(inst),backgroundColor:col(inst),borderWidth:2,pointRadius:3},
      {label:"Out-flow (citations given)",data:YEARS.map(y=>by[y].out),borderColor:css("--muted"),backgroundColor:css("--muted"),borderWidth:2,pointRadius:3,borderDash:[5,4]}]},
      options:baseOpts()}); });
  selector("cit-ctl", inst=>{ const f=D.flow[inst];
    table("t-citing",[{h:"#",v:r=>f.top_citing_institutes.indexOf(r)+1,num:true},{h:"Institute",v:r=>r.name,f:r=>esc(r.name)+(r.intra_group?' <span class="pill">group</span>':"")},
      {h:"Cluster",v:r=>r.cluster},{h:"Citations",v:r=>r.count,num:true,f:r=>fmt(r.count)}],f.top_citing_institutes);
    table("t-citpap",[{h:"Title",v:r=>r.title},{h:"Institutes",v:r=>r.institutes.join("; ")},{h:"Year",v:r=>r.year,num:true},
      {h:"Citations",v:r=>r.citations,num:true,f:r=>fmt(r.citations)},{h:"DOI",v:r=>r.doi,f:r=>doiLink(r.doi)}],f.top_citing_papers);
    document.querySelectorAll('#par-ctl input').forEach(x=>{ if(x.value===inst) x.checked=true; }); });
  selector("par-ctl", inst=>{
    table("t-part",[{h:"Partner",v:r=>r.partner_inst,f:r=>esc(r.partner_inst)+(r.intra_group?' <span class="pill">group</span>':"")},
      {h:"Cluster",v:r=>r.partner_cluster,f:r=>esc(r.partner_cluster)+(r.cross_cluster?' <span class="pill">cross-cluster</span>':"")},
      {h:"Shared papers",v:r=>r.shared_papers,num:true},{h:"Their citations",v:r=>r.total_citations,num:true,f:r=>fmt(r.total_citations)},
      {h:"Cites received",v:r=>r.citations_received_from_partner,num:true},{h:"Cites given",v:r=>r.citations_given_to_partner,num:true}],
      (D.partners||{})[inst]||[],{sort:2}); });
  if(D.cluster_links){ const cl=D.cluster_links;
    chart("c-cluster",{type:"bar",data:{labels:cl.clusters,datasets:INST.map(i=>({label:i,data:cl.values[i],backgroundColor:col(i),borderRadius:4,borderSkipped:"start"}))},
      options:baseOpts({indexAxis:"y"})}); }
  table("t-jac",[{h:"Entity A",v:r=>r.entity_a},{h:"Entity B",v:r=>r.entity_b},
    {h:"Type",v:r=>r.comparison_type,f:r=>r.comparison_type==="intra_group"?"within group":"Indian partner ("+esc(r.partner_cluster)+")"},
    {h:"Shared papers",v:r=>r.shared_papers??-1,num:true,f:r=>r.shared_papers??"–"},
    {h:"Jaccard",v:r=>r.jaccard_similarity,num:true,f:r=>r.jaccard_similarity.toFixed(3)},
    {h:"Weighted",v:r=>r.weighted_jaccard,num:true,f:r=>r.weighted_jaccard.toFixed(3)},
    {h:"Top shared subfields",v:r=>r.top_shared_subfields}],D.jaccard,{sort:4});
}

// ── Key findings ───────────────────────────────────────
function renderFindings(){
  const I=D.insights||{}; if(!I.findings){ document.getElementById("find-cards").innerHTML="<p>Run part5_insights.py.</p>"; return; }
  document.getElementById("sfind-cards").innerHTML=(ST.findings||[]).map((f,k)=>
    `<div class="card finding sfind"><h3><span class="num">${k+1}</span>${esc(f.title)}</h3><dl>
      <dt>Observation</dt><dd>${esc(f.observation)}</dd><dt>Evidence</dt><dd>${esc(f.evidence)}</dd>
      <dt>Meaning</dt><dd>${esc(f.meaning)}</dd><dt>Caveats</dt><dd>${esc(f.caveat)}</dd></dl></div>`).join("")||"<p class='muted'>Run part5b_network_structure.py.</p>";
  document.getElementById("find-cards").innerHTML=I.findings.map((f,k)=>
    `<div class="card finding"><h3><span class="num">${k+1}</span>${esc(f.title)}</h3><p>${esc(f.text)}</p></div>`).join("");
  table("t-methods",[{h:"Method",v:r=>r[0],f:r=>`<b>${esc(r[0])}</b>`},{h:"Status",v:r=>r[1],f:r=>`<span class="pill${r[1]==="implemented"?" used":""}">${r[1]}</span>`},
    {h:"Why it fits",v:r=>r[2]},{h:"Result",v:r=>r[3]},{h:"Cannot conclude",v:r=>r[4]}],METHODS());
  document.getElementById("limits").innerHTML=LIMITS.map(x=>"<li>"+x+"</li>").join("");
  const yrs=YEARS.filter(y=>y<=2025);
  chart("c-q1year",{type:"line",data:{labels:yrs,datasets:INST.map(i=>({label:i,data:yrs.map(y=>I.growth_quality[i].q1_by_year[y]??null),
    borderColor:col(i),backgroundColor:col(i),borderWidth:2,pointRadius:3}))},
    options:baseOpts({scales:{y:{max:80,title:{display:true,text:"% Q1",color:css("--text-2")}}}})});
  const ry=YEARS.filter(y=>y>2016&&y<=2025);
  chart("c-ratio",{type:"line",data:{labels:ry,datasets:INST.map(i=>({label:i,data:ry.map(y=>I.connectivity.ratio_by_year[i][y]??null),
    borderColor:col(i),backgroundColor:col(i),borderWidth:2,pointRadius:3}))},
    options:baseOpts({scales:{y:{beginAtZero:false,title:{display:true,text:"received / given",color:css("--text-2")}}}})});
  const cp=I.collaboration_premium, groups=["Single institute","Indian partner","International"];
  chart("c-ncs",{type:"bar",data:{labels:groups,datasets:[{label:"Mean normalised citation score",data:groups.map(g=>cp[g].mean_ncs),
      backgroundColor:[css("--t4"),css("--t3"),css("--t1")],borderRadius:4,borderSkipped:"start"}]},
    options:baseOpts({indexAxis:"y",plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>{const g=cp[groups[c.dataIndex]];
      return `${g.mean_ncs} (95% CI ${g.mean_ci[0]}–${g.mean_ci[1]}), n = ${g.papers}`;}}}}})});
  table("t-reg",[{h:"Factor",v:r=>r.term},{h:"Effect",v:r=>r.effect_pct,num:true,f:r=>(r.effect_pct>0?"+":"")+r.effect_pct+"%"},
    {h:"95% CI",v:r=>r.ci[0],num:true,f:r=>r.ci[0]+"% to "+r.ci[1]+"%"},{h:"p",v:r=>r.p,num:true,f:r=>r.p<0.001?"<0.001":r.p.toFixed(3)}],
    I.citation_regression.terms);
  renderNetTests();
}
function cmpTable(){
  const I=D.insights||{}; if(!I.growth_quality) return;
  const S=Object.fromEntries(D.summary.map(s=>[s.institution,s]));
  table("t-cmp",[{h:"Institution",v:r=>r},
    {h:"Growth / yr",v:r=>I.growth_quality[r].annual_growth_pct,num:true,f:r=>{const g=I.growth_quality[r]; return `${g.annual_growth_pct}% <span class="pill">${g.growth_ci[0]}–${g.growth_ci[1]}</span>`;}},
    {h:"Q1 share 16–19 → 22–25",v:r=>I.growth_quality[r].q1_share_2022_25,f:r=>{const g=I.growth_quality[r]; return `${g.q1_share_2016_19}% → ${g.q1_share_2022_25}% (${g.q1_shift_p<0.001?"p<0.001":"p="+g.q1_shift_p.toFixed(3)})`;}},
    {h:"Normalised impact",v:r=>I.normalised_impact[r].mncs,num:true,f:r=>{const n=I.normalised_impact[r]; return `${n.mncs} <span class="pill">${n.mncs_ci[0]}–${n.mncs_ci[1]}</span>`;}},
    {h:"Top-10% papers",v:r=>I.normalised_impact[r].pp_top10,num:true,f:r=>I.normalised_impact[r].pp_top10+"%"},
    {h:"Citation Gini",v:r=>I.concentration[r].gini_citations,num:true},
    {h:"Top 10% papers' citation share",v:r=>I.concentration[r].top10pct_paper_citation_share,num:true,f:r=>I.concentration[r].top10pct_paper_citation_share+"%"},
    {h:"In/out citation ratio",v:r=>(D.flow[r]||{}).impact_ratio,num:true},
    {h:"Median citations",v:r=>S[r].median_citations,num:true}], INST);
}
function renderNetTests(){
  const I=D.insights||{}, cn=I.citation_network, an=I.authorship_network;
  table("t-nettest",[{h:"Test",v:r=>r[0]},{h:"Observed",v:r=>r[1],num:true},{h:"Baseline",v:r=>r[2],num:true},{h:"Reading",v:r=>r[3]}],[
    ["Internal citations staying inside the citing institute",cn.same_institution_pct+"%",`${cn.same_institution_null_pct}% ± ${cn.same_institution_null_sd} (1000 shuffles)`,`z = ${cn.homophily_z}: strong institutional homophily`],
    ["Internal citations sharing an author (self-citation)",cn.author_self_citation_pct+"%","–",`only ${cn.non_self_edges} cross-group links`],
    ["PageRank vs raw citations (Spearman)",cn.pagerank_vs_citations_spearman,"–","internal influence is only partly aligned with global citations"],
    ["Co-authorship clustering coefficient",an.clustering,an.clustering_random+" (random graph)","dense research groups"],
    ["Average shortest path (giant component)",an.path_length,an.path_length_random+" (random graph)",`small-world σ = ${an.small_world_sigma}`],
    ["Louvain modularity",an.modularity,`${an.modularity_null} ± ${an.modularity_null_sd} (configuration model)`,"communities far stronger than chance"],
    ["Institute assortativity",an.institution_assortativity,"0 = mixing at random",`${an.inter_group_papers} papers link two of the IIITs`],
    ["Community ↔ department / institute (NMI)",`${an.nmi_community_department} / ${an.nmi_community_institution}`,"0 = unrelated","communities follow departments and institutes"],
    ["Median co-authors: core faculty vs others",`${an.core_median_degree} vs ${an.other_median_degree}`,"Mann–Whitney p<0.001","faculty are the hubs"]].map(x=>x));
}

// ── Methods & limitations (shared text) ───────────────
function METHODS(){
  const an=(D.insights||{}).authorship_network||{}, cn=(D.insights||{}).citation_network||{}, cs=ST.communities||{}, rb=ST.robustness||{}, mx=ST.mixing||{};
  const i1=(rb.fraction_removed||[]).indexOf(0.01);
  return [
    ["Louvain community detection","implemented","finds groups of authors who co-write more with each other than chance; standard for weighted undirected graphs",
      `Q = ${an.modularity}; stable over ${cs.seeds} seeds (NMI ${cs.pairwise_nmi_mean})`,"that communities are labs or departments — they are co-writing clusters (NMI with department only "+an.nmi_community_department+")"],
    ["Configuration-model null (modularity, mixing)","implemented","keeps every author's degree, so hubs cannot explain the result",
      `Q null = ${an.modularity_null}; inter-institute links ${mx.inter_links_total} vs ${Math.round(mx.inter_links_expected_total)} expected`,"why mixing is low (distance, funding, hiring are not in the data)"],
    ["Erdős–Rényi baseline","implemented","tests whether clustering / short paths exceed what random wiring with the same n, m gives",
      `C ${(ST.coauthorship||{}).avg_clustering} vs ${(ST.er_baseline||{}).clustering_sim}; L ${(ST.coauthorship||{}).giant_avg_path_length} vs ${(ST.er_baseline_giant||{}).path_length_sim}`,"ER is a deliberately naive baseline; beating it is necessary, not sufficient"],
    ["Target-shuffled citation graphs","implemented","asks whether citations stay inside the institute more than if targets were random",
      `${cn.same_institution_pct}% vs ${cn.same_institution_null_pct}% (z = ${cn.homophily_z})`,"that the institutes ignore each other's work — 94% of internal citations are self-citations"],
    ["Log-binned degree distribution","implemented","heavy-tailed data are unreadable on linear or unit-bin log axes",
      `max degree ${(ST.coauthorship||{}).degree?.max} vs ${(ST.er_baseline||{}).max_degree_sim} (ER)`,"a power law — no exponent is fitted or claimed"],
    ["Centralities (degree, betweenness, closeness, eigenvector)","implemented","identify collaborators, brokers and well-placed authors",
      "degree~betweenness ρ = "+((ST.centrality||{}).spearman||{})["degree~betweenness"],"importance outside these three institutes; eigenvector localises and is not used for comparison"],
    ["Minimum node cuts & distance matrix","implemented","measure how many people, and how many steps, separate institutes",
      Object.entries((ST.bridges||{}).min_node_cuts||{}).map(([k,v])=>k+" "+v.node_connectivity).join(", "),"that the cut authors are the only people who talk across institutes off-paper"],
    ["Robustness (targeted vs random removal)","implemented","tests dependence on brokers, the practical meaning of a hub-dominated network",
      i1>=0?`1% removed: reach ${pct(rb.targeted.cross_reach[i1])} targeted vs ${pct(rb.random.cross_reach[i1])} random`:"–","what would happen if a person left (removal is static and non-adaptive)"],
    ["Author-identity sensitivity","implemented","checks that bridge findings are not artefacts of name matching",
      `inter-institute links ${(ST.identity_sensitivity||{}).name_only?.inter_institute_links} (name-only) vs ${(ST.identity_sensitivity||{}).conservative?.inter_institute_links} (conservative)`,"that the conservative rule is error-free (it may still split some people)"],
    ["Leiden community detection","proposed","guarantees connected communities; Louvain is already stable here (NMI > 0.93)","not run","–"],
    ["Link prediction","proposed","could rank likely future inter-IIIT collaborations with a time-split evaluation (train ≤2022, test 2023–26)","not run — only ~37 inter-IIIT papers, too few positives for a reliable evaluation","–"]];
}
const LIMITS=[
  "<b>Coverage.</b> OpenAlex affiliation and reference coverage is incomplete, especially before 2018; a missing affiliation removes an author or a link.",
  "<b>Author identity.</b> OpenAlex author IDs are trusted; extra merges need a shared co-author. Some people may remain split (spelling variants) and some OpenAlex profiles may wrongly combine two people. See DECISIONS.md.",
  "<b>Institute assignment.</b> Each author is assigned to the institute with most of their papers; movers are counted once, in that institute.",
  "<b>Edges are co-authorship and references only.</b> They do not capture informal collaboration, supervision without a paper, or influence beyond citation.",
  "<b>Static snapshot.</b> All networks aggregate 2016–2026; 2026 is a partial year. Node cuts and robustness describe this snapshot, not the future.",
  "<b>No causal claims.</b> Regression and null-model comparisons establish associations and departures from chance, not causes."];

// ── Institution comparison ─────────────────────────────
function renderCompare(){
  const P=ST.per_institution||{}, mx=ST.mixing||{}, ds=(ST.distances||{}).mean_distance||{};
  const row=(lab,f)=>[lab,...INST.map(i=>P[i]?f(P[i]):"–")];
  table("t-inst",[{h:"",v:r=>r[0]},...INST.map((i,k)=>({h:`<span class="swatch" style="background:${col(i)}"></span>${AB[i]}`,v:r=>r[k+1],num:true}))],[
    row("Authors / links",p=>`${fmt(p.nodes)} / ${fmt(p.edges)}`),row("Density",p=>p.density),row("Mean degree",p=>p.degree.mean),
    row("Max degree",p=>p.degree.max),row("Giant component",p=>`${p.giant_share_pct}%`),row("Components",p=>p.components),
    row("Avg clustering",p=>p.avg_clustering),row("Path length (giant)",p=>p.giant_avg_path_length),row("Diameter (giant)",p=>p.giant_diameter),
    row("Degree assortativity",p=>p.degree_assortativity),row("Louvain communities ≥10",p=>p.communities_10plus),row("Modularity",p=>p.modularity),
    row("Core faculty",p=>p.core_faculty),row("Top broker",p=>esc(p.top_betweenness[0]?.name)),
    row("Giant after removing top broker",p=>fmt(p.giant_after_removing_top_broker)),row("Most co-authors",p=>`${esc(p.top_degree[0]?.name)} (${p.top_degree[0]?.degree})`)]);
  const pk=(a,b)=>mx.pairs.find(r=>(r.a===a&&r.b===b)||(r.a===b&&r.b===a));
  const mat=(id,cell)=>{ document.getElementById(id).innerHTML="<thead><tr><th></th>"+INST.map(i=>`<th>${AB[i]}</th>`).join("")+"</tr></thead><tbody>"+
    INST.map(a=>`<tr><th>${AB[a]}</th>`+INST.map(b=>`<td class="${a===b?"diag":""}">${cell(a,b)}</td>`).join("")+"</tr>").join("")+"</tbody>"; };
  if(mx.pairs){ mat("t-mix",(a,b)=>a===b?`${fmt(mx.within[a].coauthor_links)} <span class="muted">(${fmt(Math.round(mx.within[a].expected))})</span>`:
      `${fmt(pk(a,b).coauthor_links)} <span class="muted">(${fmt(Math.round(pk(a,b).expected_configuration_model))})</span>`);
    mat("t-dist",(a,b)=>ds[AB[a]+"-"+AB[b]]??ds[AB[b]+"-"+AB[a]]??"–");
    table("t-pairs",[{h:"Pair",v:r=>r.pair},{h:"Co-author links",v:r=>r.coauthor_links,num:true},{h:"Obs / expected",v:r=>r.ratio_observed_expected,num:true},
      {h:"Co-published papers",v:r=>r.copublished_papers,num:true},{h:"Shared Indian partners",v:r=>(ST.shared_partners||{}).shared[r.pair],num:true},
      {h:"Partner Jaccard",v:r=>(ST.shared_partners||{}).jaccard[r.pair],num:true}],mx.pairs);
  }
  const cm=ST.citation_matrix;
  if(cm) mat("t-citmat",(a,b)=>`${fmt(cm.all[AB[a]][AB[b]])} <span class="muted">/ ${fmt(cm.excluding_self_citations[AB[a]][AB[b]])}</span>`);
  const br=ST.bridges||{};
  table("t-bridges",[{h:"Author",v:r=>r.name},{h:"Main institute",v:r=>r.institution,f:r=>`<span class="swatch" style="background:${col(r.institution)}"></span>${AB[r.institution]}`},
    {h:"Reaches",v:r=>r.reaches.map(x=>AB[x]).join(", ")},{h:"Placed at two institutes",v:r=>r.also_affiliated_with.length?"yes":"",f:r=>r.also_affiliated_with.length?'<span class="pill">'+r.also_affiliated_with.map(x=>AB[x]).join(", ")+"</span>":"–"},
    {h:"Cross-inst. co-authors",v:r=>r.cross_institute_coauthors,num:true},{h:"Core faculty",v:r=>r.core_faculty?"yes":"",f:r=>r.core_faculty?"yes":"–"},
    {h:"Betweenness",v:r=>r.betweenness,num:true,f:r=>r.betweenness.toFixed(4)}],br.top_bridges||[]);
  document.getElementById("cuts").innerHTML=Object.entries(br.min_node_cuts||{}).map(([k,v])=>
    `<div class="cut"><b>${k}: ${v.node_connectivity} authors</b><span class="muted">${v.cut_authors.map(esc).join(", ")}</span></div>`).join("")+
    `<p class="note">${fmt(br.bridge_authors)} bridge authors in total (${br.bridge_share_pct}% of authors, ${br.bridges_core_faculty} core faculty); ${br.multi_affiliated_authors} are placed at two institutes by OpenAlex.</p>`;
  const sp=ST.shared_partners||{};
  table("t-common",[{h:"Partner",v:r=>r.name},{h:"Cluster",v:r=>r.cluster},...INST.map(i=>({h:AB[i],v:r=>r[AB[i]],num:true}))],sp.top_common||[]);
  cmpTable();
}

// ── Network explorer ───────────────────────────────────
function renderExplorer(){
  const E=D.explorer; if(!E){ document.getElementById("net-ex").innerHTML="<p style='padding:16px' class='muted'>No explorer data — run part5b and part4.</p>"; return; }
  const on=new Set(INST);
  document.getElementById("ex-inst").innerHTML=INST.map(i=>`<label><input type="checkbox" value="${i}" checked> <span class="swatch" style="background:${col(i)}"></span>${AB[i]}</label>`).join(" ");
  const big=(D.auth.communities||[]).slice(0,7).map(c=>c.id);
  const ccol=cm=>{ const k=big.indexOf(cm); return k>=0?css("--s"+(k+1)):css("--other"); };
  const byId=Object.fromEntries(E.nodes.map(n=>[n.id,n]));
  const nb={}; E.links.forEach(l=>{ (nb[l.source]=nb[l.source]||[]).push([l.target,l.w,l.x]); (nb[l.target]=nb[l.target]||[]).push([l.source,l.w,l.x]); });
  const maxDg=Math.max(...E.nodes.map(n=>n.dg),1), r=d3.scaleSqrt().domain([0,maxDg]).range([3,14]);
  let sel=null;
  function detail(d){
    const el=document.getElementById("ex-detail");
    if(!d){ el.innerHTML="<p class='muted'>Click an author to see their position in the network.</p>"; return; }
    const ns=(nb[d.id]||[]).map(([k,w,x])=>({n:byId[k],w,x})).sort((a,b)=>b.x-a.x||b.w-a.w);
    el.innerHTML=`<h4>${esc(d.n)}</h4><div><span class="swatch" style="background:${col(d.i)}"></span>${esc(d.i)}${d.dep?" · "+esc(d.dep):""}</div>
      <p style="margin-top:6px">${d.core?"Core faculty · ":""}${d.p} papers · ${d.dg} co-authors (full network) · betweenness ${d.b.toFixed(4)} · community C${d.cm}</p>
      ${d.x?`<p><b>${d.x}</b> co-author link(s) to another institute${d.mv?"; OpenAlex also places this author at a second institute":""}.</p>`:(d.mv?"<p>OpenAlex places this author at two institutes.</p>":"")}
      <p class="muted" style="margin-top:6px">Co-authors shown in this view (${ns.length}):</p>
      <ul>${ns.slice(0,40).map(o=>`<li>${o.x?"↔ ":""}${esc(o.n.n)} <span class="muted">${AB[o.n.i]} · ${o.w} paper${o.w>1?"s":""}</span></li>`).join("")}</ul>`;
  }
  function draw(){
    const q=document.getElementById("ex-q").value.trim().toLowerCase(), brOnly=document.getElementById("ex-br").checked, mode=document.getElementById("ex-col").value;
    let keep=new Set(E.nodes.filter(n=>on.has(n.i)).map(n=>n.id));
    if(brOnly){ const b=new Set(); E.nodes.forEach(n=>{ if(keep.has(n.id)&&(n.x||n.mv)){ b.add(n.id); (nb[n.id]||[]).forEach(([k])=>{ if(keep.has(k)) b.add(k); }); } }); keep=b; }
    const nodes=E.nodes.filter(n=>keep.has(n.id)).map(n=>({...n})), links=E.links.filter(l=>keep.has(l.source)&&keep.has(l.target)).map(l=>({...l}));
    document.getElementById("ex-n").textContent=`${nodes.length} authors · ${links.length} links · ${links.filter(l=>l.x).length} between institutes`;
    const hit=q?new Set(nodes.filter(n=>n.n.toLowerCase().includes(q)).map(n=>n.id)):null;
    forceGraph("net-ex",nodes,links,{label:"Co-authorship network explorer",dist:28,
      r:d=>r(d.dg)+(hit&&hit.has(d.id)?3:0), fill:d=>mode==="i"?col(d.i):ccol(d.cm),
      stroke:d=>hit&&hit.has(d.id)?css("--text"):(d.x||d.mv)?css("--text"):css("--surface"), sw:d=>hit&&hit.has(d.id)?3:(d.x||d.mv)?1.8:1,
      lw:d=>d.x?2.2:Math.min(1+Math.log2(d.w),3), lc:d=>d.x?css("--s5"):null,
      tip:d=>`<b>${esc(d.n)}</b>${esc(d.i)}${d.dep?" · "+esc(d.dep):""}<br>${d.dg} co-authors · betweenness ${d.b.toFixed(4)}${d.x?`<br>${d.x} cross-institute link(s)`:""}${d.core?"<br>core faculty":""}`,
      click:d=>{ sel=d.id; detail(byId[d.id]); }});
    if(hit&&hit.size===1) detail(byId[[...hit][0]]);
    if(q&&hit&&!hit.size) document.getElementById("ex-detail").innerHTML="<p class='muted'>No author in this view matches “"+esc(q)+"”. Try clearing the filters.</p>";
    document.getElementById("leg-ex").innerHTML=(mode==="i"?INST.map(i=>`<span><span class="swatch" style="background:${col(i)}"></span>${i}</span>`).join(""):
      big.map((c,k)=>`<span><span class="swatch" style="background:${css("--s"+(k+1))}"></span>C${c} (${AB[Object.entries(D.auth.communities[k].institutions).sort((a,b)=>b[1]-a[1])[0][0]]})</span>`).join("")+`<span><span class="swatch" style="background:${css("--other")}"></span>other</span>`)+
      `<span><span class="swatch" style="background:${css("--s5")}"></span>link between institutes</span><span>dark ring = bridge author · size ∝ degree · drag, scroll to zoom</span>`;
  }
  document.getElementById("ex-inst").onchange=e=>{ e.target.checked?on.add(e.target.value):on.delete(e.target.value); draw(); };
  ["ex-col","ex-br"].forEach(id=>document.getElementById(id).onchange=draw);
  let t; document.getElementById("ex-q").oninput=()=>{ clearTimeout(t); t=setTimeout(draw,300); };
  draw();
}

// ── Course connections ─────────────────────────────────
function renderCourse(){
  const co=ST.coauthorship||{}, ds=(ST.distances||{}).mean_distance||{}, rp=ST.reference_paths||{}, er=ST.er_baseline||{};
  document.getElementById("cc-deg").innerHTML=[
    tile("Mean degree ⟨k⟩ = 2m/n",co.degree?.mean,`${fmt(co.edges)} links, ${fmt(co.nodes)} authors`),
    tile("Median / max degree",`${co.degree?.median} / ${co.degree?.max}`,"mean > median: right-skewed"),
    tile("Average path length",co.giant_avg_path_length,`giant component, ${fmt(co.giant_nodes)} authors`),
    tile("Diameter",co.giant_diameter,"longest shortest path")].join("");
  document.getElementById("cc-d1").textContent=ds["IIITA-IIITB"]; document.getElementById("cc-d2").textContent=ds["IIITB-IIITB"];
  const dd=(ST.degree_distribution||{}).coauthorship;
  const lbNote={lin:"Linear axes: almost all mass is at k ≤ 5 and the tail is invisible.",
    log:"Unit bins on log axes: the tail breaks into noisy points at 1 author per degree value (p = 1/n).",
    bin:"Log-binned: each point averages a geometric bin, so the tail is readable. It is far heavier than the ER/Poisson prediction.",
    ccdf:"CCDF needs no binning at all: P(K ≥ k) for every observed k. It is the most robust view of a tail."};
  const raw={}; if(dd){ for(let i=0;i<dd.ccdf_k.length;i++){ const k=dd.ccdf_k[i], nxt=i+1<dd.ccdf.length?dd.ccdf[i+1]:0; raw[k]=(dd.ccdf[i]-nxt); } }
  function lb(m){
    if(!dd) return; document.getElementById("cc-lb-note").textContent=lbNote[m];
    const logx={type:"logarithmic",ticks:LOGT,title:{display:true,text:"degree k",color:css("--text-2")}}, logy={type:"logarithmic",beginAtZero:false,ticks:LOGT,title:{display:true,text:m==="ccdf"?"P(K ≥ k)":"p(k)",color:css("--text-2")}};
    if(m==="lin"){ const ks=Object.keys(raw).map(Number).filter(k=>k<=60);
      chart("c-lb",{type:"bar",data:{labels:ks,datasets:[{label:"share of authors",data:ks.map(k=>raw[k]),backgroundColor:css("--t2")}]},
        options:baseOpts({plugins:{legend:{display:false}},scales:{x:{title:{display:true,text:"degree k (≤ 60 shown)",color:css("--text-2")}},y:{title:{display:true,text:"p(k)",color:css("--text-2")}}}})}); return; }
    const pts=m==="log"?Object.entries(raw).map(([k,v])=>({x:+k,y:v})):m==="bin"?dd.bin_centers.map((x,i)=>({x,y:dd.pdf[i]})):dd.ccdf_k.map((x,i)=>({x,y:dd.ccdf[i]}));
    chart("c-lb",{type:"scatter",data:{datasets:[{label:m,data:pts,backgroundColor:css(m==="bin"?"--t1":"--t3"),pointRadius:m==="log"?3:5}]},
      options:baseOpts({plugins:{legend:{display:false}},scales:{x:logx,y:logy}})});
  }
  document.querySelectorAll('input[name=lb]').forEach(x=>x.onchange=()=>lb(x.value)); lb("lin");
  // ER calculator
  const nI=document.getElementById("er-n"), kI=document.getElementById("er-k");
  const giantS=k=>{ if(k<=1) return 0; let S=0.5; for(let i=0;i<200;i++) S=1-Math.exp(-k*S); return S; };
  function er_(){ const n=+nI.value, k=+kI.value; document.getElementById("er-nv").textContent=fmt(n); document.getElementById("er-kv").textContent=k.toFixed(1);
    const L=k>1?(Math.log(n)/Math.log(k)).toFixed(2):"∞ (no giant component)";
    table("t-er",[{h:"Quantity",v:r=>r[0]},{h:"ER theory for n, ⟨k⟩ above",v:r=>r[1],num:true},{h:"ER simulated (this n, m)",v:r=>r[2],num:true},{h:"Observed network",v:r=>r[3],num:true}],[
      ["Clustering C ≈ ⟨k⟩/n",(k/n).toExponential(2),er.clustering_sim,co.avg_clustering],
      ["Path length ≈ ln n / ln ⟨k⟩",L,(ST.er_baseline_giant||{}).path_length_sim+" (giant)",co.giant_avg_path_length],
      ["Giant share S = 1 − e^(−⟨k⟩S)",(giantS(k)*100).toFixed(1)+"%",er.giant_share_sim_pct+"%",co.giant_share_pct+"%"],
      ["Max degree (Poisson tail)","–",er.max_degree_sim,co.degree?.max]]);
  }
  const reset=()=>{ nI.value=co.nodes; kI.value=co.degree?.mean; er_(); };
  nI.oninput=er_; kI.oninput=er_; document.getElementById("er-reset").onclick=reset; reset();
  document.getElementById("er-ratio").textContent=`The real network keeps ER's short paths (${co.giant_avg_path_length} vs ${(ST.er_baseline_giant||{}).path_length_sim}) but has ${Math.round(co.avg_clustering/er.clustering_sim)}× its clustering, a smaller giant component (redundant links inside cliques reach fewer people) and a max degree ${Math.round(co.degree?.max/er.max_degree_sim)}× larger: a small world built from tight groups, not a random graph.`;
  // ring vs star
  const rsI=document.getElementById("rs-n");
  function rs(){ const n=+rsI.value; document.getElementById("rs-nv").textContent="n = "+fmt(n)+(n===rp.n?" (this giant component)":"");
    const ring=n%2===0?n*n/(4*(n-1)):(n+1)/4, star=2*(n-1)/n, kk=2*co.edges/co.nodes, er2=Math.log(n)/Math.log(rp.n?((ST.er_baseline_giant||{}).mean_degree||kk):kk);
    const rows=[["Star",star],["Erdős–Rényi, same ⟨k⟩",er2],...(n===rp.n?[["Observed co-authorship",rp.observed_L]]:[]),["Closed chain (ring)",ring]];
    chart("c-rs",{type:"bar",data:{labels:rows.map(r=>r[0]),datasets:[{label:"average path length",data:rows.map(r=>r[1]),
      backgroundColor:rows.map(r=>r[0].startsWith("Observed")?css("--t1"):css("--t4")),borderRadius:4,borderSkipped:"start"}]},
      options:baseOpts({indexAxis:"y",plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>"⟨d⟩ = "+c.raw.toFixed(2)}}},
        scales:{x:{type:"logarithmic",ticks:LOGT,title:{display:true,text:"average path length ⟨d⟩ (log scale)",color:css("--text-2")}}}})}); }
  rsI.value=rp.n||1000; rsI.oninput=rs; rs();
}

function renderMethod(){
  const items=[
    "<b>Source.</b> OpenAlex works whose authorships include the institution's OpenAlex ID ("+INST.map(i=>i+" "+D.meta.openalex[i]+", ROR "+D.meta.ror[i]).join("; ")+"), publication years 2016–2026, collected "+D.meta.generated+".",
    "<b>Included.</b> Journal articles/reviews and conference papers (incl. proceedings series such as LNCS). Excluded: preprints, book chapters, books, errata, editorials, datasets, peer reviews, retracted papers. Preprint / repository copies of the same paper are merged into the published version (citation count = max over versions).",
    "<b>Quartile.</b> Journals: Scimago SJR best quartile of the journal in the publication year (2026 uses SJR 2025); 'Unranked' = not indexed by Scimago. Conferences: ICORE2026 rank, matched strictly (acronym + title overlap, or near-identical title; workshops and extended abstracts never inherit the main-track rank).",
    "<b>Faculty.</b> Authors whose OpenAlex affiliation on the paper is the institution. The OpenAlex author ID is the unit of identity; two IDs (or ID-less authorships) are merged only if they have the same normalised name, the same institute, never share a paper and share at least one co-author — a matching name alone is never enough (DECISIONS.md). <i>Core faculty</i> (heuristic for permanent faculty): ≥5 papers in ≥3 different years, last author on ≥30% and first author on ≤50% of them (excludes most PhD students). Departments come from 'Department of …' in the raw affiliation strings; if an author never states one, it is inferred from their dominant OpenAlex field (marked *).",
    "<b>h-index.</b> Faculty and institutional h-indices use the 2016–2026 papers in this dataset; 'lifetime h' is OpenAlex's author summary statistic.",
    "<b>Citation network.</b> Edges are taken from OpenAlex referenced_works. PageRank (α = 0.85) and in-degree are computed on the internal graph (papers of the three institutes citing each other), as the note requires; edges to/from other Indian institutes are kept in citation_network.csv only.",
    "<b>Citation flow.</b> A citation link counts as in-flow (out-flow) when the citing (cited) work has an Indian affiliation other than the institute itself. Impact ratio = in-flow / out-flow.",
    "<b>Authorship network.</b> Nodes = authors of the three institutes, edges weighted by joint papers. Betweenness is exact; Louvain (networkx, seed 42). Papers with >50 authors do not add edges to external co-authors. Each author has one main institute (most papers there). 'Links between institutes' = links between authors with different main institutes; 'inter-group pairs' in authorship_network.csv = pairs listed at two different institutes on the same paper.",
    "<b>Structure (part5b).</b> Configuration-model expectation of links between institutes E[e<sub>AB</sub>] = d<sub>A</sub>d<sub>B</sub>/2m; ER baseline = 5 G(n, m) graphs; minimum node cuts via max-flow with super-source/sink; robustness = static removal by initial betweenness vs 10 random orders; distances = exact all-pairs BFS on the giant component; log-binning with geometric bins.",
    "<b>Clusters.</b> Partner institutions are grouped by name/type (IIT, NIT, IIIT, IISER/IISc, CSIR, DAE, central university, industry …). 'Cross-cluster' = partner outside the IIIT cluster.",
    "<b>Inference.</b> Growth = log-linear fit 2016–2025; Q1 shift = χ² test (2016–19 vs 2022–25); normalised citation score = citations ÷ mean of papers with the same year, field and type (papers up to 2024, >50-author papers excluded), bootstrap 95% CIs; regression = OLS on log(1+citations) with HC1 robust errors; homophily = 1000 target-shuffled citation graphs; modularity = 20 configuration-model graphs.",
    "<b>Jaccard.</b> Topic sets = OpenAlex subfields (primary topic) with ≥1% of an entity's 2016–2026 journal/conference output, taken from each institution's own OpenAlex profile; weighted Jaccard compares the full subfield distributions."];
  document.getElementById("defs").innerHTML=items.map(x=>"<li>"+x+"</li>").join("");
}

// ── Errors ─────────────────────────────────────────────
window.addEventListener("error",e=>{ const b=document.getElementById("errbar"); b.textContent="Something went wrong while drawing this page ("+e.message+"). Other pages still work; try reloading."; b.style.display="block"; setTimeout(()=>b.style.display="none",9000); });
if(typeof d3==="undefined"||typeof Chart==="undefined") document.getElementById("main").insertAdjacentHTML("afterbegin","<div class='warn'>Chart libraries failed to load; charts are unavailable.</div>");

// ── Navigation & theme ─────────────────────────────────
const rendered={};
function show(p){
  document.querySelectorAll(".page").forEach(x=>x.classList.toggle("on",x.id==="p-"+p));
  document.querySelectorAll(".nav").forEach(x=>x.classList.toggle("on",x.dataset.p===p));
  if(!rendered[p]){ rendered[p]=true;
    if(p==="overview") renderOverview(); else if(p==="findings") renderFindings();
    else if(p==="citation") renderCitation(); else if(p==="authorship") renderAuthorship();
    else if(p==="india") renderIndia(); else if(p==="method") renderMethod(); else if(p==="compare") renderCompare();
    else if(p==="explorer") renderExplorer(); else if(p==="course") renderCourse(); else renderInst(p); }
  try{ localStorage.setItem("g10-page",p); }catch(e){}
}
document.querySelectorAll(".nav").forEach(b=>b.onclick=()=>show(b.dataset.p));
if(D.links) document.getElementById("sidelinks").innerHTML=
  `<a href="${D.links.repo}" target="_blank" rel="noopener">GitHub repository ↗</a>`+
  `<a href="${D.links.report}" target="_blank" rel="noopener">Report (10_IIIT.pdf) ↗</a>`+
  `<span style="color:var(--muted)">Group 10 · ${esc(D.links.team)}<br>${D.links.members.map(esc).join(" · ")}</span>`;
document.getElementById("themebtn").onclick=()=>{
  const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme==="dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.dataset.theme = dark?"light":"dark";
  try{ localStorage.setItem("g10-theme",document.documentElement.dataset.theme); }catch(e){}
  const cur=document.querySelector(".nav.on").dataset.p; Object.keys(rendered).forEach(k=>delete rendered[k]); show(cur);
};
try{ const t=localStorage.getItem("g10-theme"); if(t) document.documentElement.dataset.theme=t; }catch(e){}
let start="overview"; try{ start=localStorage.getItem("g10-page")||"overview"; }catch(e){}
if(location.hash.length>1) start=location.hash.slice(1);
show(document.getElementById("p-"+start)?start:"overview");
window.addEventListener("hashchange",()=>{ const p=location.hash.slice(1); if(document.getElementById("p-"+p)) show(p); });
"""


def build_html(D):
    nav = "".join(f'<button class="nav" data-p="{k}"><span class="dot" style="background:var(--s{n + 1})"></span>{i}</button>'
                  for n, (i, k) in enumerate(KEYS.items()))
    pages = "".join(INST_PAGE.replace("%KEY%", k).replace("%NAME%", i).replace("%SV%", f"s{n + 1}")
                    .replace("%FULL%", C.INST_FULL_NAMES[i]).replace("%OA%", C.INSTITUTIONS[i][0])
                    .replace("%ROR%", C.INSTITUTIONS[i][1])
                    for n, (i, k) in enumerate(KEYS.items()))
    body = (BODY.replace("%INSTNAV%", nav).replace("%INSTPAGES%", pages)
            .replace("%CITEN%", str(CITE_GRAPH_NODES)).replace("%EXPN%", str(EXPLORER_PER_INST)))
    data = json.dumps(D, ensure_ascii=False,
                      default=lambda v: v.item() if hasattr(v, "item") else str(v)).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Group 10 Research Map</title>
<meta name="description" content="DPCN 2026 Group 10 - research output, citation and co-authorship networks of IIIT Allahabad, ABV-IIITM Gwalior and IIIT Bangalore (2016-2026)">
<style>{CSS}</style>
</head>
<body>
{body}
<script>{lib("assets/d3.min.js")}</script>
<script>{lib("assets/chart.umd.min.js")}</script>
<script>{JS.replace("%DATA%", data)}</script>
</body>
</html>"""


def main():
    print("=" * 65)
    print(" DPCN 2026 - Group 10 - Part 4: HTML dashboard")
    print("=" * 65)
    o = A.load_outputs()
    if o["df"].empty:
        print("ERROR: run the earlier parts first.")
        return
    D = build_data(o)
    html = build_html(D)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved {OUTPUT_HTML} ({os.path.getsize(OUTPUT_HTML) / 1024:.0f} KB) - open it in any browser.")
    os.makedirs(SITE_DIR, exist_ok=True)
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved {SITE_DIR}/index.html - the folder to deploy (see README, Deployment).")


if __name__ == "__main__":
    main()
