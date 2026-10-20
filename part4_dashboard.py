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
AUTH_GRAPH_NODES = 220


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
    chosen = sorted(connected, key=lambda w: -pr.get(w, 0))[:CITE_GRAPH_NODES]
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
        top = nd.sort_values(["strength", "betweenness_centrality"], ascending=False).head(AUTH_GRAPH_NODES)
        ts = set(top.index)
        ae = o["auth_edges"]
        ae = ae[ae["edge_scope"].isin(["same_institution", "inter_group"])]
        ae = ae[ae["author_a_id"].isin(ts) & ae["author_b_id"].isin(ts)]
        w = ae.groupby(["author_a_id", "author_b_id"]).size().reset_index(name="w")
        D["auth"]["graph"] = {
            "nodes": [{"id": k, "n": r["name"], "i": r["institution"], "dep": r["department"],
                       "cm": int(r["community"]), "dg": int(r["degree"]), "b": r["betweenness_centrality"],
                       "core": bool(r["is_core_faculty"])} for k, r in top.iterrows()],
            "links": [{"source": a, "target": b, "w": int(n)} for a, b, n in w.itertuples(index=False)]}

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
@media(max-width:860px){body{flex-direction:column}#side{width:100%;height:auto;position:static}
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
.finding .num{display:inline-block;width:22px;height:22px;border-radius:50%;background:var(--surface-2);
  border:1px solid var(--border);text-align:center;line-height:20px;font-size:11px;margin-right:6px;color:var(--text)}
"""

BODY = r"""
<nav id="side">
  <div class="logo"><b>Research Map · Group 10</b><span>DPCN 2026 · 2016–2026</span></div>
  <div class="navh">Overview</div>
  <button class="nav on" data-p="overview"><span class="dot" style="background:var(--muted)"></span>All institutions</button>
  <button class="nav" data-p="findings"><span class="dot" style="background:var(--s5)"></span>Key findings</button>
  <div class="navh">Institutions</div>
  %INSTNAV%
  <div class="navh">Networks</div>
  <button class="nav" data-p="citation"><span class="dot" style="background:var(--t1)"></span>Citation network</button>
  <button class="nav" data-p="authorship"><span class="dot" style="background:var(--t3)"></span>Authorship network</button>
  <button class="nav" data-p="india"><span class="dot" style="background:var(--s4)"></span>Indian connectivity</button>
  <div class="navh">About</div>
  <button class="nav" data-p="method"><span class="dot" style="background:var(--other)"></span>Data &amp; definitions</button>
  <button class="themebtn" id="themebtn">Toggle dark / light</button>
  <div class="sidelinks" id="sidelinks"></div>
</nav>
<main id="main">
<section class="page on" id="p-overview">
  <h1>Research output of three IIITs</h1>
  <div class="sub">IIIT Allahabad · ABV-IIITM Gwalior · IIIT Bangalore — journal and conference papers 2016–2026 (OpenAlex)</div>
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
  <h1>Key findings</h1>
  <div class="sub">Inferential results — every claim is tested against a baseline (null model, control variables or confidence interval)</div>
  <div class="grid g3" id="find-cards"></div>
  <div class="grid g2">
    <div class="card"><h3>Venue quality over time</h3><div class="note">Share of journal papers in Q1 venues, per year</div><div class="cw"><canvas id="c-q1year"></canvas></div></div>
    <div class="card"><h3>Citations received / given with other Indian institutes</h3><div class="note">Per year; above 1 = the institute is cited more than it cites</div><div class="cw"><canvas id="c-ratio"></canvas></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Normalised citation impact by collaboration type</h3><div class="note">Mean citation score normalised by year, field and paper type (1 = average); hover for 95% CI</div><div class="cw"><canvas id="c-ncs"></canvas></div></div>
    <div class="card"><h3>What predicts citations?</h3><div class="note">OLS on log(1 + citations) with year and field fixed effects; % change with 95% CI</div><div class="tw"><table id="t-reg"></table></div></div>
  </div>
  <div class="card" style="margin-bottom:16px"><h3>Institution comparison beyond counts</h3><div class="tw"><table id="t-cmp"></table></div></div>
  <div class="card"><h3>Network tests</h3><div class="note">Observed value vs the random-graph baseline</div><div class="tw"><table id="t-nettest"></table></div></div>
</section>
%INSTPAGES%
<section class="page" id="p-citation">
  <h1>Citation network</h1>
  <div class="sub">Directed graph within the three institutes: nodes = papers, edge A → B = A cites B</div>
  <div class="grid g4" id="cit-tiles"></div>
  <div class="card" style="margin-bottom:16px"><h3>Internal citation graph</h3>
    <div class="note">Top %CITEN% papers by PageRank that take part in internal citations. Node size ∝ PageRank, colour = institution. Drag, scroll to zoom.</div>
    <div class="net" id="net-cit"></div><div class="legend" id="leg-cit"></div></div>
  <div class="grid g2">
    <div class="card"><h3>PageRank top 10</h3><div class="note">Most influential papers inside the cluster</div><div class="tw"><table id="t-pr"></table></div></div>
    <div class="card"><h3>In-degree distribution</h3><div class="note">Times a paper is cited by other papers of the three institutes (log scale)</div><div class="cw"><canvas id="c-indeg"></canvas></div></div>
  </div>
</section>
<section class="page" id="p-authorship">
  <h1>Authorship network</h1>
  <div class="sub">Undirected co-authorship among authors of the three institutes; communities = Louvain (seed 42)</div>
  <div class="grid g4" id="auth-tiles"></div>
  <div class="card" style="margin-bottom:16px"><h3>Co-authorship graph</h3>
    <div class="note">Top %AUTHN% authors by collaboration strength; colour = Louvain community (largest 7, rest grey); ring = core faculty. Drag, scroll to zoom.</div>
    <div class="net" id="net-auth"></div><div class="legend" id="leg-auth"></div></div>
  <div class="grid g2">
    <div class="card"><h3>Degree centrality — most collaborative</h3><div class="tw"><table id="t-deg"></table></div></div>
    <div class="card"><h3>Betweenness centrality — bridges between groups</h3><div class="tw"><table id="t-bet"></table></div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Largest communities</h3><div class="tw"><table id="t-comm"></table></div></div>
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
    el.innerHTML = "<thead><tr>"+cols.map((c,i)=>`<th class="${c.num?"num":""}" data-i="${i}">${c.h}${i===sortI?(asc?" ▲":" ▼"):""}</th>`).join("")+
      "</tr></thead><tbody>"+r.map(x=>"<tr>"+cols.map(c=>`<td class="${c.num?"num":""}">${c.f?c.f(x):esc(c.v(x))}</td>`).join("")+"</tr>").join("")+"</tbody>";
    el.querySelectorAll("th").forEach(th=>th.onclick=()=>{const i=+th.dataset.i; if(i===sortI) asc=!asc; else {sortI=i; asc=false;} render();});
  }
  render();
}

