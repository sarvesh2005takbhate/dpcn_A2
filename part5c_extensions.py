"""
DPCN 2026 - Group 10 - Part 5c: Extensions requested after the first review
============================================================================
Reads the outputs of parts 1b-2 and writes outputs/group10_extensions.json,
which the dashboard and the report read.

  quality      journal papers by Scimago quartile (Q1 / Q2 / Q3 / Q4 / unranked) and by
               impact-factor band (>=10, 5-10, <5; OpenAlex 2-year mean citedness),
               per institute and per year, plus the journals behind the >=10 band
  roles        faculty by rank (Professor / Associate / Assistant, from the official
               institute lists): output, h-index, position in the faculty
               co-authorship network, who builds the links between institutes,
               and how much of each institute's output the listed faculty cover
  gcc          giant connected component: size, which institutes and ranks it
               contains, what lies outside it, and how it grew year by year
  multilayer   a two-layer multiplex on the same authors - co-authorship and
               author-to-author citation - with edge overlap, degree correlation,
               participation coefficient and the mutually connected giant
               component; plus an institute-level multiplex (co-authorship,
               citation, shared partners, topic similarity)
  anomalies    citing institutions whose citations are concentrated on a few
               papers (the Saveetha University case), with a sensitivity check
               that removes them

Usage:
    python part5c_extensions.py
"""

import json
import math
import os
from collections import Counter, defaultdict
from itertools import combinations

import networkx as nx
import numpy as np
import pandas as pd
from scipy import stats

import group10_analysis as A
import group10_common as C
import group10_roles as R

OUT_JSON = os.path.join(C.OUT_DIR, "group10_extensions.json")
ABBR = C.INST_ABBR
OUR_IDS = {v[0] for v in C.INSTITUTIONS.values()}
SAVEETHA = "I85461943"
RNG = np.random.default_rng(7)
QUARTS = ["Q1", "Q2", "Q3", "Q4"]


# ═════════════════════════════════════════════
# GRAPH
# ═════════════════════════════════════════════

def coauthor_graph(o, fac):
    nodes = o["auth_metrics"]["nodes"]
    e = o["auth_edges"]
    e = e[e["edge_scope"].isin(["same_institution", "inter_group"])]
    rank = {(r.author_id, r.institution): r.rank for r in fac.itertuples()}
    rank_any = dict(zip(fac["author_id"], fac["rank"]))
    G = nx.Graph()
    for k, v in sorted(nodes.items()):
        G.add_node(k, inst=v["institution"], name=v["name"],
                   role=rank.get((k, v["institution"]), rank_any.get(k, "Other")))
    first = e.groupby(["author_a_id", "author_b_id"])["year"].min()
    for (a, b), g in e.groupby(["author_a_id", "author_b_id"]):
        G.add_edge(a, b, weight=int(g["paper_doi"].nunique() or len(g)), year=int(first[(a, b)]))
    return G


def giant_nodes(G):
    if G.number_of_nodes() == 0:
        return set()
    return max(nx.connected_components(G), key=len)


def pct(a, b):
    return round(a / b * 100, 1) if b else 0.0


# ═════════════════════════════════════════════
# 1. QUARTILES AND IMPACT FACTOR
# ═════════════════════════════════════════════

def quality(df, fac):
    j = df[df["type"] == "journal"].copy()
    j["q"] = j["quartile"].where(j["quartile"].isin(QUARTS), "Unranked")
    j["band"] = j["if_band"].replace("", "No IF value")
    years = list(range(C.START_YEAR, C.END_YEAR + 1))
    out = {"years": years, "quartiles": QUARTS + ["Unranked"], "bands": list(C.IF_BANDS) + ["No IF value"],
           "by_inst": {}, "by_year": {}, "top_high_if_journals": {}, "top_faculty": {}}
    for inst in C.INST_NAMES:
        s = j[j["institution"] == inst]
        n = len(s)
        qc = s["q"].value_counts()
        bc = s["band"].value_counts()
        ifv = s["impact_factor"].dropna()
        out["by_inst"][inst] = {
            "journal_papers": n,
            "quartile_counts": {q: int(qc.get(q, 0)) for q in out["quartiles"]},
            "quartile_pct": {q: pct(int(qc.get(q, 0)), n) for q in out["quartiles"]},
            "if_counts": {b: int(bc.get(b, 0)) for b in out["bands"]},
            "if_pct": {b: pct(int(bc.get(b, 0)), n) for b in out["bands"]},
            "if_gt5": int((ifv >= 5).sum()), "if_gt10": int((ifv >= 10).sum()),
            "if_gt5_pct": pct(int((ifv >= 5).sum()), n), "if_gt10_pct": pct(int((ifv >= 10).sum()), n),
            "if_coverage_pct": pct(len(ifv), n),
            "median_if": round(float(ifv.median()), 2) if len(ifv) else None,
            "q1_and_if_gt5": int(((s["q"] == "Q1") & (s["impact_factor"].fillna(0) >= 5)).sum()),
        }
        out["by_year"][inst] = {
            **{q: [int(((s["year"] == y) & (s["q"] == q)).sum()) for y in years] for q in out["quartiles"]},
            "if_gt5": [int(((s["year"] == y) & (s["impact_factor"].fillna(0) >= 5)).sum()) for y in years],
            "if_gt10": [int(((s["year"] == y) & (s["impact_factor"].fillna(0) >= 10)).sum()) for y in years],
        }
        hi = s[s["impact_factor"].fillna(0) >= 10]
        out["top_high_if_journals"][inst] = [
            {"journal": k, "papers": int(len(g)), "if": float(g["impact_factor"].iloc[0]),
             "quartile": C.most_common_nonempty(g["quartile"])}
            for k, g in sorted(hi.groupby("journal_name"), key=lambda kv: (-len(kv[1]), kv[0]))[:8]]
        f = fac[(fac["institution"] == inst) & (fac["journal_papers"] > 0)]
        f = f.sort_values(["if_gt10_papers", "if_gt5_papers", "q1_papers"], ascending=False).head(10)
        out["top_faculty"][inst] = [
            {"name": r.name, "role": r.rank, "q1": int(r.q1_papers), "q2": int(r.q2_papers), "q3": int(r.q3_papers),
             "q4": int(r.q4_papers), "if5": int(r.if_gt5_papers), "if10": int(r.if_gt10_papers)}
            for r in f.itertuples()]
    # does a high-quartile journal mean a high IF? (they measure different things)
    both = j[j["impact_factor"].notna() & j["q"].isin(QUARTS)].drop_duplicates("openalex_id")
    out["if_by_quartile"] = {q: {"median_if": round(float(both[both["q"] == q]["impact_factor"].median()), 2)
                                 if (both["q"] == q).any() else None,
                                 "share_if_gt5_pct": pct(int(((both["q"] == q) & (both["impact_factor"] >= 5)).sum()),
                                                         int((both["q"] == q).sum()))}
                             for q in QUARTS}
    return out


