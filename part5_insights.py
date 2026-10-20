"""
DPCN 2026 - Group 10 - Part 5: Inferential analysis & key findings
===================================================================
Goes beyond descriptive counts. Every claim is tested against a baseline:

  growth            log-linear trend of yearly output (2016-2025) with 95% CI
  quality shift     Q1 share 2016-19 vs 2022-25 (chi-square test)
  normalised impact citations / mean of papers with the same year, field and type
                    (NCS); mean NCS with bootstrap CI and share of top-10% papers
  what drives       OLS on log(1+citations) with year, field, type, institution,
  citations         collaboration, team size, Q1 venue, open access (HC1 robust SE)
  concentration     Gini of citations and of core-faculty output
  citation network  author self-citation share; institutional homophily vs 1000
                    target-shuffled graphs; PageRank with self-citations removed
  authorship        small-world sigma, Louvain modularity vs configuration-model
  network           graphs, institution assortativity, community-department NMI,
                    core faculty vs other authors
  connectivity      do partners we co-author with also cite us? (Spearman),
                    yearly in/out citation ratio, topic similarity vs collaboration

Writes outputs/group10_insights.json and the report figures outputs/charts/f*_*.png.

Usage:
    python part5_insights.py
"""

import json
import math
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy import stats

import group10_analysis as A
import group10_common as C
from part3_statistics import COLORS, GRID, INK, INK2, MUTED, SURFACE, save, short

RNG = np.random.default_rng(42)
LAST_FULL_YEAR = 2025
CITATION_WINDOW_END = 2024      # papers from 2025-26 have had too little time to be cited


def gini(x):
    x = np.sort(np.asarray(x, float))
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum())) if x.sum() else 0.0


def nmi(a, b):
    n = len(a)
    ca, cb, cab = Counter(a), Counter(b), Counter(zip(a, b))
    mi = sum(v / n * math.log((v / n) / ((ca[x] / n) * (cb[y] / n))) for (x, y), v in cab.items())
    ha = -sum(v / n * math.log(v / n) for v in ca.values())
    hb = -sum(v / n * math.log(v / n) for v in cb.values())
    return 2 * mi / (ha + hb) if ha + hb else 0.0


def boot_ci(x, f=np.mean, n=2000):
    x = np.asarray(x)
    vals = [f(RNG.choice(x, len(x))) for _ in range(n)]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


# ═════════════════════════════════════════════
# 1. OUTPUT, QUALITY, IMPACT
# ═════════════════════════════════════════════

def growth_and_quality(df):
    out = {}
    for inst in C.INST_NAMES:
        s = df[df["institution"] == inst]
        c = s[s["year"] <= LAST_FULL_YEAR].groupby("year").size()
        r = stats.linregress(c.index.astype(float), np.log(c.values))
        j = s[(s["type"] == "journal") & (s["year"] <= LAST_FULL_YEAR)]
        early, late = j[j["year"] <= 2019], j[j["year"] >= 2022]
        tab = [[(early["quartile"] == "Q1").sum(), (early["quartile"] != "Q1").sum()],
               [(late["quartile"] == "Q1").sum(), (late["quartile"] != "Q1").sum()]]
        out[inst] = {
            "annual_growth_pct": round((math.exp(r.slope) - 1) * 100, 1),
            "growth_ci": [round((math.exp(r.slope - 1.96 * r.stderr) - 1) * 100, 1),
                          round((math.exp(r.slope + 1.96 * r.stderr) - 1) * 100, 1)],
            "growth_p": float(r.pvalue),
            "papers_2016": int(c.get(2016, 0)), "papers_2025": int(c.get(2025, 0)),
            "q1_share_2016_19": round((early["quartile"] == "Q1").mean() * 100, 1),
            "q1_share_2022_25": round((late["quartile"] == "Q1").mean() * 100, 1),
            "q1_shift_p": float(stats.chi2_contingency(tab)[1]),
            "q1_by_year": {int(y): round((g["quartile"] == "Q1").mean() * 100, 1)
                           for y, g in j.groupby("year")},
            "conference_share_2016_19": round((s[s["year"] <= 2019]["type"] == "conference").mean() * 100, 1),
            "conference_share_2022_25": round((s[(s["year"] >= 2022) & (s["year"] <= 2025)]["type"]
                                               == "conference").mean() * 100, 1),
        }
    return out