function tile(lab,val,foot){ return `<div class="card tile"><div class="lab">${lab}</div><div class="val">${val}</div><div class="foot">${foot||""}</div></div>`; }

// ── Overview ───────────────────────────────────────────
function renderOverview(){
  const S = Object.fromEntries(D.summary.map(s=>[s.institution,s]));
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
  svg.call(d3.zoom().scaleExtent([.2,8]).on("zoom",e=>g.attr("transform",e.transform)));
  if(o.directed){ svg.append("defs").append("marker").attr("id",elId+"-arr").attr("viewBox","0 -4 8 8").attr("refX",8).attr("markerWidth",5).attr("markerHeight",5).attr("orient","auto")
      .append("path").attr("d","M0,-4L8,0L0,4").attr("fill",css("--muted")); }
  const sim=d3.forceSimulation(nodes).force("link",d3.forceLink(links).id(d=>d.id).distance(o.dist||40).strength(.25))
    .force("charge",d3.forceManyBody().strength(-38)).force("center",d3.forceCenter(W/2,H/2))
    .force("x",d3.forceX(W/2).strength(.04)).force("y",d3.forceY(H/2).strength(.05))
    .force("col",d3.forceCollide(d=>o.r(d)+1.5));
  const link=g.append("g").selectAll("line").data(links).join("line").attr("stroke",css("--muted")).attr("stroke-opacity",.35)
    .attr("stroke-width",d=>o.lw?o.lw(d):1).attr("marker-end",o.directed?`url(#${elId}-arr)`:null);
  const node=g.append("g").selectAll("circle").data(nodes).join("circle").attr("r",o.r).attr("fill",o.fill)
    .attr("stroke",o.stroke||css("--surface")).attr("stroke-width",o.sw||2).style("cursor","pointer")
    .on("mousemove",(e,d)=>showTip(e,o.tip(d))).on("mouseleave",hideTip)
    .call(d3.drag().on("start",(e,d)=>{if(!e.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y;})
      .on("drag",(e,d)=>{d.fx=e.x;d.fy=e.y;}).on("end",(e,d)=>{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}));
  if(o.click) node.on("click",(e,d)=>o.click(d));
  sim.on("tick",()=>{
    link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>{ if(!o.directed) return d.target.x; const dx=d.target.x-d.source.x, dy=d.target.y-d.source.y, L=Math.hypot(dx,dy)||1; return d.target.x-dx/L*(o.r(d.target)+2);})
        .attr("y2",d=>{ if(!o.directed) return d.target.y; const dx=d.target.x-d.source.x, dy=d.target.y-d.source.y, L=Math.hypot(dx,dy)||1; return d.target.y-dy/L*(o.r(d.target)+2);});
    node.attr("cx",d=>d.x).attr("cy",d=>d.y);
  });
}