# ═════════════════════════════════════════════
# 2. FACULTY VS STUDENTS
# ═════════════════════════════════════════════

def roles(G, fac, adf):
    """Faculty by rank. Node attribute "role" holds the rank (R.RANKS)."""
    scope = {}
    try:
        with open(C.FACULTY_SCOPE_JSON, encoding="utf-8") as fh:
            scope = json.load(fh)
    except OSError:
        pass
    audit = pd.read_csv(C.ROSTER_MATCH_CSV, dtype=str).fillna("") if os.path.exists(C.ROSTER_MATCH_CSV) else pd.DataFrame()
    out = {"order": R.RANKS, "scope": scope, "sources": R.roster_sources()}
    cov = {}
    for i in C.INST_NAMES:
        a = audit[audit["institution"] == i] if len(audit) else audit
        f = fac[fac["institution"] == i]
        cov[i] = {"listed": int(len(a)), "with_papers": int((a["status"] == "matched").sum()) if len(a) else 0,
                  "ranks": {r: int((f["rank"] == r).sum()) for r in R.RANKS},
                  "listed_ranks": {r: int((a["designation"].map(R.rank_of) == r).sum()) if len(a) else 0 for r in R.RANKS},
                  "without_papers": sorted(a.loc[a["status"] != "matched", "roster_name"]) if len(a) else [],
                  "merged_profiles": int((a["merged_records"].str.count(";") > 0).sum()) if len(a) else 0,
                  "manual_check": int((a["needs_manual_check"] == "True").sum()) if len(a) else 0}
    out["coverage"] = cov

    role = nx.get_node_attributes(G, "role")
    inst = nx.get_node_attributes(G, "inst")
    bet = nx.betweenness_centrality(G)
    deg = dict(G.degree())
    gcc = giant_nodes(G)
    fi = fac.set_index("author_id")
    by_rank = {}
    for r in R.RANKS:
        ns = [n for n in G if role[n] == r]
        f = fi.loc[[n for n in ns if n in fi.index]]
        by_rank[r] = {"faculty": len(ns),
                      "median_papers": float(f["papers"].median()) if len(f) else 0,
                      "median_h": float(f["h_index"].median()) if len(f) else 0,
                      "q1_share_pct": pct(int(f["q1_papers"].sum()), int(f["journal_papers"].sum())) if len(f) else 0,
                      "mean_degree": round(float(np.mean([deg[n] for n in ns])), 2) if ns else 0,
                      "median_degree": float(np.median([deg[n] for n in ns])) if ns else 0,
                      "isolated_pct": pct(sum(1 for n in ns if deg[n] == 0), len(ns)),
                      "betweenness_share_pct": round(sum(bet[n] for n in ns) / max(sum(bet.values()), 1e-12) * 100, 1),
                      "in_gcc_pct": pct(sum(1 for n in ns if n in gcc), len(ns))}
    out["network_by_role"] = by_rank

    pairs, inter_pairs, endpoints = Counter(), Counter(), Counter()
    for a, b in G.edges():
        k = "–".join(sorted((role[a], role[b]), key=R.RANKS.index))
        pairs[k] += 1
        if inst[a] != inst[b]:
            inter_pairs[k] += 1
            endpoints[role[a]] += 1
            endpoints[role[b]] += 1
    out["edge_role_mix"] = {"all": dict(pairs), "between_institutes": dict(inter_pairs),
                            "between_institutes_total": sum(inter_pairs.values())}
    out["inter_link_endpoints_by_role"] = {r: int(endpoints.get(r, 0)) for r in R.RANKS}
    top_bet = sorted(G, key=lambda n: (-bet[n], n))[:20]
    out["top20_brokers_by_role"] = dict(Counter(role[n] for n in top_bet))
    out["top_brokers"] = [{"name": G.nodes[n]["name"], "institution": inst[n], "rank": role[n],
                           "degree": deg[n], "betweenness": round(bet[n], 4)} for n in top_bet[:10]]

    # rank tests: do professors have more faculty co-authors than assistant professors?
    dp = [deg[n] for n in G if role[n] == "Professor"]
    da = [deg[n] for n in G if role[n] == "Assistant Professor"]
    if len(dp) > 5 and len(da) > 5:
        u = stats.mannwhitneyu(dp, da, alternative="greater")
        out["prof_vs_asst_degree"] = {"professor_median": float(np.median(dp)), "assistant_median": float(np.median(da)),
                                      "mannwhitney_p": float(u.pvalue)}

    # share of each institute's output (papers with any IIIT author) covered by its listed faculty
    per = {}
    for i in C.INST_NAMES:
        si = scope.get("institutes", {}).get(i, {})
        per[i] = {"papers_with_listed_faculty_pct": pct(si.get("papers_with_listed_faculty", 0),
                                                        si.get("papers_all_affiliated_authors", 0)),
                  "faculty_authorship_share_pct": pct(si.get("authorships_listed_faculty", 0), si.get("authorships_all", 0)),
                  "first_author_rank": dict(Counter(fac.loc[fac["institution"] == i, "rank"]))}
    out["papers_by_role"] = per
    return out