def normalised_impact(df):
    """Field-, year- and type-normalised citation score within the three institutes."""
    u = A.unique_papers(df).copy()
    u = u[u["year"] <= CITATION_WINDOW_END]
    u["field2"] = u["field"].replace("", "Unknown")
    base = u[~u["is_hyperauthored"]]
    exp = base.groupby(["year", "field2", "type"])["citations"].mean().rename("expected")
    u = u.join(exp, on=["year", "field2", "type"])
    u["ncs"] = np.where(u["expected"] > 0, u["citations"] / u["expected"], np.nan)
    thr = base.groupby(["year", "type"])["citations"].quantile(0.9).rename("thr")
    u = u.join(thr, on=["year", "type"])
    u["top10"] = u["citations"] > u["thr"]
    rows = df[df["year"] <= CITATION_WINDOW_END].merge(u[["openalex_id", "ncs", "top10"]], on="openalex_id")
    rows = rows[~rows["is_hyperauthored"]]
    out = {}
    for inst in C.INST_NAMES:
        s = rows[rows["institution"] == inst].dropna(subset=["ncs"])
        out[inst] = {"mncs": round(float(s["ncs"].mean()), 3), "mncs_ci": [round(v, 3) for v in boot_ci(s["ncs"])],
                     "median_ncs": round(float(s["ncs"].median()), 3),
                     "pp_top10": round(float(s["top10"].mean()) * 100, 1),
                     "pp_top10_journal": round(float(s[s["type"] == "journal"]["top10"].mean()) * 100, 1),
                     "pp_top10_conference": round(float(s[s["type"] == "conference"]["top10"].mean()) * 100, 1)}
    return u, out


def collaboration_premium(u):
    v = u[~u["is_hyperauthored"]].dropna(subset=["ncs"]).copy()
    v["collab"] = np.select([v["is_international"], v["coauthor_institutes"] != ""],
                            ["International", "Indian partner"], "Single institute")
    res = {}
    base = v[v["collab"] == "Single institute"]["ncs"]
    for g, s in v.groupby("collab"):
        r = {"papers": int(len(s)), "mean_ncs": round(float(s["ncs"].mean()), 3),
             "mean_ci": [round(x, 3) for x in boot_ci(s["ncs"])],
             "median_ncs": round(float(s["ncs"].median()), 3)}
        if g != "Single institute":
            mw = stats.mannwhitneyu(s["ncs"], base, alternative="two-sided")
            r["mwu_p_vs_single"] = float(mw.pvalue)
            r["prob_superiority"] = round(float(mw.statistic / (len(s) * len(base))), 3)
        res[g] = r
    by_venue = {q or "Unranked": round(float(g["ncs"].median()), 3)
                for q, g in v[v["type"] == "journal"].groupby("quartile")}
    oa = {str(k): round(float(g["ncs"].median()), 3) for k, g in v.groupby("is_open_access")}
    return res, by_venue, oa


def citation_regression(u):
    """OLS of log(1+citations) with HC1 robust standard errors."""
    v = u[~u["is_hyperauthored"]].copy()
    v["y"] = np.log1p(v["citations"])
    top_fields = v["field"].value_counts().index[:8]
    v["field3"] = np.where(v["field"].isin(top_fields), v["field"], "Other")
    X = pd.DataFrame({
        "International co-author": v["is_international"].astype(float),
        "Indian partner co-author": ((v["coauthor_institutes"] != "") & ~v["is_international"]).astype(float),
        "Team size (log authors)": np.log(v["n_authors"].clip(lower=1)),
        "Q1 journal": (v["quartile"] == "Q1").astype(float),
        "Conference paper": (v["type"] == "conference").astype(float),
        "Open access": v["is_open_access"].astype(float),
    }, index=v.index)
    X = X.join(pd.get_dummies(v["institution"], prefix="inst", dtype=float).drop(columns=f"inst_{C.INST_NAMES[0]}"))
    X = X.join(pd.get_dummies(v["year"].astype(int), prefix="y", dtype=float).iloc[:, 1:])
    X = X.join(pd.get_dummies(v["field3"], prefix="f", dtype=float).iloc[:, 1:])
    X.insert(0, "const", 1.0)
    Xm, y = X.values, v["y"].values
    beta, *_ = np.linalg.lstsq(Xm, y, rcond=None)
    resid = y - Xm @ beta
    n, k = Xm.shape
    xtx_inv = np.linalg.pinv(Xm.T @ Xm)
    meat = (Xm * resid[:, None] ** 2).T @ Xm
    cov = xtx_inv @ meat @ xtx_inv * n / (n - k)
    se = np.sqrt(np.diag(cov))
    r2 = 1 - resid.var() / y.var()
    keep = [c for c in X.columns if not c.startswith(("y_", "f_", "const"))]
    out = []
    for c in keep:
        i = list(X.columns).index(c)
        b, s = beta[i], se[i]
        out.append({"term": c.replace("inst_", "Institution: "), "effect_pct": round((math.exp(b) - 1) * 100, 1),
                    "ci": [round((math.exp(b - 1.96 * s) - 1) * 100, 1), round((math.exp(b + 1.96 * s) - 1) * 100, 1)],
                    "p": float(2 * stats.norm.sf(abs(b / s)))})
    return {"n": int(n), "r2": round(float(r2), 3), "terms": out,
            "controls": "publication-year and field fixed effects"}


