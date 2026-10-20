"""
DPCN 2026 - Group 10: Research Mapping Dashboard (Streamlit)
=============================================================
IIIT Allahabad · ABV-IIITM Gwalior · IIIT Bangalore, 2016-2026.

Run locally:      streamlit run app.py
Data files come from part1 -> part1b -> part2 (see README.md). The sidebar
filters (institutions, years, publication type, search) apply to every tab;
faculty metrics are recomputed for the selected years.
"""

import math

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import group10_analysis as A
import group10_common as C

st.set_page_config(page_title="Group 10 Research Map", page_icon="🎓", layout="wide")

COLORS = C.INST_COLORS
TIER = {k: v for k, v in zip(A.QUARTILES + ["Unranked"], C.TIER_COLORS)}
TIER.update({k: v for k, v in zip(A.CORE_RANKS + ["Unranked"], C.TIER_COLORS)})
COMM_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]


@st.cache_data(show_spinner="Loading research data ...")
def load():
    return A.load_outputs()


def layout(fig, h=340, legend=True):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, title=None) if legend else None,
                      showlegend=legend)
    return fig


def faculty_stats(adf_f, fac):
    """Faculty metrics for the filtered authorships (years / type)."""
    if adf_f.empty:
        return pd.DataFrame()
    g = adf_f.drop_duplicates(["institution", "author_id", "openalex_id"])
    agg = g.groupby(["institution", "author_id"]).agg(
        papers=("openalex_id", "count"), citations=("citations", "sum"),
        q1_papers=("quartile", lambda q: int((q == "Q1").sum())),
        h_index=("citations", C.hindex)).reset_index()
    top = (g[g["journal_name"] != ""].groupby(["institution", "author_id"])["journal_name"]
           .agg(lambda s: s.value_counts().index[0]).rename("top_journal").reset_index())
    meta = fac[["institution", "author_id", "name", "department", "department_source",
                "is_core_faculty", "h_index_lifetime_openalex"]]
    out = agg.merge(top, how="left").merge(meta, how="left")
    out["is_core_faculty"] = out["is_core_faculty"].fillna(False).astype(bool)
    out["top_journal"] = out["top_journal"].fillna("")
    return out.sort_values(["h_index", "citations"], ascending=False)


O = load()
df_all, fac_all, adf_all = O["df"], O["fac"], O["adf"]
if df_all.empty:
    st.error("group10_data.csv not found - run part1_collect_data.py, part1b_enrich_data.py and part2_networks.py.")
    st.stop()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS (apply to every tab)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Group 10 · DPCN 2026")
    st.caption("Instructor: Chittaranjan Hens")
    sel = st.multiselect("Institutions", C.INST_NAMES, default=C.INST_NAMES)
    yr = st.slider("Publication years", C.START_YEAR, C.END_YEAR, (C.START_YEAR, C.END_YEAR))
    ptype = st.radio("Publication type", ["All", "journal", "conference"], horizontal=True)
    query = st.text_input("Search title / author / venue / DOI")
    core_only = st.checkbox("Faculty tables: core faculty only", value=True,
                            help="≥5 papers in ≥3 years, last author on ≥30% and first author on ≤50% of them")
    st.divider()
    st.caption("\n".join(f"**{i}** — OpenAlex {v[0]} · ROR {v[1]}" for i, v in C.INSTITUTIONS.items()))
    st.caption("2026 is a partial year. Sources: OpenAlex, Scimago SJR, ICORE2026.")

sel = sel or C.INST_NAMES
df = df_all[df_all["institution"].isin(sel) & df_all["year"].between(*yr)]
if ptype != "All":
    df = df[df["type"] == ptype]
if query.strip():
    q = query.strip().lower()
    df = df[df["title"].str.lower().str.contains(q, regex=False) | df["author"].str.lower().str.contains(q, regex=False)
            | df["journal_name"].str.lower().str.contains(q, regex=False) | df["doi"].str.lower().str.contains(q, regex=False)]
ids = set(df["openalex_id"])
adf = adf_all[adf_all["openalex_id"].isin(ids) & adf_all["institution"].isin(sel)]
fac = faculty_stats(adf, fac_all)
fac_view = fac[fac["is_core_faculty"]] if core_only and not fac.empty else fac

