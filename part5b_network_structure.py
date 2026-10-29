"""
DPCN 2026 - Group 10 - Part 5b: Network structure & inter-institution analysis
===============================================================================
Offline - reads the files written by part1b/part2. Answers the question
"how are the three IIITs connected to each other?" with structural evidence:

  properties        nodes, edges, density, components, degree statistics,
                    clustering, path length & diameter (giant component),
                    degree assortativity - for both networks, stating whether
                    each is directed / weighted / connected
  per institution   the same metrics on each institute's own co-authorship
                    subgraph (authors whose main affiliation is the institute)
  mixing            3x3 matrix of co-author links and joint papers between the
                    institutes, vs the configuration-model expectation
                    E[e_AB] = d_A d_B / 2m
  bridges           authors with co-authors in another institute, authors that
                    OpenAlex places at two institutes, the minimum set of authors
                    whose removal disconnects two institutes (node cut)
  distances         mean shortest-path length within / between institutes
  robustness        giant component and cross-institute reachability when
                    authors are removed by betweenness vs at random
  null models       Erdos-Renyi G(n, m) graphs with the same n and m
  degree            log-binned degree distribution (co-authorship, citation
                    in-degree) with the ER/Poisson expectation
  communities       Louvain stability over 10 seeds; institutional purity
  centrality        degree, betweenness, closeness, eigenvector + their agreement
  citations         3x3 citation matrix between institutes, with and without
                    author self-citations
  shared partners   overlap of the Indian partner institutions of the three IIITs
  reference paths   ring and star path lengths for the same number of nodes
                    (course-connection comparison only)

Writes outputs/group10_network_structure.json and outputs/charts/f6_*.png, f7_*.png.

Usage:
    python part5b_network_structure.py
"""

import json
import math
from collections import Counter, defaultdict
from itertools import combinations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy import stats

import group10_analysis as A
import group10_common as C
from part3_statistics import COLORS, INK2, save

RNG = np.random.default_rng(42)
ABBR = {"IIIT Allahabad": "IIITA", "ABV-IIITM Gwalior": "ABV", "IIIT Bangalore": "IIITB"}
PAIRS = list(combinations(C.INST_NAMES, 2))
pair_key = lambda a, b: f"{ABBR[a]}-{ABBR[b]}"


# ═════════════════════════════════════════════
# GRAPHS
# ═════════════════════════════════════════════

def coauthor_graph(o):
    """Undirected co-authorship graph of the three institutes; weight = joint papers."""
    nodes = o["auth_metrics"]["nodes"]
    e = o["auth_edges"]
    e = e[e["edge_scope"].isin(["same_institution", "inter_group"])]
    G = nx.Graph()
    for k, v in nodes.items():
        G.add_node(k, inst=v["institution"], name=v["name"], core=v["is_core_faculty"])
    for (a, b), g in e.groupby(["author_a_id", "author_b_id"]):
        G.add_edge(a, b, weight=int(g["paper_doi"].nunique() or len(g)))
    return G


def author_institutes(adf):
    """Every assigned institute an author (canonical ID) has a paper at."""
    return adf.groupby("author_id")["institution"].apply(lambda s: sorted(set(s))).to_dict()


def citation_graph(o):
    it = o["cite_edges"]
    it = it[it["edge_type"] == "internal"]
    G = nx.DiGraph()
    G.add_nodes_from(A.unique_papers(o["df"])["openalex_id"])
    G.add_edges_from(zip(it["source_openalex_id"], it["target_openalex_id"]))
    return G


def giant(G):
    comps = nx.connected_components(G) if not G.is_directed() else nx.weakly_connected_components(G)
    return G.subgraph(max(comps, key=len)).copy()


# ═════════════════════════════════════════════
# 1. PROPERTIES
# ═════════════════════════════════════════════

