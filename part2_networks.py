"""
DPCN 2026 - Group 10 - Part 2: Citation & Authorship Networks, Citation Flow
=============================================================================
Offline - reads ./cache/ and the files written by part1b. Produces:

  citation_network.csv      directed edges "source cites target"
                            source_doi, target_doi, source_inst, target_inst, year
                            (+ ids, edge_type, cross_institute)
                            edge_type: internal          paper of ours -> paper of ours
                                       outflow_indian    ours -> work by another Indian institute
                                       inflow_indian     work by another Indian institute -> ours
                                       self_institution  external work whose only Indian
                                                         affiliation is the same institute
  authorship_network.csv    undirected co-authorship edges
                            author_a, author_b, paper_doi, inst_a, inst_b, year
                            (+ ids, edge_scope: same_institution | inter_group |
                               cross_institution_india)
  indian_connections.csv    your_inst, partner_inst, shared_papers, total_citations
                            (+ citations received from / given to the partner, cluster flags)

  group10_citation_metrics.json   PageRank / in-degree on the INTERNAL citation graph
  group10_author_metrics.json     degree / betweenness / Louvain on the INTERNAL
                                  co-authorship graph (authors of our institutions)
  group10_citation_flow.json      citation in-flow / out-flow with other Indian institutes

As required, metrics are computed WITHIN the assigned institutions; the
cross-institute edges are only included in the raw edge files.

Usage:
    python part2_networks.py
"""

import json
import sys
from collections import Counter, defaultdict
from itertools import combinations

import networkx as nx
import pandas as pd

import group10_common as C

OUR_IDS = {v[0]: k for k, v in C.INSTITUTIONS.items()}