st.title("Research output of three IIITs, 2016–2026")
st.caption(" · ".join(sel) + f" · {yr[0]}–{yr[1]} · {ptype} papers · {len(A.unique_papers(df)):,} unique papers")

tabs = st.tabs(["Overview", "Institutions & faculty", "Citation network", "Authorship network",
                "Indian connectivity", "Data & downloads", "Key findings"])

# ═════════════════════════════════════════════
# OVERVIEW
# ═════════════════════════════════════════════
with tabs[0]:
    summ = A.institution_summary(df, fac_all[fac_all["institution"].isin(sel)])
    cols = st.columns(len(sel))
    for c, inst in zip(cols, sel):
        s = summ[summ["institution"] == inst].iloc[0]
        c.metric(inst, f"{int(s.papers):,} papers", f"{s.q1_journal_pct}% of journal papers in Q1", delta_color="off")
        c.caption(f"{int(s.citations):,} citations · median {s.median_citations} · h-index {int(s.h_index)} · "
                  f"{int(s.core_faculty)} core faculty")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Publication trend")
        t = A.publication_trend(df)
        fig = px.line(t, x="year", y="papers", color="institution", markers=True, color_discrete_map=COLORS)
        fig.update_xaxes(dtick=1)
        st.plotly_chart(layout(fig), width="stretch")
        st.caption("2026 is incomplete (collection date).")
    with c2:
        st.subheader("Median citations by publication year")
        a = A.citation_age(df)
        fig = px.line(a, x="year", y="median", color="institution", markers=True, color_discrete_map=COLORS)
        fig.update_xaxes(dtick=1)
        st.plotly_chart(layout(fig), width="stretch")

    c1, c2 = st.columns(2)
    for c, tab, title in [(c1, A.quartile_table(df), "Journal quartile distribution (SJR, % of journal papers)"),
                          (c2, A.core_table(df), "Conference rank – CORE (% of conference papers)")]:
        with c:
            st.subheader(title)
            tab = tab.loc[[i for i in sel if i in tab.index]]
            long = (tab.div(tab.sum(axis=1).replace(0, 1), axis=0) * 100).round(1).reset_index() \
                .melt(id_vars="institution", var_name="rank", value_name="share")
            long["papers"] = tab.reset_index().melt(id_vars="institution")["value"].values
            fig = px.bar(long, y="institution", x="share", color="rank", orientation="h",
                         color_discrete_map=TIER, hover_data=["papers"])
            fig.update_xaxes(range=[0, 100], title="%")
            st.plotly_chart(layout(fig, 260), width="stretch")

    st.subheader("Research area breakdown (% of papers per OpenAlex field)")
    ra = A.research_areas(df, "field", 8).loc[sel].reset_index().melt(id_vars="institution", var_name="field",
                                                                        value_name="share")
    fig = px.bar(ra, x="field", y="share", color="institution", barmode="group", color_discrete_map=COLORS)
    st.plotly_chart(layout(fig, 380), width="stretch")

    st.subheader("Top 10 most-cited papers")
    mc = A.most_cited(df, 10)
    st.dataframe(mc, hide_index=True, width="stretch",
                 column_config={"doi": st.column_config.LinkColumn("DOI"),
                                "citations": st.column_config.NumberColumn(format="%d")})

