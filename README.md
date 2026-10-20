# DPCN 2026 – Group 10 · Research Mapping of Three IIITs

Team **Titan Mandal** (Hrishikesh, Sarvesh, Shourya) · Instructor: Chittaranjan Hens

| Institution | OpenAlex | ROR |
|---|---|---|
| IIIT Allahabad | `I26072440` | `03rgjt374` |
| ABV-IIITM Gwalior | `I9747756` | `008b3ap06` |
| IIIT Bangalore | `I181514455` | `05h9eqy10` |

Period 2016–2026 (2026 is partial – data collected in 2026).

* **Report:** [10_IIIT.pdf](10_IIIT.pdf) (5 pages)
* **Dashboard:** [dashboard.html](dashboard.html) – a single offline file; open it in any browser
  ([live preview](https://htmlpreview.github.io/?https://github.com/sarvesh2005takbhate/dpcn_A2/blob/main/dashboard.html)).
  A filterable Streamlit version runs with `streamlit run app.py`.

## Key findings

All findings are computed by `part5_insights.py`; each is tested against a baseline.

* **Growth with quality:** output grows about 11–12% a year at all three institutes. The Q1 share of journal papers rose
  from about 30% to 44% (IIITA) and from 26% to 41% (ABV) between 2016–19 and 2022–25 (χ², p < 0.001).
* **Raw citations exaggerate differences:** after normalising for year, field and paper type, mean impact is
  1.05 (ABV), 1.01 (IIITA) and 0.90 (IIITB). IIITB's low raw median comes mainly from its conference-heavy output.
* **Citations are explained by venue and team size, not international co-authorship.** The raw international premium
  disappears once venue quality, paper type and team size are controlled for.
* **Internal citation is self-citation:** 94% of citations between papers of the three institutes share an author, and
  97% stay inside the citing institute (40% expected under shuffling).
* **Three islands:** the co-authorship network is small-world and strongly modular (Q = 0.87 vs 0.45 null), with
  institute assortativity 0.95. Only 37 papers link two of the IIITs.
* **Citations follow collaboration:** co-author partner institutes supply 57–72% of the Indian citations each
  institute receives (Spearman ρ ≈ 0.6–0.7). Topic similarity does not predict who collaborates.

## Repository layout

```text
├── 10_IIIT.pdf                  statistics report (≤ 5 pages)
├── dashboard.html               interactive dashboard (all required panels + key findings)
├── group10_data.csv             main dataset (14 required columns + analysis columns)
├── citation_network.csv         source_doi, target_doi, source_inst, target_inst, year (+ edge_type)
├── authorship_network.csv       author_a, author_b, paper_doi, inst_a, inst_b, year (+ edge_scope)
├── indian_connections.csv       your_inst, partner_inst, shared_papers, total_citations (+ flows, clusters)
├── part1_collect_data.py        OpenAlex download (resumable, budget-aware)
├── part1b_enrich_data.py        dataset build, quartiles, CORE ranks, faculty, Jaccard
├── part2_networks.py            citation & authorship networks, citation flow, Indian connections
├── part3_statistics.py          descriptive charts + statistics summary
├── part4_dashboard.py           builds dashboard.html
├── part5_insights.py            inferential analysis and key findings
├── part6_report.py              builds 10_IIIT.pdf
├── app.py                       Streamlit dashboard
├── group10_common.py            configuration, OpenAlex client, classification rules
├── group10_analysis.py          shared statistics used by the report and both dashboards
├── outputs/                     faculty list, authorships, metrics, flows, insights, charts
├── reference/                   Scimago SJR 2016–2025, ICORE2026 conference ranks
├── cache/                       compressed OpenAlex responses (lets the pipeline re-run offline)
├── assets/                      D3 and Chart.js, inlined into dashboard.html
└── docs/                        course instruction note and project slides
```

## How to run

```bash
pip install -r requirements.txt
python part1_collect_data.py      # only needed to refresh data; resumable
python part1b_enrich_data.py
python part2_networks.py
python part3_statistics.py
python part5_insights.py
python part4_dashboard.py
python part6_report.py
streamlit run app.py
```

With the files in `cache/`, steps 1b–6 run offline.

**OpenAlex budget.** Without an API key, OpenAlex allows about 1000 requests a day per IP and does not allow cursor paging.
The scripts use page paging and batched filters (a full download needs about 600 requests) and cache everything, so an
interrupted run resumes where it stopped. A free key can be set with `OPENALEX_API_KEY=...`.

## Definitions

* **Included papers** – journal articles/reviews and conference papers (also those in proceedings series such as
  LNCS, CCIS and LNNS). Excluded: preprints, book chapters, books, errata, editorials, datasets, peer reviews and
  retracted works. Versions of one paper (preprint / repository / published) are merged, and the citation count is
  the maximum over versions.
* **`group10_data.csv`** – one row per (paper, assigned institution). Use `openalex_id` to de-duplicate combined
  totals.
  * `author` – the paper's authors affiliated with that institution (all authors are in `all_authors`).
  * `quartile` – journals: Scimago SJR best quartile of the journal **in the publication year** (2026 uses SJR 2025).
    Conferences: CORE rank A*/A/B/C (ICORE2026). Empty means unranked.
  * `coauthor_institutes` – other Indian institutions on the paper (OpenAlex `country_code = IN`).
  * `cites_indian_inst` / `cited_by_indian_inst` – the paper cites, or is cited by, a work authored at another
    Indian institution.
* **Core faculty** – a heuristic for permanent faculty: ≥ 5 papers in ≥ 3 years, last author on ≥ 30% and first
  author on ≤ 50% of them. Departments come from "Department of …" in the affiliation strings; otherwise they are
  inferred from the author's main OpenAlex field.
* **Networks** – PageRank and in-degree use the internal citation graph. The authorship network links the authors
  of the three institutes (Louvain with seed 42, exact betweenness). Cross-institute edges appear only in the raw CSVs.
* **Inference** – log-linear growth fits; χ² test for the Q1 shift; citation scores normalised by year, field and
  type with bootstrap CIs; OLS on log(1 + citations) with HC1 robust errors; 1000 target-shuffled graphs for
  homophily; configuration-model graphs for modularity.

## Limitations

OpenAlex affiliation and reference coverage is incomplete, especially before 2018, and the core-faculty flag is a
heuristic, not an official list. IIIT Bangalore authors rarely state a department, so most of its departments are
inferred. CORE ranks cover only venues in the ICORE list.