# ═════════════════════════════════════════════
# 3. GIANT CONNECTED COMPONENT
# ═════════════════════════════════════════════

def size_bin(n):
    for lo, hi, lab in ((1, 1, "1 (isolated)"), (2, 2, "2"), (3, 5, "3–5"), (6, 10, "6–10"),
                        (11, 50, "11–50"), (51, 10 ** 9, "51+")):
        if lo <= n <= hi:
            return lab


def gcc_analysis(G, o, structure):
    inst = nx.get_node_attributes(G, "inst")
    role = nx.get_node_attributes(G, "role")
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    gc = comps[0]
    H = G.subgraph(gc)
    sizes = Counter(inst.values())
    out = {"nodes": G.number_of_nodes(), "edges": G.number_of_edges(), "components": len(comps),
           "gcc_nodes": len(gc), "gcc_share_pct": pct(len(gc), G.number_of_nodes()),
           "gcc_edges": H.number_of_edges(), "gcc_edge_share_pct": pct(H.number_of_edges(), G.number_of_edges()),
           "second_nodes": len(comps[1]) if len(comps) > 1 else 0,
           "third_nodes": len(comps[2]) if len(comps) > 2 else 0}
    bins = Counter(size_bin(len(c)) for c in comps[1:])
    nodes_in = Counter()
    for c in comps[1:]:
        nodes_in[size_bin(len(c))] += len(c)
    order = ["1 (isolated)", "2", "3–5", "6–10", "11–50", "51+"]
    out["outside_gcc"] = {"bins": order, "components": [int(bins.get(b, 0)) for b in order],
                          "authors": [int(nodes_in.get(b, 0)) for b in order]}
    gi = Counter(inst[n] for n in gc)
    out["by_inst"] = {i: {"authors": sizes[i], "in_gcc": gi[i], "in_gcc_pct": pct(gi[i], sizes[i]),
                          "share_of_gcc_pct": pct(gi[i], len(gc))} for i in C.INST_NAMES}
    gr = Counter(role[n] for n in gc)
    rs = Counter(role.values())
    out["by_role"] = {r: {"authors": rs[r], "in_gcc_pct": pct(gr[r], rs[r])} for r in R.RANKS}
    # structure of the GCC vs the whole graph
    deg_in = [d for _, d in H.degree()]
    deg_out = [G.degree(n) for n in G if n not in gc]
    out["gcc_mean_degree"] = round(float(np.mean(deg_in)), 2)
    out["outside_mean_degree"] = round(float(np.mean(deg_out)), 2) if deg_out else 0
    out["gcc_clustering"] = round(nx.average_clustering(H), 3)
    out["gcc_density"] = round(nx.density(H), 6)
    co = structure.get("coauthorship", {}) if structure else {}
    out["gcc_avg_path_length"] = co.get("giant_avg_path_length")
    out["gcc_diameter"] = co.get("giant_diameter")
    # per-institute: the institute's own subgraph GCC
    pi = structure.get("per_institution", {}) if structure else {}
    out["own_subgraph_gcc_pct"] = {i: pi.get(i, {}).get("giant_share_pct") for i in C.INST_NAMES}
    # papers whose author team lies in the GCC
    adf = o["adf"]
    pin = adf.groupby("openalex_id")["author_id"].apply(lambda s: any(a in gc for a in s))
    out["papers_touching_gcc_pct"] = pct(int(pin.sum()), len(pin))
    # growth of the GCC year by year (links enter with the pair's first joint paper)
    years = list(range(C.START_YEAR, C.END_YEAR + 1))
    first_year = adf.groupby("author_id")["year"].min().to_dict()
    gr_ = {"years": years, "authors": [], "gcc": [], "gcc_pct": [], "institutes_in_gcc": [],
           "gcc_by_inst": {i: [] for i in C.INST_NAMES}}
    for y in years:
        T = nx.Graph()
        T.add_nodes_from(n for n in G if first_year.get(n, 9999) <= y)
        T.add_edges_from((a, b) for a, b, d in G.edges(data=True) if d["year"] <= y)
        g = giant_nodes(T)
        ci = Counter(inst[n] for n in g)
        gr_["authors"].append(T.number_of_nodes())
        gr_["gcc"].append(len(g))
        gr_["gcc_pct"].append(pct(len(g), T.number_of_nodes()))
        gr_["institutes_in_gcc"].append(sum(1 for i in C.INST_NAMES if ci[i] >= 5))
        for i in C.INST_NAMES:
            gr_["gcc_by_inst"][i].append(ci[i])
    out["growth"] = gr_
    # citation network: largest weakly connected component
    ce = o["cite_edges"]
    ce = ce[ce["edge_type"] == "internal"]
    D = nx.DiGraph()
    papers = A.unique_papers(o["df"])
    D.add_nodes_from(papers["openalex_id"])
    D.add_edges_from(zip(ce["source_openalex_id"], ce["target_openalex_id"]))
    w = max(nx.weakly_connected_components(D), key=len)
    pin = o["df"].groupby("openalex_id")["institution"].apply(set).to_dict()
    wi = Counter(i for p in w for i in pin.get(p, ()))
    tot = Counter(i for p in D for i in pin.get(p, ()))
    out["citation_wcc"] = {"papers": D.number_of_nodes(), "wcc_papers": len(w), "wcc_share_pct": pct(len(w), D.number_of_nodes()),
                           "by_inst_pct": {i: pct(wi[i], tot[i]) for i in C.INST_NAMES},
                           "components": nx.number_weakly_connected_components(D)}
    return out