def degree_stats(deg):
    d = np.array(list(deg), float)
    top = np.sort(d)[::-1][:max(1, len(d) // 20)]
    return {"mean": round(d.mean(), 2), "median": float(np.median(d)), "std": round(d.std(), 2),
            "max": int(d.max()), "share_of_degree_top5pct": round(top.sum() / max(d.sum(), 1) * 100, 1),
            "zero_degree": int((d == 0).sum())}


def undirected_properties(G, exact_paths=True):
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    gc = G.subgraph(comps[0]).copy()
    out = {"directed": False, "weighted": True, "nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
           "density": round(nx.density(G), 6), "connected": nx.is_connected(G), "components": len(comps),
           "isolated_nodes": sum(1 for c in comps if len(c) == 1),
           "giant_nodes": gc.number_of_nodes(), "giant_share_pct": round(len(comps[0]) / G.number_of_nodes() * 100, 1),
           "second_component": len(comps[1]) if len(comps) > 1 else 0,
           "degree": degree_stats(dict(G.degree()).values()),
           "avg_clustering": round(nx.average_clustering(G), 3), "transitivity": round(nx.transitivity(G), 3),
           "degree_assortativity": round(nx.degree_assortativity_coefficient(G), 3)}
    if gc.number_of_nodes() > 2 and exact_paths:
        out["giant_avg_path_length"] = round(nx.average_shortest_path_length(gc), 2)
        out["giant_diameter"] = nx.diameter(gc)
    return out, gc


def citation_properties(G):
    wcc = sorted(nx.weakly_connected_components(G), key=len, reverse=True)
    scc = [c for c in nx.strongly_connected_components(G) if len(c) > 1]
    indeg, outdeg = dict(G.in_degree()), dict(G.out_degree())
    return {"directed": True, "weighted": False, "nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
            "density": round(nx.density(G), 7), "weak_components": len(wcc),
            "largest_weak_component": len(wcc[0]), "isolated_papers": sum(1 for c in wcc if len(c) == 1),
            "nontrivial_strong_components": len(scc), "papers_in_cycles": sum(len(c) for c in scc),
            "is_dag": nx.is_directed_acyclic_graph(G), "reciprocity": round(nx.reciprocity(G), 4),
            "in_degree": degree_stats(indeg.values()), "out_degree": degree_stats(outdeg.values()),
            "path_note": ("Average path length and diameter are not reported: the graph is directed, almost "
                          "acyclic and split into many weak components, so most ordered pairs have no path.")}


def per_institution(G, at):
    out = {}
    for inst in C.INST_NAMES:
        # build in a fixed node/edge order: G.subgraph() iterates a set, whose order
        # changes between runs and makes the seeded Louvain result non-reproducible
        keep = sorted(n for n, d in G.nodes(data=True) if d["inst"] == inst)
        ks = set(keep)
        H = nx.Graph()
        H.add_nodes_from((n, G.nodes[n]) for n in keep)
        H.add_edges_from(sorted((min(a, b), max(a, b), d) for a, b, d in G.edges(data=True) if a in ks and b in ks))
        p, gc = undirected_properties(H)
        comms = nx.community.louvain_communities(H, weight="weight", seed=42)
        p["communities"] = len(comms)
        p["communities_10plus"] = sum(1 for c in comms if len(c) >= 10)
        p["modularity"] = round(nx.community.modularity(H, comms, weight="weight"), 3)
        p["core_faculty"] = sum(1 for _, d in H.nodes(data=True) if d["core"])
        bet = nx.betweenness_centrality(H)
        deg = dict(H.degree())
        p["top_degree"] = [{"name": H.nodes[n]["name"], "degree": deg[n]}
                           for n in sorted(deg, key=lambda n: (-deg[n], n))[:5]]
        p["top_betweenness"] = [{"name": H.nodes[n]["name"], "betweenness": round(bet[n], 4)}
                                for n in sorted(bet, key=lambda n: (-bet[n], n))[:5]]
        # how dependent is the institute's giant component on its top broker?
        top = min(bet, key=lambda n: (-bet[n], n))
        rest = H.copy()
        rest.remove_node(top)
        p["giant_after_removing_top_broker"] = len(max(nx.connected_components(rest), key=len))
        out[inst] = p
    return out


# ═════════════════════════════════════════════
# 2. HOW THE INSTITUTES CONNECT
# ═════════════════════════════════════════════

def mixing(G, o):
    m = G.number_of_edges()
    inst = nx.get_node_attributes(G, "inst")
    dsum = Counter()
    for n, d in G.degree():
        dsum[inst[n]] += d
    obs = Counter()
    for a, b in G.edges():
        obs[tuple(sorted((inst[a], inst[b])))] += 1
    e = o["auth_edges"]
    inter = e[e["edge_scope"] == "inter_group"]
    df = o["df"]
    multi = df.groupby("openalex_id")["institution"].apply(lambda s: tuple(sorted(set(s))))
    rows = []
    for a, b in PAIRS:
        k = tuple(sorted((a, b)))
        exp = dsum[a] * dsum[b] / (2 * m)
        sel = inter[((inter["inst_a"] == a) & (inter["inst_b"] == b)) | ((inter["inst_a"] == b) & (inter["inst_b"] == a))]
        rows.append({"pair": pair_key(a, b), "a": a, "b": b, "coauthor_links": obs[k],
                     "expected_configuration_model": round(exp, 1),
                     "ratio_observed_expected": round(obs[k] / exp, 3) if exp else None,
                     "joint_papers_linking_authors": int(sel["paper_doi"].nunique()),
                     "copublished_papers": int(sum(1 for v in multi if a in v and b in v))})
    within = {i: {"coauthor_links": obs[(i, i)], "expected": round(dsum[i] ** 2 / (4 * m), 1)} for i in C.INST_NAMES}
    total_inter = sum(r["coauthor_links"] for r in rows)
    # do the linking papers come from people OpenAlex places at two institutes?
    at = author_institutes(o["adf"])
    movers = {a for a, v in at.items() if len(v) > 1}
    by_paper = inter.groupby("paper_doi").apply(
        lambda g: bool((set(g["author_a_id"]) | set(g["author_b_id"])) & movers), include_groups=False)
    years = inter.drop_duplicates("paper_doi")["year"].astype(int)
    return {"pairs": rows, "within": within, "inter_links_total": total_inter,
            "inter_papers": int(len(by_paper)), "inter_papers_with_multi_affiliated_author": int(by_paper.sum()),
            "inter_papers_by_period": {"2016-2020": int((years <= 2020).sum()), "2021-2026": int((years > 2020).sum())},
            "inter_links_expected_total": round(sum(r["expected_configuration_model"] for r in rows), 1),
            "inter_share_pct": round(total_inter / m * 100, 2),
            "all_three_papers": int(sum(1 for v in multi if len(v) == 3))}


def bridges(G, at):
    inst = nx.get_node_attributes(G, "inst")
    rows = []
    for n in G:
        cross = Counter(inst[v] for v in G[n] if inst[v] != inst[n])
        multi = [i for i in at.get(n, []) if i != inst[n]]
        if cross or multi:
            rows.append({"author_id": n, "name": G.nodes[n]["name"], "institution": inst[n],
                         "core_faculty": bool(G.nodes[n]["core"]),
                         "cross_institute_coauthors": sum(cross.values()),
                         "reaches": sorted(set(cross) | set(multi)),
                         "also_affiliated_with": multi, "degree": G.degree(n)})
    bet = nx.betweenness_centrality(G, weight=None)
    for r in rows:
        r["betweenness"] = round(bet[r["author_id"]], 5)
    rows.sort(key=lambda r: (-r["betweenness"], r["author_id"]))

    # minimum number of authors whose removal separates two institutes
    cuts = {}
    for a, b in PAIRS:
        H = G.copy()
        H.add_edges_from(("__S", n) for n in G if inst[n] == a)
        H.add_edges_from(("__T", n) for n in G if inst[n] == b)
        # only nodes that touch the other side can be cut; endpoints inside A/B are allowed
        cut = nx.minimum_node_cut(H, "__S", "__T")
        cuts[pair_key(a, b)] = {"node_connectivity": len(cut),
                                "cut_authors": sorted(G.nodes[n]["name"] for n in cut)}
    moved = [r for r in rows if r["also_affiliated_with"]]
    return {"bridge_authors": len(rows), "bridge_share_pct": round(len(rows) / G.number_of_nodes() * 100, 2),
            "bridges_core_faculty": sum(r["core_faculty"] for r in rows),
            "multi_affiliated_authors": len(moved),
            "multi_affiliated_core": sum(r["core_faculty"] for r in moved),
            "top_bridges": rows[:15], "min_node_cuts": cuts, "betweenness": bet}


def institute_distances(gc):
    """Mean shortest-path length between authors of each pair of institutes (giant component)."""
    inst = nx.get_node_attributes(gc, "inst")
    tot, cnt = Counter(), Counter()
    for s, dist in nx.all_pairs_shortest_path_length(gc):
        a = inst[s]
        for t, d in dist.items():
            if t != s:
                k = tuple(sorted((a, inst[t])))
                tot[k] += d
                cnt[k] += 1
    sizes = Counter(inst.values())
    return {"giant_component_authors": dict(sizes),
            "mean_distance": {f"{ABBR[k[0]]}-{ABBR[k[1]]}": round(tot[k] / cnt[k], 2) for k in cnt}}


def cross_reach(G, inst):
    """Share of cross-institute author pairs that are still connected by some path."""
    total = 0
    sizes = Counter(inst[n] for n in G)
    for a, b in PAIRS:
        total += sizes[a] * sizes[b]
    if not total:
        return 0.0
    conn = 0
    for c in nx.connected_components(G):
        s = Counter(inst[n] for n in c)
        conn += sum(s[a] * s[b] for a, b in PAIRS)
    return conn / total


def robustness(G, bet, steps=(0, .005, .01, .02, .03, .05, .075, .1, .15, .2)):
    inst = nx.get_node_attributes(G, "inst")
    base_ref = sum(Counter(inst[n] for n in G)[a] * Counter(inst[n] for n in G)[b] for a, b in PAIRS)
    n = G.number_of_nodes()
    order_t = sorted(G, key=lambda x: (-bet[x], x))
    out = {"fraction_removed": list(steps), "targeted": {"giant": [], "cross_reach": []},
           "random": {"giant": [], "cross_reach": [], "giant_sd": [], "cross_reach_sd": []}}
    g0 = len(max(nx.connected_components(G), key=len))

    def measure(H):
        g = len(max(nx.connected_components(H), key=len)) / g0 if H.number_of_nodes() else 0
        return g, cross_reach_fixed(H, inst, base_ref)

    for f in steps:
        k = int(round(f * n))
        H = G.copy()
        H.remove_nodes_from(order_t[:k])
        g, r = measure(H)
        out["targeted"]["giant"].append(round(g, 4))
        out["targeted"]["cross_reach"].append(round(r, 4))
        gs, rs = [], []
        for s in range(10):
            H = G.copy()
            H.remove_nodes_from(RNG.choice(list(G), k, replace=False))
            g, r = measure(H)
            gs.append(g)
            rs.append(r)
        out["random"]["giant"].append(round(float(np.mean(gs)), 4))
        out["random"]["giant_sd"].append(round(float(np.std(gs)), 4))
        out["random"]["cross_reach"].append(round(float(np.mean(rs)), 4))
        out["random"]["cross_reach_sd"].append(round(float(np.std(rs)), 4))
    return out


def cross_reach_fixed(H, inst, base):
    conn = 0
    for c in nx.connected_components(H):
        s = Counter(inst[n] for n in c)
        conn += sum(s[a] * s[b] for a, b in PAIRS)
    return conn / base if base else 0.0


def remove_bridges(G, br):
    """What happens to IIIT-IIIT reachability if the bridge authors were absent?"""
    inst = nx.get_node_attributes(G, "inst")
    ids = [r["author_id"] for r in br["top_bridges"]]
    out = {"cross_reach_full": round(cross_reach(G, inst), 4)}
    for k in (1, 3, 5, 10):
        H = G.copy()
        H.remove_nodes_from(ids[:k])
        out[f"cross_reach_without_top{k}_bridges"] = round(cross_reach(H, inst), 4)
    return out


# ═════════════════════════════════════════════
# 3. BASELINES, DEGREE, COMMUNITIES, CENTRALITY
# ═════════════════════════════════════════════

def er_baseline(n, m, reps=5):
    cl, L, gs, mx = [], [], [], []
    for s in range(reps):
        R = nx.gnm_random_graph(n, m, seed=s)
        gc = giant(R)
        cl.append(nx.average_clustering(R))
        gs.append(gc.number_of_nodes() / n)
        mx.append(max(d for _, d in R.degree()))
        src = RNG.choice(list(gc), min(300, gc.number_of_nodes()), replace=False)
        L.append(np.mean([np.mean(list(nx.single_source_shortest_path_length(gc, x).values())[1:])
                          for x in src]))
    k = 2 * m / n
    return {"reps": reps, "mean_degree": round(k, 2),
            "clustering_sim": round(float(np.mean(cl)), 5), "clustering_theory_k_over_n": round(k / n, 5),
            "giant_share_sim_pct": round(float(np.mean(gs)) * 100, 1),
            "path_length_sim": round(float(np.mean(L)), 2), "path_length_theory_lnN_lnk": round(math.log(n) / math.log(k), 2),
            "max_degree_sim": round(float(np.mean(mx)), 1)}


def log_binned(values, nbins=14):
    v = np.array([x for x in values if x > 0], float)
    edges = np.unique(np.round(np.logspace(0, math.log10(v.max() + 1), nbins)).astype(int))
    if edges[-1] <= v.max():
        edges = np.append(edges, int(v.max()) + 1)
    h, _ = np.histogram(v, bins=edges)
    width = np.diff(edges)
    pdf = h / width / len(v)
    centers = np.sqrt(edges[:-1] * (edges[1:] - 1).clip(min=edges[:-1]))
    keep = h > 0
    ks = np.sort(np.unique(v))
    return {"bin_centers": centers[keep].round(3).tolist(), "pdf": pdf[keep].tolist(), "counts": h[keep].tolist(),
            "ccdf_k": ks.astype(int).tolist(), "ccdf": [(v >= k).mean() for k in ks]}


def poisson_pdf(k_mean, ks):
    return [float(stats.poisson.pmf(int(round(k)), k_mean)) for k in ks]


def community_stability(G, seeds=10):
    parts, qs = [], []
    nodes = list(G)
    for s in range(seeds):
        cs = nx.community.louvain_communities(G, weight="weight", seed=s)
        qs.append(nx.community.modularity(G, cs, weight="weight"))
        lab = {n: i for i, c in enumerate(cs) for n in c}
        parts.append([lab[n] for n in nodes])
    from part5_insights import nmi
    nm = [nmi(parts[i], parts[j]) for i, j in combinations(range(seeds), 2)]
    inst = nx.get_node_attributes(G, "inst")
    cs = nx.community.louvain_communities(G, weight="weight", seed=42)
    big = [c for c in cs if len(c) >= 10]
    purity = [Counter(inst[n] for n in c).most_common(1)[0][1] / len(c) for c in big]
    return {"seeds": seeds, "modularity_mean": round(float(np.mean(qs)), 4), "modularity_sd": round(float(np.std(qs)), 4),
            "pairwise_nmi_mean": round(float(np.mean(nm)), 3), "pairwise_nmi_min": round(float(np.min(nm)), 3),
            "communities_10plus": len(big),
            "single_institute_communities_pct": round(sum(p >= 0.9 for p in purity) / len(big) * 100, 1),
            "mixed_communities": [{"size": len(c), "institutions": dict(sorted(Counter(inst[n] for n in c).items()))}
                                  for c, p in zip(big, purity) if p < 0.9]}


def centralities(gc, bet_full):
    deg = nx.degree_centrality(gc)
    clo = nx.closeness_centrality(gc)
    eig = nx.eigenvector_centrality_numpy(gc)
    bet = {n: bet_full[n] for n in gc}
    M = {"degree": deg, "betweenness": bet, "closeness": clo, "eigenvector": eig}
    keys = list(gc)
    corr = {f"{a}~{b}": round(float(stats.spearmanr([M[a][k] for k in keys], [M[b][k] for k in keys]).correlation), 3)
            for a, b in combinations(M, 2)}
    top = {name: [{"name": gc.nodes[n]["name"], "institution": gc.nodes[n]["inst"], "value": round(v[n], 5)}
                  for n in sorted(v, key=lambda n: (-round(v[n], 9), n))[:10]] for name, v in M.items()}
    # eigenvector mass by institute: where does "influence" concentrate?
    mass = Counter()
    for n, v in eig.items():
        mass[gc.nodes[n]["inst"]] += v ** 2
    return {"spearman": corr, "top10": top,
            "eigenvector_mass_pct": {i: round(mass[i] * 100, 1) for i in C.INST_NAMES},
            "closeness_mean_by_institute": {i: round(float(np.mean([clo[n] for n in gc if gc.nodes[n]["inst"] == i])), 4)
                                            for i in C.INST_NAMES}}


def citation_matrix(o):
    df = o["df"]
    it = o["cite_edges"]
    it = it[it["edge_type"] == "internal"]
    u = A.unique_papers(df).set_index("openalex_id")
    people = {w: {a.strip().lower() for a in s.split(";") if a.strip()} for w, s in zip(u.index, u["all_authors"])}
    insts = df.groupby("openalex_id")["institution"].apply(set).to_dict()
    allm, nos = Counter(), Counter()
    for s, t in zip(it["source_openalex_id"], it["target_openalex_id"]):
        self_c = bool(people[s] & people[t])
        for a in insts[s]:
            for b in insts[t]:
                allm[(a, b)] += 1
                if not self_c:
                    nos[(a, b)] += 1
    fmt = lambda c: {ABBR[a]: {ABBR[b]: c[(a, b)] for b in C.INST_NAMES} for a in C.INST_NAMES}
    cross_all = sum(v for (a, b), v in allm.items() if a != b)
    cross_nos = sum(v for (a, b), v in nos.items() if a != b)
    return {"all": fmt(allm), "excluding_self_citations": fmt(nos),
            "cross_institute_all": cross_all, "cross_institute_non_self": cross_nos,
            "non_self_total": sum(nos.values()),
            "cross_share_of_non_self_pct": round(cross_nos / max(sum(nos.values()), 1) * 100, 1)}


def shared_partners(o):
    ind = o["indian"].copy()
    ind = ind[~ind["intra_group"].astype(str).str.upper().eq("TRUE")]
    ind["shared_papers"] = ind["shared_papers"].astype(int)
    ind = ind[ind["shared_papers"] > 0]
    sets = {i: set(ind[ind["your_inst"] == i]["partner_openalex_id"]) for i in C.INST_NAMES}
    names = dict(zip(ind["partner_openalex_id"], ind["partner_inst"]))
    clus = dict(zip(ind["partner_openalex_id"], ind["partner_cluster"]))
    sp = {(r.your_inst, r.partner_openalex_id): r.shared_papers for r in ind.itertuples()}
    common = set.intersection(*sets.values())
    top_common = sorted(common, key=lambda p: (-min(sp[(i, p)] for i in C.INST_NAMES), names[p]))[:10]
    top_own = {i: [{"name": r.partner_inst, "papers": int(r.shared_papers)} for r in
                   ind[ind["your_inst"] == i].sort_values("shared_papers", ascending=False).head(3).itertuples()]
               for i in C.INST_NAMES}
    return {"partners": {i: len(s) for i, s in sets.items()}, "top_own": top_own,
            "jaccard": {pair_key(a, b): round(len(sets[a] & sets[b]) / len(sets[a] | sets[b]), 3) for a, b in PAIRS},
            "shared": {pair_key(a, b): len(sets[a] & sets[b]) for a, b in PAIRS},
            "common_to_all_three": len(common),
            "top_common": [{"name": names[p], "cluster": clus[p], **{ABBR[i]: sp[(i, p)] for i in C.INST_NAMES}}
                           for p in top_common]}


def reference_paths(n, observed_L, k_mean):
    """Closed chain (ring) and star with the same n - course comparison only."""
    ring = (n * n / 4) / (n - 1) if n % 2 == 0 else (n + 1) / 4
    star = 2 * (n - 1) / n
    return {"n": n, "ring_L": round(ring, 1), "star_L": round(star, 3), "er_L": round(math.log(n) / math.log(k_mean), 2),
            "observed_L": observed_L}


def sample_path_length(G, k=400):
    gc = giant(G)
    src = RNG.choice(list(gc), min(k, gc.number_of_nodes()), replace=False)
    return float(np.mean([np.mean(list(nx.single_source_shortest_path_length(gc, x).values())[1:]) for x in src]))


def identity_sensitivity(o, G):
    """Re-build the co-authorship graph with naive name-only identities (the
    pre-2026-10 rule) and compare the headline structure with the conservative one."""
    adf = o["adf"]
    key = adf["author_name"].map(C.norm_person)
    inst_of = (adf.assign(k=key).groupby(["k", "institution"]).size().reset_index(name="n")
               .sort_values("n", ascending=False).drop_duplicates("k").set_index("k")["institution"])
    N = nx.Graph()
    N.add_nodes_from(key.unique())
    for _, g in adf.assign(k=key).groupby("openalex_id"):
        ks = sorted(set(g["k"]))
        N.add_edges_from(combinations(ks, 2))
    nx.set_node_attributes(N, inst_of.to_dict(), "inst")

    def summary(H):
        inst = nx.get_node_attributes(H, "inst")
        inter = sum(1 for a, b in H.edges() if inst[a] != inst[b])
        return {"nodes": H.number_of_nodes(), "edges": H.number_of_edges(), "inter_institute_links": inter,
                "institution_assortativity": round(nx.attribute_assortativity_coefficient(H, "inst"), 3),
                "giant_nodes": len(max(nx.connected_components(H), key=len)),
                "giant_path_length_sampled": round(sample_path_length(H), 2)}
    return {"conservative": summary(G), "name_only": summary(N)}


def findings(S):
    """3-6 structural findings, each with evidence, meaning and caveats."""
    mx, br, ds, rb = S["mixing"], S["bridges"], S["distances"]["mean_distance"], S["robustness"]
    cm, sp, co, cs = S["citation_matrix"], S["shared_partners"], S["coauthorship"], S["communities"]
    p = {r["pair"]: r for r in mx["pairs"]}
    i1 = rb["fraction_removed"].index(0.01)
    i2 = rb["fraction_removed"].index(0.02)
    cut = br["min_node_cuts"]
    sens = S["identity_sensitivity"]
    return [
        {"title": "Three institutional islands inside one connected component",
         "observation": (f"Only {mx['inter_links_total']} of {co['edges']:,} co-author links ({mx['inter_share_pct']}%) join "
                         f"two different IIITs, although all three sit in one giant component of {co['giant_nodes']:,} authors."),
         "evidence": (f"A degree-preserving (configuration-model) null expects {mx['inter_links_expected_total']:,.0f} "
                      f"inter-institute links; observed / expected = {p['IIITA-ABV']['ratio_observed_expected']} (IIITA–ABV), "
                      f"{p['IIITA-IIITB']['ratio_observed_expected']} (IIITA–IIITB), {p['ABV-IIITB']['ratio_observed_expected']} "
                      f"(ABV–IIITB). {cs['single_institute_communities_pct']}% of the {cs['communities_10plus']} Louvain communities "
                      f"with ≥10 authors are ≥90% one institute; institute assortativity = "
                      f"{S['identity_sensitivity']['conservative']['institution_assortativity']}."),
         "meaning": "Collaboration is organised inside each institute; the three IIITs do not form a shared research community.",
         "caveat": ("Edges come from OpenAlex affiliations on papers; a missing affiliation hides a link. Low mixing is "
                    "common for institutes in three different cities and is not by itself a sign of weak research.")},
        {"title": "The IIITA–ABV link is carried by people who moved, not by joint projects",
         "observation": (f"IIITA–ABV accounts for {p['IIITA-ABV']['coauthor_links']} of the {mx['inter_links_total']} "
                         f"inter-institute links and {p['IIITA-ABV']['copublished_papers']} co-published papers, against "
                         f"{p['IIITA-IIITB']['copublished_papers']} (IIITA–IIITB) and {p['ABV-IIITB']['copublished_papers']} (ABV–IIITB)."),
         "evidence": (f"{mx['inter_papers_with_multi_affiliated_author']} of the {mx['inter_papers']} papers that link two IIITs "
                      f"include an author whom OpenAlex places at both institutes ({br['multi_affiliated_authors']} such authors, "
                      f"{br['multi_affiliated_core']} of them core faculty). The only two mixed communities are IIITA+ABV."),
         "meaning": ("Inter-IIIT ties mostly follow career mobility (e.g. a PhD at IIITA and a faculty post at ABV) — "
                     "relationships between people, not institutional partnerships."),
         "caveat": ("'Placed at both' is inferred from affiliations over 2016–2026; it may be a move, a dual "
                    "affiliation, or an OpenAlex affiliation error. We cannot tell these apart without CVs.")},
        {"title": "IIIT Bangalore hangs on eight people",
         "observation": (f"Every path from IIITB to IIITA or ABV passes through the same {cut['IIITA-IIITB']['node_connectivity']} "
                         f"authors (minimum node cut); IIITA–ABV needs {cut['IIITA-ABV']['node_connectivity']}."),
         "evidence": (f"Mean shortest-path distance IIITA–IIITB = {ds['IIITA-IIITB']} and ABV–IIITB = {ds['ABV-IIITB']} steps, "
                      f"vs {ds['IIITB-IIITB']} inside IIITB and {ds['ABV-IIITA']} for IIITA–ABV. In citations, IIITB papers cite "
                      f"the other two only {cm['excluding_self_citations']['IIITB']['IIITA'] + cm['excluding_self_citations']['IIITB']['ABV']} "
                      f"times once author self-citations are removed."),
         "meaning": "IIITB is structurally peripheral to the group; its attachment is fragile and runs through a handful of individuals.",
         "caveat": "Node cuts are computed on the 2016–2026 co-authorship snapshot; one new joint project could change them."},
        {"title": "Cross-institute reachability collapses when brokers are removed",
         "observation": (f"{rb['targeted']['cross_reach'][0] * 100:.0f}% of cross-institute author pairs are joined by some path. "
                         f"Removing the 1% of authors with the highest betweenness cuts this to "
                         f"{rb['targeted']['cross_reach'][i1] * 100:.0f}%, and 2% to {rb['targeted']['cross_reach'][i2] * 100:.1f}%."),
         "evidence": (f"Removing the same number of random authors leaves {rb['random']['cross_reach'][i1] * 100:.0f}% and "
                      f"{rb['random']['cross_reach'][i2] * 100:.0f}% (10 runs, sd ≤ {max(rb['random']['cross_reach_sd'][:i2 + 1]) * 100:.1f} pp). "
                      f"The top 5% of authors hold {co['degree']['share_of_degree_top5pct']}% of all co-author ties; max degree "
                      f"{co['degree']['max']} vs {S['er_baseline']['max_degree_sim']} in an ER graph of the same size."),
         "meaning": ("The network is robust to random loss but fragile to targeted loss — the signature of a hub-dominated "
                     "(heavy-tailed) network. Connectivity between institutes depends on a few dozen senior faculty."),
         "caveat": "Betweenness is computed once (non-adaptive removal); removing a person is a thought experiment, not a forecast."},
        {"title": "The IIITs are connected indirectly, through the same IITs",
         "observation": (f"{sp['common_to_all_three']} Indian institutions co-author with all three IIITs; the strongest common "
                         f"partners are {sp['top_common'][0]['name']} and {sp['top_common'][1]['name']}."),
         "evidence": (f"Jaccard overlap of partner sets: IIITA–ABV {sp['jaccard']['IIITA-ABV']}, IIITA–IIITB {sp['jaccard']['IIITA-IIITB']}, "
                      f"ABV–IIITB {sp['jaccard']['ABV-IIITB']}. Top 3 partners of each institute (shared papers): "
                      + "; ".join(f"{ABBR[i]}: " + ", ".join(f"{x['name']} ({x['papers']})" for x in sp["top_own"][i])
                                  for i in C.INST_NAMES) + "."),
         "meaning": ("Each IIIT's largest partners include institutions in its own city (MNNIT and the University of "
                     "Allahabad; Jiwaji University in Gwalior; IISc and NIMHANS in Bangalore), while what the three share "
                     "are national IITs. The IIITs occupy similar positions (common collaborators) without direct ties; "
                     "IIITA and ABV are the most alike."),
         "caveat": ("Shared partners show similar positions, not information flow between the IIITs through those "
                    "partners. Partner cities are read from the institution names, not from the data.")},
        {"title": "Author disambiguation changes the inter-institution picture",
         "observation": ("Merging authors only because their names match (the earlier rule) creates false bridges between "
                         "institutes; the conservative rule removes them."),
         "evidence": (f"Name-only identities: {sens['name_only']['inter_institute_links']} inter-institute links, assortativity "
                      f"{sens['name_only']['institution_assortativity']}, giant-component path length ≈ "
                      f"{sens['name_only']['giant_path_length_sampled']}. Conservative: {sens['conservative']['inter_institute_links']} links, "
                      f"{sens['conservative']['institution_assortativity']}, ≈ {sens['conservative']['giant_path_length_sampled']}."),
         "meaning": ("Common Indian names (e.g. 11 OpenAlex IDs named 'Amit Kumar' at IIITA and ABV become a single node) make naive merging "
                     "overstate integration and shorten paths. Bridge findings are only credible with careful identity rules."),
         "caveat": ("The conservative rule may still split one person into several nodes (e.g. name spelling variants), "
                    "which slightly lowers degree and can lengthen paths; see DECISIONS.md.")},
    ]


# ═════════════════════════════════════════════
# 4. FIGURES
# ═════════════════════════════════════════════

def fig_structure(mix, dist, rob):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.7))
    ax = axes[0]
    labels = [ABBR[i] for i in C.INST_NAMES]
    M = np.zeros((3, 3))
    for i, a in enumerate(C.INST_NAMES):
        M[i, i] = mix["within"][a]["coauthor_links"]
    for r in mix["pairs"]:
        i, j = C.INST_NAMES.index(r["a"]), C.INST_NAMES.index(r["b"])
        M[i, j] = M[j, i] = r["coauthor_links"]
    ax.imshow(np.log10(M + 1), cmap="Blues")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{int(M[i, j]):,}", ha="center", va="center", fontsize=10,
                    color="white" if M[i, j] > 500 else "#0b0b0b")
    ax.set_xticks(range(3), labels)
    ax.set_yticks(range(3), labels)
    ax.grid(False)
    ax.set_title("(a) Co-author links within and between institutes", fontsize=9.5)
    ax = axes[1]
    x = np.array(rob["fraction_removed"]) * 100
    ax.plot(x, rob["targeted"]["cross_reach"], "o-", color=C.TIER_COLORS[0], ms=4, label="cross-institute reach, by betweenness")
    ax.plot(x, rob["random"]["cross_reach"], "o--", color=C.TIER_COLORS[2], ms=4, label="cross-institute reach, random")
    ax.plot(x, rob["targeted"]["giant"], "s-", color="#eb6834", ms=3, lw=1.2, label="giant component, by betweenness")
    ax.plot(x, rob["random"]["giant"], "s--", color="#eda100", ms=3, lw=1.2, label="giant component, random")
    ax.set_xlabel("% of authors removed")
    ax.set_ylabel("fraction remaining")
    ax.set_ylim(0, 1.05)
    ax.set_title("(b) Robustness: removing brokers vs random authors", fontsize=9.5)
    ax.legend(fontsize=7)
    fig.tight_layout()
    save(fig, "f6_institution_structure.png")