// ── Citation network ───────────────────────────────────
function renderCitation(){
  const s=D.cite.summary||{};
  document.getElementById("cit-tiles").innerHTML=[
    tile("Papers (nodes)",fmt(s.nodes),"journal + conference, 3 institutes"),
    tile("Internal citation edges",fmt(s.internal_edges),`${fmt(s.cross_institution_internal_edges)} between different institutes`),
    tile("Papers cited internally",fmt(s.papers_cited_internally),`max in-degree ${fmt(s.max_in_degree)}`),
    tile("Largest weak component",fmt(s.largest_weak_component),"papers connected by citations")].join("");
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
    options:baseOpts({plugins:{legend:{display:false}},scales:{x:{type:"logarithmic",title:{display:true,text:"in-degree",color:css("--text-2")}},
      y:{type:"logarithmic",beginAtZero:false,title:{display:true,text:"papers",color:css("--text-2")}}}})});
}

// ── Authorship network ─────────────────────────────────
function renderAuthorship(){
  const s=D.auth.summary||{};
  document.getElementById("auth-tiles").innerHTML=[
    tile("Authors (nodes)",fmt(s.nodes),`${fmt(s.isolated_authors)} without co-authors at the 3 institutes`),
    tile("Co-author links",fmt(s.edges),`${fmt(s.inter_group_edges)} link two different institutes`),
    tile("Louvain communities",fmt(s.communities),`modularity ${s.modularity}`),
    tile("Giant component",fmt(s.giant_component),`avg clustering ${s.avg_clustering}`)].join("");
  const G=D.auth.graph||{nodes:[],links:[]};
  const big=(D.auth.communities||[]).slice(0,7).map(c=>c.id);
  const ccol=cm=>{ const k=big.indexOf(cm); return k>=0?css("--s"+(k+1)):css("--other"); };
  const maxDg=Math.max(...G.nodes.map(n=>n.dg),1);
  const r=d3.scaleSqrt().domain([0,maxDg]).range([3,13]);
  forceGraph("net-auth",G.nodes.map(n=>({...n})),G.links.map(l=>({...l})),{label:"Co-authorship network",dist:30,
    r:d=>r(d.dg), fill:d=>ccol(d.cm), stroke:d=>d.core?css("--text"):css("--surface"), sw:d=>d.core?1.5:1,
    lw:d=>Math.min(1+Math.log2(d.w),4),
    tip:d=>`<b>${esc(d.n)}</b>${esc(d.i)}${d.dep?" · "+esc(d.dep):""}<br>community C${d.cm} · ${d.dg} co-authors · betweenness ${d.b.toFixed(4)}${d.core?"<br>core faculty":""}`});
  document.getElementById("leg-auth").innerHTML=big.map((c,k)=>{const cc=D.auth.communities[k];
    return `<span><span class="swatch" style="background:${css("--s"+(k+1))}"></span>C${c} (${cc.size}) ${esc(cc.top_authors[0]||"")}</span>`;}).join("")+
    `<span><span class="swatch" style="background:${css("--other")}"></span>other communities</span>`;
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
  document.getElementById("find-cards").innerHTML=I.findings.map((f,k)=>
    `<div class="card finding"><h3><span class="num">${k+1}</span>${esc(f.title)}</h3><p>${esc(f.text)}</p></div>`).join("");
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
  const cn=I.citation_network, an=I.authorship_network;
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

function renderMethod(){
  const items=[
    "<b>Source.</b> OpenAlex works whose authorships include the institution's OpenAlex ID ("+INST.map(i=>i+" "+D.meta.openalex[i]+", ROR "+D.meta.ror[i]).join("; ")+"), publication years 2016–2026, collected "+D.meta.generated+".",
    "<b>Included.</b> Journal articles/reviews and conference papers (incl. proceedings series such as LNCS). Excluded: preprints, book chapters, books, errata, editorials, datasets, peer reviews, retracted papers. Preprint / repository copies of the same paper are merged into the published version (citation count = max over versions).",
    "<b>Quartile.</b> Journals: Scimago SJR best quartile of the journal in the publication year (2026 uses SJR 2025); 'Unranked' = not indexed by Scimago. Conferences: ICORE2026 rank, matched strictly (acronym + title overlap, or near-identical title; workshops and extended abstracts never inherit the main-track rank).",
    "<b>Faculty.</b> Authors whose OpenAlex affiliation on the paper is the institution. Same-name OpenAlex author IDs are merged. <i>Core faculty</i> (heuristic for permanent faculty): ≥5 papers in ≥3 different years, last author on ≥30% and first author on ≤50% of them (excludes most PhD students). Departments come from 'Department of …' in the raw affiliation strings; if an author never states one, it is inferred from their dominant OpenAlex field (marked *).",
    "<b>h-index.</b> Faculty and institutional h-indices use the 2016–2026 papers in this dataset; 'lifetime h' is OpenAlex's author summary statistic.",
    "<b>Citation network.</b> Edges are taken from OpenAlex referenced_works. PageRank (α = 0.85) and in-degree are computed on the internal graph (papers of the three institutes citing each other), as the note requires; edges to/from other Indian institutes are kept in citation_network.csv only.",
    "<b>Citation flow.</b> A citation link counts as in-flow (out-flow) when the citing (cited) work has an Indian affiliation other than the institute itself. Impact ratio = in-flow / out-flow.",
    "<b>Authorship network.</b> Nodes = authors of the three institutes, edges weighted by joint papers. Betweenness is exact; Louvain (networkx, seed 42). Papers with >50 authors do not add edges to external co-authors.",
    "<b>Clusters.</b> Partner institutions are grouped by name/type (IIT, NIT, IIIT, IISER/IISc, CSIR, DAE, central university, industry …). 'Cross-cluster' = partner outside the IIIT cluster.",
    "<b>Inference.</b> Growth = log-linear fit 2016–2025; Q1 shift = χ² test (2016–19 vs 2022–25); normalised citation score = citations ÷ mean of papers with the same year, field and type (papers up to 2024, >50-author papers excluded), bootstrap 95% CIs; regression = OLS on log(1+citations) with HC1 robust errors; homophily = 1000 target-shuffled citation graphs; modularity = 20 configuration-model graphs.",
    "<b>Jaccard.</b> Topic sets = OpenAlex subfields (primary topic) with ≥1% of an entity's 2016–2026 journal/conference output, taken from each institution's own OpenAlex profile; weighted Jaccard compares the full subfield distributions."];
  document.getElementById("defs").innerHTML=items.map(x=>"<li>"+x+"</li>").join("");
}

// ── Navigation & theme ─────────────────────────────────
const rendered={};
function show(p){
  document.querySelectorAll(".page").forEach(x=>x.classList.toggle("on",x.id==="p-"+p));
  document.querySelectorAll(".nav").forEach(x=>x.classList.toggle("on",x.dataset.p===p));
  if(!rendered[p]){ rendered[p]=true;
    if(p==="overview") renderOverview(); else if(p==="findings") renderFindings();
    else if(p==="citation") renderCitation(); else if(p==="authorship") renderAuthorship();
    else if(p==="india") renderIndia(); else if(p==="method") renderMethod(); else renderInst(p); }
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
            .replace("%CITEN%", str(CITE_GRAPH_NODES)).replace("%AUTHN%", str(AUTH_GRAPH_NODES)))
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


if __name__ == "__main__":
    main()