# ═════════════════════════════════════════════
# 4. MULTILAYER (MULTIPLEX) ANALYSIS
# ═════════════════════════════════════════════

def citation_layer(o, nodes):
    """Author-to-author citation layer on the same node set: authors x and y are
    linked if a paper by x cites a paper by y (either direction; an author citing
    their own paper is ignored)."""
    adf = o["adf"]
    auth = adf.groupby("openalex_id")["author_id"].apply(lambda s: sorted(set(a for a in s if a in nodes))).to_dict()
    ce = o["cite_edges"]
    ce = ce[ce["edge_type"] == "internal"]
    W = Counter()
    for s, t in zip(ce["source_openalex_id"], ce["target_openalex_id"]):
        for a in auth.get(s, ()):
            for b in auth.get(t, ()):
                if a != b:
                    W[(min(a, b), max(a, b))] += 1
    L = nx.Graph()
    L.add_nodes_from(sorted(nodes))
    L.add_edges_from((a, b, {"weight": w}) for (a, b), w in W.items())
    return L


def mutually_connected_giant(layers, nodes):
    """Buldyrev et al. (2010): largest set connected inside every layer at once."""
    S = set(nodes)
    while True:
        label = {n: () for n in S}
        for L in layers:
            for k, c in enumerate(nx.connected_components(L.subgraph(S))):
                for n in c:
                    label[n] = label[n] + (k,)
        groups = Counter(label.values())
        best = max(groups, key=groups.get) if groups else ()
        T = {n for n in S if label[n] == best}
        if T == S:
            return S
        S = T


def multilayer(G, o, inst_df):
    inst = nx.get_node_attributes(G, "inst")
    nodes = set(G)
    L1 = nx.Graph()
    L1.add_nodes_from(sorted(G))
    L1.add_edges_from(G.edges())
    L2 = citation_layer(o, nodes)
    layers = {"co-authorship": L1, "citation": L2}
    out = {"layers": {}, "node_count": len(nodes)}
    for name, L in layers.items():
        act = [n for n in L if L.degree(n) > 0]
        g = giant_nodes(L.subgraph(act)) if act else set()
        out["layers"][name] = {
            "edges": L.number_of_edges(), "active_nodes": len(act), "active_pct": pct(len(act), len(nodes)),
            "mean_degree": round(2 * L.number_of_edges() / max(len(act), 1), 2),
            "density": round(nx.density(L), 6), "gcc_nodes": len(g), "gcc_pct_of_all": pct(len(g), len(nodes)),
            "inter_institute_edges": sum(1 for a, b in L.edges() if inst[a] != inst[b]),
            "inter_institute_pct": pct(sum(1 for a, b in L.edges() if inst[a] != inst[b]), L.number_of_edges()),
            "institution_assortativity": round(_assort(L, inst), 3),
        }
    E1 = {tuple(sorted(e)) for e in L1.edges()}
    E2 = {tuple(sorted(e)) for e in L2.edges()}
    both = E1 & E2
    out["overlap"] = {"both": len(both), "only_coauthor": len(E1 - E2), "only_citation": len(E2 - E1),
                      "jaccard": round(len(both) / max(len(E1 | E2), 1), 4),
                      "citation_edges_between_coauthors_pct": pct(len(both), len(E2)),
                      "coauthor_pairs_that_cite_pct": pct(len(both), len(E1)),
                      "inter_institute_both": sum(1 for a, b in both if inst[a] != inst[b]),
                      "inter_institute_citation_only": sum(1 for a, b in E2 - E1 if inst[a] != inst[b])}
    # null: how much overlap if citation partners were random among the same degrees?
    sims = []
    deg2 = [d for _, d in L2.degree()]
    for s in range(5):
        Rg = nx.configuration_model(deg2, seed=s)
        Rg = nx.Graph(Rg)
        Rg.remove_edges_from(nx.selfloop_edges(Rg))
        mp = dict(zip(range(len(deg2)), list(L2)))
        Er = {tuple(sorted((mp[a], mp[b]))) for a, b in Rg.edges()}
        sims.append(len(Er & E1))
    out["overlap"]["expected_both_random"] = round(float(np.mean(sims)), 1)
    out["overlap"]["overlap_ratio_vs_random"] = round(len(both) / max(np.mean(sims), 0.5), 1)
    # degree correlation across layers, participation coefficient
    k1 = np.array([L1.degree(n) for n in sorted(nodes)], float)
    k2 = np.array([L2.degree(n) for n in sorted(nodes)], float)
    act = (k1 + k2) > 0
    rho = stats.spearmanr(k1[act], k2[act]).correlation
    out["degree_spearman"] = round(float(rho), 3)
    o_ = k1 + k2
    P = np.where(o_ > 0, 2 * (1 - (k1 / np.where(o_ > 0, o_, 1)) ** 2 - (k2 / np.where(o_ > 0, o_, 1)) ** 2), 0)
    Pa = P[act]
    out["participation"] = {"mean": round(float(Pa.mean()), 3),
                            "focused_pct": pct(int((Pa < 1 / 3).sum()), len(Pa)),
                            "mixed_pct": pct(int(((Pa >= 1 / 3) & (Pa <= 2 / 3)).sum()), len(Pa)),
                            "multiplex_pct": pct(int((Pa > 2 / 3).sum()), len(Pa)),
                            "hist": np.histogram(Pa, bins=10, range=(0, 1))[0].tolist()}
    names = nx.get_node_attributes(G, "name")
    srt = sorted(nodes)
    idx = {n: i for i, n in enumerate(srt)}
    hubs = sorted(srt, key=lambda n: (-(k1[idx[n]] + k2[idx[n]]), n))[:12]
    out["top_multiplex_hubs"] = [{"name": names[n], "institution": inst[n], "coauthor_degree": int(k1[idx[n]]),
                                  "citation_degree": int(k2[idx[n]]), "participation": round(float(P[idx[n]]), 2)}
                                 for n in hubs]
    # aggregate vs mutual connectivity
    Ag = nx.compose(L1, L2)
    act_nodes = [n for n in Ag if Ag.degree(n) > 0]
    ag = giant_nodes(Ag.subgraph(act_nodes))
    both_active = [n for n in nodes if L1.degree(n) > 0 and L2.degree(n) > 0]
    mcgc = mutually_connected_giant([L1, L2], both_active)
    out["aggregate_gcc"] = len(ag)
    out["aggregate_gcc_pct"] = pct(len(ag), len(nodes))
    out["active_in_both"] = len(both_active)
    out["mutual_gcc"] = len(mcgc)
    out["mutual_gcc_pct"] = pct(len(mcgc), len(nodes))
    out["mutual_gcc_institutes"] = dict(Counter(inst[n] for n in mcgc))

    # ── institute-level multiplex: 4 layers, one weight per institute pair ──
    pairs = list(combinations(C.INST_NAMES, 2))
    co = Counter()
    for a, b in L1.edges():
        if inst[a] != inst[b]:
            co[tuple(sorted((inst[a], inst[b])))] += 1
    ci = Counter()
    ce = o["cite_edges"]
    ce = ce[(ce["edge_type"] == "internal") & (ce["source_inst"] != ce["target_inst"])]
    for s, t in zip(ce["source_inst"], ce["target_inst"]):
        if s in C.INST_NAMES and t in C.INST_NAMES:
            ci[tuple(sorted((s, t)))] += 1
    ind = o["indian"]
    ind = ind[(ind["shared_papers"].astype(int) > 0) & ~ind["intra_group"].astype(str).str.upper().eq("TRUE")]
    psets = {i: set(ind[ind["your_inst"] == i]["partner_openalex_id"]) for i in C.INST_NAMES}
    jac = o["jaccard"]
    topic = {}
    if not jac.empty:
        for r in jac.itertuples():
            if r.entity_a in C.INST_NAMES and r.entity_b in C.INST_NAMES:
                topic[tuple(sorted((r.entity_a, r.entity_b)))] = float(r.jaccard_similarity)
    rows = []
    for a, b in pairs:
        k = tuple(sorted((a, b)))
        rows.append({"pair": f"{ABBR[a]}–{ABBR[b]}", "a": a, "b": b, "coauthor_links": co[k], "citations": ci[k],
                     "shared_partners_jaccard": round(len(psets[a] & psets[b]) / max(len(psets[a] | psets[b]), 1), 3),
                     "topic_jaccard": round(topic.get(k, float("nan")), 3) if k in topic else None})
    out["institute_multiplex"] = rows
    vals = {key: [r[key] or 0 for r in rows] for key in ("coauthor_links", "citations", "shared_partners_jaccard", "topic_jaccard")}
    out["institute_layer_spearman"] = {f"{x}~{y}": round(float(stats.spearmanr(vals[x], vals[y]).correlation), 3)
                                       for x, y in combinations(vals, 2)
                                       if np.std(vals[x]) > 0 and np.std(vals[y]) > 0}
    return out