def fig_degree(ld, er_k, cd):
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.5))
    ax = axes[0]
    ax.loglog(ld["bin_centers"], ld["pdf"], "o", color=C.TIER_COLORS[0], ms=5, label="co-authorship (log-binned)")
    ks = np.arange(1, 25)
    ax.loglog(ks, poisson_pdf(er_k, ks), "-", color=INK2, lw=1, label=f"ER / Poisson, <k> = {er_k}")
    ax.set_ylim(min(ld["pdf"]) / 3, 1)
    ax.set_xlabel("degree k (co-authors)")
    ax.set_ylabel("p(k)")
    ax.set_title("(a) Co-authorship degree distribution vs ER", fontsize=9.5)
    ax.legend(fontsize=7.5)
    ax = axes[1]
    ax.loglog(cd["bin_centers"], cd["pdf"], "o", color=C.TIER_COLORS[2], ms=5, label="citation in-degree (log-binned)")
    ax.set_xlabel("in-degree (internal citations received)")
    ax.set_ylabel("p(k)")
    ax.set_title("(b) Internal citation in-degree distribution", fontsize=9.5)
    ax.legend(fontsize=7.5)
    fig.tight_layout()
    save(fig, "f7_degree_distributions.png")


def main():
    print("=" * 65)
    print(" DPCN 2026 - Group 10 - Part 5b: Network structure & institutions")
    print("=" * 65)
    o = A.load_outputs()
    G = coauthor_graph(o)
    at = author_institutes(o["adf"])
    CG = citation_graph(o)
    S = {}
    S["coauthorship"], gc = undirected_properties(G)
    S["citation"] = citation_properties(CG)
    print("  properties done")
    S["per_institution"] = per_institution(G, at)
    S["mixing"] = mixing(G, o)
    br = bridges(G, at)
    bet = br.pop("betweenness")
    S["bridges"] = br
    S["bridge_removal"] = remove_bridges(G, br)
    print("  bridges done")
    S["distances"] = institute_distances(gc)
    S["robustness"] = robustness(G, bet)
    print("  robustness done")
    S["er_baseline"] = er_baseline(G.number_of_nodes(), G.number_of_edges())
    S["er_baseline_giant"] = er_baseline(gc.number_of_nodes(), gc.number_of_edges())
    k = S["coauthorship"]["degree"]["mean"]
    S["degree_distribution"] = {"coauthorship": log_binned([d for _, d in G.degree()]),
                                "citation_in": log_binned([d for _, d in CG.in_degree()]),
                                "citation_out": log_binned([d for _, d in CG.out_degree()])}
    S["communities"] = community_stability(G)
    S["centrality"] = centralities(gc, bet)
    S["citation_matrix"] = citation_matrix(o)
    S["shared_partners"] = shared_partners(o)
    kg = 2 * gc.number_of_edges() / gc.number_of_nodes()
    S["reference_paths"] = reference_paths(gc.number_of_nodes(), S["coauthorship"]["giant_avg_path_length"], kg)
    S["identity_sensitivity"] = identity_sensitivity(o, G)
    S["findings"] = findings(S)
    with open(C.STRUCTURE_JSON, "w", encoding="utf-8") as f:
        json.dump(S, f, indent=1, default=lambda v: v.item() if hasattr(v, "item") else str(v))
    print(f"  Saved {C.STRUCTURE_JSON}")
    fig_structure(S["mixing"], S["distances"], S["robustness"])
    fig_degree(S["degree_distribution"]["coauthorship"], k, S["degree_distribution"]["citation_in"])
    print(json.dumps(S["identity_sensitivity"], indent=1))
    for f in S["findings"]:
        print(f"\n## {f['title']}\n  {f['observation']}\n  {f['evidence']}")


if __name__ == "__main__":
    main()