# ═════════════════════════════════════════════
# INSTITUTIONS & FACULTY
# ═════════════════════════════════════════════
with tabs[1]:
    inst = st.radio("Institution", sel, horizontal=True)
    s = A.institution_summary(df, fac_all).set_index("institution").loc[inst]
    m = st.columns(6)
    m[0].metric("Papers", f"{int(s.papers):,}", f"{int(s.journal_papers)} J · {int(s.conference_papers)} C", delta_color="off")
    m[1].metric("Q1 journal share", f"{s.q1_journal_pct}%", f"{s.unranked_journal_pct}% unranked", delta_color="off")
    m[2].metric("CORE A*/A papers", int(s.core_astar_a))
    m[3].metric("Citations", f"{int(s.citations):,}", f"median {s.median_citations}", delta_color="off")
    m[4].metric("Institutional h-index", int(s.h_index))
    m[5].metric("Core faculty", int(s.core_faculty), f"{int(s.affiliated_authors)} affiliated authors", delta_color="off")
    sub = df[df["institution"] == inst]

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Papers per year by type")
        t = A.publication_trend(sub, by_type=True)
        fig = px.bar(t, x="year", y="papers", color="type",
                     color_discrete_map={"journal": C.TIER_COLORS[0], "conference": C.TIER_COLORS[3]})
        fig.update_xaxes(dtick=1)
        st.plotly_chart(layout(fig), width="stretch")
    with c2:
        st.subheader("Faculty h-index distribution")
        f = fac_view[fac_view["institution"] == inst]
        fig = px.histogram(f, x="h_index", nbins=int(f["h_index"].max() + 1) if len(f) else 1,
                           color_discrete_sequence=[COLORS[inst]])
        fig.update_layout(bargap=0.08)
        fig.update_xaxes(title="h-index (selected years)")
        fig.update_yaxes(title="faculty")
        st.plotly_chart(layout(fig, legend=False), width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 5 journals")
        st.dataframe(A.top_venues(df, inst, "journal"), hide_index=True, width="stretch")
        st.subheader("Top 5 conferences / proceedings")
        st.dataframe(A.top_venues(df, inst, "conference"), hide_index=True, width="stretch")
    with c2:
        st.subheader("Research areas (top OpenAlex subfields)")
        sf = sub[sub["subfield"] != ""]["subfield"].value_counts().head(10).sort_values()
        fig = px.bar(x=sf.values, y=sf.index, orientation="h", color_discrete_sequence=[COLORS[inst]])
        fig.update_xaxes(title="papers")
        fig.update_yaxes(title=None)
        st.plotly_chart(layout(fig, 380, legend=False), width="stretch")

    st.subheader("Departments")
    dep = A.department_breakdown(adf[adf["institution"] == inst], fac_all)
    if not dep.empty:
        st.dataframe(dep.sort_values("papers", ascending=False), hide_index=True, width="stretch")
    st.caption("Department from 'Department of …' in the authors' affiliation strings; otherwise inferred from the "
               "author's dominant OpenAlex field (department_source).")

    st.subheader("Faculty list & performance (sortable)")
    show = fac_view[fac_view["institution"] == inst][
        ["name", "department", "department_source", "papers", "q1_papers", "citations", "h_index",
         "h_index_lifetime_openalex", "top_journal"]]
    st.dataframe(show, hide_index=True, width="stretch", height=420,
                 column_config={"h_index": st.column_config.NumberColumn("h-index (selected years)"),
                                "h_index_lifetime_openalex": st.column_config.NumberColumn("lifetime h (OpenAlex)")})

    st.subheader("Top 10 most-cited papers")
    st.dataframe(A.most_cited(df, 10, inst), hide_index=True, width="stretch",
                 column_config={"doi": st.column_config.LinkColumn("DOI")})


def draw_graph(G, color_of, size_of, text_of, directed=False, height=560):
    pos = nx.spring_layout(G, k=1.2 / math.sqrt(max(G.number_of_nodes(), 1)), iterations=60, seed=42)
    ex, ey = [], []
    for a, b in G.edges():
        ex += [pos[a][0], pos[b][0], None]
        ey += [pos[a][1], pos[b][1], None]
    fig = go.Figure([go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=0.6, color="#a8a7a1"), hoverinfo="none")])
    nodes = list(G.nodes())
    fig.add_trace(go.Scatter(x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes], mode="markers",
                             marker=dict(color=[color_of(n) for n in nodes], size=[size_of(n) for n in nodes],
                                         line=dict(width=1, color="#fcfcfb")),
                             text=[text_of(n) for n in nodes], hoverinfo="text"))
    if directed:
        fig.update_layout(annotations=[dict(ax=pos[a][0], ay=pos[a][1], x=pos[b][0], y=pos[b][1], xref="x", yref="y",
                                            axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=0.8,
                                            arrowwidth=0.6, arrowcolor="#a8a7a1", opacity=0.6)
                                       for a, b in list(G.edges())[:400]])
    fig.update_layout(height=height, showlegend=False, margin=dict(l=0, r=0, t=0, b=0),
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


# ═════════════════════════════════════════════
# CITATION NETWORK
# ═════════════════════════════════════════════
with tabs[2]:
    cm = O["cite_metrics"]
    edges = O["cite_edges"]
    if not cm or edges.empty:
        st.info("Run part2_networks.py to build the citation network.")
    else:
        s = cm["summary"]
        m = st.columns(4)
        m[0].metric("Papers (nodes)", f"{s['nodes']:,}")
        m[1].metric("Internal citation edges", f"{s['internal_edges']:,}",
                    f"{s['cross_institution_internal_edges']} across institutes", delta_color="off")
        m[2].metric("Papers cited internally", f"{s['papers_cited_internally']:,}")
        m[3].metric("Largest weak component", f"{s['largest_weak_component']:,}")
        st.caption("Metrics are computed on the internal graph (papers of the three institutes citing each other). "
                   "Edges to/from other Indian institutes are in citation_network.csv (edge_type).")
        internal = edges[(edges["edge_type"] == "internal") & edges["source_openalex_id"].isin(ids)
                         & edges["target_openalex_id"].isin(ids)]
        pr, indeg = cm["pagerank"], cm["in_degree"]
        meta = df.drop_duplicates("openalex_id").set_index("openalex_id")
        insts = df.groupby("openalex_id")["institution"].apply(list).to_dict()
        c1, c2 = st.columns([3, 2])
        with c1:
            st.subheader("Internal citation graph (top papers by PageRank)")
            n_top = st.slider("Papers shown", 50, 400, 180, 10)
            nodes = set(internal["source_openalex_id"]) | set(internal["target_openalex_id"])
            top = set(sorted(nodes, key=lambda w: -pr.get(w, 0))[:n_top])
            G = nx.DiGraph()
            G.add_nodes_from(top)
            G.add_edges_from((a, b) for a, b in zip(internal["source_openalex_id"], internal["target_openalex_id"])
                             if a in top and b in top)
            maxpr = max([pr.get(n, 0) for n in G] + [1e-9])
            st.plotly_chart(draw_graph(
                G, lambda n: COLORS.get(insts.get(n, [""])[0], "#a8a7a1"),
                lambda n: 5 + 18 * math.sqrt(pr.get(n, 0) / maxpr),
                lambda n: f"<b>{meta.loc[n, 'title'][:90]}</b><br>{' & '.join(insts.get(n, []))} · {meta.loc[n, 'year']}"
                          f"<br>PageRank {pr.get(n, 0):.5f} · in-degree {indeg.get(n, 0)}",
                directed=True), width="stretch")
            st.caption("Colour = institution · size ∝ PageRank · arrow A → B means A cites B")
        with c2:
            st.subheader("PageRank top 10")
            top10 = pd.DataFrame(cm["pagerank_top10"])
            top10 = top10[top10["openalex_id"].isin(ids)]
            st.dataframe(top10[["title", "institutions", "year", "in_degree", "pagerank", "citations"]],
                         hide_index=True, width="stretch")
            st.subheader("In-degree distribution")
            d = pd.Series(indeg)
            d = d[d.index.isin(ids) & (d > 0)].value_counts().sort_index()
            fig = px.scatter(x=d.index, y=d.values, log_x=True, log_y=True)
            fig.update_xaxes(title="in-degree")
            fig.update_yaxes(title="papers")
            st.plotly_chart(layout(fig, 280, legend=False), width="stretch")

# ═════════════════════════════════════════════
# AUTHORSHIP NETWORK
# ═════════════════════════════════════════════
with tabs[3]:
    am = O["auth_metrics"]
    ae = O["auth_edges"]
    if not am:
        st.info("Run part2_networks.py to build the authorship network.")
    else:
        s = am["summary"]
        m = st.columns(4)
        m[0].metric("Authors (nodes)", f"{s['nodes']:,}")
        m[1].metric("Co-author links", f"{s['edges']:,}", f"{s['inter_group_edges']} between institutes", delta_color="off")
        m[2].metric("Louvain communities", s["communities"], f"modularity {s['modularity']}", delta_color="off")
        m[3].metric("Giant component", f"{s['giant_component']:,}")
        nd = pd.DataFrame.from_dict(am["nodes"], orient="index")
        nd = nd[nd["institution"].isin(sel)]
        big = [c["id"] for c in am["communities"][:7]]
        c1, c2 = st.columns([3, 2])
        with c1:
            st.subheader("Co-authorship graph (colour = Louvain community)")
            n_top = st.slider("Authors shown", 50, 400, 200, 10)
            top = set(nd.sort_values("strength", ascending=False).head(n_top).index)
            sub_e = ae[ae["edge_scope"].isin(["same_institution", "inter_group"]) & ae["author_a_id"].isin(top)
                       & ae["author_b_id"].isin(top) & ae["year"].between(*yr)]
            G = nx.Graph()
            G.add_nodes_from(top)
            G.add_edges_from(zip(sub_e["author_a_id"], sub_e["author_b_id"]))
            maxd = max([nd.loc[n, "degree"] for n in G] + [1])
            st.plotly_chart(draw_graph(
                G, lambda n: COMM_COLORS[big.index(nd.loc[n, "community"])] if nd.loc[n, "community"] in big else "#b5b4ae",
                lambda n: 5 + 14 * math.sqrt(nd.loc[n, "degree"] / maxd),
                lambda n: f"<b>{nd.loc[n, 'name']}</b><br>{nd.loc[n, 'institution']} · {nd.loc[n, 'department']}"
                          f"<br>community C{nd.loc[n, 'community']} · {nd.loc[n, 'degree']} co-authors"),
                width="stretch")
            st.caption("Largest 7 communities coloured; others grey. Size ∝ number of co-authors.")
        with c2:
            st.subheader("Degree centrality – top 10")
            st.dataframe(nd.sort_values("degree_centrality", ascending=False).head(10)[
                ["name", "institution", "department", "degree", "degree_centrality"]], hide_index=True,
                width="stretch")
            st.subheader("Betweenness centrality – top 10")
            st.dataframe(nd.sort_values("betweenness_centrality", ascending=False).head(10)[
                ["name", "institution", "department", "betweenness_centrality"]], hide_index=True,
                width="stretch")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Largest communities")
            st.dataframe(pd.DataFrame(am["communities"][:12]), hide_index=True, width="stretch")
        with c2:
            st.subheader("Hub authors (bridge most Indian institutes)")
            hubs = pd.DataFrame(am["hub_authors"])
            st.dataframe(hubs[hubs["institution"].isin(sel)][["name", "institution",
                                                              "external_indian_partner_institutes",
                                                              "betweenness_centrality"]],
                         hide_index=True, width="stretch")

# ═════════════════════════════════════════════
# INDIAN CONNECTIVITY
# ═════════════════════════════════════════════
with tabs[4]:
    flow, ind, jac = O["flow"], O["indian"], O["jaccard"]
    if not flow:
        st.info("Run part2_networks.py to compute the citation flow.")
    else:
        cols = st.columns(len(sel))
        for c, inst in zip(cols, sel):
            f = flow[inst]
            c.metric(f"{inst} – in/out ratio", f["impact_ratio"],
                     f"{f['in_citations']:,} received · {f['out_citations']:,} given", delta_color="off")
        st.subheader("Year-wise citation flow with other Indian institutes")
        rows = [{"institution": i, "year": int(y), "direction": d, "citations": v[d]}
                for i in sel for y, v in flow[i]["by_year"].items() for d in ("in", "out")
                if yr[0] <= int(y) <= yr[1]]
        fig = px.line(pd.DataFrame(rows), x="year", y="citations", color="institution", line_dash="direction",
                      markers=True, color_discrete_map=COLORS)
        fig.update_xaxes(dtick=1)
        st.plotly_chart(layout(fig, 360), width="stretch")
        st.caption("in = citations received from works with another Indian affiliation (by citing year); "
                   "out = citations our papers give to such works (by our paper's year).")

        inst = st.radio("Institution ", sel, horizontal=True)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Top 10 Indian institutes citing us")
            st.dataframe(pd.DataFrame(flow[inst]["top_citing_institutes"])[["name", "cluster", "count"]],
                         hide_index=True, width="stretch")
            st.subheader("Top 10 Indian institutes we cite")
            st.dataframe(pd.DataFrame(flow[inst]["top_cited_institutes"])[["name", "cluster", "count"]],
                         hide_index=True, width="stretch")
        with c2:
            st.subheader("Top 10 most-cited papers citing us")
            st.dataframe(pd.DataFrame(flow[inst]["top_citing_papers"]), hide_index=True, width="stretch")
            st.subheader("Citations by partner cluster")
            cl = pd.DataFrame({"received": flow[inst]["in_by_cluster"], "given": flow[inst]["out_by_cluster"]}).fillna(0)
            st.dataframe(cl.sort_values("received", ascending=False), width="stretch")

        st.subheader("Co-authorship partners (connectivity map)")
        part = A.top_partners(ind, inst, 30)
        st.dataframe(part[["partner_inst", "partner_cluster", "shared_papers", "total_citations",
                           "citations_received_from_partner", "citations_given_to_partner", "cross_cluster",
                           "intra_group"]], hide_index=True, width="stretch")
        cl = A.cluster_links(ind)
        cl = cl.loc[[i for i in sel if i in cl.index]].reset_index().melt(id_vars="your_inst", var_name="cluster",
                                                                         value_name="shared_papers")
        fig = px.bar(cl, y="cluster", x="shared_papers", color="your_inst", orientation="h", barmode="group",
                     color_discrete_map=COLORS)
        st.plotly_chart(layout(fig, 420), width="stretch")

        st.subheader("Research-topic similarity (Jaccard on OpenAlex subfields)")
        st.dataframe(jac[jac["entity_a"].isin(sel)], hide_index=True, width="stretch",
                     column_config={"jaccard_similarity": st.column_config.ProgressColumn(
                         "Jaccard", min_value=0.0, max_value=1.0, format="%.3f"),
                         "weighted_jaccard": st.column_config.ProgressColumn(
                             "Weighted Jaccard", min_value=0.0, max_value=1.0, format="%.3f")})

# ═════════════════════════════════════════════
# DATA & DOWNLOADS
# ═════════════════════════════════════════════
with tabs[5]:
    st.subheader("Filtered dataset")
    req = ["group", "institution", "author", "title", "year", "type", "journal_name", "issn", "doi", "citations",
           "quartile", "coauthor_institutes", "cites_indian_inst", "cited_by_indian_inst"]
    st.dataframe(df[req], hide_index=True, width="stretch", height=420)
    st.download_button("Download filtered rows (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
                       "group10_data_filtered.csv", "text/csv")
    st.subheader("Submission files")
    for path in (C.DATA_CSV, C.CITATION_CSV, C.AUTHORSHIP_CSV, C.INDIAN_CSV, C.FACULTY_CSV, C.JACCARD_CSV):
        try:
            with open(path, "rb") as fh:
                st.download_button(f"Download {path}", fh.read(), path, "text/csv", key=path)
        except FileNotFoundError:
            st.caption(f"{path} not generated yet")

# ═════════════════════════════════════════════
# KEY FINDINGS (inferential results from part5_insights.py; full dataset)
# ═════════════════════════════════════════════
with tabs[6]:
    I = O["insights"]
    if not I:
        st.info("Run part5_insights.py to compute the inferential results.")
    else:
        st.caption("Computed on the full dataset (sidebar filters do not apply). Each claim is tested against a "
                   "baseline: null model, control variables or confidence interval.")
        for k, f in enumerate(I["findings"], 1):
            st.markdown(f"**{k}. {f['title']}** — {f['text']}")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Share of journal papers in Q1 venues")
            q = pd.DataFrame([{"institution": i, "year": int(y), "q1_pct": v}
                              for i in C.INST_NAMES for y, v in I["growth_quality"][i]["q1_by_year"].items()
                              if int(y) <= 2025])
            fig = px.line(q, x="year", y="q1_pct", color="institution", markers=True, color_discrete_map=COLORS)
            st.plotly_chart(layout(fig), width="stretch")
        with c2:
            st.subheader("What predicts citations? (OLS, % effect)")
            st.dataframe(pd.DataFrame(I["citation_regression"]["terms"]), hide_index=True, width="stretch")
        st.subheader("Network tests")
        cn, an = I["citation_network"], I["authorship_network"]
        st.dataframe(pd.DataFrame([
            ["Internal citations inside citing institute (%)", cn["same_institution_pct"],
             f"{cn['same_institution_null_pct']} ± {cn['same_institution_null_sd']} (shuffled)"],
            ["Internal citations sharing an author (%)", cn["author_self_citation_pct"], "–"],
            ["Co-authorship clustering", an["clustering"], f"{an['clustering_random']} (random)"],
            ["Average path length", an["path_length"], f"{an['path_length_random']} (random)"],
            ["Louvain modularity", an["modularity"], f"{an['modularity_null']} ± {an['modularity_null_sd']} (null)"],
            ["Institute assortativity", an["institution_assortativity"], "0 (random mixing)"],
        ], columns=["test", "observed", "baseline"]), hide_index=True, width="stretch")