def _assort(L, inst):
    H = L.subgraph([n for n in L if L.degree(n) > 0]).copy()
    if H.number_of_edges() == 0:
        return 0.0
    nx.set_node_attributes(H, {n: inst[n] for n in H}, "inst")
    return nx.attribute_assortativity_coefficient(H, "inst")


# ═════════════════════════════════════════════
# 5. CITATION ANOMALIES (SAVEETHA UNIVERSITY)
# ═════════════════════════════════════════════

def anomalies(o, fac):
    inflow = C.load_json_gz(C.INFLOW_CACHE)["works"]
    df = o["df"]
    papers = A.unique_papers(df).set_index("openalex_id")
    inst_of = df.groupby("openalex_id")["institution"].apply(list).to_dict()
    corpus = set(papers.index)
    names, cnt_works, links, targets, years = {}, Counter(), Counter(), defaultdict(Counter), defaultdict(Counter)
    paper_links = defaultdict(Counter)       # paper -> citing institution -> citing works
    for cw in inflow.values():
        tg = [t for t in cw.get("cites", []) if t in corpus]
        if not tg:
            continue
        ext = {i: v for i, v in cw["insts"].items() if i not in OUR_IDS}
        for i, v in ext.items():
            names[i] = v["name"]
            cnt_works[i] += 1
            years[i][cw["year"]] += 1
            for t in tg:
                links[i] += 1
                targets[i][t] += 1
                paper_links[t][i] += 1
    ind = o["indian"]
    shared = ind.groupby("partner_openalex_id")["shared_papers"].apply(lambda s: int(s.astype(int).sum())).to_dict()
    rows = []
    for i, n in links.most_common(40):
        t = targets[i]
        top3 = sum(v for _, v in t.most_common(3))
        recent = sum(v for y, v in years[i].items() if y and y >= 2022)
        dominated = sum(1 for p, c in t.items()
                        if papers.loc[p, "citations"] >= 10 and c / papers.loc[p, "citations"] >= 0.5)
        rows.append({"id": i, "name": names[i], "citing_works": cnt_works[i], "citation_links": n,
                     "papers_cited": len(t), "links_per_paper": round(n / len(t), 2),
                     "top3_share_pct": pct(top3, n), "since_2022_pct": pct(recent, cnt_works[i]),
                     "shared_papers": shared.get(i, 0),
                     "links_per_shared_paper": round(n / max(shared.get(i, 0), 1), 1),
                     "papers_dominated": dominated})
    # robust outlier score on links per co-authored paper and dominated papers
    lp = np.log1p([r["links_per_shared_paper"] for r in rows])
    med, mad = np.median(lp), np.median(np.abs(lp - np.median(lp))) or 1
    for r, v in zip(rows, lp):
        r["z_links_per_shared"] = round(float((v - med) / (1.4826 * mad)), 2)
        r["flag"] = bool(r["z_links_per_shared"] >= 2 or r["papers_dominated"] >= 3)
    out = {"citing_institutions": rows}

    # ── Saveetha in detail ──
    S = SAVEETHA
    st = targets.get(S, Counter())
    yrs = list(range(C.START_YEAR, C.END_YEAR + 1))
    all_years = Counter()
    for cw in inflow.values():
        if any(t in corpus for t in cw.get("cites", [])):
            all_years[cw["year"]] += 1
    sv = {"name": names.get(S, "Saveetha University"), "years": yrs,
          "citing_works_by_year": [int(years[S].get(y, 0)) for y in yrs],
          "all_indian_citing_works_by_year": [int(all_years.get(y, 0)) for y in yrs],
          "rank_by_links": [r["id"] for r in rows].index(S) + 1 if S in [r["id"] for r in rows] else None}
    per_inst = Counter()
    for p, c in st.items():
        for i in inst_of.get(p, []):
            per_inst[i] += c
    sv["links_by_inst"] = {i: int(per_inst.get(i, 0)) for i in C.INST_NAMES}
    sv["shared_papers_by_inst"] = {i: int(ind[(ind["your_inst"] == i) & (ind["partner_openalex_id"] == S)]["shared_papers"]
                                          .astype(int).sum()) for i in C.INST_NAMES}
    # rank of Saveetha among each institute's citing partners
    rk = {}
    for i in C.INST_NAMES:
        s = ind[ind["your_inst"] == i].copy()
        s["r"] = s["citations_received_from_partner"].astype(int).rank(ascending=False, method="min")
        hit = s[s["partner_openalex_id"] == S]
        rk[i] = int(hit["r"].iloc[0]) if len(hit) else None
    sv["rank_among_citing_partners"] = rk
    top = []
    for p, c in st.most_common(15):
        tot = int(papers.loc[p, "citations"])
        top.append({"title": papers.loc[p, "title"][:140], "year": int(papers.loc[p, "year"]),
                    "institution": "; ".join(inst_of.get(p, [])), "citations": tot, "saveetha": int(c),
                    "share_pct": pct(c, tot), "doi": C.normalize_doi(papers.loc[p, "doi"]),
                    "authors": papers.loc[p, "author"]})
    sv["top_papers"] = top
    sv["papers_majority_saveetha"] = sum(1 for p, c in st.items()
                                        if papers.loc[p, "citations"] >= 10 and c / papers.loc[p, "citations"] >= 0.5)
    sv["concentration_top10_pct"] = pct(sum(v for _, v in st.most_common(10)), sum(st.values()))
    # are the cited papers ones that a Saveetha-affiliated author co-wrote?
    co_sets = df.groupby("openalex_id")["coauthor_institute_ids"].apply(
        lambda s: {i for x in s.fillna("").astype(str) for i in x.split(";") if i}).to_dict()
    sv_links = sum(st.values())
    sv["links_to_papers_with_saveetha_coauthor_pct"] = pct(
        sum(c for p, c in st.items() if S in co_sets.get(p, ())), sv_links)
    sv["papers_with_saveetha_coauthor"] = sum(1 for v in co_sets.values() if S in v)
    # same share for every other top citing institution, for comparison
    other = []
    for r in rows:
        if r["id"] == S:
            continue
        t = targets[r["id"]]
        n_co = sum(c for p, c in t.items() if r["id"] in co_sets.get(p, ()))
        other.append(pct(n_co, sum(t.values())))
    sv["other_top_citers_links_to_coauthored_median_pct"] = float(np.median(other)) if other else None
    # affected authors and h-index without Saveetha's citations
    adf = o["adf"]
    rows_a = []
    for (aid, inst), g in adf.groupby(["author_id", "institution"]):
        ps = g.drop_duplicates("openalex_id")
        sc = sum(st.get(p, 0) for p in ps["openalex_id"])
        if sc < 10:
            continue
        cit = [int(papers.loc[p, "citations"]) for p in ps["openalex_id"]]
        cit_wo = [max(int(papers.loc[p, "citations"]) - st.get(p, 0), 0) for p in ps["openalex_id"]]
        rows_a.append({"name": g["author_name"].iloc[0], "institution": inst, "papers": len(ps),
                       "citations": sum(cit), "saveetha_citations": sc, "saveetha_share_pct": pct(sc, sum(cit)),
                       "h": C.hindex(cit), "h_without": C.hindex(cit_wo)})
    rows_a.sort(key=lambda r: -r["saveetha_citations"])
    role = dict(zip(zip(fac["name"], fac["institution"]), fac["rank"]))
    for r in rows_a:
        r["role"] = role.get((r["name"], r["institution"]), "")
    sv["affected_authors"] = rows_a[:15]
    # institute-level sensitivity
    sens = {}
    for i in C.INST_NAMES:
        s = df[df["institution"] == i]
        cit = s["citations"].astype(int).tolist()
        wo = [max(int(c) - st.get(w, 0), 0) for w, c in zip(s["openalex_id"], s["citations"])]
        sens[i] = {"citations": int(sum(cit)), "citations_without": int(sum(wo)),
                   "drop_pct": pct(sum(cit) - sum(wo), sum(cit)), "h": C.hindex(cit), "h_without": C.hindex(wo)}
    sv["sensitivity"] = sens
    # citing works by subject keywords in their titles (what Saveetha papers are about)
    kw = {"molecular docking / drug design": r"docking|inhibitor|drug|molecular dynamics|ligand",
          "nanomaterials": r"nano", "machine / deep learning": r"learning|neural|cnn|lstm|transformer",
          "dental / oral": r"dental|oral|periodont|tooth|teeth", "IoT / networks": r"iot|network|wireless|sensor"}
    import re
    sw = [cw for cw in inflow.values() if S in cw["insts"] and any(t in corpus for t in cw.get("cites", []))]
    sv["citing_topics"] = {k: sum(1 for cw in sw if re.search(p, (cw["title"] or "").lower())) for k, p in kw.items()}
    sv["citing_works"] = len(sw)
    sv["citing_works_citing_1"] = sum(1 for cw in sw if len([t for t in cw["cites"] if t in corpus]) == 1)
    out["saveetha"] = sv
    out["legit_vs_boosting"] = legit_vs_boosting(rows, inflow, corpus, df, papers, o["adf"])
    return out


