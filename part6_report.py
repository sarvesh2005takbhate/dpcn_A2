"""
DPCN 2026 - Group 10 - Part 6: Statistics report (PDF)
=======================================================
Builds 10_IIIT.pdf (max. 5 pages, as required by the instruction note) from the
files written by parts 1b-5. Every number is read from those files.

Usage:
    python part6_report.py
"""

import os
from types import SimpleNamespace
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

import group10_analysis as A
import group10_common as C

OUT = "10_IIIT.pdf"
MARGIN = 34
WIDTH = A4[0] - 2 * MARGIN
PRIMARY = colors.HexColor("#184f95")
INK2 = colors.HexColor("#52514e")
RULE = colors.HexColor("#d9d8d3")
HEAD_BG = colors.HexColor("#eef3fa")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=15, leading=18, textColor=PRIMARY, spaceAfter=2)
SUB = ParagraphStyle("sub", parent=ss["Normal"], fontSize=8.6, leading=11, textColor=INK2, alignment=1)
H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=10.5, leading=12.5, textColor=PRIMARY,
                    spaceBefore=5, spaceAfter=2, keepWithNext=1)
BODY = ParagraphStyle("body", parent=ss["Normal"], fontSize=7.9, leading=9.7, spaceAfter=1.5)
BUL = ParagraphStyle("bul", parent=BODY, leftIndent=8, bulletIndent=0)
CAP = ParagraphStyle("cap", parent=BODY, fontSize=7, leading=8.4, textColor=INK2, spaceAfter=3)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=6.7, leading=7.9, spaceAfter=0)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="Helvetica-Bold")


SUBS = {"\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2212": "-", "\u00a0": " ", "\u2009": " ",
        "\u202f": " "}


def clean(text):
    text = str(text)
    for a, b in SUBS.items():
        text = text.replace(a, b)
    return text


def cut(text, n):
    text = clean(text)
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


def P(text, style=BODY):
    return Paragraph(clean(text), style)


def bullets(items):
    return [Paragraph(clean(t), BUL, bulletText="•") for t in items]


def fig(path, width=WIDTH, caption=None):
    w, h = ImageReader(path).getSize()
    out = [Image(path, width=width, height=width * h / w)]
    if caption:
        out.append(P(caption, CAP))
    return KeepTogether(out)


def table(rows, widths, header=True, align_right=()):
    data = [[Paragraph(escape(clean(c)) if not str(c).startswith("<") else clean(c),
                       CELLB if (header and i == 0) else CELL) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.3, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), HEAD_BG))
    for c in align_right:
        st.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(st))
    return t


def link(url, text=None):
    return f'<link href="{url}" color="#184f95"><u>{escape(text or url)}</u></link>'


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(INK2)
    canvas.drawString(MARGIN, 20, "DPCN 2026 · Group 10 · Titan Mandal · Research mapping of three IIITs")
    canvas.drawRightString(A4[0] - MARGIN, 20, f"Page {doc.page}")
    canvas.restoreState()


# ─────────────────────────────────────────────
# CONTRIBUTIONS (effort weighted by difficulty, learning curve and time)
# ─────────────────────────────────────────────
# (member, work package, difficulty 1-5, learning curve 1-5, hours)
WORK = [
    ("Hrishikesh", "OpenAlex collection under the 1000-request/day limit: batched cites / cited_by "
                   "filters, page paging, resumable caches", 4, 4, 14),
    ("Hrishikesh", "Corpus rules: journal/conference classification, version merging, de-duplication, "
                   "100-author truncation fix", 3, 3, 8),
    ("Hrishikesh", "Year-matched Scimago quartiles and strict ICORE2026 matching", 3, 3, 7),
    ("Hrishikesh", "Data validation: flag checks, cluster labels, partner-ID alignment, folder clean-up", 2, 2, 6),
    ("Sarvesh", "Citation network: internal / in-flow / out-flow edges, PageRank, in-degree, "
                "self-citation and homophily null model", 4, 4, 12),
    ("Sarvesh", "Authorship network: author disambiguation, Louvain, exact betweenness, small-world and "
                "configuration-model tests", 4, 4, 11),
    ("Sarvesh", "Indian connectivity: citation flow, impact ratio, partner clusters, Jaccard topic similarity",
     3, 3, 7),
    ("Shourya", "Faculty and department identification, core-faculty rule, h-indices", 3, 3, 8),
    ("Shourya", "Statistical inference: normalised impact, OLS with robust errors, trend and "
                "concentration tests", 4, 4, 10),
    ("Shourya", "Interactive dashboards (D3 / Chart.js and Streamlit) and report figures", 3, 3, 12),
    ("Shourya", "Report writing and layout", 2, 2, 6),
]


