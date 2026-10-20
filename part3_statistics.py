"""
DPCN 2026 - Group 10 - Part 3: Statistics report material
==========================================================
Reads the outputs of part1b + part2 and writes

  outputs/charts/*.png           figures for the <=10-slide statistics report
  outputs/group10_statistics_summary.md  every number the report needs, in tables

Report coverage (instruction note section 8):
  publication trend, Q1 fraction, h-index distribution, top-5 journals,
  top-10 cited papers, research areas, citation network (PageRank top-10,
  in-degree distribution, cross-institute flow), authorship network
  (degree & betweenness, communities) + departments, CORE ranks,
  Indian connectivity and topic similarity.

Usage:
    python part3_statistics.py
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import group10_analysis as A
import group10_common as C

INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"
COLORS = C.INST_COLORS

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linestyle": "-", "grid.linewidth": 0.6,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "legend.frameon": False, "legend.fontsize": 9, "font.size": 10,
    "savefig.bbox": "tight", "savefig.dpi": 160, "lines.linewidth": 2,
})


def save(fig, name):
    path = os.path.join(C.CHARTS_DIR, name)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def short(s, n=42):
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + "…"


# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────

def chart_trend(df):
    t = A.publication_trend(df).pivot(index="year", columns="institution", values="papers").fillna(0)
    t = t.reindex(range(C.START_YEAR, C.END_YEAR + 1), fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for inst in C.INST_NAMES:
        y = t[inst].values
        ax.plot(t.index[:-1], y[:-1], color=COLORS[inst], marker="o", ms=5, label=inst)
        ax.plot(t.index[-2:], y[-2:], color=COLORS[inst], ls=":", marker="o", ms=5, mfc=SURFACE)
        ax.annotate(f"{int(y[-2])}", (t.index[-2], y[-2]), xytext=(0, 7), textcoords="offset points",
                    ha="center", fontsize=8, color=INK2)
    ax.set_title("Publications per year (journal + conference)")
    ax.set_xticks(t.index)
    ax.set_ylabel("Papers")
    ax.grid(axis="x", visible=False)
    ax.text(C.PARTIAL_YEAR, ax.get_ylim()[1] * 0.97, "2026 partial", ha="center", fontsize=8, color=MUTED)
    ax.legend(loc="upper left")
    save(fig, "01_publication_trend.png")


def chart_quartiles(df):
    q = A.quartile_table(df)
    pct = q.div(q.sum(axis=1), axis=0) * 100
    core = A.core_table(df)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
    for ax, tab, title, cols in [(axes[0], pct, "Journal papers by SJR quartile (%)", A.QUARTILES + ["Unranked"]),
                                 (axes[1], core.div(core.sum(axis=1), axis=0) * 100,
                                  "Conference papers by CORE rank (%)", A.CORE_RANKS + ["Unranked"])]:
        left = np.zeros(len(tab))
        for col, color in zip(cols, C.TIER_COLORS):
            vals = tab[col].values
            ax.barh(tab.index, vals, left=left, color=color, edgecolor=SURFACE, linewidth=2,
                    height=0.55, label=col)
            for i, (v, l) in enumerate(zip(vals, left)):
                if v >= 10:
                    ax.text(l + v / 2, i, f"{v:.0f}", ha="center", va="center", fontsize=8,
                            color="white" if col in cols[:2] else INK)
            left += vals
        ax.set_title(title)
        ax.set_xlim(0, 100)
        if ax is axes[0]:
            ax.invert_yaxis()       # shared y-axis: invert once
        ax.grid(axis="y", visible=False)
        ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    save(fig, "02_quartile_core_distribution.png")


def chart_hindex(fac):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    for ax, inst in zip(axes, C.INST_NAMES):
        f = fac[(fac["institution"] == inst) & fac["is_core_faculty"]]
        h = f["h_index"].values
        ax.hist(h, bins=range(0, max(h.max() if len(h) else 1, 1) + 2), color=COLORS[inst],
                edgecolor=SURFACE, linewidth=2)
        if len(h):
            ax.axvline(np.median(h), color=INK2, lw=1)
            ax.text(np.median(h), ax.get_ylim()[1] * 0.92, f" median {np.median(h):.0f}",
                    fontsize=8, color=INK2)
        ax.set_title(f"{inst} (n={len(f)})", fontsize=10)
        ax.set_xlabel("h-index (papers 2016–2026)")
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Core faculty")
    fig.suptitle("h-index distribution of core faculty", x=0.01, ha="left", fontweight="bold")
    save(fig, "03_hindex_distribution.png")


def chart_top_journals(df):
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.2))
    for ax, inst in zip(axes, C.INST_NAMES):
        t = A.top_venues(df, inst, "journal", 5)
        ax.barh([short(n, 38) for n in t["journal_name"]], t["papers"], color=COLORS[inst], height=0.55)
        for i, (p, q) in enumerate(zip(t["papers"], t["quartile"])):
            ax.text(p, i, f" {p}  {q}", va="center", fontsize=8, color=INK2)
        ax.invert_yaxis()
        ax.set_title(inst, fontsize=10)
        ax.set_xlabel("Papers")
        ax.grid(axis="y", visible=False)
    fig.suptitle("Top 5 journals per institution (label: papers, SJR quartile)",
                 x=0.01, ha="left", fontweight="bold")
    save(fig, "04_top5_journals.png")


def chart_most_cited(df):
    t = A.most_cited(df, 10)
    fig, ax = plt.subplots(figsize=(15, 4.4))
    ax.axis("off")
    ax.set_title("Top 10 most-cited papers 2016–2026 (OpenAlex citations)")
    rows = [[i + 1, short(r.title, 70), short(r.institution, 34), short(r.journal_name, 34),
             int(r.year), f"{r.citations:,}", "yes" if r.n_authors > C.HYPERAUTHOR_THRESHOLD else ""]
            for i, r in t.iterrows()]
    tbl = ax.table(cellText=rows, colLabels=["#", "Title", "Institution", "Venue", "Year", "Citations",
                                             f">{C.HYPERAUTHOR_THRESHOLD} authors"],
                   colWidths=[0.03, 0.42, 0.16, 0.2, 0.05, 0.07, 0.07], loc="center", cellLoc="left")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.5)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_facecolor("#f1f0ec" if r == 0 else SURFACE)
        if r == 0:
            cell.set_text_props(weight="bold")
    save(fig, "05_most_cited_papers.png")


def chart_research_areas(df):
    t = A.research_areas(df, "field", 8)
    fig, ax = plt.subplots(figsize=(12, 4.6))
    x = np.arange(len(t.columns))
    w = 0.26
    for k, inst in enumerate(C.INST_NAMES):
        ax.bar(x + (k - 1) * w, t.loc[inst].values, width=w - 0.02, color=COLORS[inst], label=inst)
    ax.set_xticks(x)
    ax.set_xticklabels([short(c, 22) for c in t.columns], rotation=20, ha="right")
    ax.set_ylabel("% of the institution's papers")
    ax.set_title("Research area breakdown (OpenAlex field of each paper's primary topic)")
    ax.grid(axis="x", visible=False)
    ax.legend()
    save(fig, "06_research_areas.png")


def chart_departments(adf, fac):
    d = A.department_breakdown(adf, fac)
    if d.empty:
        return
    piv = d.pivot(index="department", columns="institution", values="papers").fillna(0)
    piv = piv.reindex(columns=C.INST_NAMES, fill_value=0).sort_values(C.INST_NAMES[0])
    fig, ax = plt.subplots(figsize=(11, 4.4))
    y = np.arange(len(piv))
    h = 0.26
    for k, inst in enumerate(C.INST_NAMES):
        ax.barh(y + (k - 1) * h, piv[inst].values, height=h - 0.02, color=COLORS[inst], label=inst)
    ax.set_yticks(y)
    ax.set_yticklabels(piv.index)
    ax.set_xlabel("Papers with at least one author from the department")
    ax.set_title("Department-level output")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right")
    save(fig, "07_departments.png")


def chart_citation_network(cm):
    s = cm.get("summary", {})
    dist = {int(k): v for k, v in s.get("in_degree_distribution", {}).items() if int(k) > 0}
    fig, axes = plt.subplots(1, 2, figsize=(15, 4.4), gridspec_kw={"width_ratios": [1, 1.7]})
    ax = axes[0]
    if dist:
        ax.scatter(list(dist), list(dist.values()), color=C.TIER_COLORS[1], s=30)
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.set_xlabel("In-degree (citations from papers of the 3 institutes)")
    ax.set_ylabel("Papers")
    ax.set_title(f"Internal in-degree distribution\n{s.get('internal_edges', 0):,} internal citation "
                 f"edges, {s.get('papers_cited_internally', 0):,} papers cited internally", fontsize=10)
    ax = axes[1]
    ax.axis("off")
    ax.set_title("PageRank top 10 (internal citation graph)", fontsize=10)
    rows = [[i + 1, short(t["title"], 58), short(" & ".join(t["institutions"]), 30), t["year"],
             t["in_degree"], f"{t['pagerank']:.5f}"] for i, t in enumerate(cm.get("pagerank_top10", []))]
    if rows:
        tbl = ax.table(cellText=rows, colLabels=["#", "Title", "Institution", "Year", "In-deg", "PageRank"],
                       colWidths=[0.04, 0.52, 0.22, 0.07, 0.07, 0.1], loc="center", cellLoc="left")
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1, 1.45)
        for (r, c), cell in tbl.get_celld().items():
            cell.set_edgecolor(GRID)
            cell.set_facecolor("#f1f0ec" if r == 0 else SURFACE)
    save(fig, "08_citation_network.png")


def chart_flow(flow):
    if not flow:
        return
    fig, axes = plt.subplots(1, 2, figsize=(15, 4.4), gridspec_kw={"width_ratios": [1.6, 1]})
    ax = axes[0]
    years = list(range(C.START_YEAR, C.END_YEAR + 1))
    for inst in C.INST_NAMES:
        by = flow[inst]["by_year"]
        ax.plot(years, [by[str(y)]["in"] for y in years], color=COLORS[inst], label=f"{inst} in-flow")
        ax.plot(years, [by[str(y)]["out"] for y in years], color=COLORS[inst], ls="--", lw=1.4,
                label=f"{inst} out-flow")
    ax.set_xticks(years)
    ax.set_title("Citations exchanged with other Indian institutes per year\n"
                 "solid = received (in-flow), dashed = given (out-flow)", fontsize=10)
    ax.set_ylabel("Citation links")
    ax.grid(axis="x", visible=False)
    ax.legend(fontsize=7, ncol=2)
    ax = axes[1]
    ratios = [flow[i]["impact_ratio"] or 0 for i in C.INST_NAMES]
    ax.barh(C.INST_NAMES, ratios, color=[COLORS[i] for i in C.INST_NAMES], height=0.5)
    ax.axvline(1, color=INK2, lw=1)
    for k, (r, inst) in enumerate(zip(ratios, C.INST_NAMES)):
        ax.text(r, k, f" {r:.2f}  ({flow[inst]['in_citations']:,} in / {flow[inst]['out_citations']:,} out)",
                va="center", fontsize=8, color=INK2)
    ax.set_xlim(0, max(ratios + [1]) * 1.6)
    ax.invert_yaxis()
    ax.set_title("Citation impact ratio = in-cites / out-cites", fontsize=10)
    ax.grid(axis="y", visible=False)
    save(fig, "09_citation_flow.png")


def chart_partners(indian, flow):
    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    for ax, inst in zip(axes, C.INST_NAMES):
        t = A.top_partners(indian, inst, 10)
        labels = [f"{short(p, 48)}  [{cl}]" for p, cl in zip(t["partner_inst"], t["partner_cluster"])]
        vals = t["shared_papers"].astype(int).values
        ax.barh(labels, vals, color=COLORS[inst], height=0.55)
        for k, v in enumerate(vals):
            ax.text(v, k, f" {v}", va="center", fontsize=8, color=INK2)
        ax.invert_yaxis()
        ax.set_title(inst, fontsize=10)
        ax.grid(axis="y", visible=False)
    axes[-1].set_xlabel("Co-authored papers")
    fig.suptitle("Top Indian co-authorship partners  [partner cluster]", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout()
    save(fig, "10_indian_partners.png")


def chart_authorship(am):
    nodes = am.get("nodes", {})
    if not nodes:
        return
    nd = pd.DataFrame.from_dict(nodes, orient="index")
    fig, axes = plt.subplots(1, 3, figsize=(17, 4.6))
    for ax, col, title in [(axes[0], "degree_centrality", "Degree centrality (most collaborative)"),
                           (axes[1], "betweenness_centrality", "Betweenness centrality (bridges)")]:
        t = nd.sort_values(col, ascending=False).head(10)
        ax.barh([short(n, 26) for n in t["name"]], t[col], color=[COLORS[i] for i in t["institution"]],
                height=0.55)
        ax.invert_yaxis()
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", visible=False)
    comms = am.get("communities", [])[:12]
    ax = axes[2]
    bottom = np.zeros(len(comms))
    for inst in C.INST_NAMES:
        v = np.array([c["institutions"].get(inst, 0) for c in comms])
        ax.bar([f"C{c['id']}" for c in comms], v, bottom=bottom, color=COLORS[inst], label=inst,
               edgecolor=SURFACE, linewidth=1)
        bottom += v
    s = am.get("summary", {})
    ax.set_title(f"Largest Louvain communities ({s.get('communities')} total, "
                 f"modularity {s.get('modularity')})", fontsize=10)
    ax.set_ylabel("Authors")
    ax.grid(axis="x", visible=False)
    ax.legend(fontsize=8)
    fig.suptitle("Co-authorship network of the three institutes", x=0.01, ha="left", fontweight="bold")
    save(fig, "11_authorship_network.png")


def chart_jaccard(jac):
    if jac.empty:
        return
    t = jac.sort_values("jaccard_similarity", ascending=True).tail(16)
    labels = [f"{short(a, 18)} ↔ {short(b, 30)}" for a, b in zip(t["entity_a"], t["entity_b"])]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    colors = [COLORS.get(a, MUTED) for a in t["entity_a"]]
    ax.barh(labels, t["jaccard_similarity"], color=colors, height=0.55)
    for k, (j, w) in enumerate(zip(t["jaccard_similarity"], t["weighted_jaccard"])):
        ax.text(j, k, f" {j:.2f} (weighted {w:.2f})", va="center", fontsize=8, color=INK2)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Jaccard similarity of research subfields (subfields with ≥1% of output)")
    ax.set_title("Research-topic similarity: our institutes vs each other and key Indian partners")
    ax.grid(axis="y", visible=False)
    save(fig, "12_topic_jaccard.png")


def chart_citation_age(df):
    t = A.citation_age(df).pivot(index="year", columns="institution", values="median")
    fig, ax = plt.subplots(figsize=(10, 4))
    for inst in C.INST_NAMES:
        ax.plot(t.index, t[inst], color=COLORS[inst], marker="o", ms=4, label=inst)
    ax.set_title("Median citations per paper by publication year (recent papers have had less time)")
    ax.set_xticks(t.index)
    ax.set_ylabel("Median citations")
    ax.grid(axis="x", visible=False)
    ax.legend()
    save(fig, "13_citation_age.png")


# ─────────────────────────────────────────────
# SUMMARY MARKDOWN
# ─────────────────────────────────────────────

def md_table(df, floatfmt=None):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(v).replace("|", "/") for v in r.values) + " |")
    return "\n".join(out)


def write_summary(o):
    df, fac, flow, cm, am = o["df"], o["fac"], o["flow"], o["cite_metrics"], o["auth_metrics"]
    L = ["# Group 10 – Statistics summary (IIIT Allahabad, ABV-IIITM Gwalior, IIIT Bangalore)", "",
         "Source: OpenAlex (collected 2026), Scimago SJR (year-matched), ICORE2026. Journal and "
         "conference papers only; 2026 is a partial year.", ""]
    s = A.institution_summary(df, fac)
    L += ["## Institution overview", "", md_table(s.T.reset_index().rename(columns={"index": "metric"})), ""]
    trend = A.publication_trend(df).pivot(index="year", columns="institution", values="papers").fillna(0).astype(int)
    L += ["## Publication trend", "", md_table(trend.reset_index()), ""]
    L += ["## Journal quartiles (papers)", "", md_table(A.quartile_table(df).reset_index()), ""]
    L += ["## Conference CORE ranks (papers)", "", md_table(A.core_table(df).reset_index()), ""]
    for inst in C.INST_NAMES:
        L += [f"## Top 5 journals – {inst}", "", md_table(A.top_venues(df, inst, "journal", 5)), ""]
    L += ["## Top 10 most-cited papers", "", md_table(A.most_cited(df, 10)), ""]
    L += ["## Research areas (% of papers per OpenAlex field)", "",
          md_table(A.research_areas(df, "field", 8).reset_index()), ""]
    dep = A.department_breakdown(o["adf"], fac)
    if not dep.empty:
        L += ["## Departments", "", md_table(dep.round(1)), ""]
    hs = (fac[fac["is_core_faculty"]].groupby("institution")["h_index"]
          .describe()[["count", "mean", "25%", "50%", "75%", "max"]].round(1).reset_index())
    L += ["## Core-faculty h-index distribution (papers 2016–2026)", "", md_table(hs), ""]
    for inst in C.INST_NAMES:
        L += [f"## Top 10 faculty by h-index – {inst}", "",
              md_table(A.faculty_list(fac, inst).head(10)[["name", "department", "papers", "citations",
                                                           "h_index", "h_index_lifetime_openalex"]]), ""]
    if cm:
        L += ["## Citation network (internal)", "", md_table(pd.DataFrame([cm["summary"]]).drop(
            columns=["in_degree_distribution", "edge_types"]).T.reset_index()), "",
            md_table(pd.DataFrame(cm["pagerank_top10"])[["title", "institutions", "year", "in_degree",
                                                          "pagerank", "citations"]]), ""]
    if flow:
        rows = [{"institution": i, "in_citations": f["in_citations"], "out_citations": f["out_citations"],
                 "impact_ratio": f["impact_ratio"], "citing_works": f["in_citing_works"],
                 "cited_works": f["out_cited_works"]} for i, f in flow.items()]
        L += ["## Citation flow with other Indian institutes", "", md_table(pd.DataFrame(rows)), ""]
        for inst in C.INST_NAMES:
            L += [f"### Top 10 Indian institutes citing {inst}", "",
                  md_table(pd.DataFrame(flow[inst]["top_citing_institutes"])[["name", "cluster", "count"]]), ""]
    if am:
        L += ["## Authorship network (internal)", "", md_table(pd.DataFrame([am["summary"]]).drop(
            columns=["edge_scopes"]).T.reset_index()), ""]
        nd = pd.DataFrame.from_dict(am["nodes"], orient="index")
        for col in ("degree_centrality", "betweenness_centrality"):
            L += [f"### Top 10 by {col}", "", md_table(nd.sort_values(col, ascending=False).head(10)[
                ["name", "institution", "department", col, "community"]]), ""]
        L += ["### Largest communities", "", md_table(pd.DataFrame(am["communities"][:10])), ""]
        L += ["### Hub authors (bridge most Indian partner institutes)", "",
              md_table(pd.DataFrame(am["hub_authors"][:10])[["name", "institution",
                                                             "external_indian_partner_institutes",
                                                             "betweenness_centrality"]]), ""]
    if not o["indian"].empty:
        L += ["## Co-authorship by partner cluster (shared papers)", "",
              md_table(A.cluster_links(o["indian"]).reset_index()), ""]
    if not o["jaccard"].empty:
        L += ["## Topic similarity (Jaccard on OpenAlex subfields)", "",
              md_table(o["jaccard"][["entity_a", "entity_b", "comparison_type", "shared_papers",
                                     "jaccard_similarity", "weighted_jaccard", "top_shared_subfields"]]), ""]
    with open(C.SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"  Saved {C.SUMMARY_MD}")


def main():
    print("=" * 65)
    print(" DPCN 2026 - Group 10 - Part 3: Statistics & charts")
    print("=" * 65)
    o = A.load_outputs()
    if o["df"].empty:
        print("ERROR: run part1b_enrich_data.py and part2_networks.py first.")
        sys.exit(1)
    os.makedirs(C.CHARTS_DIR, exist_ok=True)
    df, fac = o["df"], o["fac"]
    chart_trend(df)
    chart_quartiles(df)
    chart_hindex(fac)
    chart_top_journals(df)
    chart_most_cited(df)
    chart_research_areas(df)
    chart_departments(o["adf"], fac)
    chart_citation_network(o["cite_metrics"])
    chart_flow(o["flow"])
    chart_partners(o["indian"], o["flow"])
    chart_authorship(o["auth_metrics"])
    chart_jaccard(o["jaccard"])
    chart_citation_age(df)
    write_summary(o)
    print("\n" + A.institution_summary(df, fac).set_index("institution").T.to_string())
    print("=" * 65)
    print(" Part 3 complete. Next: python part4_dashboard.py  /  streamlit run app.py")
    print("=" * 65)


if __name__ == "__main__":
    main()