# ─────────────────────────────────────────────
# Is the citing explained by size, by a few authors, by topic?
# ─────────────────────────────────────────────
CITER_CACHE = os.path.join(C.CACHE_DIR, "citer_details.json.gz")


def _citer_cache(oa, inst_ids, inflow, corpus):
    """Indian output per institution (size baseline) and, for the institutions
    compared, the authors and topic of every work that cites our papers."""
    cache = C.load_json_gz(CITER_CACHE, {"output": {}, "works": {}, "india_total": None})
    try:
        if cache["india_total"] is None:
            d = oa.get("works", {"filter": f"authorships.institutions.country_code:IN,"
                                           f"publication_year:{C.START_YEAR}-{C.END_YEAR}", "per_page": 1})
            cache["india_total"] = d["meta"]["count"]
        for i in inst_ids:
            if i not in cache["output"]:
                d = oa.get("works", {"filter": f"authorships.institutions.id:{i},"
                                               f"publication_year:{C.START_YEAR}-{C.END_YEAR}", "per_page": 1})
                cache["output"][i] = d["meta"]["count"]
        want = sorted(w for w, cw in inflow.items()
                      if set(cw["insts"]) & set(inst_ids) and any(t in corpus for t in cw.get("cites", []))
                      and w not in cache["works"])
        for k in range(0, len(want), 50):
            chunk = want[k:k + 50]
            d = oa.get("works", {"filter": "openalex:" + "|".join(chunk), "per_page": 50,
                                 "select": "id,authorships,primary_topic"})
            for r in d.get("results", []):
                pt = r.get("primary_topic") or {}
                cache["works"][C.short_id(r["id"])] = {
                    "authors": [[C.short_id((a.get("author") or {}).get("id")),
                                 [C.short_id(x.get("id")) for x in a.get("institutions") or []]]
                                for a in r.get("authorships") or []],
                    "field": (pt.get("field") or {}).get("display_name") or "",
                    "subfield": (pt.get("subfield") or {}).get("display_name") or ""}
            for w in chunk:
                cache["works"].setdefault(w, {"authors": [], "field": "", "subfield": ""})
            C.save_json_gz(cache, CITER_CACHE)
    except C.BudgetExhausted as e:
        print(f"    [budget] {e} - legitimacy tests use what is cached")
    C.save_json_gz(cache, CITER_CACHE)
    return cache