def load():
    try:
        df = pd.read_csv(C.DATA_CSV, encoding="utf-8-sig", dtype=str, keep_default_na=False)
        adf = pd.read_csv(C.AUTHORSHIPS_CSV, encoding="utf-8-sig", dtype=str, keep_default_na=False)
        fac = pd.read_csv(C.FACULTY_CSV, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    except FileNotFoundError as e:
        print(f"ERROR: {e}. Run part1b_enrich_data.py first.")
        sys.exit(1)
    df["citations"] = df["citations"].astype(int)
    df["year"] = df["year"].astype(int)
    works = C.load_json_gz(C.WORKS_CACHE)["works"]
    inflow = C.load_json_gz(C.INFLOW_CACHE, {}).get("works", {})
    outflow = C.load_json_gz(C.OUTFLOW_CACHE, {}).get("works", {})
    return df, adf, fac, works, inflow, outflow


def corpus_index(df, works):
    """Canonical papers, their institutions and the alias -> canonical map."""
    papers = {}
    for wid, g in df.groupby("openalex_id"):
        r = g.iloc[0]
        papers[wid] = {"doi": C.normalize_doi(r["doi"]), "year": int(r["year"]),
                       "insts": sorted(g["institution"]), "title": r["title"],
                       "citations": int(r["citations"]), "type": r["type"],
                       "venue": r["journal_name"]}
    scimago = C.Scimago()
    _, _, aliases = C.select_corpus(works, scimago)
    aliases = {a: c for a, c in aliases.items() if c in papers}
    return papers, aliases


# ═══════════════════════════════════════════════════
# CITATION NETWORK + FLOW
# ═══════════════════════════════════════════════════

def inst_names(insts):
    return "; ".join(v["name"] for v in insts.values())


def build_citation_network(papers, aliases, works, inflow, outflow):
    edges = []
    internal = set()
    for src, p in papers.items():
        for ref in works[src]["refs"]:
            tgt = aliases.get(ref, ref)
            if tgt in papers and tgt != src and (src, tgt) not in internal:
                internal.add((src, tgt))
                t = papers[tgt]
                edges.append({
                    "source_doi": C.doi_or_id(p["doi"], src), "target_doi": C.doi_or_id(t["doi"], tgt),
                    "source_inst": "; ".join(p["insts"]), "target_inst": "; ".join(t["insts"]),
                    "year": p["year"], "source_openalex_id": src, "target_openalex_id": tgt,
                    "edge_type": "internal",
                    "cross_institute": not (set(p["insts"]) & set(t["insts"])),
                })

    # flows: (pair list) per institution
    flow_pairs = {"in": [], "out": []}
    corpus_like = set(papers) | set(aliases)

    for src, p in papers.items():
        for ref in works[src]["refs"]:
            if ref in corpus_like or ref not in outflow:
                continue
            cw = outflow[ref]
            own_ids = {C.INSTITUTIONS[i][0] for i in p["insts"]}
            others = {k: v for k, v in cw["insts"].items() if k not in own_ids}
            edges.append({
                "source_doi": C.doi_or_id(p["doi"], src), "target_doi": C.doi_or_id(cw["doi"], ref),
                "source_inst": "; ".join(p["insts"]), "target_inst": inst_names(cw["insts"]),
                "year": p["year"], "source_openalex_id": src, "target_openalex_id": ref,
                "edge_type": "outflow_indian" if others else "self_institution",
                "cross_institute": bool(others),
            })
    for cid, cw in inflow.items():
        if cid in corpus_like:
            continue
        for t in cw.get("cites", []):
            tgt = aliases.get(t, t)
            if tgt not in papers:
                continue
            p = papers[tgt]
            own_ids = {C.INSTITUTIONS[i][0] for i in p["insts"]}
            others = {k: v for k, v in cw["insts"].items() if k not in own_ids}
            edges.append({
                "source_doi": C.doi_or_id(cw["doi"], cid), "target_doi": C.doi_or_id(p["doi"], tgt),
                "source_inst": inst_names(cw["insts"]), "target_inst": "; ".join(p["insts"]),
                "year": cw["year"], "source_openalex_id": cid, "target_openalex_id": tgt,
                "edge_type": "inflow_indian" if others else "self_institution",
                "cross_institute": bool(others),
            })
    edge_df = pd.DataFrame(edges).drop_duplicates(["source_openalex_id", "target_openalex_id"])
    return edge_df


def citation_flow(papers, aliases, works, inflow, outflow):
    """In-/out-flow of citations between each assigned institution and every
    OTHER Indian institution (including the other two group institutions)."""
    flow = {}
    corpus_like = set(papers) | set(aliases)
    for inst, (iid, _) in C.INSTITUTIONS.items():
        mine = {w for w, p in papers.items() if inst in p["insts"]}
        in_pairs = out_pairs = 0
        in_works, out_works = set(), set()
        in_by_year, out_by_year = Counter(), Counter()
        in_partner, out_partner = Counter(), Counter()
        in_cluster, out_cluster = Counter(), Counter()
        names, clusters = {}, {}
        citing_papers = {}

        def note(pid, v):
            names[pid] = v["name"]
            clusters[pid] = C.institution_cluster(v["name"], v.get("type", ""))

        for cid, cw in inflow.items():
            others = {k: v for k, v in cw["insts"].items() if k != iid}
            if not others:
                continue
            targets = {aliases.get(t, t) for t in cw.get("cites", [])} & mine
            targets.discard(cid)
            if not targets:
                continue
            n = len(targets)
            in_pairs += n
            in_works.add(cid)
            if cw.get("year"):
                in_by_year[int(cw["year"])] += n
            for k, v in others.items():
                note(k, v)
                in_partner[k] += n
            for cl in {C.institution_cluster(v["name"], v.get("type", "")) for v in others.values()}:
                in_cluster[cl] += n
            if cid not in corpus_like:
                citing_papers[cid] = cw

        for src in mine:
            for ref in works[src]["refs"]:
                if ref not in outflow or aliases.get(ref, ref) == src:
                    continue
                cw = outflow[ref]
                others = {k: v for k, v in cw["insts"].items() if k != iid}
                if not others:
                    continue
                out_pairs += 1
                out_works.add(ref)
                out_by_year[papers[src]["year"]] += 1
                for k, v in others.items():
                    note(k, v)
                    out_partner[k] += 1
                for cl in {C.institution_cluster(v["name"], v.get("type", "")) for v in others.values()}:
                    out_cluster[cl] += 1

        def top(counter, k=10):
            return [{"id": pid, "name": names[pid], "cluster": clusters[pid],
                     "intra_group": pid in OUR_IDS, "count": n}
                    for pid, n in counter.most_common(k)]

        top_citing = sorted(citing_papers.values(), key=lambda w: -w["cited_by_count"])[:10]
        flow[inst] = {
            "in_citations": in_pairs, "out_citations": out_pairs,
            "in_citing_works": len(in_works), "out_cited_works": len(out_works),
            "impact_ratio": round(in_pairs / out_pairs, 3) if out_pairs else None,
            "by_year": {str(y): {"in": in_by_year.get(y, 0), "out": out_by_year.get(y, 0)}
                        for y in range(C.START_YEAR, C.END_YEAR + 1)},
            "top_citing_institutes": top(in_partner),
            "top_cited_institutes": top(out_partner),
            "in_by_cluster": dict(in_cluster.most_common()),
            "out_by_cluster": dict(out_cluster.most_common()),
            "top_citing_papers": [{"title": w["title"], "doi": w["doi"], "year": w["year"],
                                   "citations": w["cited_by_count"],
                                   "institutes": [v["name"] for v in w["insts"].values()][:4]}
                                  for w in top_citing],
            "partner_in": dict(in_partner), "partner_out": dict(out_partner),
            "partner_names": names, "partner_clusters": clusters,
        }
    return flow


def citation_metrics(papers, edge_df):
    internal = edge_df[edge_df["edge_type"] == "internal"]
    G = nx.DiGraph()
    G.add_nodes_from(papers)
    G.add_edges_from(zip(internal["source_openalex_id"], internal["target_openalex_id"]))
    pr = nx.pagerank(G, alpha=0.85, max_iter=500)
    indeg = dict(G.in_degree())
    wcc = max(nx.weakly_connected_components(G), key=len) if G.number_of_edges() else set()
    deg_dist = Counter(indeg.values())
    top = sorted(papers, key=lambda w: (-pr[w], -papers[w]["citations"]))[:10]
    cross = internal["cross_institute"].astype(str).str.upper().eq("TRUE").sum()
    summary = {
        "nodes": G.number_of_nodes(), "internal_edges": G.number_of_edges(),
        "cross_institution_internal_edges": int(cross),
        "papers_cited_internally": sum(1 for v in indeg.values() if v > 0),
        "largest_weak_component": len(wcc),
        "mean_in_degree": round(G.number_of_edges() / max(G.number_of_nodes(), 1), 4),
        "max_in_degree": max(indeg.values()) if indeg else 0,
        "in_degree_distribution": {str(k): v for k, v in sorted(deg_dist.items())},
        "edge_types": edge_df["edge_type"].value_counts().to_dict(),
    }
    top10 = [{"openalex_id": w, "doi": papers[w]["doi"], "title": papers[w]["title"],
              "institutions": papers[w]["insts"], "year": papers[w]["year"],
              "in_degree": indeg[w], "pagerank": round(pr[w], 8),
              "citations": papers[w]["citations"]} for w in top]
    return {"summary": summary, "pagerank_top10": top10,
            "pagerank": {k: round(v, 8) for k, v in pr.items()}, "in_degree": indeg}


# ═══════════════════════════════════════════════════
# AUTHORSHIP NETWORK
# ═══════════════════════════════════════════════════

def build_authorship(df, adf, fac, works):
    paper_meta = df.drop_duplicates("openalex_id").set_index("openalex_id")
    node_inst = (adf.groupby(["author_id", "institution"]).size().reset_index(name="n")
                 .sort_values("n", ascending=False).drop_duplicates("author_id")
                 .set_index("author_id")["institution"].to_dict())
    node_name = adf.drop_duplicates("author_id").set_index("author_id")["author_name"].to_dict()
    raw_to_canon = dict(zip(adf["raw_author_id"], adf["author_id"]))

    rows = []
    G = nx.Graph()
    G.add_nodes_from(node_inst)
    ext_partners = defaultdict(set)      # our author -> external Indian institution ids
    for wid, g in adf.groupby("openalex_id"):
        meta = paper_meta.loc[wid]
        doi = C.normalize_doi(meta["doi"])
        year = int(meta["year"])
        ours = {}
        for aid, inst in zip(g["author_id"], g["institution"]):
            ours.setdefault(aid, inst)
        for a, b in combinations(sorted(ours), 2):
            ia, ib = ours[a], ours[b]
            scope = "same_institution" if ia == ib else "inter_group"
            rows.append({"author_a": node_name[a], "author_b": node_name[b], "paper_doi": doi,
                         "inst_a": ia, "inst_b": ib, "year": year,
                         "author_a_id": a, "author_b_id": b, "edge_scope": scope})
            if G.has_edge(a, b):
                G[a][b]["weight"] += 1
            else:
                G.add_edge(a, b, weight=1)
        if meta["is_hyperauthored"] == "True":
            continue      # mega-collaborations would add thousands of meaningless edges
        for au in works[wid]["authorships"]:
            if raw_to_canon.get(au["aid"]) in ours:
                continue
            ind = [i for i in au["insts"] if i["cc"] == "IN" and i["id"] not in OUR_IDS]
            if not ind:
                continue
            ext = ind[0]
            for a, ia in ours.items():
                ext_partners[a].add(ext["id"])
                rows.append({"author_a": node_name[a], "author_b": au["name"], "paper_doi": doi,
                             "inst_a": ia, "inst_b": ext["name"], "year": year,
                             "author_a_id": a, "author_b_id": au["aid"],
                             "edge_scope": "cross_institution_india"})
    edge_df = pd.DataFrame(rows)

    print(f"  Internal graph: {G.number_of_nodes()} authors, {G.number_of_edges()} edges")
    deg = nx.degree_centrality(G)
    strength = dict(G.degree(weight="weight"))
    if G.number_of_nodes() <= 6000:
        bet = nx.betweenness_centrality(G, normalized=True)
    else:
        bet = nx.betweenness_centrality(G, k=1500, normalized=True, seed=42)
    comms = nx.community.louvain_communities(G, weight="weight", seed=42)
    comms = sorted(comms, key=len, reverse=True)
    modularity = nx.community.modularity(G, comms, weight="weight")
    part = {n: i for i, c in enumerate(comms) for n in c}
    components = list(nx.connected_components(G))
    giant = max(components, key=len)

    fac_idx = fac.drop_duplicates("author_id").set_index("author_id")
    nodes = {}
    for n in G.nodes():
        f = fac_idx.loc[n] if n in fac_idx.index else None
        nodes[n] = {
            "name": node_name[n], "institution": node_inst[n],
            "department": f["department"] if f is not None else "",
            "is_core_faculty": (f["is_core_faculty"] == "True") if f is not None else False,
            "papers": int(f["papers"]) if f is not None else 0,
            "degree": G.degree(n), "strength": strength[n],
            "degree_centrality": round(deg[n], 6),
            "betweenness_centrality": round(bet[n], 8),
            "community": part[n],
            "external_indian_partner_institutes": len(ext_partners.get(n, ())),
        }

    comm_info = []
    for i, c in enumerate(comms[:25]):
        insts = Counter(nodes[n]["institution"] for n in c)
        depts = Counter(nodes[n]["department"] for n in c if nodes[n]["department"])
        lead = sorted(c, key=lambda n: -nodes[n]["strength"])[:3]
        comm_info.append({"id": i, "size": len(c), "institutions": dict(insts),
                          "dominant_department": depts.most_common(1)[0][0] if depts else "",
                          "top_authors": [nodes[n]["name"] for n in lead]})

    # hub authors: bridge many Indian institutes and sit between communities
    hubs = sorted(nodes.items(), key=lambda kv: (-kv[1]["external_indian_partner_institutes"],
                                                 -kv[1]["betweenness_centrality"]))[:15]
    summary = {
        "nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
        # distinct author pairs who co-wrote a paper while at two different assigned institutes
        "inter_group_edges": int(edge_df[edge_df["edge_scope"] == "inter_group"]
                                 [["author_a_id", "author_b_id"]].drop_duplicates().shape[0]),
        "components": len(components), "giant_component": len(giant),
        "isolated_authors": sum(1 for c in components if len(c) == 1),
        "density": round(nx.density(G), 6),
        "avg_clustering": round(nx.average_clustering(G), 4),
        "communities": len(comms), "modularity": round(modularity, 4),
        "edge_scopes": edge_df["edge_scope"].value_counts().to_dict(),
    }
    return edge_df, {"summary": summary, "communities": comm_info,
                     "hub_authors": [dict(v, author_id=k) for k, v in hubs], "nodes": nodes}


# ═══════════════════════════════════════════════════
# INDIAN CONNECTIONS
# ═══════════════════════════════════════════════════

def build_indian_connections(df, flow):
    shared, cites, names = defaultdict(int), defaultdict(int), {}
    for inst, ids, nms, c in zip(df["institution"], df["coauthor_institute_ids"],
                                 df["coauthor_institutes"], df["citations"]):
        for iid, nm in zip(ids.split(";"), nms.split(";")):
            if iid:
                shared[(inst, iid)] += 1
                cites[(inst, iid)] += c
                names[iid] = nm
    rows = []
    for inst in C.INST_NAMES:
        f = flow[inst]
        partner_ids = ({p for (i, p) in shared if i == inst} |
                       set(f["partner_in"]) | set(f["partner_out"]))
        for pid in partner_ids:
            name = names.get(pid) or f["partner_names"].get(pid, pid)
            cl = f["partner_clusters"].get(pid) or C.institution_cluster(name)
            rows.append({
                "your_inst": inst, "partner_inst": name,
                "shared_papers": shared.get((inst, pid), 0),
                "total_citations": cites.get((inst, pid), 0),
                "citations_received_from_partner": f["partner_in"].get(pid, 0),
                "citations_given_to_partner": f["partner_out"].get(pid, 0),
                "partner_openalex_id": pid, "partner_cluster": cl,
                "cross_cluster": cl != C.OUR_CLUSTER,
                "cluster_link": f"{C.OUR_CLUSTER} <-> {cl}",
                "intra_group": pid in OUR_IDS,
            })
    return (pd.DataFrame(rows)
            .sort_values(["your_inst", "shared_papers", "citations_received_from_partner"],
                         ascending=[True, False, False]))


def main():
    print("=" * 65)
    print(" DPCN 2026 - Group 10 - Part 2: Networks & citation flow")
    print("=" * 65)
    df, adf, fac, works, inflow, outflow = load()
    papers, aliases = corpus_index(df, works)
    print(f"  {len(papers)} unique papers | in-flow cache {len(inflow)} | out-flow cache {len(outflow)}")

    print("\n[A] Citation network")
    cedges = build_citation_network(papers, aliases, works, inflow, outflow)
    cedges.to_csv(C.CITATION_CSV, index=False, encoding="utf-8-sig")
    print(f"  Saved {C.CITATION_CSV}: {len(cedges)} edges")
    print("  " + str(cedges["edge_type"].value_counts().to_dict()))
    cm = citation_metrics(papers, cedges)
    with open(C.CITE_METRICS, "w", encoding="utf-8") as f:
        json.dump(cm, f, indent=1)
    print(f"  Internal graph: {cm['summary']}")
    for t in cm["pagerank_top10"][:5]:
        print(f"    PR={t['pagerank']:.5f} in={t['in_degree']:3d}  {t['title'][:70]}")

    print("\n[B] Citation flow with other Indian institutes")
    flow = citation_flow(papers, aliases, works, inflow, outflow)
    with open(C.FLOW_JSON, "w", encoding="utf-8") as f:
        json.dump(flow, f, indent=1)
    for inst, fl in flow.items():
        print(f"  {inst:18s} in={fl['in_citations']:6d} out={fl['out_citations']:6d} "
              f"ratio={fl['impact_ratio']}")

    print("\n[C] Authorship network")
    aedges, am = build_authorship(df, adf, fac, works)
    aedges.to_csv(C.AUTHORSHIP_CSV, index=False, encoding="utf-8-sig")
    with open(C.AUTH_METRICS, "w", encoding="utf-8") as f:
        json.dump(am, f, indent=1)
    print(f"  Saved {C.AUTHORSHIP_CSV}: {len(aedges)} edges | {am['summary']}")

    print("\n[D] Indian connections")
    ind = build_indian_connections(df, flow)
    ind.to_csv(C.INDIAN_CSV, index=False, encoding="utf-8-sig")
    print(f"  Saved {C.INDIAN_CSV}: {len(ind)} rows")
    print(ind[ind["shared_papers"] > 0].groupby("your_inst").head(3)
          [["your_inst", "partner_inst", "shared_papers", "partner_cluster"]].to_string(index=False))

    print("=" * 65)
    print(" Part 2 complete. Next: python part3_statistics.py")
    print("=" * 65)


if __name__ == "__main__":
    main()