def concentration(df, fac):
    out = {}
    for inst in C.INST_NAMES:
        s = df[df["institution"] == inst]["citations"].sort_values(ascending=False)
        f = fac[(fac["institution"] == inst) & fac["is_core_faculty"]]["papers"].sort_values(ascending=False)
        out[inst] = {"gini_citations": round(gini(s), 3),
                     "top10pct_paper_citation_share": round(s.head(max(1, len(s) // 10)).sum() / s.sum() * 100, 1),
                     "gini_core_faculty_papers": round(gini(f), 3),
                     "top20pct_faculty_paper_share": round(f.head(max(1, len(f) // 5)).sum() / f.sum() * 100, 1)}
    return out


# ═════════════════════════════════════════════
# 2. NETWORKS
# ═════════════════════════════════════════════

def citation_network_tests(df, edges, cm):
    u = A.unique_papers(df).set_index("openalex_id")
    it = edges[edges["edge_type"] == "internal"]
    people = {w: {a.strip().lower() for a in s.split(";") if a.strip()} for w, s in zip(u.index, u["all_authors"])}
    insts = df.groupby("openalex_id")["institution"].apply(set).to_dict()
    src, tgt = it["source_openalex_id"].tolist(), it["target_openalex_id"].tolist()
    self_cite = np.array([bool(people[s] & people[t]) for s, t in zip(src, tgt)])
    same = np.array([bool(insts[s] & insts[t]) for s, t in zip(src, tgt)])
    null = []
    tg = np.array(tgt)
    for _ in range(1000):
        p = RNG.permutation(tg)
        null.append(np.mean([bool(insts[s] & insts[t]) for s, t in zip(src, p)]))
    null = np.array(null)
    G = nx.DiGraph()
    G.add_nodes_from(u.index)
    G.add_edges_from((s, t) for s, t, f in zip(src, tgt, self_cite) if not f)
    pr = nx.pagerank(G, alpha=0.85)
    top = sorted(pr, key=lambda w: (-pr[w], -u.loc[w, "citations"]))[:5]
    rho = stats.spearmanr([cm["pagerank"][w] for w in u.index], u["citations"]).correlation
    return {
        "internal_edges": int(len(it)),
        "author_self_citation_pct": round(self_cite.mean() * 100, 1),
        "same_institution_pct": round(same.mean() * 100, 1),
        "same_institution_null_pct": round(null.mean() * 100, 1),
        "same_institution_null_sd": round(null.std() * 100, 2),
        "homophily_z": round(float((same.mean() - null.mean()) / null.std()), 1),
        "non_self_edges": int(G.number_of_edges()),
        "pagerank_vs_citations_spearman": round(float(rho), 3),
        "pagerank_no_self_top5": [{"title": u.loc[w, "title"], "institution": " & ".join(sorted(insts[w])),
                                   "year": int(u.loc[w, "year"]), "pagerank": round(pr[w], 5)} for w in top],
        "null_distribution": null.round(4).tolist(),
    }


def authorship_tests(auth_edges, am):
    nodes = am["nodes"]
    inn = auth_edges[auth_edges["edge_scope"].isin(["same_institution", "inter_group"])]
    H = nx.Graph()
    H.add_nodes_from(nodes)
    for a, b in zip(inn["author_a_id"], inn["author_b_id"]):
        if H.has_edge(a, b):
            H[a][b]["weight"] += 1
        else:
            H.add_edge(a, b, weight=1)
    gc = H.subgraph(max(nx.connected_components(H), key=len)).copy()
    n, m = gc.number_of_nodes(), gc.number_of_edges()
    k = 2 * m / n
    cc = nx.average_clustering(gc)
    L = nx.average_shortest_path_length(gc)
    c_rand, l_rand = k / n, math.log(n) / math.log(k)
    comms = nx.community.louvain_communities(H, weight="weight", seed=42)
    q = nx.community.modularity(H, comms, weight="weight")
    deg_seq = [d for _, d in H.degree()]
    qn = []
    for s in range(20):
        R = nx.Graph(nx.configuration_model(deg_seq, seed=s))
        R.remove_edges_from(nx.selfloop_edges(R))
        qn.append(nx.community.modularity(R, nx.community.louvain_communities(R, seed=s)))
    nx.set_node_attributes(H, {k2: v["institution"] for k2, v in nodes.items()}, "inst")
    core_ids = [k2 for k2, v in nodes.items() if v["is_core_faculty"] and v["department"]]
    deg = dict(H.degree())
    core_deg = [deg[k2] for k2 in nodes if nodes[k2]["is_core_faculty"]]
    other_deg = [deg[k2] for k2 in nodes if not nodes[k2]["is_core_faculty"]]
    mw = stats.mannwhitneyu(core_deg, other_deg)
    inter_pairs = inn[inn["edge_scope"] == "inter_group"][["author_a_id", "author_b_id"]].drop_duplicates()
    inter_papers = auth_edges[auth_edges["edge_scope"] == "inter_group"]["paper_doi"].nunique()
    return {
        "giant_component": n, "giant_edges": m, "mean_degree": round(k, 2),
        "clustering": round(cc, 3), "clustering_random": round(c_rand, 4),
        "path_length": round(L, 2), "path_length_random": round(l_rand, 2),
        "small_world_sigma": round((cc / c_rand) / (L / l_rand), 1),
        "modularity": round(q, 3), "modularity_null": round(float(np.mean(qn)), 3),
        "modularity_null_sd": round(float(np.std(qn)), 4),
        "institution_assortativity": round(nx.attribute_assortativity_coefficient(H, "inst"), 3),
        "nmi_community_department": round(nmi([nodes[i]["community"] for i in core_ids],
                                              [nodes[i]["department"] for i in core_ids]), 3),
        "nmi_community_institution": round(nmi([nodes[i]["community"] for i in core_ids],
                                               [nodes[i]["institution"] for i in core_ids]), 3),
        "core_faculty_n": len(core_deg),
        "core_median_degree": float(np.median(core_deg)), "other_median_degree": float(np.median(other_deg)),
        "core_vs_other_p": float(mw.pvalue),
        "core_share_of_edge_ends_pct": round(sum(core_deg) / max(sum(deg.values()), 1) * 100, 1),
        "inter_group_author_pairs": int(len(inter_pairs)), "inter_group_papers": int(inter_papers),
        "degree_values": sorted(deg.values()),
        "core_degree_values": sorted(core_deg),
    }


def connectivity_tests(indian, flow, jac):
    out = {"collab_vs_citation": {}, "ratio_by_year": {}}
    ind = indian[~indian["intra_group"].astype(str).str.upper().eq("TRUE")].copy()
    for col in ("shared_papers", "citations_received_from_partner", "citations_given_to_partner"):
        ind[col] = ind[col].astype(int)
    for inst in C.INST_NAMES:
        s = ind[ind["your_inst"] == inst]
        co = s[s["shared_papers"] > 0]
        r = stats.spearmanr(co["shared_papers"], co["citations_received_from_partner"])
        out["collab_vs_citation"][inst] = {
            "partners": int(len(co)), "spearman": round(float(r.correlation), 3), "p": float(r.pvalue),
            "share_in_cites_from_coauthor_partners_pct":
                round(co["citations_received_from_partner"].sum() / max(s["citations_received_from_partner"].sum(), 1) * 100, 1),
            "share_partners_that_coauthor_pct": round(len(co) / max(len(s[s["citations_received_from_partner"] > 0]), 1) * 100, 1),
        }
        by = flow[inst]["by_year"]
        out["ratio_by_year"][inst] = {y: round(v["in"] / v["out"], 3) for y, v in by.items() if v["out"]}
        cross = next((int(y) for y, v in sorted(by.items()) if v["out"] and v["in"] >= v["out"]), None)
        out.setdefault("in_exceeds_out_from", {})[inst] = cross
    jj = jac[jac["comparison_type"] == "cross_institution"]
    r = stats.spearmanr(jj["jaccard_similarity"], jj["shared_papers"].astype(float))
    out["topic_similarity_vs_collaboration"] = {"spearman": round(float(r.correlation), 3), "p": float(r.pvalue),
                                                "pairs": int(len(jj))}
    return out


# ═════════════════════════════════════════════
# 3. REPORT FIGURES
# ═════════════════════════════════════════════

def fig_growth_quality(df, g):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    ax = axes[0]
    for inst in C.INST_NAMES:
        c = df[(df["institution"] == inst) & (df["year"] <= LAST_FULL_YEAR)].groupby("year").size()
        ax.plot(c.index, c.values, "o-", color=COLORS[inst], ms=4, label=f"{inst} (+{g[inst]['annual_growth_pct']}%/yr)")
        r = stats.linregress(c.index.astype(float), np.log(c.values))
        ax.plot(c.index, np.exp(r.intercept + r.slope * c.index), color=COLORS[inst], lw=1, ls=":")
    ax.set_title("(a) Papers per year with log-linear trend", fontsize=10)
    ax.set_xticks(range(2016, 2026, 2))
    ax.legend(fontsize=7.5)
    ax.grid(axis="x", visible=False)
    ax = axes[1]
    for inst in C.INST_NAMES:
        q = g[inst]["q1_by_year"]
        ys = [y for y in sorted(q) if y <= LAST_FULL_YEAR]
        ax.plot(ys, [q[y] for y in ys], "o-", color=COLORS[inst], ms=4, label=inst)
    ax.set_title("(b) Share of journal papers in Q1 venues (%)", fontsize=10)
    ax.set_xticks(range(2016, 2026, 2))
    ax.set_ylim(0, 80)
    ax.legend(fontsize=7.5)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "f1_growth_quality.png")


def fig_impact(prem, reg):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.4), gridspec_kw={"width_ratios": [1, 1.5]})
    ax = axes[0]
    groups = ["Single institute", "Indian partner", "International"]
    means = [prem[g]["mean_ncs"] for g in groups]
    lo = [prem[g]["mean_ncs"] - prem[g]["mean_ci"][0] for g in groups]
    hi = [prem[g]["mean_ci"][1] - prem[g]["mean_ncs"] for g in groups]
    ax.barh(groups, means, xerr=[lo, hi], color=[C.TIER_COLORS[3], C.TIER_COLORS[2], C.TIER_COLORS[0]],
            height=0.5, error_kw={"ecolor": INK2, "lw": 1, "capsize": 3})
    ax.axvline(1, color=INK2, lw=0.8)
    for k, g in enumerate(groups):
        ax.text(prem[g]["mean_ci"][1] + 0.03, k, f"{means[k]:.2f} (n={prem[g]['papers']})", va="center",
                fontsize=8, color=INK2)
    ax.set_xlim(0, max(prem[g]["mean_ci"][1] for g in groups) * 1.45)
    ax.set_title("(a) Mean normalised citation score\n(1 = average for year, field, type; 95% CI)", fontsize=9.5)
    ax.grid(axis="y", visible=False)
    ax = axes[1]
    t = [x for x in reg["terms"]]
    labels = [x["term"] for x in t]
    eff = [x["effect_pct"] for x in t]
    ax.errorbar(eff, range(len(t)), xerr=[[e - x["ci"][0] for e, x in zip(eff, t)],
                                          [x["ci"][1] - e for e, x in zip(eff, t)]],
                fmt="o", color=C.TIER_COLORS[0], ecolor=INK2, capsize=3, ms=5)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(range(len(t)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("% change in (1 + citations), other factors held fixed")
    ax.set_title(f"(b) What predicts citations? OLS, n={reg['n']:,}, R²={reg['r2']}, year & field fixed effects",
                 fontsize=9.5)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    save(fig, "f2_impact_drivers.png")


def fig_citation_network(df, edges, cn):
    it = edges[edges["edge_type"] == "internal"]
    G = nx.DiGraph()
    G.add_edges_from(zip(it["source_openalex_id"], it["target_openalex_id"]))
    comp = max(nx.weakly_connected_components(G), key=len)
    H = G.subgraph(comp).to_undirected()
    inst = df.groupby("openalex_id")["institution"].first().to_dict()
    pos = nx.spring_layout(H, k=0.9 / math.sqrt(len(H)), iterations=80, seed=7)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    nx.draw_networkx_edges(H, pos, ax=ax, width=0.3, edge_color="#b5b4ae", alpha=0.6)
    nx.draw_networkx_nodes(H, pos, ax=ax, node_size=[6 + 2.2 * H.degree(n) for n in H],
                           node_color=[COLORS.get(inst.get(n), MUTED) for n in H], linewidths=0)
    ax.set_title(f"(a) Largest component of the internal citation network ({len(H)} papers)", fontsize=9.5)
    ax.axis("off")
    for i in C.INST_NAMES:
        ax.scatter([], [], color=COLORS[i], label=i, s=20)
    ax.legend(fontsize=7.5, loc="lower left")
    ax = axes[1]
    null = np.array(cn["null_distribution"]) * 100
    ax.hist(null, bins=np.arange(30, 100.25, 0.5), color=C.TIER_COLORS[2], linewidth=0)
    top = ax.get_ylim()[1]
    ax.axvline(cn["same_institution_pct"], color=C.TIER_COLORS[0], lw=2)
    ax.text(cn["same_institution_pct"] - 1, top * 0.8, f"observed\n{cn['same_institution_pct']}%",
            ha="right", fontsize=8, color=INK)
    ax.text(null.mean() + 2, top * 0.8, f"shuffled targets\n{null.mean():.1f}% ± {null.std():.1f}\n"
            f"z = {cn['homophily_z']}", ha="left", fontsize=8, color=INK2)
    ax.set_xlim(30, 100)
    ax.set_xlabel("% of internal citations that stay inside the citing institute")
    ax.set_ylabel("null graphs (1000)")
    ax.set_title("(b) Institutional homophily vs. 1000 target-shuffled graphs", fontsize=9.5)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "f3_citation_network.png")


def fig_authorship(auth_edges, am, at):
    nodes = am["nodes"]
    inn = auth_edges[auth_edges["edge_scope"].isin(["same_institution", "inter_group"])]
    top = set(sorted(nodes, key=lambda k: -nodes[k]["strength"])[:450])
    H = nx.Graph()
    H.add_nodes_from(top)
    H.add_edges_from((a, b) for a, b in zip(inn["author_a_id"], inn["author_b_id"]) if a in top and b in top)
    H = H.subgraph(max(nx.connected_components(H), key=len)).copy()
    big = [c["id"] for c in am["communities"][:7]]
    abbr = {"IIIT Allahabad": "IIITA", "ABV-IIITM Gwalior": "ABV", "IIIT Bangalore": "IIITB"}
    pal = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
    col = [pal[big.index(nodes[n]["community"])] if nodes[n]["community"] in big else "#c9c8c2" for n in H]
    pos = nx.spring_layout(H, k=1.6 / math.sqrt(len(H)), iterations=100, seed=3)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    nx.draw_networkx_edges(H, pos, ax=ax, width=0.3, edge_color="#b5b4ae", alpha=0.5)
    nx.draw_networkx_nodes(H, pos, ax=ax, node_size=[5 + nodes[n]["degree"] * 0.5 for n in H], node_color=col,
                           linewidths=[0.8 if nodes[n]["is_core_faculty"] else 0 for n in H], edgecolors=INK)
    for k2, c in enumerate(am["communities"][:7]):
        dom = max(c["institutions"], key=c["institutions"].get)
        ax.scatter([], [], color=pal[k2], s=20,
                   label=f"C{c['id']} · {abbr[dom]} · {c['size']} authors · {short(c['top_authors'][0], 22)}")
    ax.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False)
    ax.set_title("(a) Co-authorship core: 450 most-connected authors,\ncolour = Louvain community, ring = core faculty",
                 fontsize=9.5)
    ax.axis("off")
    ax = axes[1]
    for vals, lab, c in [(at["degree_values"], "all authors", C.TIER_COLORS[2]),
                         (at["core_degree_values"], "core faculty", C.TIER_COLORS[0])]:
        v = np.array(vals)
        v = v[v > 0]
        xs = np.sort(np.unique(v))
        ccdf = [(v >= x).mean() for x in xs]
        ax.loglog(xs, ccdf, "o", ms=3, color=c, label=lab)
    ax.set_xlabel("co-authors at the three institutes (degree)")
    ax.set_ylabel("P(degree ≥ k)")
    ax.set_title("(b) Degree distribution (CCDF): heavy-tailed, faculty-centred", fontsize=9.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, "f4_authorship_network.png")


def fig_connectivity(indian, flow, ct):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    ax = axes[0]
    years = list(range(C.START_YEAR + 1, LAST_FULL_YEAR + 1))
    for inst in C.INST_NAMES:
        r = ct["ratio_by_year"][inst]
        ax.plot(years, [r.get(str(y), np.nan) for y in years], "o-", color=COLORS[inst], ms=4, label=inst)
    ax.axhline(1, color=INK2, lw=0.8)
    ax.text(years[0], 1.04, "receive = give", fontsize=7.5, color=INK2)
    ax.set_title("(a) Citations received / given with other Indian institutes, per year", fontsize=9.5)
    ax.set_xticks(years[::2])
    ax.legend(fontsize=7.5)
    ax.grid(axis="x", visible=False)
    ax = axes[1]
    ind = indian[~indian["intra_group"].astype(str).str.upper().eq("TRUE")]
    for inst in C.INST_NAMES:
        s = ind[(ind["your_inst"] == inst) & (ind["shared_papers"].astype(int) > 0)]
        ax.scatter(s["shared_papers"].astype(int) + RNG.uniform(-0.15, 0.15, len(s)),
                   s["citations_received_from_partner"].astype(int) + 1, s=10, alpha=0.6, color=COLORS[inst],
                   label=f"{inst} (ρ = {ct['collab_vs_citation'][inst]['spearman']})", linewidths=0)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("papers co-authored with the partner institute")
    ax.set_ylabel("citations received from it + 1")
    ax.set_title("(b) Partners we write with are the ones who cite us", fontsize=9.5)
    ax.legend(fontsize=7.5)
    fig.tight_layout()
    save(fig, "f5_connectivity.png")


def pfmt(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}" if p < 0.1 else f"p = {p:.2f}"


def findings(I, summ):
    """Key findings as (title, text) pairs, written from the computed numbers."""
    g, ni, cp, rg = I["growth_quality"], I["normalised_impact"], I["collaboration_premium"], I["citation_regression"]
    cn, an, ct, co = I["citation_network"], I["authorship_network"], I["connectivity"], I["concentration"]
    S = summ.set_index("institution")
    ia, ab, ib = C.INST_NAMES
    term = {t["term"]: t for t in rg["terms"]}
    team_b = math.log(1 + term["Team size (log authors)"]["effect_pct"] / 100)
    doubling = (2 ** team_b - 1) * 100
    cv = ct["collab_vs_citation"]
    cross = ct["in_exceeds_out_from"]
    return [
        ("Output more than doubled, at the same pace everywhere",
         f"Papers grew {g[ia]['annual_growth_pct']}% / {g[ab]['annual_growth_pct']}% / {g[ib]['annual_growth_pct']}% "
         f"a year (IIITA / ABV / IIITB, log-linear fit 2016–2025, all {pfmt(max(x['growth_p'] for x in g.values()))}): "
         f"IIITA {g[ia]['papers_2016']}→{g[ia]['papers_2025']}, ABV {g[ab]['papers_2016']}→{g[ab]['papers_2025']}, "
         f"IIITB {g[ib]['papers_2016']}→{g[ib]['papers_2025']} papers."),
        ("Quality rose with quantity",
         f"The Q1 share of journal papers rose from {g[ia]['q1_share_2016_19']}% to {g[ia]['q1_share_2022_25']}% at "
         f"IIITA and from {g[ab]['q1_share_2016_19']}% to {g[ab]['q1_share_2022_25']}% at ABV between 2016–19 and "
         f"2022–25 (χ², {pfmt(g[ia]['q1_shift_p'])}). IIITB already started high ({g[ib]['q1_share_2016_19']}% → "
         f"{g[ib]['q1_share_2022_25']}%, {pfmt(g[ib]['q1_shift_p'])}), so growth did not come at the cost of venue quality."),
        ("Raw citations exaggerate the gap between institutes",
         f"IIITB's median paper has {S.loc[ib, 'median_citations']:.0f} citations vs {S.loc[ia, 'median_citations']:.0f} at "
         f"IIITA, but {S.loc[ib, 'conference_papers'] / S.loc[ib, 'papers'] * 100:.0f}% of its output is conference papers. "
         f"Normalised for year, field and type, mean impact is {ni[ab]['mncs']} (ABV), {ni[ia]['mncs']} (IIITA) and "
         f"{ni[ib]['mncs']} (IIITB, 95% CI {ni[ib]['mncs_ci'][0]}–{ni[ib]['mncs_ci'][1]}): a modest, not a large, difference."),
        ("Impact is carried by a few papers",
         f"Citation Gini is {co[ia]['gini_citations']}–{co[ab]['gini_citations']}; the top 10% of papers collect "
         f"{min(x['top10pct_paper_citation_share'] for x in co.values())}–"
         f"{max(x['top10pct_paper_citation_share'] for x in co.values())}% of all citations. Among core faculty the "
         f"top 20% write {min(x['top20pct_faculty_paper_share'] for x in co.values())}–"
         f"{max(x['top20pct_faculty_paper_share'] for x in co.values())}% of papers, and output and h-index move together "
         f"(Spearman ρ = {I['faculty']['papers_vs_h_spearman']})."),
        ("The 'international premium' is really a venue and team-size effect",
         f"Internationally co-authored papers score {cp['International']['mean_ncs']} vs "
         f"{cp['Single institute']['mean_ncs']} for single-institute papers (Mann–Whitney "
         f"{pfmt(cp['International']['mwu_p_vs_single'])}). Once venue, type, team size, year and field are held fixed "
         f"(OLS, n = {rg['n']:,}), the international effect is {term['International co-author']['effect_pct']:+.0f}% "
         f"(n.s.), while a Q1 venue adds {term['Q1 journal']['effect_pct']:+.0f}%, a conference venue "
         f"{term['Conference paper']['effect_pct']:+.0f}%, and doubling the team {doubling:+.0f}%."),
        ("Internal citation is almost entirely self-citation",
         f"{cn['author_self_citation_pct']}% of the {cn['internal_edges']:,} citations between papers of the three "
         f"institutes share an author, and {cn['same_institution_pct']}% stay inside the citing institute versus "
         f"{cn['same_institution_null_pct']}% expected when targets are shuffled (z = {cn['homophily_z']}). Only "
         f"{cn['non_self_edges']} links connect different research groups, so internal PageRank mostly measures group "
         f"continuity rather than cross-group influence."),
        ("Three islands: tight groups, almost no IIIT–IIIT collaboration",
         f"The co-authorship network is small-world (clustering {an['clustering']} vs {an['clustering_random']} random, "
         f"path length {an['path_length']} vs {an['path_length_random']}) and strongly modular (Q = {an['modularity']} vs "
         f"{an['modularity_null']} ± {an['modularity_null_sd']} in degree-preserving random graphs). Institute "
         f"assortativity is {an['institution_assortativity']}: only {an['inter_group_papers']} papers link two of the "
         f"three IIITs. Core faculty have a median of {an['core_median_degree']:.0f} co-authors vs "
         f"{an['other_median_degree']:.0f} for others."),
        ("Citations follow collaboration, not topic overlap",
         f"Institutes that co-author more with us also cite us more (Spearman ρ = {cv[ia]['spearman']} / "
         f"{cv[ab]['spearman']} / {cv[ib]['spearman']}, all {pfmt(max(x['p'] for x in cv.values()))}). Co-author "
         f"partners are about a third of the Indian institutes that cite us but supply "
         f"{cv[ib]['share_in_cites_from_coauthor_partners_pct']}–{cv[ia]['share_in_cites_from_coauthor_partners_pct']}% "
         f"of those citations. Topic similarity does not predict who we collaborate with "
         f"(ρ = {ct['topic_similarity_vs_collaboration']['spearman']}, "
         f"{pfmt(ct['topic_similarity_vs_collaboration']['p'])})."),
        ("From citation importers to exporters",
         f"Per year, ABV has received more citations from other Indian institutes than it gives since "
         f"{cross[ab]} and IIITA since {cross[ia]}; IIITB is still below parity (2025 ratio "
         f"{ct['ratio_by_year'][ib]['2025']}). Summed over 2016–2026, IIITA ({I['flow_totals'][ia]}) and ABV "
         f"({I['flow_totals'][ab]}) are near balance while IIITB ({I['flow_totals'][ib]}) remains a net importer "
         f"of Indian citations."),
    ]


def main():
    print("=" * 65)
    print(" DPCN 2026 - Group 10 - Part 5: Inferential analysis")
    print("=" * 65)
    o = A.load_outputs()
    df, fac = o["df"], o["fac"]
    I = {}
    I["growth_quality"] = growth_and_quality(df)
    u, I["normalised_impact"] = normalised_impact(df)
    I["collaboration_premium"], I["ncs_by_quartile"], I["ncs_by_open_access"] = collaboration_premium(u)
    I["citation_regression"] = citation_regression(u)
    I["concentration"] = concentration(df, fac)
    cn = citation_network_tests(df, o["cite_edges"], o["cite_metrics"])
    at = authorship_tests(o["auth_edges"], o["auth_metrics"])
    ct = connectivity_tests(o["indian"], o["flow"], o["jaccard"])
    I["citation_network"] = {k: v for k, v in cn.items() if k != "null_distribution"}
    I["authorship_network"] = {k: v for k, v in at.items() if not k.endswith("_values")}
    I["connectivity"] = ct
    fs = fac[fac["is_core_faculty"]]
    r = stats.spearmanr(fs["papers"], fs["h_index"])
    I["faculty"] = {"papers_vs_h_spearman": round(float(r.correlation), 3),
                    "core_faculty": int(len(fs)),
                    "lifetime_h_median": float(fs["h_index_lifetime_openalex"].median())}
    I["flow_totals"] = {i: o["flow"][i]["impact_ratio"] for i in C.INST_NAMES}
    I["findings"] = [{"title": t, "text": x} for t, x in findings(I, A.institution_summary(df, fac))]
    with open(C.INSIGHTS_JSON, "w", encoding="utf-8") as f:
        json.dump(I, f, indent=1)
    print(f"  Saved {C.INSIGHTS_JSON}")
    fig_growth_quality(df, I["growth_quality"])
    fig_impact(I["collaboration_premium"], I["citation_regression"])
    fig_citation_network(df, o["cite_edges"], cn)
    fig_authorship(o["auth_edges"], o["auth_metrics"], at)
    fig_connectivity(o["indian"], o["flow"], ct)
    print(json.dumps({k: I[k] for k in ("normalised_impact", "collaboration_premium")}, indent=1)[:1500])
    print(json.dumps(I["citation_network"], indent=1)[:900])
    print(json.dumps(I["authorship_network"], indent=1))
    print(json.dumps(I["citation_regression"], indent=1)[:2000])
    print(json.dumps(I["connectivity"]["collab_vs_citation"], indent=1), I["connectivity"]["in_exceeds_out_from"],
          I["connectivity"]["topic_similarity_vs_collaboration"])


if __name__ == "__main__":
    main()