def legit_vs_boosting(rows, inflow, corpus, df, papers, adf):
    """Three tests that separate 'cites us because it is big / interested' from
    'citations concentrated in a small circle':
      1. size: share of our Indian citing works vs share of all Indian output
      2. who cites: concentration on a few citing authors, and how many of the
         citing authors ever co-authored with the cited paper's authors
      3. topic: citing work in the same OpenAlex field / subfield as the cited paper
    Saveetha is compared with the other ten largest citing institutions."""
    compare = [r["id"] for r in rows[:11]]
    if SAVEETHA not in compare:
        compare.append(SAVEETHA)
    cache = _citer_cache(C.OpenAlex(), compare, inflow, corpus)
    total_citing = sum(1 for cw in inflow.values() if any(t in corpus for t in cw.get("cites", [])))
    # co-author network of our authors with ANYONE (OpenAlex author IDs, from works cache)
    works = C.load_json_gz(C.WORKS_CACHE)["works"]
    coauth = defaultdict(set)          # our paper -> all OpenAlex author ids on it
    for p in corpus:
        coauth[p] = {a["aid"] for a in works.get(p, {}).get("authorships", []) if a.get("aid")}
    # every author id that has ever co-authored with an author of paper p (within our corpus)
    by_author = defaultdict(set)
    for p, ids in coauth.items():
        for a in ids:
            by_author[a] |= ids
    memo = {}

    def circle(t):
        """Authors of paper t plus everyone who co-wrote any corpus paper with them."""
        if t not in memo:
            memo[t] = set().union(coauth[t], *(by_author[a] for a in coauth[t]))
        return memo[t]
    field = papers["field"].to_dict()
    subf = papers["subfield"].to_dict()
    names = {r["id"]: r["name"] for r in rows}
    links = {r["id"]: r["citation_links"] for r in rows}
    out = {"india_total_works": cache["india_total"], "institutions": []}
    for i in compare:
        ws = [(w, cw) for w, cw in inflow.items() if i in cw["insts"] and any(t in corpus for t in cw.get("cites", []))]
        n = len(ws)
        outp = cache["output"].get(i)
        size_share = outp / cache["india_total"] * 100 if outp and cache["india_total"] else None
        cite_share = n / total_citing * 100 if total_citing else 0
        # citing authors affiliated with this institution
        per_author = Counter()
        coauthor_links = same_field = same_sub = known = 0
        n_links = 0
        for w, cw in ws:
            det = cache["works"].get(w)
            if not det or not det["authors"]:
                continue
            known += 1
            mine = [a for a, insts in det["authors"] if i in insts and a]
            for a in set(mine):
                per_author[a] += 1
            all_auth = {a for a, _ in det["authors"] if a}
            for t in cw["cites"]:
                if t not in corpus:
                    continue
                n_links += 1
                # does any author of the citing work co-author with any author of the cited paper?
                if all_auth & circle(t):
                    coauthor_links += 1
                if det["field"] and det["field"] == field.get(t):
                    same_field += 1
                if det["subfield"] and det["subfield"] == subf.get(t):
                    same_sub += 1
        tot_a = sum(per_author.values())
        top5 = sum(v for _, v in per_author.most_common(5))
        out["institutions"].append({
            "id": i, "name": names.get(i, i), "citing_works": n, "citation_links": links.get(i),
            "indian_output_works": outp, "share_of_indian_output_pct": round(size_share, 2) if size_share else None,
            "share_of_our_citing_works_pct": round(cite_share, 2),
            "over_representation": round(cite_share / size_share, 2) if size_share else None,
            "works_with_author_data": known, "distinct_citing_authors": len(per_author),
            "top5_authors_share_pct": pct(top5, tot_a),
            "top_author_works": per_author.most_common(1)[0][1] if per_author else 0,
            "works_per_citing_author": round(tot_a / max(len(per_author), 1), 2),
            "links_from_coauthors_pct": pct(coauthor_links, n_links),
            "same_field_pct": pct(same_field, n_links), "same_subfield_pct": pct(same_sub, n_links),
            "is_saveetha": i == SAVEETHA})
    others = [r for r in out["institutions"] if not r["is_saveetha"] and r["works_with_author_data"] >= 20]
    med = lambda k: round(float(np.median([r[k] for r in others if r[k] is not None])), 2) if others else None
    out["others_median"] = {k: med(k) for k in ("over_representation", "top5_authors_share_pct",
                                                "works_per_citing_author", "links_from_coauthors_pct",
                                                "same_field_pct", "same_subfield_pct")}
    sv = next((r for r in out["institutions"] if r["is_saveetha"]), None)
    if sv:
        m = out["others_median"]
        verdicts = []
        def cmp(key, higher_is_red, label, unit="", fmtv=lambda v: v):
            a, b = sv[key], m[key]
            if a is None or b is None:
                return
            red = (a > b * 1.5) if higher_is_red else (a < b / 1.5)
            verdicts.append({"test": label, "saveetha": a, "others_median": b, "unit": unit, "red_flag": bool(red)})
        cmp("over_representation", True, "Citing share ÷ share of Indian output (1 = explained by size)", "×")
        cmp("top5_authors_share_pct", True, "Share of citing works written by its 5 most active citing authors", "%")
        cmp("links_from_coauthors_pct", True, "Citations from someone in the cited authors' co-author circle", "%")
        cmp("same_field_pct", False, "Citing paper in the same research field as the cited paper", "%")
        out["saveetha_tests"] = verdicts
        out["saveetha_red_flags"] = sum(v["red_flag"] for v in verdicts)
    return out