def contribution_table():
    rows = [["Member", "Work package", "Difficulty", "Learning", "Hours", "Effort"]]
    tot = {}
    for m, w, d, l, h in WORK:
        e = h * (d + l) / 2
        tot[m] = tot.get(m, 0) + e
        rows.append([m, w, d, l, h, f"{e:.0f}"])
    total = sum(tot.values())
    shares = ", ".join(f"{m} {v:.0f} ({v / total * 100:.1f}%)" for m, v in tot.items())
    return rows, shares


# ─────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────

def build():
    o = A.load_outputs()
    df, fac, I, flow = o["df"], o["fac"], o["insights"], o["flow"]
    cm, am = o["cite_metrics"], o["auth_metrics"]
    S = A.institution_summary(df, fac).set_index("institution")
    ia, ab, ib = C.INST_NAMES
    story = []

    # ── title & links ──
    story += [P("Research Mapping of IIIT Allahabad, ABV-IIITM Gwalior and IIIT Bangalore, 2016–2026", H1),
              P("DPCN 2026 Course Project · <b>Group 10</b> · Team Titan Mandal · Hrishikesh, Sarvesh, Shourya "
                "· Instructor: Chittaranjan Hens", SUB), Spacer(1, 4)]
    dash = link(C.DASHBOARD_LIVE_URL, "open dashboard") if C.DASHBOARD_LIVE_URL else \
        "dashboard.html / site/index.html, built by part4_dashboard.py (public URL in the README)"
    links = [["Resource", "Link"],
             ["Interactive dashboard (all panels, networks, findings)", dash],
             ["Code and documentation (README.md, DECISIONS.md)", link(C.REPO_URL)],
             ["Streamlit dashboard (filters by institute / year / type)", "streamlit run app.py (in the repository)"],
             ["Submission files (to the instructor; not in the public repository)",
              "group10_data.csv · citation_network.csv · authorship_network.csv · indian_connections.csv · "
              "group10_faculty.csv"]]
    story += [table(links, [WIDTH * 0.42, WIDTH * 0.58]), Spacer(1, 4)]

    # ── key findings ──
    SN = o["structure"]
    story.append(P("Research question and key findings", H2))
    story.append(P("<b>How do the research networks of the three IIITs compare, and how — and through whom — are the "
                   "institutes connected?</b> Co-authorship edges = two authors on one paper (undirected, weighted by "
                   "joint papers); citation edges = paper A lists paper B as a reference (directed).", BODY))
    story += bullets([f"<b>{escape(f['title'])}.</b> {escape(f['observation'])}" for f in SN["findings"]] +
                     [f"<b>{escape(f['title'])}.</b> {escape(f['text'])}" for f in I["findings"]
                      if not f["title"].startswith(("Internal citation", "From citation", "Impact is carried"))])

    # ── overview table ──
    story.append(P("1. Data and institution overview", H2))
    rows = [["Metric", ia, ab, ib, "All (unique)"]]
    spec = [("Papers (journal / conference)", lambda s: f"{s.papers:,} ({s.journal_papers:,} / {s.conference_papers:,})"),
            ("Q1 share of journal papers", lambda s: f"{s.q1_journal_pct}%"),
            ("CORE A*/A conference papers", lambda s: f"{s.core_astar_a}"),
            ("Citations (median per paper)", lambda s: f"{s.citations:,} ({s.median_citations:g})"),
            ("Institutional h-index (2016–2026 papers)", lambda s: f"{s.h_index}"),
            ("Core faculty / affiliated authors", lambda s: f"{s.core_faculty} / {s.affiliated_authors:,}"),
            ("Median core-faculty h-index", lambda s: f"{s.median_faculty_h:g}"),
            ("Papers with another Indian institute / international", lambda s: f"{s.indian_collab_pct}% / {s.international_pct}%"),
            ("Cite an Indian institute / cited by one", lambda s: f"{s.cites_indian_pct}% / {s.cited_by_indian_pct}%")]
    def row_of(inst):
        return SimpleNamespace(**{k: int(v) if isinstance(v, float) and float(v).is_integer() else v
                                  for k, v in S.loc[inst].items()})
    for name, f in spec:
        rows.append([name] + [f(row_of(i)) for i in C.INST_NAMES + ["All (unique papers)"]])
    story.append(table(rows, [WIDTH * 0.32] + [WIDTH * 0.17] * 4, align_right=(1, 2, 3, 4)))
    story.append(P(
        "<b>Data.</b> OpenAlex works affiliated with each institute's OpenAlex ID (I26072440, I9747756, I181514455), "
        "2016–2026; journal and conference papers only (preprints, book chapters, errata, retracted and duplicate "
        "versions removed; a version's citations are merged into the published paper). Journal quartile = Scimago "
        "SJR quartile of the journal in the publication year; conference rank = ICORE2026 (strict acronym + title "
        "match). Indian institutions = OpenAlex country code IN. <i>Core faculty</i> = authors with ≥5 papers in ≥3 "
        "years, last author on ≥30% and first author on ≤50% of them; departments come from 'Department of …' in the "
        "affiliation strings. 2026 is a partial year.", CAP))

    # ── publication statistics ──
    story.append(P("2. Publication trend and venue quality", H2))
    story.append(fig(os.path.join(C.CHARTS_DIR, "f1_growth_quality.png"), WIDTH * 0.85, caption=
                     "Figure 1. (a) Yearly output with fitted log-linear growth (2026 omitted as partial). "
                     "(b) Share of journal papers in Q1 venues."))
    tj = [["Institution", "Top 5 journals (papers, SJR quartile)"]]
    for inst in C.INST_NAMES:
        t = A.top_venues(df, inst, "journal", 5)
        tj.append([inst, "; ".join(f"{r.journal_name} ({r.papers}, {r.quartile or '–'})" for r in t.itertuples())])
    story.append(table(tj, [WIDTH * 0.15, WIDTH * 0.85]))

    # ── faculty & areas ──
    story.append(P("3. Faculty, departments and research areas", H2))
    story.append(fig(os.path.join(C.CHARTS_DIR, "03_hindex_distribution.png"), WIDTH * 0.9, caption=
                     f"Figure 2. h-index (2016–2026 papers) of core faculty. Output and h-index are strongly related "
                     f"(Spearman ρ = {I['faculty']['papers_vs_h_spearman']}); median OpenAlex lifetime h-index of core "
                     f"faculty = {I['faculty']['lifetime_h_median']:g}."))
    fa = A.research_areas(df, "field", 6)
    rows = [["Field (% of papers)"] + list(fa.columns)]
    for inst in C.INST_NAMES:
        rows.append([inst] + [f"{v:g}" for v in fa.loc[inst]])
    story.append(table(rows, [WIDTH * 0.19] + [WIDTH * 0.81 / len(fa.columns)] * len(fa.columns),
                       align_right=tuple(range(1, len(fa.columns) + 1))))
    dep = A.department_breakdown(o["adf"], fac)
    dl = []
    for inst in C.INST_NAMES:
        d = dep[dep["institution"] == inst].sort_values("papers", ascending=False).head(3)
        dl.append(f"<b>{inst}</b>: " + ", ".join(f"{r.department} ({r.papers})" for r in d.itertuples()))
    story.append(P("Largest departments by papers — " + "; ".join(dl) + ".", CAP))
    tf = [["Institution", "Top 5 core faculty by h-index (papers, h, department)"]]
    for inst in C.INST_NAMES:
        f = A.faculty_list(fac, inst).head(5)
        tf.append([inst, "; ".join(f"{r.name} ({r.papers}, h={r.h_index}, {r.department.split(' &')[0]})"
                                   for r in f.itertuples())])
    story.append(table(tf, [WIDTH * 0.15, WIDTH * 0.85]))

    # ── impact ──
    story.append(P("4. Citation impact beyond raw counts", H2))
    mc = A.most_cited(df, 10)
    rows = [["#", "Most-cited paper", "Institution", "Venue", "Year", "Cites", "DOI"]]
    for k, r in mc.iterrows():
        rows.append([k + 1, cut(r.title, 110), r.institution, cut(r.journal_name or "–", 40), int(r.year),
                     f"{r.citations:,}" + (" *" if r.n_authors > C.HYPERAUTHOR_THRESHOLD else ""),
                     link(r.doi, "doi") if r.doi else "–"])
    story.append(table(rows, [WIDTH * 0.03, WIDTH * 0.45, WIDTH * 0.13, WIDTH * 0.22, WIDTH * 0.05, WIDTH * 0.07,
                              WIDTH * 0.05], align_right=(0, 4, 5)))
    story.append(P("* &gt;50-author collaboration (Astropy, 100+ authors) – excluded from normalised scores and "
                   "the regression.", CAP))
    story.append(fig(os.path.join(C.CHARTS_DIR, "f2_impact_drivers.png"), WIDTH * 0.8, caption=
                     "Figure 3. (a) Mean normalised citation score (citations ÷ mean of papers with the same year, "
                     "field and type; papers up to 2024; bootstrap 95% CI). (b) OLS of log(1+citations) with year and "
                     "field fixed effects and HC1 robust standard errors."))
    ni = I["normalised_impact"]
    rows = [["Institution", "Growth / yr (95% CI)", "Q1 share 2016–19 → 2022–25", "Mean normalised impact (95% CI)",
             "Papers in top 10%", "Citation Gini", "Top-10% papers' share"]]
    for inst in C.INST_NAMES:
        g, n, c = I["growth_quality"][inst], ni[inst], I["concentration"][inst]
        rows.append([inst, f"{g['annual_growth_pct']}% ({g['growth_ci'][0]}–{g['growth_ci'][1]})",
                     f"{g['q1_share_2016_19']}% → {g['q1_share_2022_25']}%",
                     f"{n['mncs']} ({n['mncs_ci'][0]}–{n['mncs_ci'][1]})", f"{n['pp_top10']}%",
                     c["gini_citations"], f"{c['top10pct_paper_citation_share']}%"])
    story.append(table(rows, [WIDTH * 0.15, WIDTH * 0.15, WIDTH * 0.16, WIDTH * 0.17, WIDTH * 0.11, WIDTH * 0.11,
                              WIDTH * 0.15], align_right=(1, 2, 3, 4, 5, 6)))

    # ── citation network ──
    s, cn = cm["summary"], I["citation_network"]
    story.append(P("5. Citation network", H2))
    story += bullets([
        f"<b>Construction.</b> Directed paper → paper edges from OpenAlex <i>referenced_works</i>: {s['nodes']:,} papers, "
        f"{s['internal_edges']:,} internal edges ({s['papers_cited_internally']:,} papers cited at least once, "
        f"largest weak component {s['largest_weak_component']}). citation_network.csv also holds "
        f"{s['edge_types'].get('outflow_indian', 0):,} out-flow and {s['edge_types'].get('inflow_indian', 0):,} "
        f"in-flow edges with other Indian institutes.",
        f"<b>In-degree</b> is heavy-tailed (distribution on the dashboard's citation-network page): "
        f"{s['in_degree_distribution'].get('0', 0):,} papers are never cited internally, "
        f"{s['in_degree_distribution'].get('1', 0):,} once, and the maximum is {s['max_in_degree']}.",
        f"<b>Self-citation and homophily.</b> {cn['author_self_citation_pct']}% of internal edges share an author and "
        f"{cn['same_institution_pct']}% stay inside the citing institute (shuffled baseline "
        f"{cn['same_institution_null_pct']}% ± {cn['same_institution_null_sd']}, z = {cn['homophily_z']}). PageRank "
        f"therefore ranks the most-continued research lines; it correlates only moderately with global citations "
        f"(ρ = {cn['pagerank_vs_citations_spearman']})."])
    rows = [["#", "PageRank top 10 (internal graph)", "Institution", "Year", "In-deg", "PageRank"]]
    for k, t in enumerate(cm["pagerank_top10"], 1):
        rows.append([k, cut(t["title"], 105), " & ".join(t["institutions"]), t["year"], t["in_degree"],
                     f"{t['pagerank']:.5f}"])
    story.append(table(rows, [WIDTH * 0.03, WIDTH * 0.59, WIDTH * 0.15, WIDTH * 0.06, WIDTH * 0.07, WIDTH * 0.1],
                       align_right=(0, 3, 4, 5)))
    story.append(fig(os.path.join(C.CHARTS_DIR, "f3_citation_network.png"), WIDTH * 0.8, caption=
                     "Figure 4. (a) Largest weakly connected component of the internal citation network, coloured by "
                     "institute: the three institutes form separate regions. (b) Observed same-institute share versus "
                     "1000 graphs with shuffled citation targets."))

    # ── authorship network ──
    an, asum = I["authorship_network"], am["summary"]
    story.append(P("6. Authorship network", H2))
    story += bullets([
        f"<b>Construction.</b> Undirected co-authorship among the {asum['nodes']:,} authors of the three institutes "
        f"(OpenAlex author IDs; extra merges only with same name, same institute and a shared co-author — "
        f"DECISIONS.md), {asum['edges']:,} weighted edges; authorship_network.csv adds "
        f"{asum['edge_scopes'].get('cross_institution_india', 0):,} edges to co-authors at other Indian institutes.",
        f"<b>Structure.</b> Small-world (clustering {an['clustering']} vs {an['clustering_random']}, path length "
        f"{an['path_length']} vs {an['path_length_random']}; σ = {an['small_world_sigma']}), {asum['communities']} Louvain "
        f"communities with modularity {an['modularity']} (configuration-model graphs: {an['modularity_null']}). "
        f"Communities align with institutes (NMI {an['nmi_community_institution']}) and departments "
        f"(NMI {an['nmi_community_department']}); institute assortativity {an['institution_assortativity']}.",
        f"<b>Centrality.</b> Core faculty are the hubs (median degree {an['core_median_degree']:.0f} vs "
        f"{an['other_median_degree']:.0f}). Bridges with the highest betweenness link otherwise separate groups."])
    nd = pd.DataFrame.from_dict(am["nodes"], orient="index")
    tdeg = nd.sort_values("degree_centrality", ascending=False).head(8)
    tbet = nd.sort_values("betweenness_centrality", ascending=False).head(8)
    rows = [["Degree centrality (co-authors)", "Institution", "Betweenness centrality", "Institution"]]
    for (_, a), (_, b) in zip(tdeg.iterrows(), tbet.iterrows()):
        rows.append([f"{a['name']} ({a['degree']})", a["institution"], f"{b['name']} ({b['betweenness_centrality']:.3f})",
                     b["institution"]])
    story.append(table(rows, [WIDTH * 0.3, WIDTH * 0.2, WIDTH * 0.3, WIDTH * 0.2]))
    co, mx, br = SN["coauthorship"], SN["mixing"], SN["bridges"]
    story.append(P("6b. How the three institutes connect", H2))
    ds = SN["distances"]["mean_distance"]
    rows = [["Pair", "Co-author links (expected)", "Co-published papers", "Min. node cut", "Mean distance",
             "Shared Indian partners (Jaccard)", "Non-self citations A→B / B→A"]]
    nos = SN["citation_matrix"]["excluding_self_citations"]
    for r in mx["pairs"]:
        a, b = r["pair"].split("-")
        rows.append([r["pair"], f"{r['coauthor_links']} ({r['expected_configuration_model']:,.0f})", r["copublished_papers"],
                     br["min_node_cuts"][r["pair"]]["node_connectivity"], ds.get(r["pair"], ds.get(f"{b}-{a}")),
                     f"{SN['shared_partners']['shared'][r['pair']]} ({SN['shared_partners']['jaccard'][r['pair']]})",
                     f"{nos[a][b]} / {nos[b][a]}"])
    story.append(table(rows, [WIDTH * 0.1, WIDTH * 0.16, WIDTH * 0.12, WIDTH * 0.1, WIDTH * 0.1, WIDTH * 0.2,
                              WIDTH * 0.22], align_right=(1, 2, 3, 4, 5, 6)))
    story += bullets([f"<b>{escape(f['title'])}.</b> {escape(f['evidence'])} <i>Caveat:</i> {escape(f['caveat'])}"
                      for f in SN["findings"][1:4]])
    story.append(fig(os.path.join(C.CHARTS_DIR, "f6_institution_structure.png"), WIDTH * 0.8, caption=
                     f"Figure 5. (a) Co-author links within (diagonal) and between institutes. (b) Share of "
                     f"cross-institute author pairs still connected, and giant-component size, when authors are removed "
                     f"by betweenness or at random. Within-institute distances: IIITA {ds['IIITA-IIITA']}, ABV "
                     f"{ds['ABV-ABV']}, IIITB {ds['IIITB-IIITB']} steps; network diameter {co['giant_diameter']}."))

    # ── Indian connectivity ──
    story.append(P("7. Indian connectivity: citation flow and collaboration", H2))
    rows = [["Institution", "Cites received / given", "Ratio", "Top 5 Indian institutes citing us",
             "Top 3 co-author partners"]]
    ind = o["indian"]
    for inst in C.INST_NAMES:
        f = flow[inst]
        tp = A.top_partners(ind, inst, 3)
        rows.append([inst, f"{f['in_citations']:,} / {f['out_citations']:,}", f["impact_ratio"],
                     "; ".join(f"{x['name']} ({x['count']})" for x in f["top_citing_institutes"][:5]),
                     "; ".join(f"{r.partner_inst} ({r.shared_papers}, {r.partner_cluster})" for r in tp.itertuples())])
    story.append(table(rows, [WIDTH * 0.12, WIDTH * 0.12, WIDTH * 0.06, WIDTH * 0.38, WIDTH * 0.32],
                       align_right=(1, 2)))
    cl = A.cluster_links(ind)
    story.append(P("Co-authorship by partner cluster (shared papers, all three institutes): " + ", ".join(
        f"{c} {int(cl[c].sum())}" for c in cl.sum().sort_values(ascending=False).index[:8]) +
        f". Cross-cluster links (partner not an IIIT) dominate. Topic similarity (Jaccard over OpenAlex subfields) is "
        f"highest between IIITA and IIITB "
        f"({o['jaccard'].iloc[0]['jaccard_similarity']}) and with IIIT Hyderabad for IIITB, yet it does not predict "
        f"collaboration volume.", CAP))
    story.append(fig(os.path.join(C.CHARTS_DIR, "f5_connectivity.png"), WIDTH * 0.8, caption=
                     "Figure 6. (a) Yearly ratio of citations received from / given to other Indian institutes. "
                     "(b) Co-authored papers vs citations received per partner institute."))

    # ── limitations & contributions ──
    story.append(P("8. Limitations", H2))
    story += bullets([
        "OpenAlex affiliation and reference coverage is incomplete, especially before 2018. Author identity trusts "
        "OpenAlex IDs and merges further only with co-author evidence, so some people may remain split; with a "
        f"name-only rule there would be {SN['identity_sensitivity']['name_only']['inter_institute_links']} instead of "
        f"{SN['identity_sensitivity']['conservative']['inter_institute_links']} inter-institute links. The "
        "core-faculty rule is a heuristic, not an official faculty list.",
        "Networks are 2016–2026 snapshots; node cuts and robustness describe that snapshot, and an author's 'main' "
        "institute is where most of their papers are.",
        "IIIT Bangalore authors rarely state a department, so most of its departments are inferred from the research "
        "field; CORE ranks cover only venues on the ICORE list.",
        "Citation counts are taken at collection time; 2025–26 papers are excluded from normalised scores. The "
        "regression shows associations, not causal effects."])
    story.append(P("9. Conclusions", H2))
    ct = I["connectivity"]["collab_vs_citation"]
    story += bullets([
        "All three IIITs roughly doubled their output in ten years while moving to better journals, so the growth is "
        "not a volume-only effect. Differences in raw citations between them largely disappear once papers are "
        "compared with others of the same year, field and type.",
        "Citation success depends far more on where a paper is published (Q1 journal vs conference) and how large the "
        "team is than on whether it has foreign co-authors.",
        f"Both networks show three largely separate research systems: internal citations are almost all "
        f"self-citations, and only {mx['inter_papers']} papers connect two of the IIITs — "
        f"{mx['inter_papers_with_multi_affiliated_author']} of them through people placed at two institutes. IIITB is "
        f"attached to the others through {br['min_node_cuts']['IIITA-IIITB']['node_connectivity']} authors. "
        f"Their Indian links run through NITs, IITs and nearby universities, and partners that co-author with an "
        f"institute supply most of its Indian citations "
        f"({min(x['share_in_cites_from_coauthor_partners_pct'] for x in ct.values())}–"
        f"{max(x['share_in_cites_from_coauthor_partners_pct'] for x in ct.values())}%).",
        "Implication: joint IIIT projects and targeted partnerships are the clearest lever for visibility; topic "
        "overlap alone does not create collaboration."])
    guide = [["Required panel / analysis", "Dashboard page"],
             ["Publication trend · quartile (Q1–Q4) · CORE rank · research areas · top-10 cited papers with DOIs",
              "All institutions"],
             ["Faculty list (name, department, h-index, papers) · sortable performance table · h-index histogram · "
              "top-5 journals and conferences · departments", "IIIT Allahabad / ABV-IIITM Gwalior / IIIT Bangalore"],
             ["Directed citation graph (D3) · PageRank top-10 · in-degree distribution", "Citation network"],
             ["Interactive co-authorship graph (filters, search, author details, Louvain colouring)", "Network explorer"],
             ["Network properties · log-binned degree distribution · centralities · communities · robustness · null models",
              "Network analysis"],
             ["Per-institute structure · links, distances and citations between institutes · bridges · node cuts",
              "Institution comparison"],
             ["Citation in/out-flow per year · impact ratio · top-10 citing institutes and papers · partner ranking "
              "with cross-cluster flags · Jaccard similarity", "Indian connectivity"],
             ["Structural findings · growth and Q1 tests · normalised impact · regression · methods · limitations",
              "Findings & modelling"],
             ["Degree & paths · log-binning · Erdős–Rényi · ring/star path lengths", "Course connections"]]
    story.append(KeepTogether([P("10. Dashboard guide", H2),
                               P(" · ".join(f"<b>{page}</b>: {what}" for what, page in guide[1:]), CAP)]))
    rows, shares = contribution_table()
    story.append(KeepTogether([
        P("11. Individual contributions", H2),
        table(rows, [WIDTH * 0.1, WIDTH * 0.62, WIDTH * 0.07, WIDTH * 0.07, WIDTH * 0.06, WIDTH * 0.08],
              align_right=(2, 3, 4, 5)),
        P(f"Effort = hours × mean(difficulty, learning curve), both on a 1–5 scale. Totals: {shares} — an equal "
          "three-way split. Every part was discussed, cross-checked and reviewed by all three members.", CAP)]))

    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=28, bottomMargin=32,
                            title="Group 10 - Research Mapping of Three IIITs", author="Titan Mandal (Group 10)",
                            subject="DPCN 2026 statistics report")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"  Saved {OUT} ({os.path.getsize(OUT) / 1024:.0f} KB)")


if __name__ == "__main__":
    build()
