# Research networks of five IIITs (DPCN 2026 · Group 10)

Team **Titan Mandal** (Hrishikesh, Sarvesh, Shourya) · Instructor: Chittaranjan Hens

A network-science study of the research output of the **faculty** of
**IIIT Allahabad (IIITA)**, **ABV-IIITM Gwalior (ABV)**, **IIIT Bangalore (IIITB)**,
**IIIT Hyderabad (IIITH)** and **IIIT Delhi (IIITD)**, 2016–2026, built from
OpenAlex. It covers citation and faculty co-authorship networks, statistical
baselines, an interactive dashboard and a 6-page report. IIITH and IIITD, the
journal-quality split (Q1–Q4, impact factor), faculty ranks, the giant-component and
multilayer analyses and the citation anomaly check (Saveetha University) were added
after the first review — see [Review additions](#review-additions-november-2026).

> **Unit of analysis: faculty (since November 2026).** Following the instructor's
> review ("the analysis should be based on faculties"), every result is computed on
> the people listed on the five institutes' official faculty lists — 375 of 418
> listed faculty have papers — and on the 10,473 papers that have at least one of
> them as an author. Earlier versions used every OpenAlex author affiliated with
> the institutes (9,451 people, mostly students); see
> [DECISIONS.md §5](DECISIONS.md#5-review-additions-november-2026).

* **Live dashboard: <https://heroic-gumdrop-32cb8b.netlify.app/>** (Netlify)
* **Report:** [10_IIIT.pdf](10_IIIT.pdf) (6 pages)
* **Decision log:** [DECISIONS.md](DECISIONS.md)

## Contents
[Overview](#project-overview) · [Key findings](#key-findings) · [Review additions](#review-additions-november-2026) ·
[Screenshots](#dashboard-screenshots) · [Dataset & privacy](#dataset-and-privacy) · [Methodology](#methodology) ·
[Network analysis](#network-analysis) · [Results](#results-and-interpretation) · [Architecture](#project-architecture) ·
[Setup](#installation-and-setup) · [Reproducibility](#reproducibility) · [Deployment](#deployment) ·
[Limitations](#limitations-and-future-work) · [Decision log](#decision-log)

## Project overview

**Research question.** How do the research networks of the faculty of the five
IIITs compare, and how — and through which faculty — are the institutes connected
to each other?

The course asks every group to map the output of Indian institutes of the same
cluster: publication statistics, a citation network, a co-authorship network and
their Indian connections. The five IIITs are similar institutes in different
cities, so they make a natural test case. Do institutes of the same type and
cluster form one research community, or separate ones? Who holds them together?

| Institution | OpenAlex | ROR | Listed faculty (with papers) | Faculty papers 2016–2026 | Share of all papers with an institute author |
|---|---|---|---|---|---|
| IIIT Allahabad | `I26072440` | `03rgjt374` | 76 (70) | 2,068 | 70% of 2,945 |
| ABV-IIITM Gwalior | `I9747756` | `008b3ap06` | 80 (73) | 1,815 | 83% of 2,198 |
| IIIT Bangalore | `I181514455` | `05h9eqy10` | 57 (47) | 988 | 69% of 1,436 |
| IIIT Hyderabad | `I64189192` | `05f11g639` | 108 (96) | 3,281 | 73% of 4,512 |
| IIIT Delhi | `I119939252` | `03vfp4g33` | 97 (89) | 2,372 | 62% of 3,819 |

10,473 unique journal and conference papers with at least one listed faculty
author (51 carry listed faculty of two institutes). 2026 is a partial year.

## Key findings

All values are computed by the pipeline. Evidence, interpretation and caveats for
each finding are on the dashboard's *Findings & modelling* page and in the report.

**How the institutes connect** (`part5b_network_structure.py`)
1. **Faculty of the five IIITs form institutional islands.** Only 21 of 488
   faculty co-author links (4.3%) join two IIITs; a degree-preserving null model
   expects ≈382. 92% of the Louvain communities with ≥10 faculty are ≥90% one
   institute, and institute assortativity is 0.945. The faculty network splits
   into two blocs: the largest component holds ABV, IIITA and IIITB faculty, the
   second IIITH and IIITD faculty.
2. **Direct faculty ties between IIITs are rare.** The strongest pairs are
   IIITA–ABV (9 links, 13 joint papers) and IIITH–IIITD (8 links, 31 joint
   papers); 5 of the 10 institute pairs have no faculty link at all.
3. **IIIT Bangalore is the most weakly attached.** Removing 3 faculty cuts IIITB
   off from its best-connected partner IIIT (5 for the others).
4. **Connectivity depends on a few brokers.** 19% of cross-institute faculty pairs
   are connected by a path; removing the 1% of faculty with the highest
   betweenness cuts this to 12%, random removal leaves 18%.
5. **Indirect ties through the same IITs.** 22 Indian institutions co-author with
   all five IIITs; IIT Kanpur, IIT Roorkee and IISc are the strongest common
   partners.
6. **Many faculty have no faculty co-author.** 103 of 375 faculty (27%) share no
   paper with another listed faculty member; they publish with their students and
   external partners.

**Faculty ranks** (`part5c_extensions.py`)
* Professors are 104 of 375 faculty but hold 52% of all brokerage (betweenness).
  42% of Assistant Professors have no faculty co-author, against 13% of
  Professors (median faculty co-authors 3 vs 1; Mann–Whitney p < 0.001).

**Output and impact** (`part5_insights.py`)
* Faculty output grew 10.6–16.2% a year at all five institutes (log-linear fit,
  2016–2025). The Q1 share of journal papers rose significantly at IIITA, ABV and
  IIITH (χ², p < 0.001); IIITD started highest (70% → 74%).
* After normalising for year, field and paper type, mean citation impact is highest
  at IIITH (1.33) and IIITD (1.03) and lowest at conference-heavy IIITB (0.63).
* Citations are explained mostly by venue (Q1 +94%, conference −49%) and team
  size; international co-authorship adds +12% once these are held fixed (OLS,
  robust errors).
* 95% of citations between the five institutes' papers share an author
  (self-citation); 97% stay inside the citing institute, against 26% if targets
  are shuffled.

## Review additions (November 2026)

Built in `part5c_extensions.py` (+ `group10_roles.py`) and shown on five new
dashboard pages under *Review additions*. All numbers below are for the
faculty-only data.

| Request | What was done | Result |
|---|---|---|
| **Q1 / Q2 / Q3 / Q4 and IF >5, >10** | Journal papers split by Scimago quartile and by impact-factor band (≥10, 5–10, <5). IF = OpenAlex 2-year mean citedness of the journal (the JIF formula on open data). Per institute, per year and per faculty member. | Q1 share: IIITD 71%, IIITH 67%, IIITB 60%, IIITA 42%, ABV 41%. IF ≥10: IIITH 102 papers (8%), IIITD 98 (8%), ABV 58, IIITA 53, IIITB 28 (10%). Only 69% of Q1 papers are in IF ≥5 journals, so the two measures are not interchangeable. |
| **Analysis based on faculty** | The official faculty lists of all five institute websites (`reference/faculty_rosters/`, regular posts only) define who is analysed. Names are matched to OpenAlex authors (any order, initials allowed, e.g. "Jawahar C V" = "C. V. Jawahar"); one person's several OpenAlex profiles are joined only with co-author evidence. Only papers with a listed faculty author are kept. Faculty are grouped by rank (Professor / Associate / Assistant). | 375 of 418 listed faculty have papers (IIITA 70/76, ABV 73/80, IIITB 47/57, IIITH 96/108, IIITD 89/97); they cover 62–83% of each institute's OpenAlex output. Every match is in `outputs/group10_faculty_roster_match.csv` (50 common-name cases flagged for manual check). Professors hold 52% of the brokerage; 42% of Assistant Professors have no faculty co-author. |
| **GCC** | Giant connected component: size, composition by institute and rank, what lies outside it, year-by-year growth. | 145 of 375 faculty (38.7%) and 54% of links; the second component (119 faculty) is the IIITH–IIITD bloc. Share inside the GCC: IIITA 77%, ABV 75%, IIITB 72%, IIITH 2%, IIITD 0%. Grew from 7% of faculty (2016) to 39%. |
| **Multilayer graph analysis** | Two-layer multiplex on the same faculty (co-authorship, faculty-to-faculty citation): edge overlap vs a degree-preserving null, degree correlation, participation coefficient, mutually connected giant component; plus a 4-layer institute-level multiplex. | 48% of citation links join co-authors (17× random); layer degrees correlate (ρ = 0.77); 33% of faculty are mutually connected in both layers. Between institutes the citation layer has 175 links among faculty who never co-wrote vs 21 co-author links — the IIITs' faculty read each other far more than they collaborate. |
| **Saveetha University issue** | Citing institutions screened for citations out of proportion to collaboration and for papers dominated by one citer; three tests (size, who cites, topic) against the other top citers; sensitivity analysis. | Saveetha is #5 among Indian institutions citing the five IIITs' faculty papers (#1 for IIITA) with only 3 joint papers. But it writes 1.81% of all Indian papers and supplies 2.09% of the works citing us (1.16×, vs 2.12× for other large citers), and its citations do not come from the cited authors' co-author circle (17% vs 33%). Its prominence is explained by its size, not a citation circle aimed at the IIITs. Unusual: citing began only in 2022, fewer citing papers in the same field (57% vs 76%), and citing without collaborating. Removing its citations changes institute totals by ≤1.2%. |
| **IIIT Hyderabad and IIIT Delhi** | Added to every script, the dashboard (own pages and colours) and the report. | See the table above. |

## Dashboard screenshots

Screenshots of the implemented dashboard (`part4_dashboard.py`). Views that list
individual people are not included here.

| Overview | Network explorer |
|---|---|
| ![Overview: research question, network summary and main findings](docs/images/overview.png) | ![Network explorer: co-authorship graph coloured by institute, links between institutes highlighted](docs/images/explorer.png) |
| **Network analysis** | **Course connections** |
| ![Network analysis: properties, log-binned degree distribution, robustness, baselines](docs/images/authorship.png) | ![Course connections: degree and paths, log-binning, ER graphs, ring and star path lengths](docs/images/course.png) |

![Findings and modelling page](docs/images/findings.png)

Dashboard pages: Overview · Findings & modelling (each finding labelled *Strong
evidence* or *Suggestive*) · Institution comparison · Publications & research areas
(research-profile radar, top venues, quartile mix by field, Lorenz curve, active
topics) · Faculty (all-institute table with rank, Q1–Q4 and IF ≥5/≥10 columns, compare two faculty, papers-vs-citations) ·
one page per institute (faculty table, h-index, quartiles, top venues, departments,
most-cited papers) · Network explorer · **Degrees of separation** · **Network
growth** · Network analysis · Citation network · Indian connectivity · Course
connections · Data & methods (with a glossary of every term used). Behind *Show advanced
analysis*: Graph analytics (strongest pairs, recurring teams, local clustering, a
heuristic cross-institute "synergy" list) and Data audit & rigour (OpenAlex
completeness per institute, window vs career h-index).

The Overview follows the layout of a research-profile page suggested by the
instructor ([example](https://jfmendes-sciart.github.io/research.html)), with
every element drawn from our own data:
* a hero banner drawn from the real faculty co-authorship network, with pulses along the
  links between institutes;
* a summary-of-statistics band with a **year selector** (From/To, period presets,
  click a lollipop, or a link such as `?years=2016-2019`) that recomputes papers,
  citations, h-index, Q1 share, active faculty, faculty co-author links and links between
  institutes for the chosen years, plus a citations-per-year lollipop chart (peak and
  partial year marked);
* research-interest chips per institute;
* a scrolling strip of the main partner institutions;
* a "selected publications" list of the 10 most-cited papers.

The Network explorer adds a top-N selector and summary counters.

Interactive features across the whole dashboard:
* **Search (Ctrl+K or `/`).** One search box for all 375 faculty, all 10,473
  papers and every page, used with the keyboard.
* **Faculty profiles.** Clicking a name anywhere (any table, the explorer, search,
  the growth map) opens a side panel: papers, co-authors, betweenness rank,
  Louvain community, papers per year, faculty co-authors at the five IIITs (those at
  another IIIT outlined), most-cited papers with DOI links and the OpenAlex
  profile. Profiles have shareable links (`#author=<OpenAlex ID>`), and every page
  has its own (`#explorer`, `#paths`, …).
* **Degrees of separation.** Pick two faculty to see the shortest co-authorship
  chain between them in the full network (breadth-first search): where the chain
  crosses institutes, how many equally short chains exist, and how far every
  other faculty member is from the first one. Buttons pick a random pair from two
  institutes or from one.
* **Network growth.** The full faculty co-authorship network on one fixed layout, played
  year by year from 2016 to 2026 (faculty appear with their first paper, links
  with the pair's first joint paper; links between institutes in pink). Counters
  and two charts follow the giant component and the links between institutes.

## Dataset and privacy

**What it is.** One row per (paper, assigned institute) for every journal or
conference paper 2016–2026 with at least one author on that institute's official
faculty list, from [OpenAlex](https://openalex.org); the `author` column lists the
institute's faculty on the paper. The 14 columns required by the
course are present, plus analysis columns. Three network edge lists accompany it.
Quartiles come from Scimago SJR (year-matched) and conference ranks from ICORE2026
(`reference/`).

**Why it is not in this repository.** The dataset and its derived edge lists hold
author-level records. They are submitted privately to the instructor, so the
public repository contains only code, documentation, the report and aggregate
figures. These files are gitignored: `group10_data.csv`,
`citation_network.csv`, `authorship_network.csv`, `indian_connections.csv`,
`cache/`, `outputs/*.csv|json|md`, `dashboard.html`, `site/` and the scraped student
lists `reference/faculty_rosters/*_students.csv`. The faculty lists in
`reference/faculty_rosters/` are public directory information and are committed
with their source URLs. Impact factors come from OpenAlex source statistics
(`cache/sources.json.gz`).

> **Note.** These files were part of the initial commit (`4a161f4`), so they still
> exist in this repository's Git history. Purging them requires a history rewrite
> and force-push, which has not been done.

**Providing the data locally (authorised users).** Place the private `cache/`
folder in the project root, or regenerate it from OpenAlex (see
[Reproducibility](#reproducibility)).

## Methodology

* **Collection** (`part1_collect_data.py`): every OpenAlex work 2016–2026
  affiliated with the five institution IDs, plus Indian works that cite or are
  cited by them, fetched with batched filters. Requests are budget-aware and the
  caches make runs resumable.
* **Cleaning** (`group10_common.select_corpus`): journal and conference papers
  only. Preprints, book chapters, errata, editorials, datasets and retracted works
  are removed. Versions of one paper are merged by title + shared author, or by
  DOI, and citations are the maximum over versions.
* **Author identities** (`part1b_enrich_data.resolve_author_identities`): the
  OpenAlex author ID is the unit of identity. Records with the same name are
  merged only if they are at the same institute, never on the same paper, and
  share a co-author: 10,581 records → 9,451 authors.
* **Faculty selection** (`part1b_enrich_data.select_faculty`, `group10_roles.py`):
  each author is matched by name to the official faculty list of the institute
  (regular posts; adjunct, visiting and staff entries excluded). Names may be
  written in any order and with initials ("Jawahar C V" = "C. V. Jawahar"); an
  initial alone is not accepted for very common surnames, and a name that fits two
  listed people is left unmatched. One listed person's several OpenAlex profiles
  become one node only if they never share a paper and share a co-author. Result:
  375 of 418 listed faculty, 10,473 papers. Every decision is written to
  `outputs/group10_faculty_roster_match.csv`. ORCID verification is **not**
  implemented; see DECISIONS.md.
* **Networks** (`part2_networks.py`):
  * *Citation:* node = paper, directed edge A → B if A references B (unweighted).
  * *Co-authorship:* node = faculty member, undirected edge if two faculty
    members share a paper, weight = joint papers.
  * Edges to other Indian institutes go only into the CSV files, as the course
    requires.
* **Statistics and inference** (`part3`, `part5`): publication trends, quartiles,
  h-indices; log-linear growth; χ² test; normalised citation scores with bootstrap
  CIs; OLS with HC1 errors; homophily against 1,000 shuffled citation graphs.

## Network analysis

| | Faculty co-authorship | Citation |
|---|---|---|
| Type | undirected, weighted | directed, unweighted |
| Nodes / edges | 375 / 488 | 10,473 / 13,020 |
| Connected? | no — 109 components (103 isolated faculty), giant 38.7% | no — 4,465 weak components, largest 2,890 |
| Degree | mean 2.6, median 2, max 13 | in-degree mean 1.24, max 88 |
| Clustering | 0.185 (ER: 0.005) | — |
| Path length / diameter (giant) | 5.63 / 15 (ER: 5.91) | not meaningful (almost acyclic, fragmented) |
| Communities | Louvain Q = 0.847 (configuration-model null 0.553), stable over 10 seeds | — |

Implemented in `part5b_network_structure.py`:
* properties of both networks and of each institute's subgraph;
* a 5×5 mixing matrix compared with the configuration-model expectation d_A·d_B/2m;
* bridge authors and minimum node cuts between institutes;
* an all-pairs distance matrix;
* robustness under targeted vs random removal;
* ER G(n, m) baselines and a log-binned degree distribution;
* Louvain stability over 10 seeds;
* agreement between four centralities;
* a 5×5 citation matrix with and without self-citations;
* shared Indian partners;
* the identity-sensitivity analysis (all-author identities; no effect on the faculty network).

**Proposed, not run:** Leiden communities (Louvain is already stable) and link
prediction (too few inter-IIIT positives for a fair evaluation).

## Results and interpretation

The five IIITs' faculty are productive and growing. IIITH and IIITD lead on venue
quality (Q1 share, IF ≥10 papers) and normalised impact; IIITA and ABV are improving
fastest in Q1 share. Structurally, though, the faculty form **separate research
systems**:
* Faculty collaborate and cite inside their own institute.
* Direct faculty ties between IIITs are few; IIITA–ABV and IIITH–IIITD are the only
  substantial pairs, and the faculty network splits into a north/IIITB bloc and an
  IIITH–IIITD bloc.
* IIITB connects to the group only through a handful of faculty.
* Professors hold the faculty network together; many Assistant Professors have no
  faculty co-author yet.
* The institutes' faculty read (cite) each other far more than they collaborate
  (multilayer analysis).

Each institute's largest partners include institutions in its own city, while
national IITs are what the five have in common. The faculty network is robust to
random loss but fragile to the loss of a few well-connected faculty. Saveetha
University's large citation volume is explained by its size; it does not change
any result materially.

Practical reading: direct IIIT–IIIT faculty collaboration is rare and fragile. Joint
projects, co-supervised students and mentoring links for junior faculty are the
levers that would connect them. Nothing here establishes causes; see the
limitations.

## Project architecture

```text
part1_collect_data.py        OpenAlex download → cache/ (private)
part1b_enrich_data.py        corpus rules, quartiles, author identity, faculty selection, Jaccard → group10_data.csv, outputs/
part2_networks.py            citation & co-authorship networks, citation flow, Indian connections
part3_statistics.py          descriptive charts + statistics summary
part5_insights.py            inferential tests, output/impact findings, report figures f1–f5
part5b_network_structure.py  structure & inter-institution analysis, structural findings, figures f6–f7
part5c_extensions.py         review additions: Q1–Q4 & IF bands, faculty ranks, GCC, multilayer, citation anomalies
group10_roles.py             name matching against the institute faculty lists; designation → rank
part4_dashboard.py           builds dashboard.html and site/index.html (D3 + Chart.js inlined)
part6_report.py              builds 10_IIIT.pdf (6 pages)
app.py                       Streamlit dashboard with filters (local use)
group10_common.py            configuration, OpenAlex client, classification rules
group10_analysis.py          shared loading and statistics (one source for every output)
reference/                   Scimago SJR 2016–2025, ICORE2026 ranks, institute faculty lists (public sources;
                             the scraped student lists are local only)
assets/                      D3 and Chart.js (inlined into the dashboard)
docs/                        course instructions, slides, README screenshots
netlify.toml                 static hosting config (publish = site/)
```

Data flow: `cache/` → `group10_data.csv` + network CSVs → `outputs/*.json` →
figures, `10_IIIT.pdf`, `site/index.html`. The report and both dashboards read the
same JSON files, so they cannot disagree.

## Installation and setup

Prerequisites: Python ≥ 3.10 (tested with 3.13). No Node.js is needed.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

Optional environment variables are listed in [.env.example](.env.example); none
are needed for an offline rebuild.

## Reproducibility

With the private `cache/` in place, every step runs offline (≈25 minutes for five institutes; `part5c_extensions.py` makes
≈25 extra OpenAlex requests the first time, for the Saveetha tests):

```bash
python part1b_enrich_data.py
python part2_networks.py
python part3_statistics.py
python part5_insights.py
python part5b_network_structure.py
python part5c_extensions.py
python part4_dashboard.py      # → dashboard.html and site/index.html
python part6_report.py         # → 10_IIIT.pdf
streamlit run app.py           # optional, local filtered dashboard
```

Without the cache, start with `python part1_collect_data.py`. It needs about 600
OpenAlex requests and resumes the next day if the free daily budget runs out.
OpenAlex is updated continuously, so a fresh download will differ slightly from
the numbers above.

## Deployment

**Live:** <https://heroic-gumdrop-32cb8b.netlify.app/>, hosted on Netlify and
deployed with Netlify Drop from a local build of `site/`. It was checked after
deployment: the served page matches the local build apart from a comment Netlify
adds, and every page renders without errors.

The dashboard is a static, self-contained HTML file. It needs no server, build
step or external requests, because D3 and Chart.js are inlined. `site/` is
gitignored because the page embeds author names and paper records, so it is
deployed from a local build rather than built from the repository.

**Netlify (recommended)**
1. Build: `python part4_dashboard.py` (creates `site/index.html`).
2. Either drag the `site/` folder onto <https://app.netlify.com/drop>, or use the CLI:
   ```bash
   npm install -g netlify-cli
   netlify login
   netlify deploy --dir=site --prod
   ```
3. To update the live site after re-running the pipeline, open the site in the
   Netlify UI → **Deploys** and drag the new `site/` folder onto it (or run
   `netlify deploy --dir=site --prod`). The URL stays the same.

The URL is the default of `DASHBOARD_LIVE_URL` in `group10_common.py`, which the
report uses. Set `DASHBOARD_URL` to override it if the site moves.

**Vercel alternative:** `npx vercel deploy site --prod`.

## Limitations and future work

* OpenAlex affiliation and reference coverage is incomplete, especially before
  2018. A missing affiliation removes an author or a link.
* Faculty are matched to OpenAlex by name and are not verified against ORCID. The
  faculty lists are *current* (retrieved 2026-11-07): former faculty are not
  included, and someone who moved between two IIITs counts only where listed now.
  43 listed faculty have no papers (mostly recent joiners). Papers written only by
  students, postdocs or staff (17–38% of each institute's OpenAlex output) are
  excluded. Common-name profiles (e.g. Kumar, Singh) were joined only with co-author
  evidence; 50 are flagged for manual checking.
* Impact factor is an open proxy (OpenAlex 2-year mean citedness, current value),
  not the Clarivate JIF, and is not year-matched.
* The Saveetha tests describe citation patterns; they cannot show intent. They cover
  Saveetha's citations *to the five IIITs*, not Saveetha's citations of its own
  faculty (the subject of the 2023 *Science* / Retraction Watch investigation).
* The networks are 2016–2026 snapshots, and node cuts and robustness describe that
  snapshot only.
* Departments come from affiliation strings or, failing that, research fields
  (the IIITH and IIITD lists name research centres, not departments; the list's
  own unit is kept in the `roster_department` column). CORE ranks cover only
  listed venues.
* The analyses are associations and departures from null models, not causal
  effects.
* **Future work:**
  * ORCID verification of bridge faculty, and archived (Wayback) faculty lists for
    former faculty;
  * a temporal analysis beyond the descriptive *Network growth* page (do
    inter-IIIT ties grow after moves?);
  * link prediction with a time-split evaluation once more inter-IIIT papers exist;
  * Leiden communities.

## Decision log

[DECISIONS.md](DECISIONS.md) records how faculty were selected and authors verified, how identical
names are handled, the full pipeline stage by stage, the key methodological
trade-offs, and what is public versus private. Read it before reusing the data or
extending the analysis.