# ═════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════

def main():
    print("=" * 65)
    print(" DPCN 2026 - Group 10 - Part 5c: extensions")
    print("=" * 65)
    o = A.load_outputs()
    fac = o["fac"]
    if "rank" not in fac:
        raise SystemExit("faculty table has no rank column - re-run part1b_enrich_data.py")
    G = coauthor_graph(o, fac)
    print(f"  co-authorship graph: {G.number_of_nodes()} authors, {G.number_of_edges()} links")
    E = {}
    print("  [1/5] quartiles and impact factor ...")
    E["quality"] = quality(o["df"], fac)
    print("  [2/5] faculty by rank ...")
    E["roles"] = roles(G, fac, o["adf"])
    print("  [3/5] giant connected component ...")
    E["gcc"] = gcc_analysis(G, o, o["structure"])
    print("  [4/5] multilayer network ...")
    E["multilayer"] = multilayer(G, o, o["df"])
    print("  [5/5] citation anomalies ...")
    E["anomalies"] = anomalies(o, fac)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(E, f, ensure_ascii=False, indent=1, default=lambda v: v.item() if hasattr(v, "item") else str(v))
    print(f"  Saved {OUT_JSON}")
    q = E["quality"]["by_inst"]
    for i in C.INST_NAMES:
        print(f"    {i:18s} Q1-Q4 {[q[i]['quartile_counts'][k] for k in QUARTS]}  IF>=5 {q[i]['if_gt5']}  IF>=10 {q[i]['if_gt10']}")
    print("    ranks:", {i: E["roles"]["coverage"][i]["ranks"] for i in C.INST_NAMES})
    print("    by rank:", json.dumps(E["roles"]["network_by_role"], indent=1), E["roles"].get("prof_vs_asst_degree"))
    m = E["multilayer"]
    print(f"    multiplex: overlap {m['overlap']}, rho={m['degree_spearman']}, mutual GCC={m['mutual_gcc']}")
    sv = E["anomalies"]["saveetha"]
    print(f"    Saveetha: rank {sv['rank_by_links']}, links {sv['links_by_inst']}, majority papers {sv['papers_majority_saveetha']}")
    print("=" * 65)


if __name__ == "__main__":
    main()
