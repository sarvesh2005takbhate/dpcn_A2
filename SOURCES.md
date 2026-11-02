# SOURCES — Group 10 (IIIT Allahabad · ABV-IIITM Gwalior · IIIT Bangalore)

DPCN 2026 course project · Team Titan Mandal (Hrishikesh, Sarvesh, Shourya) · Instructor: Chittaranjan Hens

This file lists every source our data came from: the database and API we queried, the identifiers used, the ranking lists for journals and conferences, and (Appendix) every journal and conference that appears in our dataset.

Data collected: October 2026 · Period covered: 2016–2026 (2026 partial) · 6,543 unique papers (3,501 journal, 3,042 conference) in `group10_data.csv`.

## 1. Primary data source — OpenAlex

* **OpenAlex** — open catalogue of scholarly works, authors, venues and institutions (CC0 licence).
  * Website: https://openalex.org · API: https://api.openalex.org · Docs: https://docs.openalex.org
  * Accessed through the public REST API by `part1_collect_data.py` and `part1b_enrich_data.py` (responses cached in `cache/`).

| What we took from OpenAlex | API endpoint / filter | Used for |
|---|---|---|
| All works of the three institutes, 2016–2026 | `/works?filter=authorships.institutions.id:<ID>,publication_year:2016-2026` | the main dataset (`group10_data.csv`) |
| Per work: title, DOI, year, type, venue (locations / source, ISSN), authorships with author IDs and raw affiliation strings, institutions with country code, `referenced_works`, `cited_by_count`, `counts_by_year`, primary topic → subfield → field, retraction and open-access flags | `select=id,doi,display_name,publication_year,type,primary_location,locations,authorships,cited_by_count,counts_by_year,referenced_works,primary_topic,is_retracted,open_access` | every column of the dataset; citation and co-authorship networks |
| Indian works that **cite** our papers (citation in-flow) | `/works?filter=cites:<W…>,authorships.institutions.country_code:IN` (100 IDs per request) | `cited_by_indian_inst`, `citation_network.csv` (inflow), `indian_connections.csv` |
| Indian works that our papers **cite** (citation out-flow) | `/works?filter=cited_by:<W…>,authorships.institutions.country_code:IN` | `cites_indian_inst`, `citation_network.csv` (outflow), `indian_connections.csv` |
| Lifetime h-index of core faculty | `/authors?filter=openalex:<A…>` (`summary_stats.h_index`, `works_count`) | faculty table (lifetime h-index column) |
| Research-topic profile of each institute and of its top Indian partners | `/works?filter=authorships.institutions.id:<ID>,publication_year:2016-2026,type:article\|review\|conference-paper&group_by=primary_topic.subfield.id` | Jaccard topic similarity |

**Institutions** (OpenAlex institution IDs, cross-checked with the ROR registry, https://ror.org):

| Institute | OpenAlex | ROR |
|---|---|---|
| Indian Institute of Information Technology Allahabad | [I26072440](https://openalex.org/I26072440) | [03rgjt374](https://ror.org/03rgjt374) |
| Atal Bihari Vajpayee Indian Institute of Information Technology and Management Gwalior | [I9747756](https://openalex.org/I9747756) | [008b3ap06](https://ror.org/008b3ap06) |
| International Institute of Information Technology Bangalore | [I181514455](https://openalex.org/I181514455) | [05h9eqy10](https://ror.org/05h9eqy10) |

Indian partner institutions were identified from OpenAlex institution records with country code `IN`; their OpenAlex IDs are in `indian_connections.csv` (`partner_openalex_id`).

## 2. Journal ranking source — Scimago Journal & Country Rank (SJR)

* Website: https://www.scimagojr.com/journalrank.php
* Yearly journal rankings **2016–2025** (Scimago's own `sourceid`, title, type, ISSNs, best quartile, subject areas), combined in `reference/scimago_sjr_2016_2025.csv.gz` (338,293 journal-year rows).
* Used for the `quartile` column of journal papers: the journal's best SJR quartile **in the paper's publication year** (±2-year fallback if a year is missing; 2026 papers use SJR 2025). Matching is by ISSN (OpenAlex ISSN-L and ISSNs).
* Also used to recognise conference proceedings that Scimago lists as type “conference and proceedings”.

## 3. Conference ranking source — CORE (ICORE2026)

* CORE Rankings Portal (Computing Research and Education Association of Australasia): https://portal.core.edu.au/conf-ranks/
* Edition **ICORE2026**, exported to `reference/core_conference_rankings.csv` (987 conferences; ranks A*, A, B, C used).
* Used for the `quartile` column of conference papers (A*/A/B/C). Matching is strict: conference acronym in the venue name plus title overlap, or a near-identical title; workshops and companion volumes never inherit the main-conference rank. Conferences not in the CORE list are left unranked.

## 4. Other references

* **ROR — Research Organization Registry** (https://ror.org): identifiers of the three institutes.
* **OpenAlex topic classification** (domain → field → subfield → topic, https://docs.openalex.org/api-entities/topics): research-area breakdown and topic similarity.
* **Course material**: *DPCN Research Mapping Project — Instruction Note* and project slides (`docs/`), which define the required columns and network files.
* **Layout reference** (no data taken): the research-profile page suggested by the instructor, https://jfmendes-sciart.github.io/research.html, which the dashboard Overview follows.
* No data was taken from Scopus, Web of Science, Google Scholar, IRINS or institute websites.

## 5. Software (not data sources)

Python (pandas, NetworkX, SciPy, NumPy, Matplotlib, ReportLab, Streamlit, Plotly, requests); dashboard charts with D3.js (https://d3js.org; force layouts, zoom and the growth map) and Chart.js (https://www.chartjs.org), both inlined into the page. The dashboard's search, author profiles, degrees-of-separation path finder and network-growth view run in plain JavaScript on the same OpenAlex-derived data; they add no new data source. Code: https://github.com/sarvesh2005takbhate/dpcn_A2 · Dashboard: https://heroic-gumdrop-32cb8b.netlify.app/

## Appendix A — Journals in the dataset

1,394 journals, 3,501 journal papers. Columns: papers (unique) and papers per institute; ISSN-L; SJR quartile(s) of the papers in their publication years; years covered. Sorted by number of papers.

| # | Journal | ISSN | SJR quartile | Papers | IIITA | ABV | IIITB | Years |
|---|---|---|---|---|---|---|---|---|
| 1 | Multimedia Tools and Applications | 1380-7501 | Q1, Q2 | 89 | 56 | 28 | 5 | 2016–2024 |
| 2 | IEEE Access | 2169-3536 | Q1 | 58 | 30 | 17 | 11 | 2018–2026 |
| 3 | Wireless Personal Communications | 0929-6212 | Q2, Q3 | 52 | 32 | 20 | 0 | 2016–2025 |
| 4 | Journal of Biomolecular Structure and Dynamics | 0739-1102 | Q2, Q3 | 44 | 44 | 0 | 0 | 2016–2026 |
| 5 | Scientific Reports | 2045-2322 | Q1 | 40 | 23 | 12 | 5 | 2016–2026 |
| 6 | IEEE Sensors Journal | 1530-437X | Q1 | 39 | 24 | 14 | 1 | 2016–2026 |
| 7 | Applied Intelligence | 0924-669X | Q2 | 30 | 19 | 10 | 1 | 2016–2025 |
| 8 | The Journal of Supercomputing | 0920-8542 | Q2 | 29 | 20 | 9 | 0 | 2020–2026 |
| 9 | International Journal of Communication Systems | 1074-5351 | Q2 | 28 | 6 | 23 | 0 | 2016–2026 |
| 10 | Expert Systems with Applications | 0957-4174 | Q1 | 23 | 5 | 16 | 2 | 2018–2026 |
| 11 | Wireless Networks | 1022-0038 | Q2 | 23 | 6 | 15 | 2 | 2016–2026 |
| 12 | IEEE Internet of Things Journal | 2327-4662 | Q1 | 22 | 4 | 17 | 1 | 2020–2026 |
| 13 | Neural Computing and Applications | 0941-0643 | Q1, Q2 | 22 | 12 | 9 | 1 | 2016–2026 |
| 14 | Physical Communication | 1874-4907 | Q2 | 19 | 10 | 7 | 2 | 2017–2026 |
| 15 | AEU - International Journal of Electronics and Communications | 1434-8411 | Q2 | 18 | 5 | 13 | 0 | 2017–2026 |
| 16 | Journal of Electronic Materials | 0361-5235 | Q2, Q3 | 18 | 13 | 5 | 0 | 2016–2025 |
| 17 | Computers & Electrical Engineering | 0045-7906 | Q1, Q2 | 17 | 6 | 10 | 1 | 2017–2026 |
| 18 | International Journal of Systems Assurance Engineering and Management | 0975-6809 | Q2, Q3 | 17 | 1 | 16 | 0 | 2016–2026 |
| 19 | IEEE Transactions on Vehicular Technology | 0018-9545 | Q1 | 16 | 9 | 3 | 4 | 2017–2025 |
| 20 | Journal of Circuits Systems and Computers | 0218-1266 | Q3 | 16 | 11 | 4 | 1 | 2016–2026 |
| 21 | Arabian Journal for Science and Engineering | 1319-8025 | Q1, Q2 | 15 | 7 | 9 | 0 | 2016–2025 |
| 22 | IETE Journal of Research | 0377-2063 | Q3 | 14 | 9 | 5 | 0 | 2016–2026 |
| 23 | Journal of Materials Science Materials in Electronics | 0957-4522 | Q2 | 14 | 14 | 0 | 0 | 2019–2026 |
| 24 | Neurocomputing | 0925-2312 | Q1 | 14 | 9 | 3 | 2 | 2016–2026 |
| 25 | IEEE Communications Letters | 1089-7798 | Q1, Q2 | 13 | 2 | 4 | 7 | 2016–2026 |
| 26 | IEEE Transactions on Artificial Intelligence | 2691-4581 | Q1 | 13 | 5 | 7 | 1 | 2022–2026 |
| 27 | International Journal of Computer Sciences and Engineering | 2347-2693 | unranked | 12 | 0 | 5 | 7 | 2019–2025 |
| 28 | International Journal of Engineering Science and Technology | 2141-2820 | unranked | 12 | 0 | 12 | 0 | 2022 |
| 29 | Physical review. D/Physical review. D. | 2470-0010 | Q1 | 12 | 12 | 0 | 0 | 2017–2026 |
| 30 | SN Computer Science | 2661-8907 | Q2 | 12 | 4 | 4 | 4 | 2020–2026 |
| 31 | ACS Omega | 2470-1343 | Q1, Q2 | 11 | 10 | 1 | 0 | 2018–2025 |
| 32 | IEEE Sensors Letters | 2475-1472 | Q2 | 11 | 6 | 6 | 0 | 2020–2025 |
| 33 | IEEE Transactions on Electron Devices | 0018-9383 | Q1, Q2 | 11 | 6 | 5 | 0 | 2016–2026 |
| 34 | Acta Psychologica | 0001-6918 | Q1 | 10 | 10 | 0 | 0 | 2024–2026 |
| 35 | Applied Physics A | 0947-8396 | Q2 | 10 | 8 | 2 | 0 | 2018–2026 |
| 36 | Applied Soft Computing | 1568-4946 | Q1 | 10 | 3 | 6 | 1 | 2016–2026 |
| 37 | Cluster Computing | 1386-7857 | Q1, Q2, Q3 | 10 | 5 | 5 | 0 | 2019–2026 |
| 38 | IEEE Systems Journal | 1932-8184 | Q1 | 10 | 6 | 1 | 3 | 2016–2023 |
| 39 | IEEE Transactions on Communications | 0090-6778 | Q1 | 10 | 0 | 2 | 8 | 2021–2026 |
| 40 | IEEE Transactions on Green Communications and Networking | 2473-2400 | Q1 | 10 | 4 | 5 | 1 | 2018–2025 |
| 41 | IEEE Transactions on Nanotechnology | 1536-125X | Q2 | 10 | 2 | 8 | 0 | 2017–2025 |
| 42 | IEEE Transactions on Network and Service Management | 1932-4537 | Q1 | 10 | 4 | 2 | 4 | 2017–2026 |
| 43 | Sadhana | 0256-2499 | Q2 | 10 | 2 | 4 | 4 | 2019–2024 |
| 44 | Soft Computing | 1432-7643 | Q2 | 10 | 1 | 9 | 0 | 2017–2026 |
| 45 | Applied Surface Science | 0169-4332 | Q1 | 9 | 4 | 6 | 0 | 2016–2025 |
| 46 | IEEE Open Journal of the Communications Society | 2644-125X | Q1 | 9 | 0 | 5 | 4 | 2022–2026 |
| 47 | IEEE Wireless Communications Letters | 2162-2337 | Q1 | 9 | 0 | 5 | 4 | 2016–2026 |
| 48 | Integration | 0167-9260 | Q2, Q3 | 9 | 4 | 5 | 0 | 2017–2026 |
| 49 | International Journal of Biological Macromolecules | 0141-8130 | Q1 | 9 | 9 | 0 | 0 | 2020–2026 |
| 50 | International Journal of Business Information Systems | 1746-0972 | Q2, Q3 | 9 | 3 | 6 | 0 | 2016–2023 |
| 51 | International Journal of Intelligent Systems and Applications in Engineering | 2147-6799 | Q4 | 9 | 1 | 3 | 5 | 2023–2024 |
| 52 | National Academy Science Letters | 0250-541X | Q2, Q3 | 9 | 6 | 3 | 0 | 2019–2026 |
| 53 | Peer-to-Peer Networking and Applications | 1936-6442 | Q2 | 9 | 5 | 4 | 0 | 2021–2026 |
| 54 | Transactions on Emerging Telecommunications Technologies | 2161-3915 | Q2 | 9 | 6 | 3 | 0 | 2018–2026 |
| 55 | ACM Computing Surveys | 0360-0300 | Q1 | 8 | 3 | 2 | 3 | 2017–2025 |
| 56 | Analog Integrated Circuits and Signal Processing | 0925-1030 | Q3 | 8 | 5 | 2 | 1 | 2018–2025 |
| 57 | Benchmarking An International Journal | 1463-5771 | Q1, Q2 | 8 | 0 | 8 | 0 | 2018–2026 |
| 58 | ChemistrySelect | 2365-6549 | Q2, Q3 | 8 | 5 | 2 | 1 | 2018–2026 |
| 59 | Current Bioinformatics | 1574-8936 | Q2, Q3, Q4 | 8 | 8 | 0 | 0 | 2016–2026 |
| 60 | IEEE Networking Letters | 2576-3156 | Q1 | 8 | 1 | 6 | 1 | 2025–2026 |
| 61 | IEEE Transactions on Computational Social Systems | 2329-924X | Q1, Q2 | 8 | 2 | 3 | 3 | 2018–2026 |
| 62 | International Journal of Indian Culture and Business Management | 1753-0806 | unranked | 8 | 5 | 3 | 0 | 2017–2024 |
| 63 | Internet of Things | 2542-6605 | Q1 | 8 | 7 | 1 | 0 | 2019–2026 |
| 64 | Journal of Electronic Testing | 0923-8174 | Q3 | 8 | 0 | 8 | 0 | 2017–2025 |
| 65 | Journal of Molecular Structure | 0022-2860 | Q2, Q3 | 8 | 1 | 7 | 0 | 2016–2025 |
| 66 | Journal of Network and Computer Applications | 1084-8045 | Q1 | 8 | 2 | 6 | 0 | 2019–2025 |
| 67 | Kybernetes | 0368-492X | Q1, Q2 | 8 | 0 | 8 | 0 | 2018–2025 |
| 68 | Microelectronics Journal | 1879-2391 | Q2, Q3 | 8 | 2 | 5 | 1 | 2016–2026 |
| 69 | Network Modeling Analysis in Health Informatics and Bioinformatics | 2192-6670 | Q3, Q4 | 8 | 7 | 1 | 0 | 2016–2021 |
| 70 | Pattern Recognition Letters | 0167-8655 | Q1 | 8 | 7 | 1 | 0 | 2017–2025 |
| 71 | RSC Advances | 2046-2069 | Q1, Q2 | 8 | 5 | 3 | 0 | 2016–2023 |
| 72 | Signal Image and Video Processing | 1863-1703 | Q2 | 8 | 7 | 1 | 0 | 2022–2026 |
| 73 | The TQM Journal | 0954-478X | Q1, Q2 | 8 | 0 | 8 | 0 | 2018–2025 |
| 74 | Ad Hoc Networks | 1570-8705 | Q1 | 7 | 6 | 1 | 0 | 2016–2025 |
| 75 | Advanced Theory and Simulations | 2513-0390 | Q1 | 7 | 1 | 6 | 0 | 2021–2026 |
| 76 | Business Strategy and the Environment | 0964-4733 | Q1 | 7 | 0 | 7 | 0 | 2019–2026 |
| 77 | Chemical Physics Letters | 0009-2614 | Q2 | 7 | 0 | 6 | 1 | 2016–2023 |
| 78 | Circuits Systems and Signal Processing | 0278-081X | Q2, Q3 | 7 | 1 | 5 | 1 | 2017–2026 |
| 79 | INTERANTIONAL JOURNAL OF SCIENTIFIC RESEARCH IN ENGINEERING AND MANAGEMENT | 2582-3930 | unranked | 7 | 7 | 0 | 0 | 2023–2024 |
| 80 | Interdisciplinary Sciences Computational Life Sciences | 1867-1462 | Q3 | 7 | 7 | 0 | 0 | 2016–2020 |
| 81 | International Journal of Business Excellence | 1756-0047 | Q2, Q3, Q4 | 7 | 1 | 6 | 0 | 2017–2025 |
| 82 | International Journal of Machine Learning and Cybernetics | 1868-8071 | Q1, Q2 | 7 | 6 | 1 | 0 | 2016–2024 |
| 83 | Journal of Applied Mathematics and Computing | 1226-0061 | Q2, Q3 | 7 | 0 | 7 | 0 | 2018–2025 |
| 84 | Knowledge-Based Systems | 0950-7051 | Q1 | 7 | 5 | 2 | 0 | 2017–2026 |
| 85 | Modern Physics Letters B | 0217-9849 | Q3, Q4 | 7 | 1 | 6 | 0 | 2018–2020 |
| 86 | Physica Scripta | 0031-8949 | Q2 | 7 | 4 | 3 | 0 | 2024–2026 |
| 87 | Proceedings of the National Academy of Sciences India Section A Physical Sciences | 0369-8203 | Q3, Q4 | 7 | 7 | 0 | 0 | 2016–2025 |
| 88 | Proceedings of the National Academy of Sciences India Section B Biological Sciences | 0369-8211 | Q2, Q3 | 7 | 7 | 0 | 0 | 2018–2025 |
| 89 | Superlattices and Microstructures | 0749-6036 | Q2 | 7 | 4 | 3 | 0 | 2016–2021 |
| 90 | Telecommunication Systems | 1018-4864 | Q2 | 7 | 3 | 3 | 1 | 2018–2025 |
| 91 | 3 Biotech | 2190-572X | Q1, Q2 | 6 | 6 | 0 | 0 | 2016–2026 |
| 92 | Biomedical Physics & Engineering Express | 2057-1976 | Q3 | 6 | 5 | 1 | 0 | 2016–2025 |
| 93 | Biomedical Signal Processing and Control | 1746-8094 | Q1 | 6 | 2 | 2 | 2 | 2021–2026 |
| 94 | Chaos Solitons & Fractals | 0960-0779 | Q1 | 6 | 5 | 1 | 1 | 2020–2026 |
| 95 | Computer Networks | 1389-1286 | Q1, Q2 | 6 | 2 | 0 | 4 | 2016–2025 |
| 96 | Computers in Biology and Medicine | 0010-4825 | Q1 | 6 | 4 | 2 | 0 | 2021–2025 |
| 97 | Environment Development and Sustainability | 1387-585X | Q1, Q2 | 6 | 4 | 2 | 0 | 2020–2023 |
| 98 | Facta universitatis - series Electronics and Energetics | 0353-3670 | Q3, Q4 | 6 | 0 | 6 | 0 | 2019–2025 |
| 99 | IEEE Geoscience and Remote Sensing Letters | 1545-598X | Q1 | 6 | 3 | 0 | 3 | 2017–2024 |
| 100 | IEEE Transactions on Computational Biology and Bioinformatics | 1545-5963 | Q2 | 6 | 4 | 2 | 0 | 2020–2025 |
| 101 | IEEE Transactions on Consumer Electronics | 0098-3063 | Q1 | 6 | 1 | 5 | 0 | 2019–2026 |
| 102 | IEEE Transactions on Instrumentation and Measurement | 0018-9456 | Q1 | 6 | 3 | 2 | 1 | 2022–2025 |
| 103 | IEEE Transactions on Intelligent Transportation Systems | 1524-9050 | Q1 | 6 | 3 | 2 | 1 | 2020–2023 |
| 104 | IEEE Transactions on Wireless Communications | 1536-1276 | Q1 | 6 | 0 | 1 | 5 | 2016–2026 |
| 105 | IET Circuits Devices & Systems | 1751-858X | Q2, Q3 | 6 | 4 | 1 | 1 | 2017–2022 |
| 106 | IETE Technical Review | 0256-4602 | Q2, Q3 | 6 | 2 | 3 | 1 | 2018–2022 |
| 107 | Image and Vision Computing | 0262-8856 | Q1, Q2 | 6 | 6 | 0 | 0 | 2020–2025 |
| 108 | Intelligent Service Robotics | 1861-2776 | Q1, Q2 | 6 | 4 | 2 | 0 | 2017–2026 |
| 109 | International Journal of Microwave and Wireless Technologies | 1759-0787 | Q3 | 6 | 2 | 4 | 0 | 2021–2025 |
| 110 | International Journal of Services and Operations Management | 1744-2370 | Q2, Q3 | 6 | 0 | 6 | 0 | 2016–2025 |
| 111 | Journal of Intelligent & Fuzzy Systems | 1064-1246 | Q1, Q2 | 6 | 6 | 0 | 0 | 2018–2023 |
| 112 | Materials Chemistry and Physics | 0254-0584 | Q1, Q2 | 6 | 2 | 3 | 1 | 2019–2025 |
| 113 | Materials Today Communications | 2352-4928 | Q1, Q2 | 6 | 5 | 1 | 0 | 2018–2026 |
| 114 | Mathematical Methods in the Applied Sciences | 0170-4214 | Q1, Q2 | 6 | 0 | 6 | 0 | 2019–2026 |
| 115 | Mathematics | 2227-7390 | Q2 | 6 | 3 | 3 | 0 | 2021–2025 |
| 116 | Mediterranean Journal of Mathematics | 1660-5446 | Q1, Q2 | 6 | 3 | 3 | 0 | 2021–2025 |
| 117 | Nanotechnology | 0957-4484 | Q1, Q2 | 6 | 6 | 0 | 0 | 2019–2026 |
| 118 | Physica B Condensed Matter | 0921-4526 | Q2 | 6 | 5 | 1 | 0 | 2021–2026 |
| 119 | Physical Chemistry Chemical Physics | 1463-9076 | Q1, Q2 | 6 | 4 | 0 | 2 | 2019–2024 |
| 120 | Physical review. B./Physical review. B | 2469-9950 | Q1 | 6 | 6 | 0 | 0 | 2018–2026 |
| 121 | Robotica | 0263-5747 | Q2 | 6 | 6 | 0 | 0 | 2018–2023 |
| 122 | Solid State Communications | 0038-1098 | Q2 | 6 | 0 | 6 | 0 | 2016–2023 |
| 123 | The European Physical Journal Plus | 2190-5444 | Q2 | 6 | 2 | 4 | 0 | 2022–2026 |
| 124 | The Visual Computer | 0178-2789 | Q2, Q3 | 6 | 2 | 4 | 0 | 2018–2024 |
| 125 | Theoretical Computer Science | 0304-3975 | Q1, Q2 | 6 | 1 | 1 | 4 | 2016–2025 |
| 126 | Asian Journal of Civil Engineering | 1563-0854 | Q2 | 5 | 0 | 5 | 0 | 2024–2025 |
| 127 | Biologia | 0006-3088 | Q2, Q3 | 5 | 5 | 0 | 0 | 2022–2026 |
| 128 | Computational and Applied Mathematics | 0101-8205 | Q2 | 5 | 0 | 5 | 0 | 2016–2026 |
| 129 | Computational Biology and Chemistry | 1476-9271 | Q2 | 5 | 4 | 1 | 0 | 2017–2026 |
| 130 | Concurrency and Computation Practice and Experience | 1532-0626 | Q2, Q3 | 5 | 4 | 0 | 1 | 2018–2024 |
| 131 | CSI Transactions on ICT | 2277-9078 | unranked | 5 | 0 | 1 | 4 | 2018–2020 |
| 132 | Discrete and Continuous Dynamical Systems - S | 1937-1179 | Q2 | 5 | 5 | 0 | 0 | 2024–2026 |
| 133 | Evolving Systems | 1868-6478 | Q1, Q2 | 5 | 4 | 1 | 0 | 2022–2026 |
| 134 | Global Business Review | 0972-1509 | Q2 | 5 | 2 | 3 | 0 | 2016–2020 |
| 135 | IEEE Signal Processing Letters | 1070-9908 | Q1 | 5 | 2 | 3 | 0 | 2017–2025 |
| 136 | IEEE Transactions on Circuits & Systems II Express Briefs | 1549-7747 | Q1 | 5 | 4 | 2 | 0 | 2022–2026 |
| 137 | IEEE Transactions on Circuits and Systems I Regular Papers | 1549-8328 | Q1 | 5 | 1 | 2 | 2 | 2023–2026 |
| 138 | IEEE Transactions on Dielectrics and Electrical Insulation | 1070-9878 | Q1 | 5 | 1 | 4 | 0 | 2024–2026 |
| 139 | IEEE Transactions on Reliability | 0018-9529 | Q1 | 5 | 0 | 5 | 0 | 2021–2026 |
| 140 | IET Communications | 1751-8628 | Q2 | 5 | 3 | 2 | 0 | 2019–2026 |
| 141 | International Journal of Computer Applications | 0975-8887 | unranked | 5 | 5 | 0 | 0 | 2016–2026 |
| 142 | International Journal of Interactive Multimedia and Artificial Intelligence | 1989-1660 | Q2 | 5 | 4 | 0 | 1 | 2016–2022 |
| 143 | Journal of Advances in Management Research | 0972-7981 | Q2 | 5 | 0 | 5 | 0 | 2018–2022 |
| 144 | Journal of Ambient Intelligence and Humanized Computing | 1868-5137 | Q1 | 5 | 4 | 2 | 0 | 2019–2023 |
| 145 | Journal of Computational Electronics | 1569-8025 | Q2, Q3 | 5 | 2 | 3 | 0 | 2018–2025 |
| 146 | Journal of Molecular Modeling | 0948-5023 | Q2, Q3 | 5 | 1 | 5 | 0 | 2018–2025 |
| 147 | Machine Vision and Applications | 0932-8092 | Q2 | 5 | 5 | 0 | 0 | 2021–2025 |
| 148 | Microbial Pathogenesis | 0882-4010 | Q2 | 5 | 5 | 0 | 0 | 2017–2023 |
| 149 | Microprocessors and Microsystems | 0141-9331 | Q2, Q3 | 5 | 1 | 4 | 0 | 2016–2023 |
| 150 | Microwave and Optical Technology Letters | 0895-2477 | Q2, Q3 | 5 | 5 | 0 | 0 | 2016–2020 |
| 151 | Modeling Earth Systems and Environment | 2363-6203 | Q1, Q2 | 5 | 0 | 5 | 0 | 2016–2023 |
| 152 | Pattern Analysis and Applications | 1433-7541 | Q2 | 5 | 4 | 1 | 0 | 2016–2024 |
| 153 | physica status solidi (b) | 0370-1972 | Q1, Q2, Q3 | 5 | 1 | 4 | 0 | 2016–2025 |
| 154 | Pramana | 0304-4289 | Q2, Q3 | 5 | 0 | 5 | 0 | 2017–2021 |
| 155 | Ricerche di Matematica | 0035-5038 | Q2, Q3 | 5 | 3 | 2 | 0 | 2019–2026 |
| 156 | Signal Processing | 0165-1684 | Q1 | 5 | 1 | 4 | 0 | 2018–2026 |
| 157 | ACM Transactions on Asian and Low-Resource Language Information Processing | 2375-4699 | Q2 | 4 | 1 | 1 | 2 | 2021–2026 |
| 158 | Applied Acoustics | 0003-682X | Q1 | 4 | 0 | 4 | 0 | 2019–2022 |
| 159 | Artificial Intelligence Review | 0269-2821 | Q1 | 4 | 2 | 2 | 0 | 2022–2025 |
| 160 | Computing | 0010-485X | Q2 | 4 | 0 | 4 | 0 | 2017–2025 |
| 161 | Current Computer - Aided Drug Design | 1573-4099 | Q3 | 4 | 4 | 0 | 0 | 2016–2025 |
| 162 | Electronics | 2079-9292 | Q2 | 4 | 2 | 2 | 0 | 2016–2026 |
| 163 | Engineering Applications of Artificial Intelligence | 0952-1976 | Q1 | 4 | 2 | 2 | 0 | 2017–2026 |
| 164 | Expert Systems | 0266-4720 | Q2 | 4 | 2 | 2 | 0 | 2023–2024 |
| 165 | Future Generation Computer Systems | 0167-739X | Q1 | 4 | 3 | 1 | 0 | 2017–2025 |
| 166 | IEEE Communications Standards Magazine | 2471-2825 | Q1 | 4 | 0 | 4 | 0 | 2025–2026 |
| 167 | IEEE Open Journal of Vehicular Technology | 2644-1330 | Q1 | 4 | 2 | 2 | 0 | 2021–2026 |
| 168 | IEEE Transactions on Components Packaging and Manufacturing Technology | 2156-3950 | Q1, Q2 | 4 | 1 | 3 | 0 | 2019–2026 |
| 169 | IEEE Transactions on Emerging Topics in Computational Intelligence | 2471-285X | Q1 | 4 | 2 | 2 | 0 | 2022–2026 |
| 170 | IEEE Transactions on Emerging Topics in Computing | 2168-6750 | Q1 | 4 | 1 | 4 | 0 | 2018–2022 |
| 171 | IEEE Transactions on Information Theory | 0018-9448 | Q1 | 4 | 0 | 0 | 4 | 2016–2025 |
| 172 | IEEE Transactions on Sustainable Computing | 2377-3782 | Q1 | 4 | 1 | 3 | 0 | 2024–2025 |
| 173 | IET Image Processing | 1751-9659 | Q2 | 4 | 4 | 0 | 0 | 2019–2021 |
| 174 | Indian Journal of Finance and Banking | 2574-6081 | unranked | 4 | 4 | 0 | 0 | 2020–2022 |
| 175 | Indian Journal of Physics | 0019-5480 | Q3 | 4 | 4 | 0 | 0 | 2020–2026 |
| 176 | Indian Journal of Pure and Applied Mathematics | 0019-5588 | Q3 | 4 | 3 | 0 | 1 | 2022–2026 |
| 177 | Information Sciences | 0020-0255 | Q1 | 4 | 0 | 4 | 0 | 2018–2021 |
| 178 | International Journal of Biomathematics | 1793-5245 | Q2, Q3 | 4 | 0 | 4 | 0 | 2020–2023 |
| 179 | International Journal of Database Theory and Application | 2005-4270 | Q3 | 4 | 4 | 0 | 0 | 2016 |
| 180 | International Journal of Dynamics and Control | 2195-268X | Q2 | 4 | 0 | 4 | 0 | 2021–2023 |
| 181 | International Journal of Emerging Markets | 1746-8809 | Q2 | 4 | 1 | 3 | 0 | 2021–2022 |
| 182 | International Journal of Environmental Sciences | 2229-7359 | Q4 | 4 | 0 | 4 | 0 | 2025 |
| 183 | International Journal of Pattern Recognition and Artificial Intelligence | 0218-0014 | Q3 | 4 | 4 | 0 | 0 | 2021–2026 |
| 184 | International Journal of Productivity and Performance Management | 0043-8022 | Q1, Q2 | 4 | 1 | 3 | 0 | 2020–2024 |
| 185 | International Journal of RF and Microwave Computer-Aided Engineering | 1096-4290 | Q2 | 4 | 2 | 2 | 0 | 2019–2022 |
| 186 | International Journal of Sensor Networks | 1748-1279 | Q3 | 4 | 4 | 0 | 0 | 2016–2018 |
| 187 | Journal of Applied Biomedicine | 0208-5216 | Q1, Q2 | 4 | 1 | 1 | 2 | 2020–2023 |
| 188 | Journal of Computational and Theoretical Nanoscience | 1546-1955 | Q3, Q4 | 4 | 0 | 4 | 0 | 2017–2020 |
| 189 | Journal of Computational Science | 1877-7503 | Q1, Q2 | 4 | 0 | 2 | 2 | 2019–2026 |
| 190 | Journal of Energy Storage | 2352-152X | Q1 | 4 | 0 | 4 | 0 | 2022–2026 |
| 191 | Journal of Environmental Management | 0301-4797 | Q1 | 4 | 3 | 1 | 0 | 2018–2021 |
| 192 | Journal of Indian Business Research | 1755-4195 | Q2, Q3 | 4 | 1 | 3 | 0 | 2018–2022 |
| 193 | Journal of Industrial Information Integration | 2452-414X | Q1 | 4 | 1 | 3 | 0 | 2023–2024 |
| 194 | Journal of Mathematics and Computer Science | 2008-949X | Q2 | 4 | 0 | 4 | 0 | 2022–2024 |
| 195 | Journal of Physics and Chemistry of Solids | 0022-3697 | Q1, Q2 | 4 | 2 | 2 | 0 | 2021–2026 |
| 196 | Journal of Quantum Science and Technology. | 3048-6351 | unranked | 4 | 0 | 0 | 4 | 2024 |
| 197 | Journal of the Association for Information Systems | 1536-9323 | Q1 | 4 | 3 | 0 | 1 | 2020–2026 |
| 198 | Journal of the Optical Society of America A | 1084-7529 | Q1, Q2 | 4 | 4 | 0 | 0 | 2019–2020 |
| 199 | Knowledge and Information Systems | 0219-1377 | Q1, Q2 | 4 | 3 | 1 | 0 | 2024–2026 |
| 200 | Letters in Drug Design & Discovery | 1570-1808 | Q2, Q3 | 4 | 4 | 0 | 0 | 2016–2025 |
| 201 | Materials Research Express | 2053-1591 | Q2 | 4 | 2 | 1 | 1 | 2018–2020 |
| 202 | Materials Science in Semiconductor Processing | 1369-8001 | Q1 | 4 | 3 | 2 | 0 | 2021–2026 |
| 203 | Micro and Nanostructures | 2773-0123 | Q2 | 4 | 3 | 1 | 0 | 2022–2026 |
| 204 | Multimedia Systems | 0942-4962 | Q1 | 4 | 3 | 0 | 1 | 2022–2024 |
| 205 | Neural Processing Letters | 1370-4621 | Q2 | 4 | 3 | 1 | 0 | 2019–2024 |
| 206 | OPSEARCH | 0030-3887 | Q2 | 4 | 0 | 4 | 0 | 2019–2026 |
| 207 | Pervasive and Mobile Computing | 1574-1192 | Q1 | 4 | 2 | 1 | 1 | 2018–2025 |
| 208 | Physics of Fluids | 1070-6631 | Q1 | 4 | 1 | 2 | 1 | 2022–2026 |
| 209 | Plasmonics | 1557-1955 | Q2, Q3 | 4 | 4 | 0 | 0 | 2020–2024 |
| 210 | PLoS ONE | 1932-6203 | Q1 | 4 | 2 | 1 | 1 | 2019–2024 |
| 211 | Results in Control and Optimization | 2666-7207 | Q2 | 4 | 0 | 4 | 0 | 2023–2024 |
| 212 | Sensors and Actuators B Chemical | 0925-4005 | Q1 | 4 | 4 | 0 | 0 | 2019–2021 |
| 213 | Silicon | 1876-990X | Q2, Q3 | 4 | 2 | 2 | 0 | 2017–2023 |
| 214 | Sustainable Computing Informatics and Systems | 2210-5379 | Q1, Q2 | 4 | 2 | 1 | 1 | 2019–2022 |
| 215 | Telecommunications Policy | 0308-5961 | Q1 | 4 | 0 | 0 | 4 | 2020–2023 |
| 216 | The Journal of Analysis | 0971-3611 | Q2, Q3 | 4 | 3 | 1 | 0 | 2022–2026 |
| 217 | The Journal of the Acoustical Society of America | 0001-4966 | Q1 | 4 | 4 | 0 | 0 | 2016–2026 |
| 218 | ACM Transactions on Intelligent Systems and Technology | 2157-6904 | Q1 | 3 | 0 | 3 | 0 | 2024–2026 |
| 219 | Advances in Complex Systems | 0219-5259 | Q2, Q3 | 3 | 0 | 1 | 2 | 2021–2026 |
| 220 | Analytica Chimica Acta | 0003-2670 | Q1 | 3 | 1 | 0 | 2 | 2022–2025 |
| 221 | Annals of Operations Research | 0254-5330 | Q1 | 3 | 0 | 3 | 0 | 2020–2023 |
| 222 | Applied Sciences | 2076-3417 | Q2 | 3 | 2 | 1 | 0 | 2021–2024 |
| 223 | Archives of Computational Methods in Engineering | 1134-3060 | Q1 | 3 | 0 | 2 | 1 | 2026 |
| 224 | Asian Journal of Chemistry | 0970-7077 | Q4 | 3 | 0 | 3 | 0 | 2023 |
| 225 | Australian Journal of Maritime & Ocean Affairs | 1836-6503 | Q2, Q3 | 3 | 0 | 2 | 1 | 2022–2026 |
| 226 | Chaos An Interdisciplinary Journal of Nonlinear Science | 1054-1500 | Q1, Q2 | 3 | 0 | 0 | 3 | 2016–2026 |
| 227 | Chemistry - A European Journal | 0947-6539 | Q1 | 3 | 0 | 1 | 2 | 2016–2026 |
| 228 | Clinical and Experimental Medical Letters | 1689-6807 | Q4 | 3 | 3 | 0 | 0 | 2018 |
| 229 | Complex & Intelligent Systems | 2198-6053 | Q1 | 3 | 1 | 2 | 0 | 2022–2026 |
| 230 | Computational and Mathematical Biophysics | 2544-7297 | Q3 | 3 | 0 | 2 | 1 | 2023 |
| 231 | Computational and Theoretical Chemistry | 2210-271X | Q2, Q3 | 3 | 0 | 2 | 1 | 2018–2024 |
| 232 | Computational Intelligence | 0824-7935 | Q2, Q3 | 3 | 2 | 1 | 0 | 2017–2023 |
| 233 | Computer Applications in Engineering Education | 1061-3773 | Q1 | 3 | 1 | 2 | 0 | 2016–2024 |
| 234 | Computer Science Review | 1574-0137 | Q1 | 3 | 3 | 0 | 0 | 2019–2021 |
| 235 | Computers & Security | 0167-4048 | Q1 | 3 | 1 | 1 | 1 | 2018–2024 |
| 236 | Computers and Education Artificial Intelligence | 2666-920X | Q1 | 3 | 0 | 0 | 3 | 2022 |
| 237 | Current Genomics | 1389-2029 | Q3 | 3 | 3 | 0 | 0 | 2019–2020 |
| 238 | Current Topics in Medicinal Chemistry | 1568-0266 | Q1, Q2 | 3 | 3 | 0 | 0 | 2018–2022 |
| 239 | Darpan International Research Analysis | 2321-3094 | unranked | 3 | 0 | 1 | 2 | 2024–2025 |
| 240 | Digital Signal Processing | 1051-2004 | Q1, Q2 | 3 | 1 | 2 | 0 | 2020–2026 |
| 241 | Drones | 2504-446X | Q1 | 3 | 2 | 0 | 1 | 2022–2026 |
| 242 | Environmental Science and Pollution Research | 0944-1344 | Q1 | 3 | 2 | 1 | 0 | 2021–2024 |
| 243 | Ferroelectrics | 0015-0193 | Q3 | 3 | 2 | 1 | 0 | 2016–2017 |
| 244 | Ferroelectrics Letters Section | 0731-5171 | Q3, Q4 | 3 | 3 | 0 | 0 | 2019–2021 |
| 245 | Frontiers in Education | 2504-284X | Q1, Q2 | 3 | 0 | 3 | 0 | 2024–2025 |
| 246 | Frontiers in Energy Research | 2296-598X | Q2 | 3 | 3 | 0 | 0 | 2021–2025 |
| 247 | Frontiers in Signal Processing | 2673-8198 | Q2 | 3 | 0 | 1 | 2 | 2022–2026 |
| 248 | Global Journal of Flexible Systems Management | 0972-2696 | Q1, Q2 | 3 | 0 | 3 | 0 | 2016–2026 |
| 249 | Health Information Science and Systems | 2047-2501 | Q2 | 3 | 3 | 0 | 0 | 2024–2026 |
| 250 | Heliyon | 2405-8440 | Q1 | 3 | 1 | 2 | 0 | 2024 |
| 251 | Humanities and Social Sciences Communications | 2055-1045 | Q1 | 3 | 3 | 0 | 0 | 2023–2026 |
| 252 | IEEE Communications Surveys & Tutorials | 1553-877X | Q1 | 3 | 1 | 2 | 0 | 2019–2025 |
| 253 | IEEE Embedded Systems Letters | 1943-0663 | Q2 | 3 | 3 | 0 | 0 | 2020–2025 |
| 254 | IEEE Journal on Selected Areas in Information Theory | 2641-8770 | unranked | 3 | 0 | 0 | 3 | 2021 |
| 255 | IEEE Transactions on Aerospace and Electronic Systems | 0018-9251 | Q1 | 3 | 1 | 1 | 1 | 2018–2026 |
| 256 | IEEE Transactions on Cognitive Communications and Networking | 2332-7731 | Q1 | 3 | 0 | 3 | 0 | 2023 |
| 257 | IEEE Transactions on Geoscience and Remote Sensing | 0196-2892 | Q1 | 3 | 3 | 0 | 0 | 2017–2022 |
| 258 | IEEE Transactions on Industrial Informatics | 1551-3203 | Q1 | 3 | 0 | 3 | 0 | 2021–2025 |
| 259 | IEEE Transactions on Network Science and Engineering | 2327-4697 | Q1 | 3 | 3 | 0 | 0 | 2018–2025 |
| 260 | IEEE Transactions on Plasma Science | 0093-3813 | Q2 | 3 | 2 | 1 | 0 | 2023–2026 |
| 261 | IEEE Transactions on Very Large Scale Integration (VLSI) Systems | 1063-8210 | Q1, Q2 | 3 | 1 | 1 | 1 | 2021–2026 |
| 262 | IET Biometrics | 2047-4938 | Q2, Q3 | 3 | 2 | 1 | 0 | 2016–2021 |
| 263 | Indian Journal of Information Sources and Services | 2231-6094 | Q2 | 3 | 0 | 0 | 3 | 2026 |
| 264 | Indian Journal of Marketing | 0973-8703 | Q3 | 3 | 0 | 3 | 0 | 2016–2023 |
| 265 | Indian Journal of Science and Technology | 0974-5645 | Q2, Q3 | 3 | 1 | 2 | 0 | 2016–2017 |
| 266 | Information Processing Letters | 0020-0190 | Q2, Q3 | 3 | 0 | 1 | 2 | 2018–2024 |
| 267 | Information Security Journal A Global Perspective | 1939-3547 | Q2, Q3 | 3 | 0 | 3 | 0 | 2017–2020 |
| 268 | International Journal For Multidisciplinary Research | 2582-2160 | unranked | 3 | 1 | 2 | 0 | 2023–2026 |
| 269 | International Journal of Accounting & Finance Review | 2576-1285 | unranked | 3 | 3 | 0 | 0 | 2020–2023 |
| 270 | International Journal of Applied and Computational Mathematics | 2199-5796 | Q3 | 3 | 0 | 3 | 0 | 2017–2018 |
| 271 | International Journal of Blockchains and Cryptocurrencies | 2516-6425 | unranked | 3 | 3 | 0 | 0 | 2019–2021 |
| 272 | International Journal of Business Forecasting and Marketing Intelligence | 1744-6635 | unranked | 3 | 1 | 2 | 0 | 2016–2018 |
| 273 | International Journal of Computer Applications in Technology | 0952-8091 | Q2, Q3 | 3 | 3 | 0 | 0 | 2016–2019 |
| 274 | International Journal of Electronic Marketing and Retailing | 1741-1025 | Q3 | 3 | 0 | 3 | 0 | 2017–2021 |
| 275 | International Journal of Electronics | 0020-7217 | Q3 | 3 | 3 | 0 | 0 | 2017–2024 |
| 276 | International Journal of Human-Computer Interaction | 1044-7318 | Q1 | 3 | 1 | 2 | 0 | 2023–2025 |
| 277 | International Journal of Information Security | 1615-5262 | Q1, Q2 | 3 | 2 | 1 | 0 | 2021–2024 |
| 278 | International Journal of Information Technology | 2511-2104 | Q2 | 3 | 0 | 2 | 1 | 2018–2021 |
| 279 | International Journal of Peptide Research and Therapeutics | 1573-3149 | Q3 | 3 | 3 | 0 | 0 | 2024 |
| 280 | International Journal of Reliability Quality and Safety Engineering | 0218-5393 | Q3 | 3 | 0 | 3 | 0 | 2024 |
| 281 | International Journal of Research in Engineering Science and Management | 2581-5792 | unranked | 3 | 0 | 0 | 3 | 2020 |
| 282 | JMIR mhealth and uhealth | 2291-5222 | Q1 | 3 | 0 | 0 | 3 | 2025–2026 |
| 283 | Journal of Alloys and Compounds | 0925-8388 | Q1 | 3 | 1 | 2 | 0 | 2021–2022 |
| 284 | Journal of Applied Remote Sensing | 1931-3195 | Q2 | 3 | 3 | 0 | 0 | 2016–2024 |
| 285 | Journal of Cleaner Production | 0959-6526 | Q1 | 3 | 1 | 2 | 0 | 2019–2024 |
| 286 | Journal of Creative Communications | 0973-2586 | Q2, Q3 | 3 | 0 | 3 | 0 | 2017–2024 |
| 287 | Journal of Experimental & Theoretical Artificial Intelligence | 0952-813X | Q2, Q3 | 3 | 1 | 2 | 0 | 2016–2022 |
| 288 | Journal of Information Technology Teaching Cases | 2043-8869 | Q3, Q4 | 3 | 0 | 0 | 3 | 2017–2020 |
| 289 | Journal of King Saud University - Computer and Information Sciences | 1319-1578 | Q1 | 3 | 1 | 2 | 0 | 2019–2024 |
| 290 | Journal of Magnetism and Magnetic Materials | 0304-8853 | Q2 | 3 | 2 | 1 | 0 | 2018–2026 |
| 291 | Journal of Physics D Applied Physics | 0022-3727 | Q1 | 3 | 3 | 0 | 0 | 2023–2024 |
| 292 | Journal of Sensors | 1687-725X | Q3 | 3 | 2 | 0 | 1 | 2016–2024 |
| 293 | Journal of the American Ceramic Society | 0002-7820 | Q1, Q2 | 3 | 3 | 0 | 0 | 2020–2026 |
| 294 | Journal of the Indian Society of Remote Sensing | 0255-660X | Q2 | 3 | 3 | 0 | 0 | 2022–2024 |
| 295 | Journal of theoretical and applied electronic commerce research | 0718-1876 | Q1 | 3 | 3 | 0 | 0 | 2024–2025 |
| 296 | Journal of Visual Communication and Image Representation | 1047-3203 | Q1 | 3 | 2 | 1 | 0 | 2017–2024 |
| 297 | Materials Science and Engineering B | 0921-5107 | Q2 | 3 | 0 | 3 | 0 | 2021–2022 |
| 298 | Materials Science and Engineering C | 0928-4931 | Q1 | 3 | 2 | 1 | 0 | 2018–2019 |
| 299 | Materials Technology | 1066-7857 | Q2 | 3 | 3 | 0 | 0 | 2021–2022 |
| 300 | Mathematics and Computers in Simulation | 0378-4754 | Q1 | 3 | 0 | 3 | 0 | 2023–2026 |
| 301 | Measurement | 0263-2241 | Q1 | 3 | 3 | 0 | 0 | 2019–2021 |
| 302 | Medical & Biological Engineering & Computing | 0140-0118 | Q2 | 3 | 0 | 2 | 1 | 2020–2025 |
| 303 | MethodsX | 2215-0161 | Q1, Q2 | 3 | 1 | 2 | 0 | 2024–2025 |
| 304 | Microelectronics Reliability | 0026-2714 | Q2 | 3 | 2 | 1 | 0 | 2021–2026 |
| 305 | Mobile Information Systems | 1574-017X | Q2, Q3 | 3 | 1 | 1 | 1 | 2016–2022 |
| 306 | Molecular Diversity | 1381-1991 | Q2 | 3 | 3 | 0 | 0 | 2024 |
| 307 | Neural Networks | 0893-6080 | Q1 | 3 | 2 | 0 | 1 | 2021–2023 |
| 308 | Next Materials | 2949-8228 | Q1 | 3 | 2 | 1 | 0 | 2025–2026 |
| 309 | Non-coding RNA Research | 2468-0540 | Q1, Q3 | 3 | 3 | 0 | 0 | 2016–2019 |
| 310 | Physica A Statistical Mechanics and its Applications | 0378-4371 | Q1, Q2 | 3 | 0 | 2 | 1 | 2018–2021 |
| 311 | Physica E Low-dimensional Systems and Nanostructures | 1386-9477 | Q2 | 3 | 2 | 1 | 0 | 2021–2022 |
| 312 | Physics of the Solid State | 0367-3294 | Q3, Q4 | 3 | 0 | 3 | 0 | 2020–2025 |
| 313 | Qualitative Theory of Dynamical Systems | 1575-5460 | Q1, Q2 | 3 | 0 | 3 | 0 | 2023–2025 |
| 314 | Results in Optics | 2666-9501 | Q3 | 3 | 3 | 0 | 0 | 2021–2023 |
| 315 | Sensors | 1424-8220 | Q1 | 3 | 1 | 1 | 1 | 2021–2024 |
| 316 | Social Network Analysis and Mining | 1869-5450 | Q1 | 3 | 1 | 2 | 0 | 2016–2022 |
| 317 | Surfaces and Interfaces | 2468-0230 | Q1 | 3 | 2 | 1 | 0 | 2021–2025 |
| 318 | Sustainable Development | 0968-0802 | Q1 | 3 | 2 | 1 | 0 | 2021–2026 |
| 319 | Technology in Society | 0160-791X | Q1 | 3 | 1 | 2 | 0 | 2020–2025 |
| 320 | The European Physical Journal Special Topics | 1951-6355 | Q2 | 3 | 2 | 1 | 0 | 2021–2023 |
| 321 | The Journal of Physical Chemistry C | 1932-7447 | Q1 | 3 | 3 | 0 | 0 | 2021–2024 |
| 322 | TURKISH JOURNAL OF ELECTRICAL ENGINEERING & COMPUTER SCIENCES | 1300-0632 | Q2, Q3 | 3 | 3 | 0 | 0 | 2016–2022 |
| 323 | Vision The Journal of Business Perspective | 0972-2629 | Q3 | 3 | 2 | 1 | 0 | 2021–2022 |
| 324 | ACM Journal on Computing and Sustainable Societies | 2834-5533 | unranked | 2 | 0 | 0 | 2 | 2024–2025 |
| 325 | ACM SIGSOFT Software Engineering Notes | 0163-5948 | unranked | 2 | 0 | 1 | 2 | 2018–2026 |
| 326 | ACM Transactions on Computing for Healthcare | 2637-8051 | Q1 | 2 | 0 | 1 | 1 | 2024–2026 |
| 327 | ACM Transactions on Cyber-Physical Systems | 2378-962X | Q1, Q2 | 2 | 1 | 1 | 0 | 2024–2025 |
| 328 | ACM Transactions on Multimedia Computing Communications and Applications | 1551-6857 | Q1 | 2 | 2 | 0 | 0 | 2020 |
| 329 | Advanced Materials Letters | 0976-3961 | Q2 | 2 | 0 | 2 | 0 | 2016 |
| 330 | Advances in Condensed Matter Physics | 1687-8108 | Q3 | 2 | 2 | 0 | 0 | 2024–2025 |
| 331 | Advances in Global Economics and Business Journal | 2723-2042 | unranked | 2 | 0 | 2 | 0 | 2025 |
| 332 | Advances in Materials and Processing Technologies | 2374-068X | Q2 | 2 | 2 | 0 | 0 | 2023–2024 |
| 333 | Applied Artificial Intelligence | 0883-9514 | Q3 | 2 | 1 | 1 | 0 | 2020–2021 |
| 334 | Applied Mathematics and Computation | 0096-3003 | Q1 | 2 | 1 | 1 | 0 | 2024–2025 |
| 335 | Applied Nanoscience | 2190-5509 | Q2 | 2 | 1 | 1 | 0 | 2018–2020 |
| 336 | Array | 2590-0056 | Q1 | 2 | 1 | 0 | 1 | 2021–2022 |
| 337 | Asian-European Journal of Mathematics | 1793-5571 | Q3 | 2 | 2 | 0 | 0 | 2021–2025 |
| 338 | Augmented Human Research | 2365-4317 | unranked | 2 | 2 | 0 | 0 | 2023–2024 |
| 339 | Bangladesh Journal of Multidisciplinary Scientific Research | 2687-850X | Q3, Q4 | 2 | 2 | 0 | 0 | 2024–2026 |
| 340 | Beilstein Journal of Nanotechnology | 2190-4286 | Q2 | 2 | 2 | 1 | 0 | 2024–2025 |
| 341 | Bio-Algorithms and Med-Systems | 1895-9091 | Q4 | 2 | 0 | 2 | 0 | 2018–2020 |
| 342 | Biochemical and Biophysical Research Communications | 0006-291X | Q2 | 2 | 2 | 0 | 0 | 2024 |
| 343 | Bioengineering | 2306-5354 | Q2 | 2 | 0 | 0 | 2 | 2025–2026 |
| 344 | Bioinformatics | 1367-4803 | Q1 | 2 | 1 | 0 | 1 | 2020–2025 |
| 345 | Biomedical Materials | 1748-6041 | Q2 | 2 | 2 | 0 | 0 | 2022–2023 |
| 346 | Biomolecules | 2218-273X | Q1 | 2 | 2 | 0 | 0 | 2018–2024 |
| 347 | Bioorganic Chemistry | 0045-2068 | Q1, Q2 | 2 | 2 | 0 | 0 | 2021–2025 |
| 348 | Bioresource Technology | 0960-8524 | Q1 | 2 | 2 | 0 | 0 | 2016–2020 |
| 349 | Brain Sciences | 2076-3425 | Q3 | 2 | 2 | 0 | 0 | 2022 |
| 350 | British Food Journal | 0007-070X | Q1 | 2 | 1 | 1 | 0 | 2023–2026 |
| 351 | Bulletin of Materials Science | 0250-4707 | Q2, Q3 | 2 | 1 | 1 | 0 | 2018–2023 |
| 352 | Business Strategy & Development | 2572-3170 | Q1 | 2 | 0 | 2 | 0 | 2019–2026 |
| 353 | Case Studies in Thermal Engineering | 2214-157X | Q1 | 2 | 2 | 0 | 0 | 2019–2020 |
| 354 | Ceramics International | 0272-8842 | Q1 | 2 | 2 | 0 | 0 | 2025 |
| 355 | Chemical Engineering Journal | 1385-8947 | Q1 | 2 | 2 | 0 | 0 | 2024–2025 |
| 356 | Classical and Quantum Gravity | 0264-9381 | Q1 | 2 | 2 | 0 | 0 | 2018–2023 |
| 357 | Colloids and Surfaces B Biointerfaces | 0927-7765 | Q1 | 2 | 2 | 0 | 0 | 2022–2026 |
| 358 | Colloquium Mathematicum | 0010-1354 | Q2 | 2 | 2 | 0 | 0 | 2019–2021 |
| 359 | Communications in Algebra | 0092-7872 | Q2 | 2 | 2 | 0 | 0 | 2024 |
| 360 | Communications in Nonlinear Science and Numerical Simulation | 1007-5704 | Q1 | 2 | 0 | 2 | 0 | 2020 |
| 361 | Communications of the Association for Information Systems | 1529-3181 | Q2 | 2 | 1 | 0 | 1 | 2016–2023 |
| 362 | Computer Communications | 0140-3664 | Q1, Q2 | 2 | 1 | 0 | 1 | 2017–2020 |
| 363 | Computer Methods and Programs in Biomedicine | 0169-2607 | Q1, Q2 | 2 | 1 | 1 | 0 | 2016–2019 |
| 364 | Current Medicinal Chemistry | 0929-8673 | Q1 | 2 | 2 | 0 | 0 | 2021–2022 |
| 365 | Current Neuropharmacology | 1570-159X | Q1 | 2 | 2 | 0 | 0 | 2018–2026 |
| 366 | Current Pharmaceutical Design | 1381-6128 | Q2 | 2 | 2 | 0 | 0 | 2019–2022 |
| 367 | Current Proteomics | 1570-1646 | Q4 | 2 | 2 | 0 | 0 | 2016 |
| 368 | Current Science | 0011-3891 | Q2 | 2 | 1 | 0 | 1 | 2018–2021 |
| 369 | Diagnostics | 2075-4418 | Q2 | 2 | 1 | 1 | 0 | 2022–2026 |
| 370 | Differential Equations and Dynamical Systems | 0971-3514 | Q3 | 2 | 0 | 2 | 0 | 2019 |
| 371 | Digital Policy Regulation and Governance | 2398-5038 | Q2 | 2 | 0 | 0 | 2 | 2023–2024 |
| 372 | Discover Artificial Intelligence | 2731-0809 | Q1 | 2 | 1 | 1 | 0 | 2026 |
| 373 | Discover Computing | 2948-2992 | Q2 | 2 | 2 | 0 | 0 | 2024–2026 |
| 374 | Discrete Applied Mathematics | 0166-218X | Q1, Q2 | 2 | 1 | 0 | 1 | 2016–2022 |
| 375 | Educational Administration Theory and Practice journal | 1300-4832 | Q4 | 2 | 0 | 2 | 0 | 2024 |
| 376 | Electrochimica Acta | 0013-4686 | Q1 | 2 | 1 | 1 | 0 | 2025–2026 |
| 377 | Energies | 1996-1073 | Q1 | 2 | 2 | 0 | 0 | 2023–2026 |
| 378 | Energy Conversion and Economics | 2634-1581 | unranked | 2 | 0 | 2 | 0 | 2022 |
| 379 | Energy Sources Part A Recovery Utilization and Environmental Effects | 1556-7036 | Q2, Q3 | 2 | 2 | 0 | 0 | 2018–2021 |
| 380 | Energy Storage | 2578-4862 | Q2, Q3 | 2 | 1 | 1 | 0 | 2023–2024 |
| 381 | Energy Systems | 1868-3967 | Q2 | 2 | 1 | 0 | 1 | 2026 |
| 382 | Energy Technology | 2194-4288 | Q2 | 2 | 1 | 1 | 0 | 2024–2025 |
| 383 | EURASIP Journal on Audio Speech and Music Processing | 1687-4714 | Q2 | 2 | 0 | 0 | 2 | 2023–2025 |
| 384 | European journal of training and development | 2046-9012 | Q1 | 2 | 0 | 2 | 0 | 2026 |
| 385 | Evolutionary Intelligence | 1864-5909 | Q1, Q3 | 2 | 0 | 2 | 0 | 2020–2025 |
| 386 | Food and Chemical Toxicology | 0278-6915 | Q1 | 2 | 2 | 0 | 0 | 2023 |
| 387 | foresight | 1463-6689 | unranked | 2 | 0 | 2 | 0 | 2017–2019 |
| 388 | Fractals | 0218-348X | Q1 | 2 | 2 | 0 | 0 | 2022–2023 |
| 389 | Fractional Calculus and Applied Analysis | 1311-0454 | Q1 | 2 | 2 | 0 | 0 | 2022–2023 |
| 390 | Frontiers in Bioscience-Landmark | 2768-6698 | Q2 | 2 | 2 | 0 | 0 | 2021 |
| 391 | Frontiers in Computer Science | 2624-9898 | Q1 | 2 | 0 | 0 | 2 | 2023 |
| 392 | Frontiers in Life Science | 2155-3769 | Q3 | 2 | 2 | 0 | 0 | 2016 |
| 393 | Frontiers in Neuroscience | 1662-453X | Q2 | 2 | 1 | 0 | 1 | 2020–2022 |
| 394 | Frontiers in Plant Science | 1664-462X | Q1 | 2 | 2 | 0 | 0 | 2017 |
| 395 | Future Business Journal | 2314-7202 | unranked | 2 | 0 | 2 | 0 | 2025 |
| 396 | Genes & Genomics | 1976-9571 | Q4 | 2 | 2 | 0 | 0 | 2018 |
| 397 | Georgian Mathematical Journal | 1072-947X | Q2 | 2 | 2 | 0 | 0 | 2024–2025 |
| 398 | Global Knowledge, Memory and Communication | 0307-4803 | Q2 | 2 | 1 | 1 | 0 | 2024 |
| 399 | IACR Transactions on Cryptographic Hardware and Embedded Systems | 2569-2925 | Q1 | 2 | 0 | 0 | 2 | 2020–2021 |
| 400 | ICT Express | 2405-9595 | Q1 | 2 | 2 | 0 | 0 | 2022–2026 |
| 401 | IEEE Antennas and Wireless Propagation Letters | 1536-1225 | Q1 | 2 | 1 | 1 | 0 | 2020–2023 |
| 402 | IEEE Consumer Electronics Magazine | 2162-2248 | Q1 | 2 | 0 | 2 | 0 | 2019–2020 |
| 403 | IEEE Design and Test | 2168-2356 | Q2, Q3 | 2 | 2 | 0 | 0 | 2024–2025 |
| 404 | IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing | 1939-1404 | Q1 | 2 | 0 | 0 | 2 | 2018–2026 |
| 405 | IEEE Journal on Miniaturization for Air and Space Systems | 2576-3164 | Q2 | 2 | 2 | 0 | 0 | 2025–2026 |
| 406 | IEEE Magnetics Letters | 1949-307X | Q2, Q3 | 2 | 1 | 0 | 1 | 2018–2026 |
| 407 | IEEE Photonics Technology Letters | 1041-1135 | Q1, Q2 | 2 | 1 | 0 | 1 | 2018–2025 |
| 408 | IEEE Technology and Society Magazine | 0278-0097 | Q2 | 2 | 0 | 0 | 2 | 2024–2025 |
| 409 | IEEE Transactions on Affective Computing | 1949-3045 | Q1 | 2 | 2 | 0 | 0 | 2019–2021 |
| 410 | IEEE Transactions on Antennas and Propagation | 0018-926X | Q1 | 2 | 0 | 0 | 2 | 2017–2019 |
| 411 | IEEE Transactions on Circuits and Systems for Video Technology | 1051-8215 | Q1 | 2 | 2 | 0 | 0 | 2016–2020 |
| 412 | IEEE Transactions on Cloud Computing | 2168-7161 | Q1 | 2 | 0 | 1 | 1 | 2016–2026 |
| 413 | IEEE Transactions on Device and Materials Reliability | 1530-4388 | Q2 | 2 | 0 | 2 | 0 | 2020–2021 |
| 414 | IEEE Transactions on Image Processing | 1057-7149 | Q1 | 2 | 1 | 1 | 0 | 2016–2020 |
| 415 | IEEE Transactions on Information Forensics and Security | 1556-6013 | Q1 | 2 | 0 | 2 | 0 | 2019–2023 |
| 416 | IEEE Transactions on Intelligent Vehicles | 2379-8858 | Q1 | 2 | 0 | 2 | 0 | 2026 |
| 417 | IEEE Transactions on Medical Imaging | 0278-0062 | Q1 | 2 | 1 | 1 | 0 | 2021–2024 |
| 418 | IEEE Transactions on Services Computing | 1939-1374 | Q1 | 2 | 1 | 1 | 0 | 2021–2023 |
| 419 | IEEE Transactions on Systems Man and Cybernetics Systems | 2168-2216 | Q1 | 2 | 1 | 0 | 1 | 2016–2023 |
| 420 | IEEE Transactions on Technology and Society | 2637-6415 | Q1 | 2 | 0 | 0 | 2 | 2024–2025 |
| 421 | IEEE Transactions on Visualization and Computer Graphics | 1077-2626 | Q1 | 2 | 0 | 0 | 2 | 2021–2023 |
| 422 | IET Computers & Digital Techniques | 1751-8601 | Q3 | 2 | 1 | 0 | 1 | 2022–2024 |
| 423 | IET Cyber-Physical Systems Theory & Applications | 2398-3396 | Q2 | 2 | 0 | 2 | 0 | 2017–2019 |
| 424 | IIMB Management Review | 0970-3896 | Q2, Q3 | 2 | 0 | 1 | 1 | 2024–2025 |
| 425 | Indian Journal of Finance | 0973-8711 | Q3, Q4 | 2 | 1 | 1 | 0 | 2016–2024 |
| 426 | Indian Journal of Neurosurgery | 2277-9167 | unranked | 2 | 0 | 0 | 2 | 2019–2020 |
| 427 | Indian Journal of Psychological Medicine | 0253-7176 | Q2 | 2 | 0 | 0 | 2 | 2026 |
| 428 | Informatics and Automation | 2078-9181 | Q3, Q4 | 2 | 2 | 0 | 0 | 2023–2024 |
| 429 | Information Communication & Society | 1369-118X | Q1 | 2 | 0 | 0 | 2 | 2019–2024 |
| 430 | Information Fusion | 1566-2535 | Q1 | 2 | 1 | 0 | 1 | 2024 |
| 431 | Information Technology and People | 0959-3845 | Q1 | 2 | 1 | 0 | 1 | 2019–2021 |
| 432 | Information Technology for Development | 0268-1102 | Q1 | 2 | 1 | 0 | 1 | 2020–2021 |
| 433 | Intelligent Data Analysis | 1088-467X | Q3 | 2 | 2 | 0 | 0 | 2026 |
| 434 | International Journal for Global Academic & Scientific Research | 2583-3081 | Q3 | 2 | 0 | 2 | 0 | 2023–2026 |
| 435 | International Journal of Advanced Research and Multidisciplinary Trends (IJARMT) | 3048-9458 | unranked | 2 | 0 | 2 | 0 | 2026 |
| 436 | International Journal of Bifurcation and Chaos | 0218-1274 | Q1 | 2 | 0 | 2 | 0 | 2016–2019 |
| 437 | International Journal of Bio-Inspired Computation | 1758-0366 | Q1, Q2 | 2 | 2 | 0 | 0 | 2016–2019 |
| 438 | International Journal of Bioinformatics Research and Applications | 1744-5485 | Q4 | 2 | 2 | 0 | 0 | 2017–2020 |
| 439 | International Journal of Business Innovation and Research | 1751-0252 | Q2, Q3 | 2 | 0 | 2 | 0 | 2017–2024 |
| 440 | International Journal of Computational Intelligence Systems | 1875-6883 | Q1, Q2 | 2 | 0 | 2 | 0 | 2023–2026 |
| 441 | INTERNATIONAL JOURNAL OF COMPUTER ENGINEERING & TECHNOLOGY | 0976-6367 | unranked | 2 | 2 | 0 | 0 | 2019 |
| 442 | International Journal of Computers and Applications | 1206-212X | Q4 | 2 | 0 | 2 | 0 | 2016–2018 |
| 443 | International Journal of Data Science and Analytics | 2364-415X | Q1 | 2 | 1 | 2 | 0 | 2025 |
| 444 | International Journal of Digital Enterprise Technology | 1756-2554 | unranked | 2 | 1 | 0 | 1 | 2018 |
| 445 | International Journal of Economics and Financial Issues | 2146-4138 | unranked | 2 | 1 | 1 | 0 | 2022–2024 |
| 446 | International Journal of Engineering Sciences | 0976-6693 | unranked | 2 | 0 | 2 | 0 | 2022 |
| 447 | International Journal of Grid and Distributed Computing | 2005-4262 | Q4 | 2 | 1 | 1 | 0 | 2016 |
| 448 | International Journal of Information and Computer Security | 1744-1765 | Q3, Q4 | 2 | 2 | 0 | 0 | 2024–2025 |
| 449 | International Journal of Information Technology & Decision Making | 0219-6220 | Q2 | 2 | 2 | 0 | 0 | 2025–2026 |
| 450 | International Journal of Information Technology and Management | 1461-4111 | Q4 | 2 | 1 | 1 | 0 | 2017–2024 |
| 451 | International Journal of Innovative Research in Engineering & Management | 2350-0557 | unranked | 2 | 2 | 0 | 0 | 2023 |
| 452 | International Journal of Intelligent Enterprise | 1745-3232 | Q4 | 2 | 0 | 2 | 0 | 2018 |
| 453 | International Journal of Intelligent Systems and Applications | 2074-904X | Q4 | 2 | 2 | 0 | 0 | 2016 |
| 454 | International Journal of Internet Technology and Secured Transactions | 1748-569X | Q4 | 2 | 1 | 1 | 0 | 2018–2022 |
| 455 | International Journal of Mathematical Engineering and Management Sciences | 2455-7749 | Q3 | 2 | 0 | 2 | 0 | 2020 |
| 456 | International Journal of Modern Education and Computer Science | 2075-0161 | unranked | 2 | 0 | 2 | 0 | 2016–2018 |
| 457 | International Journal of Production Research | 0020-7543 | Q1 | 2 | 0 | 2 | 0 | 2017–2018 |
| 458 | International Journal of Reliability and Safety | 1479-389X | Q3 | 2 | 0 | 2 | 0 | 2016–2021 |
| 459 | International Journal of Remote Sensing | 0143-1161 | Q1, Q2 | 2 | 2 | 0 | 0 | 2019–2024 |
| 460 | INTERNATIONAL JOURNAL OF RESEARCH AND ANALYTICAL REVIEWS | 2348-1269 | unranked | 2 | 0 | 2 | 0 | 2026 |
| 461 | International Journal of Robotics Applications and Technologies | 2166-7195 | unranked | 2 | 0 | 2 | 0 | 2017 |
| 462 | International Journal of Science and Research (IJSR) | 2319-7064 | unranked | 2 | 1 | 0 | 1 | 2021–2025 |
| 463 | International Journal of Semantic Computing | 1793-7108 | Q2 | 2 | 0 | 0 | 2 | 2021–2023 |
| 464 | International Journal of Service Science Management Engineering and Technology | 1947-959X | Q2 | 2 | 1 | 1 | 0 | 2016–2021 |
| 465 | International Journal of Social Robotics | 1875-4791 | Q1 | 2 | 2 | 0 | 0 | 2017–2020 |
| 466 | International Journal of Speech Technology | 1381-2416 | Q1, Q2 | 2 | 1 | 0 | 1 | 2019–2023 |
| 467 | International Journal of Strategic Decision Sciences | 1947-8569 | unranked | 2 | 0 | 2 | 0 | 2017–2018 |
| 468 | International Journal of Swarm Intelligence Research | 1947-9263 | Q3, Q4 | 2 | 1 | 1 | 0 | 2018–2021 |
| 469 | International Journal of Tourism Cities | 2056-5607 | Q1, Q2 | 2 | 0 | 2 | 0 | 2020–2021 |
| 470 | Internet Technology Letters | 2476-1508 | unranked | 2 | 1 | 0 | 1 | 2020 |
| 471 | Investment Management and Financial Innovations | 1810-4967 | Q2 | 2 | 1 | 1 | 0 | 2025 |
| 472 | Ionics | 0947-7047 | Q2 | 2 | 2 | 0 | 0 | 2022–2024 |
| 473 | Iranian Journal of Science | 2731-8095 | Q2, Q3 | 2 | 0 | 2 | 0 | 2024–2025 |
| 474 | JMIR Research Protocols | 1929-0748 | Q2 | 2 | 0 | 0 | 2 | 2025–2026 |
| 475 | Journal of Astrophysics and Astronomy | 0250-6335 | Q2 | 2 | 1 | 0 | 1 | 2024–2026 |
| 476 | Journal of Biological Systems | 0218-3390 | Q2 | 2 | 0 | 2 | 0 | 2021–2023 |
| 477 | Journal of Business Economics and Management | 1611-1699 | Q2 | 2 | 2 | 0 | 0 | 2019–2021 |
| 478 | Journal of Combinatorial Optimization | 1382-6905 | Q2 | 2 | 1 | 0 | 1 | 2019–2020 |
| 479 | Journal of Computational and Applied Mathematics | 0377-0427 | Q1, Q2 | 2 | 0 | 2 | 0 | 2022–2025 |
| 480 | Journal of Cryptology | 0933-2790 | Q1 | 2 | 0 | 0 | 2 | 2023 |
| 481 | Journal of Electrical Systems | 1112-5209 | Q4 | 2 | 1 | 1 | 0 | 2024–2025 |
| 482 | Journal of Electromagnetic Waves and Applications | 0920-5071 | Q3 | 2 | 2 | 0 | 0 | 2017–2020 |
| 483 | Journal of Electronic Imaging | 1017-9909 | Q3 | 2 | 2 | 0 | 0 | 2023 |
| 484 | Journal of Engineering Science and Technology Review | 1791-2377 | Q3, Q4 | 2 | 2 | 0 | 0 | 2020–2022 |
| 485 | Journal of Global Operations and Strategic Sourcing | 2398-5364 | Q2 | 2 | 1 | 1 | 0 | 2022–2023 |
| 486 | Journal of High Energy Physics | 1029-8479 | Q2 | 2 | 2 | 0 | 0 | 2021–2025 |
| 487 | Journal of Imaging Informatics in Medicine | 0897-1889 | Q1, Q2 | 2 | 1 | 1 | 0 | 2020–2026 |
| 488 | Journal of Information & Knowledge Management | 0219-6492 | Q3 | 2 | 1 | 1 | 0 | 2017 |
| 489 | Journal of Information Policy | 2158-3897 | Q2 | 2 | 0 | 0 | 2 | 2016–2022 |
| 490 | Journal of Information Security and Applications | 2214-2126 | Q1, Q2 | 2 | 1 | 0 | 1 | 2017–2021 |
| 491 | Journal of Intelligent Systems | 0334-1860 | Q4 | 2 | 1 | 1 | 0 | 2016–2017 |
| 492 | Journal of Lie Theory | 0949-5932 | Q3 | 2 | 2 | 0 | 0 | 2021–2024 |
| 493 | Journal of Manufacturing Systems | 0278-6125 | Q1 | 2 | 0 | 2 | 0 | 2020–2022 |
| 494 | Journal of Materials Chemistry A | 2050-7488 | Q1 | 2 | 2 | 2 | 0 | 2026 |
| 495 | Journal of Materials Science | 0022-2461 | Q1 | 2 | 1 | 1 | 0 | 2018–2022 |
| 496 | Journal of Mathematics | 2314-4629 | Q3 | 2 | 2 | 0 | 0 | 2020–2022 |
| 497 | Journal of Modern Optics | 0950-0340 | Q3 | 2 | 2 | 0 | 0 | 2020–2022 |
| 498 | Journal of Multidisciplinary Healthcare | 1178-2390 | Q1 | 2 | 2 | 0 | 0 | 2023–2024 |
| 499 | Journal of Nanoscience and Nanotechnology | 1533-4880 | Q3 | 2 | 1 | 1 | 0 | 2019 |
| 500 | Journal of Neonatal Surgery | 2226-0439 | Q4 | 2 | 0 | 2 | 0 | 2025 |
| 501 | Journal of Network and Systems Management | 1064-7570 | Q1, Q2 | 2 | 0 | 2 | 0 | 2021–2026 |
| 502 | Journal of Nonprofit & Public Sector Marketing | 1049-5142 | Q2, Q3 | 2 | 0 | 2 | 0 | 2022–2023 |
| 503 | Journal of Operations and Strategic Planning | 2516-600X | unranked | 2 | 0 | 2 | 0 | 2021–2022 |
| 504 | Journal of Pure and Applied Algebra | 0022-4049 | Q1 | 2 | 2 | 0 | 0 | 2018–2024 |
| 505 | Journal of Relationship Marketing | 1533-2667 | Q3 | 2 | 0 | 2 | 0 | 2017–2020 |
| 506 | Journal of Research in Marketing and Entrepreneurship | 1471-5201 | Q3 | 2 | 0 | 2 | 0 | 2019 |
| 507 | Journal of Retailing and Consumer Services | 0969-6989 | Q1 | 2 | 1 | 1 | 0 | 2021–2025 |
| 508 | Journal of risk and financial management | 1911-8066 | Q2 | 2 | 1 | 1 | 0 | 2023 |
| 509 | Journal of Science Advanced Materials and Devices | 2468-2179 | Q1 | 2 | 1 | 2 | 0 | 2022–2026 |
| 510 | Journal of Scientific & Industrial Research | 0022-4456 | Q2, Q3 | 2 | 1 | 1 | 0 | 2023–2025 |
| 511 | Journal of Signal Processing Systems | 1939-8018 | Q2 | 2 | 0 | 2 | 0 | 2023–2026 |
| 512 | Journal of Simulation | 1747-7778 | Q2 | 2 | 0 | 0 | 2 | 2022 |
| 513 | Journal of Software Evolution and Process | 2047-7473 | Q3 | 2 | 2 | 0 | 0 | 2017–2018 |
| 514 | Journal of Sol-Gel Science and Technology | 0928-0707 | Q2 | 2 | 2 | 0 | 0 | 2018–2025 |
| 515 | Journal of the Optical Society of America B | 0740-3224 | Q2 | 2 | 2 | 0 | 0 | 2023–2024 |
| 516 | KSII Transactions on Internet and Information Systems | 1976-7277 | Q3 | 2 | 2 | 0 | 0 | 2018–2025 |
| 517 | Leisure/Loisir | 1492-7713 | Q2 | 2 | 0 | 2 | 0 | 2023–2024 |
| 518 | Life | 2075-1729 | Q1, Q2 | 2 | 2 | 0 | 0 | 2022–2026 |
| 519 | Memórias do Instituto Oswaldo Cruz | 0074-0276 | Q2 | 2 | 0 | 0 | 2 | 2020–2021 |
| 520 | Microchemical Journal | 0026-265X | Q1, Q2 | 2 | 1 | 0 | 1 | 2024–2025 |
| 521 | Microelectronics International | 1356-5362 | Q2, Q3 | 2 | 2 | 0 | 0 | 2018–2020 |
| 522 | Microsystem Technologies | 0946-7076 | Q3 | 2 | 0 | 2 | 0 | 2026 |
| 523 | Molecular Diagnosis & Therapy | 1177-1062 | Q1 | 2 | 2 | 0 | 0 | 2023–2026 |
| 524 | Molecular Neurobiology | 0893-7648 | Q1 | 2 | 2 | 0 | 0 | 2021–2024 |
| 525 | Nanoscale | 2040-3364 | Q1 | 2 | 2 | 0 | 0 | 2020–2023 |
| 526 | NMIMS Management Review | 0971-1023 | unranked | 2 | 0 | 2 | 0 | 2025 |
| 527 | Nonlinear studies | 1359-8678 | Q4 | 2 | 0 | 2 | 0 | 2020–2025 |
| 528 | npj 2D Materials and Applications | 2397-7132 | Q1 | 2 | 2 | 0 | 0 | 2022–2026 |
| 529 | Numerical Algorithms | 1017-1398 | Q2 | 2 | 2 | 0 | 0 | 2022–2023 |
| 530 | Oncology Letters | 1792-1074 | Q3 | 2 | 2 | 0 | 0 | 2017 |
| 531 | Online Social Networks and Media | 2468-6964 | Q1 | 2 | 0 | 2 | 0 | 2025–2026 |
| 532 | Organic Electronics | 1566-1199 | Q1 | 2 | 0 | 2 | 0 | 2017–2018 |
| 533 | Photoacoustics | 2213-5979 | Q1 | 2 | 2 | 0 | 0 | 2024–2025 |
| 534 | Photonics and Nanostructures - Fundamentals and Applications | 1569-4410 | Q2 | 2 | 2 | 0 | 0 | 2020–2026 |
| 535 | physica status solidi (a) | 0031-8965 | Q2 | 2 | 1 | 1 | 0 | 2024–2026 |
| 536 | Physics Letters A | 0375-9601 | Q2 | 2 | 0 | 2 | 0 | 2019–2025 |
| 537 | Proceedings of the ACM on Human-Computer Interaction | 2573-0142 | Q1, Q2 | 2 | 0 | 0 | 2 | 2018–2022 |
| 538 | Quality & Quantity | 0033-5177 | Q1, Q2 | 2 | 0 | 2 | 0 | 2018–2021 |
| 539 | Quality Engineering | 0898-2112 | Q2 | 2 | 0 | 2 | 0 | 2023–2024 |
| 540 | Radioengineering | 1210-2512 | Q3 | 2 | 2 | 0 | 0 | 2022–2025 |
| 541 | RAIRO - Operations Research | 0399-0559 | Q3 | 2 | 0 | 2 | 0 | 2022–2024 |
| 542 | Remote Sensing Letters | 2150-704X | Q1, Q2 | 2 | 1 | 1 | 0 | 2020–2025 |
| 543 | Rendiconti del Circolo Matematico di Palermo Series 2 | 0009-725X | Q2, Q3 | 2 | 0 | 2 | 0 | 2021–2023 |
| 544 | Results in Engineering | 2590-1230 | Q1 | 2 | 0 | 2 | 0 | 2026 |
| 545 | Results in Mathematics | 0378-6218 | Q1 | 2 | 2 | 0 | 0 | 2024–2026 |
| 546 | Robotics and Autonomous Systems | 0921-8890 | Q1 | 2 | 2 | 0 | 0 | 2016 |
| 547 | RSC Sustainability | 2753-8125 | Q1 | 2 | 2 | 0 | 0 | 2024–2025 |
| 548 | Security and Communication Networks | 1939-0114 | Q2 | 2 | 2 | 0 | 0 | 2022 |
| 549 | Security and Privacy | 2475-6725 | unranked | 2 | 1 | 1 | 0 | 2024–2025 |
| 550 | Semiconductor Science and Technology | 0268-1242 | Q2 | 2 | 1 | 1 | 0 | 2021–2024 |
| 551 | SN Applied Sciences | 2523-3963 | Q2 | 2 | 1 | 1 | 0 | 2019–2020 |
| 552 | Software Quality Journal | 0963-9314 | Q1, Q2 | 2 | 0 | 2 | 0 | 2023–2026 |
| 553 | South Eastern European Journal of Public Health | 2197-5248 | Q4 | 2 | 1 | 0 | 1 | 2024–2025 |
| 554 | Sustainable Cities and Society | 2210-6707 | Q1 | 2 | 1 | 0 | 1 | 2017–2024 |
| 555 | Systems | 2079-8954 | Q2 | 2 | 0 | 0 | 2 | 2021–2022 |
| 556 | Systems Engineering | 1098-1241 | Q2, Q3 | 2 | 0 | 1 | 1 | 2019–2023 |
| 557 | Technological Forecasting and Social Change | 0040-1625 | Q1 | 2 | 1 | 0 | 1 | 2021–2022 |
| 558 | Technology Analysis and Strategic Management | 0953-7325 | Q2 | 2 | 2 | 0 | 0 | 2016–2022 |
| 559 | The Computer Journal | 0010-4620 | Q2 | 2 | 0 | 2 | 0 | 2017–2018 |
| 560 | The Information Society | 0197-2243 | Q1 | 2 | 0 | 0 | 2 | 2017–2020 |
| 561 | The Journal of Adult Protection | 1466-8203 | Q2 | 2 | 0 | 2 | 0 | 2020 |
| 562 | The Journal of Open Source Software | 2475-9066 | unranked | 2 | 0 | 2 | 0 | 2020 |
| 563 | The Journal of Organic Chemistry | 0022-3263 | Q1, Q2 | 2 | 2 | 0 | 0 | 2020–2023 |
| 564 | The Journal of Physical Chemistry Letters | 1948-7185 | Q1 | 2 | 1 | 1 | 0 | 2020–2024 |
| 565 | Total Quality Management & Business Excellence | 1478-3363 | Q1 | 2 | 0 | 2 | 0 | 2024–2025 |
| 566 | Transportation in Developing Economies | 2199-9287 | unranked | 2 | 0 | 2 | 0 | 2024–2025 |
| 567 | Vehicular Communications | 2214-2096 | Q1 | 2 | 2 | 0 | 0 | 2021–2024 |
| 568 | VirusDisease | 2347-3517 | Q3 | 2 | 2 | 0 | 0 | 2021–2026 |
| 569 | Viruses | 1999-4915 | Q1 | 2 | 2 | 0 | 0 | 2021–2023 |
| 570 | Water Practice & Technology | 1751-231X | Q2, Q3 | 2 | 2 | 0 | 0 | 2024–2025 |
| 571 | World Journal of Microbiology and Biotechnology | 0959-3993 | Q1, Q2 | 2 | 2 | 0 | 0 | 2024–2026 |
| 572 | 28th Annual Meeting | – | unranked | 1 | 0 | 0 | 1 | 2016 |
| 573 | 2D Materials | 2053-1583 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 574 | Academia Letters | 2771-9359 | unranked | 1 | 0 | 1 | 0 | 2021 |
| 575 | Academia Revista Latinoamericana de Administración | 1012-8255 | Q3 | 1 | 1 | 0 | 0 | 2018 |
| 576 | ACM SIGIR Forum | 0163-5840 | unranked | 1 | 0 | 0 | 1 | 2025 |
| 577 | ACM Transactions on Algorithms | 1549-6325 | Q1 | 1 | 0 | 0 | 1 | 2018 |
| 578 | ACM Transactions on Sensor Networks | 1550-4859 | Q2 | 1 | 0 | 1 | 0 | 2020 |
| 579 | ACM Transactions on the Web | 1559-1131 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 580 | ACS Applied Bio Materials | 2576-6422 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 581 | ACS Applied Electronic Materials | 2637-6113 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 582 | ACS Applied Engineering Materials | 2771-9545 | unranked | 1 | 1 | 0 | 0 | 2023 |
| 583 | ACS Applied Nano Materials | 2574-0970 | Q1 | 1 | 1 | 0 | 0 | 2026 |
| 584 | Acta Astronautica | 0094-5765 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 585 | Acta Turistica | 0353-4316 | Q4 | 1 | 1 | 0 | 0 | 2017 |
| 586 | Adarsh Journal of Management Research | 0974-7028 | unranked | 1 | 0 | 0 | 1 | 2024 |
| 587 | Advance Research Journal of Multidisciplinary Studies | 3051-0287 | unranked | 1 | 0 | 1 | 0 | 2026 |
| 588 | Advanced Materials | 0935-9648 | Q1 | 1 | 0 | 1 | 0 | 2016 |
| 589 | Advances in Applied Mathematics and Mechanics | 2070-0733 | Q2 | 1 | 0 | 1 | 0 | 2024 |
| 590 | Advances in Artificial Intelligence | 1687-7470 | unranked | 1 | 1 | 0 | 0 | 2016 |
| 591 | Advances in Developing Human Resources | 1523-4223 | Q2 | 1 | 0 | 1 | 0 | 2017 |
| 592 | Advances in Difference Equations | 1687-1839 | Q2 | 1 | 0 | 1 | 0 | 2017 |
| 593 | Advances in Operator Theory | 2538-225X | Q3 | 1 | 0 | 1 | 0 | 2024 |
| 594 | Advances in Water Resources | 0309-1708 | Q1 | 1 | 0 | 0 | 1 | 2026 |
| 595 | Ageing International | 0163-5158 | Q3 | 1 | 0 | 1 | 0 | 2022 |
| 596 | Agricultural Economics (Zemědělská ekonomika) | 0139-570X | Q1 | 1 | 1 | 0 | 0 | 2019 |
| 597 | Agriculture | 2077-0472 | Q2 | 1 | 0 | 1 | 0 | 2021 |
| 598 | AI | 2673-2688 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 599 | AI & Society | 0951-5666 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 600 | AI and Ethics | 2730-5953 | unranked | 1 | 0 | 0 | 1 | 2024 |
| 601 | AI Communications | 0921-7126 | Q3 | 1 | 1 | 0 | 0 | 2018 |
| 602 | AIP Advances | 2158-3226 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 603 | AKCE International Journal of Graphs and Combinatorics | 0972-8600 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 604 | Alexandria Engineering Journal | 1110-0168 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 605 | AMC Indian Journal of Entrepreneurship | 2581-7302 | unranked | 1 | 0 | 1 | 0 | 2019 |
| 606 | American Journal of Operations Research | 2160-8830 | unranked | 1 | 0 | 1 | 0 | 2016 |
| 607 | American Journal of Potato Research | 0003-0589 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 608 | Analele Universităţii "Ovidius" Constanţa. Seria Matematică | 1224-1784 | Q3 | 1 | 1 | 0 | 0 | 2026 |
| 609 | Annals of Medicine and Surgery | 2049-0801 | unranked | 1 | 1 | 0 | 0 | 2025 |
| 610 | Annals of Telecommunications | 0003-4347 | Q2 | 1 | 1 | 0 | 0 | 2018 |
| 611 | AoIR Selected Papers of Internet Research | 2162-3317 | unranked | 1 | 0 | 0 | 1 | 2020 |
| 612 | Applicable Algebra in Engineering Communication and Computing | 0938-1279 | Q2 | 1 | 0 | 0 | 1 | 2019 |
| 613 | Applied Biochemistry and Biotechnology | 0273-2289 | Q2 | 1 | 1 | 0 | 0 | 2023 |
| 614 | Applied Computational Intelligence and Soft Computing | 1687-9724 | Q3 | 1 | 1 | 0 | 0 | 2016 |
| 615 | Applied Economics | 0003-6846 | Q2 | 1 | 0 | 0 | 1 | 2022 |
| 616 | Applied Finance Letters | 2253-5799 | unranked | 1 | 0 | 1 | 0 | 2020 |
| 617 | Applied Numerical Mathematics | 0168-9274 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 618 | Applied Physics B | 0721-7269 | Q2 | 1 | 1 | 0 | 0 | 2019 |
| 619 | Arabian Journal of Geosciences | 1866-7511 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 620 | Arabian Journal of Mathematics | 2193-5343 | Q3 | 1 | 0 | 1 | 0 | 2022 |
| 621 | Architecture Structures and Construction | 2730-9886 | unranked | 1 | 0 | 0 | 1 | 2022 |
| 622 | Archives of Biochemistry and Biophysics | 0003-9861 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 623 | Area Development and Policy | 2379-2949 | Q1 | 1 | 0 | 0 | 1 | 2018 |
| 624 | Asia-Pacific Financial Markets | 1380-2011 | Q3 | 1 | 1 | 0 | 0 | 2019 |
| 625 | Asia-Pacific Journal of Management Research and Innovation | 2319-510X | unranked | 1 | 0 | 1 | 0 | 2019 |
| 626 | Asian Business & Management | 1472-4782 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 627 | Asian Case Research Journal | 0218-9275 | Q4 | 1 | 0 | 1 | 0 | 2022 |
| 628 | ASIAN JOURNAL OF CONVERGENCE IN TECHNOLOGY | 2350-1146 | unranked | 1 | 1 | 0 | 0 | 2020 |
| 629 | Asian Journal of Finance & Accounting | 1946-052X | unranked | 1 | 1 | 0 | 0 | 2016 |
| 630 | Asian Journal of Management Cases | 0972-8201 | Q4 | 1 | 0 | 1 | 0 | 2022 |
| 631 | Asian Journal of Managerial Science | 2249-6300 | unranked | 1 | 1 | 0 | 0 | 2017 |
| 632 | Asian Journal of Organic Chemistry | 2193-5807 | Q3 | 1 | 1 | 0 | 0 | 2026 |
| 633 | Asian Journal of Psychiatry | 1876-2018 | Q2 | 1 | 0 | 0 | 1 | 2020 |
| 634 | Asian Journal of Research in Chemistry | 0974-4150 | unranked | 1 | 0 | 1 | 0 | 2025 |
| 635 | Asian Pacific Journal of Tropical Medicine | 1995-7645 | Q2 | 1 | 1 | 0 | 0 | 2019 |
| 636 | Asian Social Science | 1911-2017 | Q3 | 1 | 1 | 0 | 0 | 2020 |
| 637 | Asian-Pacific Journal of Second and Foreign Language Education | 2363-5169 | Q1 | 1 | 0 | 1 | 0 | 2024 |
| 638 | Association Journal of Interdisciplinary Technics in Engineering Mechanics | 3049-0898 | unranked | 1 | 0 | 0 | 1 | 2024 |
| 639 | Atmospheric Research | 0169-8095 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 640 | Automatika | 0005-1144 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 641 | Axioms | 2075-1680 | Q3 | 1 | 0 | 1 | 0 | 2022 |
| 642 | Banach Journal of Mathematical Analysis | 1735-8787 | Q2 | 1 | 1 | 0 | 0 | 2016 |
| 643 | Behavioral and Brain Sciences | 0140-525X | Q3 | 1 | 1 | 0 | 0 | 2023 |
| 644 | Behaviour and Information Technology | 0144-929X | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 645 | BIBECHANA | 2382-5340 | unranked | 1 | 0 | 1 | 0 | 2018 |
| 646 | Big Data | 2167-6461 | Q2 | 1 | 1 | 0 | 0 | 2021 |
| 647 | Big Data & Society | 2053-9517 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 648 | Biochemistry Research International | 2090-2247 | Q3 | 1 | 1 | 0 | 0 | 2016 |
| 649 | Biochimica et Biophysica Acta (BBA) - General Subjects | 0304-4165 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 650 | Biochimie | 0037-9042 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 651 | Biologically Inspired Cognitive Architectures | 2212-683X | Q3 | 1 | 0 | 1 | 0 | 2016 |
| 652 | Biology Engineering Medicine and Science Reports | 2454-6895 | unranked | 1 | 1 | 0 | 0 | 2016 |
| 653 | Biomaterials Science | 2047-4830 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 654 | Biomedical Engineering Letters | 2093-985X | Q2 | 1 | 0 | 1 | 0 | 2020 |
| 655 | Biomedical Optics Express | 2156-7085 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 656 | Biomedizinische Technik/Biomedical Engineering | 0013-5585 | Q3 | 1 | 0 | 1 | 0 | 2019 |
| 657 | Biophysical Reviews | 1867-2450 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 658 | Biosensors and Bioelectronics | 0956-5663 | Q1 | 1 | 1 | 0 | 0 | 2019 |
| 659 | Biotechnology Letters | 0141-5492 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 660 | Biotechnology Reports | 2215-017X | Q1 | 1 | 1 | 0 | 0 | 2020 |
| 661 | Blockchain Research and Applications | 2096-7209 | Q1 | 1 | 0 | 0 | 1 | 2022 |
| 662 | BMC Bioinformatics | 1471-2105 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 663 | BMC Plant Biology | 1471-2229 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 664 | BMC Psychiatry | 1471-244X | Q1 | 1 | 0 | 0 | 1 | 2025 |
| 665 | BMC Structural Biology | 1472-6807 | Q4 | 1 | 1 | 0 | 0 | 2018 |
| 666 | Boletim da Sociedade Paranaense de Matemática | 0037-8712 | Q3 | 1 | 0 | 1 | 0 | 2025 |
| 667 | Borsa Istanbul Review | 2214-8450 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 668 | Brazilian Journal of Operations & Production Management | 1679-8171 | Q3 | 1 | 0 | 1 | 0 | 2025 |
| 669 | Brazilian Journal of Physics | 0103-9733 | Q4 | 1 | 1 | 0 | 0 | 2023 |
| 670 | British Journal of Sociology | 0007-1315 | Q1 | 1 | 0 | 1 | 0 | 2017 |
| 671 | Business Perspectives and Research | 2278-5337 | Q3 | 1 | 0 | 1 | 0 | 2020 |
| 672 | Cancer Epidemiology | 1877-7821 | Q1 | 1 | 1 | 0 | 0 | 2018 |
| 673 | Cancer Research Statistics and Treatment | 2590-3225 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 674 | Carbon | 0008-6223 | Q1 | 1 | 1 | 0 | 0 | 2016 |
| 675 | Carbon Management | 1758-3004 | Q2 | 1 | 1 | 0 | 0 | 2018 |
| 676 | Carbon Trends | 2667-0569 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 677 | Catalysts | 2073-4344 | Q2 | 1 | 1 | 1 | 0 | 2023 |
| 678 | ChemCatChem | 1867-3880 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 679 | Chemical Communications | 1359-7345 | Q1 | 1 | 0 | 1 | 0 | 2019 |
| 680 | Chemical Physics | 0301-0104 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 681 | Chemistry & Biodiversity | 1612-1872 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 682 | Chemistry Africa | 2522-5758 | Q3 | 1 | 1 | 0 | 0 | 2023 |
| 683 | ChemPhysChem | 1439-4235 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 684 | Chinese Optics Letters | 1671-7694 | Q2 | 1 | 1 | 0 | 0 | 2019 |
| 685 | Circular Economy and Sustainability | 2730-597X | Q1 | 1 | 1 | 0 | 0 | 2026 |
| 686 | Clean Energy | 2515-396X | Q1 | 1 | 0 | 0 | 1 | 2026 |
| 687 | Clean Technologies and Environmental Policy | 1618-954X | Q1 | 1 | 1 | 0 | 0 | 2016 |
| 688 | Climate Policy | 1469-3062 | Q1 | 1 | 1 | 0 | 0 | 2017 |
| 689 | Cognitive Computation | 1866-9956 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 690 | Combinatorial Chemistry & High Throughput Screening | 1386-2073 | Q3 | 1 | 1 | 0 | 0 | 2016 |
| 691 | Communications Biology | 2399-3642 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 692 | Communications in Mathematics and Applications | 0975-8607 | unranked | 1 | 0 | 1 | 0 | 2025 |
| 693 | Communications of the ACM | 0001-0782 | Q1 | 1 | 0 | 0 | 1 | 2022 |
| 694 | Communications Sustainability | 3059-4308 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 695 | Competition and Regulation in Network Industries | 1783-5917 | Q3 | 1 | 0 | 0 | 1 | 2026 |
| 696 | Competition Commission of India Journal on Competition Law and Policy | 2582-838X | unranked | 1 | 0 | 0 | 1 | 2023 |
| 697 | Computación y Sistemas | 1405-5546 | Q4 | 1 | 1 | 0 | 0 | 2020 |
| 698 | Computational Condensed Matter | 2352-2143 | Q3 | 1 | 0 | 1 | 0 | 2023 |
| 699 | Computational Economics | 0927-7099 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 700 | Computational Geometry | 0925-7721 | Q2 | 1 | 0 | 0 | 1 | 2016 |
| 701 | Computational Management Science | 1619-697X | Q2 | 1 | 0 | 0 | 1 | 2025 |
| 702 | Computational Materials Science | 0927-0256 | Q1 | 1 | 0 | 1 | 0 | 2017 |
| 703 | Computational Statistics | 0943-4062 | Q2 | 1 | 0 | 1 | 0 | 2023 |
| 704 | Computer Fraud & Security | 1361-3723 | Q2 | 1 | 1 | 0 | 0 | 2020 |
| 705 | Computer Methods in Biomechanics and Biomedical Engineering Imaging & Visualization | 2168-1163 | Q2 | 1 | 0 | 1 | 0 | 2019 |
| 706 | Computerized Medical Imaging and Graphics | 0730-4862 | Q1 | 1 | 1 | 0 | 0 | 2020 |
| 707 | Computers & Industrial Engineering | 0360-8352 | Q1 | 1 | 0 | 1 | 0 | 2023 |
| 708 | Computers and Electronics in Agriculture | 0168-1699 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 709 | Computers, materials & continua/Computers, materials & continua (Print) | 1546-2218 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 710 | Constructive Approximation | 0176-4276 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 711 | Contemporary Education Dialogue | 0973-1849 | Q4 | 1 | 0 | 0 | 1 | 2024 |
| 712 | Contemporary South Asia | 0958-4935 | Q3 | 1 | 0 | 0 | 1 | 2017 |
| 713 | Corporate Social Responsibility and Environmental Management | 1535-3958 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 714 | Critical Reviews in Microbiology | 1040-841X | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 715 | Crystals | 2073-4352 | Q2 | 1 | 1 | 0 | 0 | 2020 |
| 716 | CSVTU International Journal of Biotechnology Bioinformatics and Biomedical | 2455-5762 | unranked | 1 | 0 | 1 | 0 | 2016 |
| 717 | Cureus | 2168-8184 | unranked | 1 | 0 | 0 | 1 | 2025 |
| 718 | Current Alzheimer Research | 1567-2050 | Q2 | 1 | 1 | 0 | 0 | 2018 |
| 719 | Current Analytical Chemistry | 1573-4110 | Q3 | 1 | 1 | 0 | 0 | 2025 |
| 720 | Current Computer Science | 2950-3779 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 721 | Current Drug Metabolism | 1389-2002 | Q2 | 1 | 1 | 0 | 0 | 2017 |
| 722 | Current Green Chemistry | 2213-3461 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 723 | Current Nanoscience | 1573-4137 | Q3 | 1 | 1 | 0 | 0 | 2023 |
| 724 | Current Plant Biology | 2214-6628 | Q1 | 1 | 1 | 0 | 0 | 2019 |
| 725 | Current Traditional Medicine | 2215-0838 | Q3 | 1 | 1 | 0 | 0 | 2023 |
| 726 | Cybernetics and Information Technologies | 1311-9702 | Q3 | 1 | 0 | 1 | 0 | 2023 |
| 727 | Cytokine & Growth Factor Reviews | 1359-6101 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 728 | Dandao Xuebao/Journal of Ballistics | 1004-499X | Q4 | 1 | 0 | 1 | 0 | 2026 |
| 729 | Data Technologies and Applications | 0033-0337 | Q3 | 1 | 0 | 0 | 1 | 2020 |
| 730 | Data-Centric Engineering | 2632-6736 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 731 | DECISION | 0304-0941 | unranked | 1 | 0 | 0 | 1 | 2023 |
| 732 | Decision Analytics Journal | 2772-6622 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 733 | Development in Learning Organizations An International Journal | 1477-7282 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 734 | Diamond and Related Materials | 0925-9635 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 735 | Digital Finance | 2524-6186 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 736 | Digital Government Research and Practice | 2639-0175 | Q2 | 1 | 0 | 0 | 1 | 2024 |
| 737 | Digital Intelligence in Agriculture | 3069-3187 | unranked | 1 | 1 | 0 | 0 | 2025 |
| 738 | Digital Threats Research and Practice | 2576-5337 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 739 | Discover Agriculture | 2731-9598 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 740 | Discover Electrochemistry. | 3005-1215 | unranked | 1 | 0 | 1 | 0 | 2026 |
| 741 | Discover Electronics | 2948-1600 | unranked | 1 | 1 | 0 | 0 | 2024 |
| 742 | Discover Geoscience | 2948-1589 | unranked | 1 | 1 | 0 | 0 | 2025 |
| 743 | Discover Mental Health | 2731-4383 | Q2 | 1 | 0 | 0 | 1 | 2025 |
| 744 | Discover Public Health | 3005-0774 | Q3 | 1 | 0 | 1 | 0 | 2026 |
| 745 | Discover Robotics | 3059-3204 | unranked | 1 | 0 | 1 | 0 | 2026 |
| 746 | Discover Sustainability | 2662-9984 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 747 | Discrete and Continuous Dynamical Systems - B | 1531-3492 | Q1 | 1 | 0 | 1 | 0 | 2024 |
| 748 | DLSU Business & Economics Review | 0116-7111 | Q3 | 1 | 1 | 0 | 0 | 2021 |
| 749 | Drug Development and Industrial Pharmacy | 0363-9045 | Q2 | 1 | 1 | 0 | 0 | 2018 |
| 750 | Dynamic Systems and Applications | 1056-2176 | unranked | 1 | 1 | 0 | 0 | 2024 |
| 751 | Earth Science Informatics | 1865-0473 | Q1 | 1 | 0 | 0 | 1 | 2026 |
| 752 | East European Journal of Physics | 2312-4334 | Q4 | 1 | 1 | 0 | 0 | 2022 |
| 753 | Ecological Informatics | 1574-9541 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 754 | Economics Business Accounting & Society Review | 2810-0018 | unranked | 1 | 1 | 0 | 0 | 2022 |
| 755 | Education and Information Technologies | 1360-2357 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 756 | Electric Power Systems Research | 0378-7796 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 757 | Electrical Control and Communication Engineering | 2255-9140 | unranked | 1 | 1 | 0 | 0 | 2020 |
| 758 | Electrical Engineering | 0003-9039 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 759 | Electronics Letters | 0013-5194 | Q2 | 1 | 1 | 0 | 0 | 2016 |
| 760 | Emergent Materials | 2522-5731 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 761 | Energy | 0360-5442 | Q1 | 1 | 0 | 1 | 0 | 2023 |
| 762 | Engaging Science Technology and Society | 2413-8053 | unranked | 1 | 0 | 0 | 1 | 2020 |
| 763 | Engineering Technology & Applied Science Research | 1792-8036 | Q2 | 1 | 0 | 0 | 1 | 2026 |
| 764 | Entertainment Computing | 1875-9521 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 765 | Environmental Engineering and Management Journal | 1582-9596 | Q3 | 1 | 0 | 1 | 0 | 2018 |
| 766 | Environmental Hazards | 1464-2867 | Q1 | 1 | 0 | 1 | 0 | 2022 |
| 767 | Environmental Modeling & Assessment | 1420-2026 | Q2 | 1 | 0 | 1 | 0 | 2019 |
| 768 | Environmental Progress & Sustainable Energy | 1944-7442 | Q2 | 1 | 1 | 0 | 0 | 2019 |
| 769 | Environmental Research Letters | 1748-9326 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 770 | Environmental Science & Policy | 1462-9011 | Q1 | 1 | 0 | 1 | 0 | 2017 |
| 771 | EPH - International Journal of Science And Engineering | 2454-2016 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 772 | Epidemiologic Methods | 2161-962X | Q3 | 1 | 1 | 0 | 0 | 2021 |
| 773 | EPRA International Journal of Environmental Economics Commerce and Educational Management | 2348-814X | unranked | 1 | 1 | 0 | 0 | 2023 |
| 774 | Eurasian Journal of Medical Advances | 2822-2288 | unranked | 1 | 1 | 0 | 0 | 2022 |
| 775 | European Biophysics Journal | 0175-7571 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 776 | European J of International Management | 1751-6757 | Q3 | 1 | 1 | 0 | 0 | 2023 |
| 777 | European Journal of Control | 0947-3580 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 778 | European Journal of Integrative Medicine | 1876-3820 | Q2 | 1 | 1 | 0 | 0 | 2020 |
| 779 | European Research on Management and Business Economics | 2444-8834 | Q1 | 1 | 1 | 0 | 0 | 2020 |
| 780 | Evergreen | 2189-0420 | Q3 | 1 | 0 | 1 | 0 | 2023 |
| 781 | Experimental Astronomy | 0922-6435 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 782 | Exploration of BioMat-X | 2996-9476 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 783 | F1000Research | 2046-1402 | Q1 | 1 | 0 | 0 | 1 | 2023 |
| 784 | FIIB Business Review | 2319-7145 | Q3 | 1 | 0 | 1 | 0 | 2021 |
| 785 | Financial Innovation | 2199-4730 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 786 | Flexible and Printed Electronics | 2058-8585 | Q2 | 1 | 0 | 1 | 0 | 2024 |
| 787 | Folia Microbiologica | 0015-5632 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 788 | Formal Methods in System Design | 0925-9856 | Q3 | 1 | 0 | 0 | 1 | 2021 |
| 789 | Foundations and Trends® in Communications and Information Theory | 1567-2190 | Q1 | 1 | 0 | 0 | 1 | 2022 |
| 790 | Franklin Open | 2773-1863 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 791 | Frontiers in Artificial Intelligence | 2624-8212 | Q1 | 1 | 0 | 0 | 1 | 2025 |
| 792 | Frontiers in Big Data | 2624-909X | Q1 | 1 | 1 | 0 | 0 | 2019 |
| 793 | Frontiers in Carbon | 2813-4192 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 794 | Frontiers in Ecology and Evolution | 2296-701X | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 795 | Frontiers in Microbiology | 1664-302X | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 796 | Frontiers in Radiology | 2673-8740 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 797 | Frontiers in Robotics and AI | 2296-9144 | Q2 | 1 | 0 | 0 | 1 | 2022 |
| 798 | Frontiers in Virology | 2673-818X | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 799 | Frontiers in Virtual Reality | 2673-4192 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 800 | Functional & Integrative Genomics | 1438-793X | Q1 | 1 | 1 | 0 | 0 | 2017 |
| 801 | Future Computing and Informatics Journal | 2314-7288 | unranked | 1 | 0 | 1 | 0 | 2017 |
| 802 | Future Internet | 1999-5903 | Q2 | 1 | 0 | 0 | 1 | 2021 |
| 803 | Genomics & Informatics | 1598-866X | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 804 | Geocarto International | 1010-6049 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 805 | Government Information Quarterly | 0740-624X | Q1 | 1 | 0 | 0 | 1 | 2016 |
| 806 | Groundwater for Sustainable Development | 2352-801X | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 807 | Healthcare Engineering | 3115-8250 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 808 | High-Confidence Computing | 2667-2952 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 809 | Human Behavior and Emerging Technologies | 2578-1863 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 810 | IEEE Computational Intelligence Magazine | 1556-603X | Q1 | 1 | 0 | 0 | 1 | 2019 |
| 811 | IEEE Geoscience and Remote Sensing Magazine | 2168-6831 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 812 | IEEE Industry Applications Magazine | 1077-2618 | Q3 | 1 | 0 | 1 | 0 | 2025 |
| 813 | IEEE Internet of Things Magazine | 2576-3180 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 814 | IEEE Journal of Photovoltaics | 2156-3381 | Q1 | 1 | 1 | 0 | 0 | 2016 |
| 815 | IEEE Journal of Radio Frequency Identification | 2469-7281 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 816 | IEEE journal on multiscale and multiphysics computational techniques | 2379-8793 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 817 | IEEE Microwave and Wireless Technology Letters | 2771-957X | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 818 | IEEE Microwave Magazine | 1527-3342 | Q1 | 1 | 0 | 1 | 0 | 2022 |
| 819 | IEEE Network | 0890-8044 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 820 | IEEE Open Journal of Engineering in Medicine and Biology | 2644-1276 | Q2 | 1 | 0 | 0 | 1 | 2023 |
| 821 | IEEE Open Journal of the Computer Society | 2644-1268 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 822 | IEEE photonics journal | 1943-0647 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 823 | IEEE Potentials | 0278-6648 | Q3 | 1 | 0 | 0 | 1 | 2018 |
| 824 | IEEE Robotics and Automation Letters | 2377-3766 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 825 | IEEE Transactions on Audio Speech and Language Processing | 2998-4173 | unranked | 1 | 0 | 0 | 1 | 2026 |
| 826 | IEEE Transactions on Automation Science and Engineering | 1545-5955 | Q1 | 1 | 1 | 0 | 0 | 2016 |
| 827 | IEEE Transactions on Biometrics Behavior and Identity Science | 2637-6407 | unranked | 1 | 0 | 1 | 0 | 2019 |
| 828 | IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems | 0278-0070 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 829 | IEEE Transactions on Control Systems Technology | 1063-6536 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 830 | IEEE Transactions on Electromagnetic Compatibility | 0018-9375 | Q1 | 1 | 0 | 1 | 0 | 2021 |
| 831 | IEEE Transactions on Engineering Management | 0018-9391 | Q1 | 1 | 0 | 1 | 0 | 2024 |
| 832 | IEEE Transactions on Fuzzy Systems | 1063-6706 | Q1 | 1 | 1 | 0 | 0 | 2026 |
| 833 | IEEE Transactions on Human-Machine Systems | 2168-2291 | Q1 | 1 | 0 | 1 | 0 | 2024 |
| 834 | IEEE Transactions on Industrial Electronics | 0278-0046 | Q1 | 1 | 0 | 0 | 1 | 2026 |
| 835 | IEEE Transactions on Industry Applications | 0093-9994 | Q1 | 1 | 1 | 0 | 0 | 2026 |
| 836 | IEEE Transactions on Learning Technologies | 1939-1382 | Q1 | 1 | 0 | 0 | 1 | 2022 |
| 837 | IEEE Transactions on Magnetics | 0018-9464 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 838 | IEEE Transactions on Mobile Computing | 1536-1233 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 839 | IEEE Transactions on Neural Networks and Learning Systems | 2162-237X | Q1 | 1 | 0 | 1 | 0 | 2020 |
| 840 | IEEE Transactions on Neural Systems and Rehabilitation Engineering | 1534-4320 | Q1 | 1 | 0 | 0 | 1 | 2022 |
| 841 | IEEE Transactions on Parallel and Distributed Systems | 1045-9219 | Q1 | 1 | 1 | 0 | 0 | 2019 |
| 842 | IEEE Transactions on Pattern Analysis and Machine Intelligence | 0162-8828 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 843 | IEEE Transactions on Radar Systems | 2832-7357 | unranked | 1 | 0 | 0 | 1 | 2025 |
| 844 | IEEE Transactions on Transportation Electrification | 2332-7782 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 845 | IEEE Transactions on Ultrasonics Ferroelectrics and Frequency Control | 0885-3010 | Q1 | 1 | 1 | 0 | 0 | 2020 |
| 846 | IEEE Vehicular Technology Magazine | 1556-6072 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 847 | IEEE/ACM Transactions on Audio Speech and Language Processing | 2329-9290 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 848 | IEEE/CAA Journal of Automatica Sinica | 2329-9266 | Q1 | 1 | 0 | 1 | 0 | 2017 |
| 849 | IET Blockchain | 2634-1573 | Q2 | 1 | 0 | 1 | 0 | 2022 |
| 850 | IET Optoelectronics | 1751-8768 | Q2 | 1 | 1 | 0 | 0 | 2020 |
| 851 | IET Software | 1751-8806 | Q2 | 1 | 1 | 0 | 0 | 2021 |
| 852 | IIM Kozhikode Society & Management Review | 2277-9752 | unranked | 1 | 0 | 1 | 0 | 2019 |
| 853 | IIMS Journal of Management Science | 0976-030X | unranked | 1 | 0 | 1 | 0 | 2026 |
| 854 | IJARCCE | 2278-1021 | unranked | 1 | 1 | 0 | 0 | 2023 |
| 855 | In Silico Pharmacology | 2193-9616 | unranked | 1 | 1 | 0 | 0 | 2022 |
| 856 | Indagationes Mathematicae | 0019-3577 | Q2 | 1 | 1 | 0 | 0 | 2023 |
| 857 | India Review | 1473-6489 | Q3 | 1 | 0 | 1 | 0 | 2022 |
| 858 | Indian Growth and Development Review | 1753-8254 | Q3 | 1 | 0 | 1 | 0 | 2021 |
| 859 | Indian Horticulture | 0019-4875 | unranked | 1 | 0 | 1 | 0 | 2019 |
| 860 | Indian Journal of Chemistry | 0019-5103 | Q3 | 1 | 1 | 0 | 0 | 2024 |
| 861 | Indian Journal of Computer Science and Engineering | 0976-5166 | Q4 | 1 | 0 | 1 | 0 | 2021 |
| 862 | Indian Journal of Extension Education | 0537-1996 | unranked | 1 | 0 | 1 | 0 | 2021 |
| 863 | Indian Journal of Gastroenterology | 0254-8860 | Q3 | 1 | 1 | 0 | 0 | 2016 |
| 864 | Indian Journal of Labour Economics | 0019-5308 | Q2 | 1 | 0 | 0 | 1 | 2024 |
| 865 | Indian Journal of Pharmaceutical Education and Research | 0019-5464 | Q3 | 1 | 1 | 0 | 0 | 2017 |
| 866 | Industrial and Commercial Training | 0019-7858 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 867 | Industrial Robot the international journal of robotics research and application | 0143-991X | Q3 | 1 | 1 | 0 | 0 | 2020 |
| 868 | Industry and Innovation | 1366-2716 | Q1 | 1 | 0 | 0 | 1 | 2020 |
| 869 | Infant Behavior and Development | 0163-6383 | Q2 | 1 | 0 | 0 | 1 | 2026 |
| 870 | Infection Genetics and Evolution | 1567-1348 | Q1 | 1 | 0 | 0 | 1 | 2020 |
| 871 | Informatics in Medicine Unlocked | 2352-9148 | Q3 | 1 | 1 | 0 | 0 | 2020 |
| 872 | Information and Computer Security | 2056-4961 | Q2 | 1 | 0 | 1 | 0 | 2019 |
| 873 | Information Polity | 1570-1255 | Q2 | 1 | 0 | 0 | 1 | 2023 |
| 874 | Information Processing & Management | 0020-0271 | Q1 | 1 | 0 | 1 | 0 | 2020 |
| 875 | Information Systems Frontiers | 1387-3326 | Q1 | 1 | 0 | 0 | 1 | 2020 |
| 876 | Inhalation Toxicology | 0895-8378 | Q3 | 1 | 1 | 0 | 0 | 2023 |
| 877 | Innovative Journal of Integrated Research and Technological Innovations | 3107-9415 | unranked | 1 | 0 | 0 | 1 | 2025 |
| 878 | Inorganic Chemistry | 0020-1669 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 879 | Integrated ferroelectrics | 1026-7530 | Q3 | 1 | 0 | 1 | 0 | 2020 |
| 880 | Intelligent Systems with Applications | 2667-3053 | Q1 | 1 | 0 | 0 | 1 | 2022 |
| 881 | Intermetallics | 0966-9795 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 882 | International Journal for Numerical Methods in Biomedical Engineering | 2040-7939 | Q2 | 1 | 1 | 0 | 0 | 2023 |
| 883 | International Journal for Research Publication and Seminars | 2278-6848 | unranked | 1 | 0 | 0 | 1 | 2020 |
| 884 | International Journal of Academic Medicine | 2455-5568 | Q4 | 1 | 1 | 0 | 0 | 2023 |
| 885 | International Journal of Accounting and Business Finance | 2448-9867 | unranked | 1 | 1 | 0 | 0 | 2021 |
| 886 | International Journal of Ad Hoc and Ubiquitous Computing | 1743-8225 | Q3 | 1 | 0 | 1 | 0 | 2021 |
| 887 | International Journal of Advanced Computer Science and Applications | 2156-5570 | unranked | 1 | 1 | 0 | 0 | 2016 |
| 888 | International Journal of Advanced Intelligence Paradigms | 1755-0386 | Q4 | 1 | 1 | 0 | 0 | 2024 |
| 889 | International Journal of Advanced Research | 2320-5407 | unranked | 1 | 1 | 0 | 0 | 2016 |
| 890 | International Journal of Advanced Research in Computer Science | 0976-5697 | unranked | 1 | 0 | 1 | 0 | 2017 |
| 891 | International Journal of Advanced Research in Science Communication and Technology | 2581-9429 | unranked | 1 | 1 | 0 | 0 | 2021 |
| 892 | International Journal of Advances in Engineering Sciences and Applied Mathematics | 0975-0770 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 893 | International Journal of Advances in Signal and Image Sciences | 2457-0370 | Q3 | 1 | 0 | 1 | 0 | 2026 |
| 894 | International Journal of Bank Marketing | 0265-2323 | Q2 | 1 | 0 | 1 | 0 | 2017 |
| 895 | International Journal of Basic and Applied Sciences | 2227-5053 | unranked | 1 | 0 | 1 | 0 | 2025 |
| 896 | International Journal of Biosensors & Bioelectronics | 2573-2838 | unranked | 1 | 1 | 0 | 0 | 2017 |
| 897 | International Journal of Business and Emerging Markets | 1753-6219 | unranked | 1 | 1 | 0 | 0 | 2016 |
| 898 | International Journal of Business and Globalisation | 1753-3627 | Q4 | 1 | 0 | 1 | 0 | 2023 |
| 899 | International Journal of Business Performance and Supply Chain Modelling | 1758-9401 | Q2 | 1 | 0 | 1 | 0 | 2016 |
| 900 | International Journal of Business Performance Management | 1368-4892 | Q3 | 1 | 0 | 1 | 0 | 2017 |
| 901 | International Journal of Cell Biology | 1687-8876 | Q4 | 1 | 1 | 0 | 0 | 2023 |
| 902 | International Journal of Circuit Theory and Applications | 0098-9886 | Q2 | 1 | 0 | 1 | 0 | 2021 |
| 903 | International journal of communication | 1932-8036 | Q1 | 1 | 0 | 0 | 1 | 2018 |
| 904 | International Journal of Computational and Experimental Science and Engineering | 2149-9144 | Q3 | 1 | 0 | 0 | 1 | 2025 |
| 905 | International Journal of Computational Geometry & Applications | 0218-1959 | Q4 | 1 | 0 | 0 | 1 | 2018 |
| 906 | International Journal of Computational Methods | 0219-8762 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 907 | International Journal of Computational Systems Engineering | 2046-3391 | unranked | 1 | 1 | 0 | 0 | 2018 |
| 908 | International Journal of Computer Systems & Software Engineering | 2180-0650 | unranked | 1 | 1 | 0 | 0 | 2022 |
| 909 | International Journal of Computer Vision and Image Processing | 2155-6989 | unranked | 1 | 1 | 0 | 0 | 2021 |
| 910 | International Journal of Control | 0020-7179 | Q2 | 1 | 0 | 0 | 1 | 2022 |
| 911 | International Journal of Data Analysis Techniques and Strategies | 1755-8050 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 912 | International Journal of Diabetes in Developing Countries | 0973-3930 | Q3 | 1 | 0 | 1 | 0 | 2025 |
| 913 | International Journal of Digital Crime and Forensics | 1941-6210 | Q4 | 1 | 1 | 0 | 0 | 2018 |
| 914 | International Journal of Distributed Systems and Technologies | 1947-3532 | Q4 | 1 | 0 | 1 | 0 | 2016 |
| 915 | International Journal of Drug Delivery Technology | 0975-4415 | Q3 | 1 | 0 | 1 | 0 | 2026 |
| 916 | International Journal of Economics and Business Research | 1756-9850 | Q3 | 1 | 1 | 0 | 0 | 2018 |
| 917 | International Journal of Electrical and Electronics Research | 2347-470X | Q4 | 1 | 0 | 1 | 0 | 2024 |
| 918 | International Journal of Electronics Letters | 2168-1724 | Q4 | 1 | 0 | 1 | 0 | 2024 |
| 919 | International Journal of Engineering & Technology | 2227-524X | Q4 | 1 | 0 | 1 | 0 | 2018 |
| 920 | International Journal of Engineering Research in Electronics and Communication Engineering | 2394-6849 | unranked | 1 | 0 | 1 | 0 | 2022 |
| 921 | International Journal of Engineering Researches and Management Studies | 2394-7659 | unranked | 1 | 0 | 0 | 1 | 2017 |
| 922 | International Journal of Engineering Trends and Technology | 2231-5381 | Q4 | 1 | 0 | 0 | 1 | 2026 |
| 923 | International Journal of Environmental & Analytical Chemistry | 0306-7319 | Q3 | 1 | 0 | 1 | 0 | 2019 |
| 924 | International Journal of Environmental Research and Public Health | 1660-4601 | Q1 | 1 | 0 | 0 | 1 | 2026 |
| 925 | International Journal of Environmental Science and Technology | 1735-1472 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 926 | International Journal of Ethics and Systems | 0828-8666 | Q2 | 1 | 0 | 1 | 0 | 2019 |
| 927 | International Journal of Event and Festival Management | 1758-2954 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 928 | International Journal of experimental research and review | 2455-4855 | Q4 | 1 | 0 | 1 | 0 | 2024 |
| 929 | International Journal of Financial Innovation in Banking | 2055-6780 | unranked | 1 | 0 | 1 | 0 | 2016 |
| 930 | International Journal of Financial Markets and Derivatives | 1756-7130 | unranked | 1 | 0 | 1 | 0 | 2022 |
| 931 | International Journal of Future Generation Communication and Networking | 2207-9645 | Q4 | 1 | 0 | 1 | 0 | 2017 |
| 932 | International Journal of Global Business and Competitiveness | 0973-4619 | unranked | 1 | 0 | 1 | 0 | 2025 |
| 933 | International Journal of Global Management Perspectives | 3049-4214 | unranked | 1 | 0 | 1 | 0 | 2026 |
| 934 | International journal of greenhouse gas control | 1750-5836 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 935 | International Journal of Health Care Quality Assurance | 0952-6862 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 936 | International Journal of Health Sciences | 2550-696X | unranked | 1 | 0 | 1 | 0 | 2022 |
| 937 | International Journal of Healthcare Management | 2047-9700 | Q3 | 1 | 0 | 1 | 0 | 2019 |
| 938 | International Journal of Higher Education and Sustainability | 2056-4023 | unranked | 1 | 0 | 1 | 0 | 2018 |
| 939 | International Journal of Human Capital and Information Technology Professionals | 1947-3478 | Q3 | 1 | 1 | 0 | 0 | 2019 |
| 940 | International Journal of Human Resources Development and Management | 1465-6612 | Q4 | 1 | 0 | 1 | 0 | 2018 |
| 941 | International Journal of Human Rights in Healthcare | 2056-4902 | Q2 | 1 | 0 | 1 | 0 | 2022 |
| 942 | International Journal of Human-Computer Studies | 1071-5819 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 943 | International Journal of Hydrogen Energy | 0360-3199 | Q1 | 1 | 0 | 1 | 0 | 2019 |
| 944 | International Journal of Image and Graphics | 0219-4678 | unranked | 1 | 1 | 0 | 0 | 2016 |
| 945 | International Journal of Image Graphics and Signal Processing | 2074-9074 | Q3 | 1 | 0 | 1 | 0 | 2024 |
| 946 | International Journal of Imaging Systems and Technology | 0899-9457 | Q2 | 1 | 0 | 1 | 0 | 2022 |
| 947 | International journal of industrial engineering | 1072-4761 | Q3 | 1 | 0 | 1 | 0 | 2023 |
| 948 | International Journal of Industrial Engineering and Operations Management | 2690-6090 | Q2 | 1 | 0 | 1 | 0 | 2023 |
| 949 | International Journal of Infectious Diseases | 1201-9712 | Q1 | 1 | 0 | 1 | 0 | 2016 |
| 950 | International Journal of Information and Electronics Engineering | 2010-3719 | unranked | 1 | 0 | 0 | 1 | 2016 |
| 951 | International Journal of Information Management | 0268-4012 | Q1 | 1 | 1 | 0 | 0 | 2018 |
| 952 | International Journal of Information Management Data Insights | 2667-0968 | Q1 | 1 | 0 | 1 | 0 | 2021 |
| 953 | International Journal of Information Retrieval Research | 2155-6377 | unranked | 1 | 1 | 0 | 0 | 2017 |
| 954 | International Journal of Information Security and Privacy | 1930-1650 | Q3 | 1 | 1 | 0 | 0 | 2021 |
| 955 | International Journal of Information Technology Communications and Convergence | 2042-3217 | unranked | 1 | 1 | 0 | 0 | 2019 |
| 956 | International Journal of Innovative Research in Applied Sciences and Engineering | 2456-8910 | unranked | 1 | 0 | 0 | 1 | 2020 |
| 957 | International Journal of Intelligent Robotics and Applications | 2366-5971 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 958 | International Journal of Intelligent Transportation Systems Research | 1348-8503 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 959 | International Journal of Leading Research Publication. | 2582-8010 | unranked | 1 | 0 | 1 | 0 | 2026 |
| 960 | International Journal of Lean Enterprise Research | 1754-2294 | unranked | 1 | 0 | 1 | 0 | 2016 |
| 961 | International Journal of Learning and Intellectual Capital | 1479-4853 | Q3 | 1 | 0 | 1 | 0 | 2017 |
| 962 | International Journal of Linguistics Applied Psychology and Technology (IJLAPT) | 3048-4529 | unranked | 1 | 0 | 1 | 0 | 2026 |
| 963 | International Journal of Logistics Systems and Management | 1742-7967 | Q2 | 1 | 0 | 1 | 0 | 2016 |
| 964 | International Journal of Machine Learning and Computing | 2010-3700 | Q4 | 1 | 0 | 0 | 1 | 2017 |
| 965 | International Journal of Management Practice | 1477-9064 | Q4 | 1 | 0 | 1 | 0 | 2016 |
| 966 | International Journal of Materials and Product Technology | 0268-1900 | Q4 | 1 | 0 | 1 | 0 | 2025 |
| 967 | International Journal of Materials Engineering Innovation | 1757-2754 | Q4 | 1 | 0 | 1 | 0 | 2022 |
| 968 | International Journal of Materials Research (formerly Zeitschrift fuer Metallkunde) | 0044-3093 | Q3 | 1 | 0 | 1 | 0 | 2025 |
| 969 | International Journal of Mathematics And its Applications | 2347-1557 | unranked | 1 | 0 | 0 | 1 | 2019 |
| 970 | International Journal of Mobile Communications | 1470-949X | Q1 | 1 | 0 | 1 | 0 | 2018 |
| 971 | International Journal of Modern Computer Science and IT Innovations | 3087-4289 | unranked | 1 | 1 | 0 | 0 | 2025 |
| 972 | International Journal of Multidisciplinary Research and Development | 2349-4182 | unranked | 1 | 1 | 0 | 0 | 2026 |
| 973 | International Journal of Multidisciplinary Research and Studies | 2640-7272 | unranked | 1 | 0 | 1 | 0 | 2023 |
| 974 | International Journal of Multimedia and Ubiquitous Engineering | 1975-0080 | Q4 | 1 | 0 | 1 | 0 | 2017 |
| 975 | International Journal of Multimedia Information Retrieval | 2192-6611 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 976 | International Journal of Nanomedicine | 1176-9114 | Q1 | 1 | 0 | 1 | 0 | 2018 |
| 977 | International Journal of Network Management | 1055-7148 | Q2 | 1 | 0 | 1 | 0 | 2020 |
| 978 | International Journal of Numerical Methods for Heat &amp Fluid Flow | 0961-5539 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 979 | International Journal of Numerical Modelling Electronic Networks Devices and Fields | 0894-3370 | Q3 | 1 | 1 | 0 | 0 | 2024 |
| 980 | International Journal of Parallel Programming | 0885-7458 | Q2 | 1 | 1 | 0 | 0 | 2021 |
| 981 | International Journal of Pharma and Bio Sciences | 0975-6299 | Q4 | 1 | 1 | 0 | 0 | 2017 |
| 982 | International Journal of Pharmaceutical and Healthcare Marketing | 1750-6123 | Q4 | 1 | 0 | 1 | 0 | 2018 |
| 983 | International Journal of Pharmaceutical Investigation | 2230-9713 | Q1 | 1 | 1 | 0 | 0 | 2019 |
| 984 | International Journal of Pharmacology | 1811-7775 | Q3 | 1 | 1 | 0 | 0 | 2017 |
| 985 | International Journal of Process Management and Benchmarking | 1460-6739 | Q3 | 1 | 0 | 1 | 0 | 2021 |
| 986 | International Journal of Product Development | 1477-9056 | Q3 | 1 | 0 | 1 | 0 | 2019 |
| 987 | International Journal of Production Economics | 0925-5273 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 988 | International Journal of Progressive Research in Science and Engineering | 2582-7898 | unranked | 1 | 0 | 1 | 0 | 2020 |
| 989 | International Journal of Quality & Reliability Management | 0265-671X | Q2 | 1 | 0 | 1 | 0 | 2021 |
| 990 | International Journal of Recent Advances in Multidisciplinary Topics | 2582-7839 | unranked | 1 | 0 | 0 | 1 | 2021 |
| 991 | International Journal of Research in Ayurveda and Pharmacy | 2229-3566 | Q4 | 1 | 1 | 0 | 0 | 2017 |
| 992 | International Journal of Research in Engineering and Technology | 2319-1163 | unranked | 1 | 0 | 1 | 0 | 2018 |
| 993 | International Journal of Research in Library Science | 2455-104X | unranked | 1 | 0 | 0 | 1 | 2026 |
| 994 | International Journal of Research in Management | 2664-8792 | unranked | 1 | 1 | 0 | 0 | 2024 |
| 995 | International Journal of Scientific Research in Computer Science Engineering and Information Technology | 2456-3307 | unranked | 1 | 0 | 0 | 1 | 2024 |
| 996 | International Journal of Scientific Research in Computer Sciences and Engineering | 2320-7639 | unranked | 1 | 0 | 1 | 0 | 2017 |
| 997 | International Journal of Scientific Research in Network Security and Communication | 2321-3256 | unranked | 1 | 0 | 1 | 0 | 2019 |
| 998 | International Journal of Scientific Research in Science Engineering and Technology | 2394-4099 | unranked | 1 | 0 | 1 | 0 | 2017 |
| 999 | International Journal of Security and Its Applications | 1738-9976 | Q3 | 1 | 1 | 0 | 0 | 2016 |
| 1000 | International Journal of Security and Networks | 1747-8405 | Q4 | 1 | 1 | 0 | 0 | 2019 |
| 1001 | International Journal of Selection and Assessment | 0965-075X | Q1 | 1 | 0 | 0 | 1 | 2023 |
| 1002 | International Journal of Sensors Wireless Communications and Control | 2210-3279 | Q4 | 1 | 1 | 0 | 0 | 2024 |
| 1003 | International Journal of Social Ecology and Sustainable Development | 1947-8402 | Q4 | 1 | 0 | 1 | 0 | 2022 |
| 1004 | International Journal of Social Economics | 0306-8293 | Q2 | 1 | 0 | 1 | 0 | 2020 |
| 1005 | International Journal of Society Systems Science | 1756-2511 | unranked | 1 | 0 | 1 | 0 | 2016 |
| 1006 | International Journal of Sports Marketing and Sponsorship | 1464-6668 | Q2 | 1 | 1 | 0 | 0 | 2021 |
| 1007 | International Journal of Strategic Property Management | 1648-715X | Q3 | 1 | 1 | 0 | 0 | 2024 |
| 1008 | International Journal of Sustainable Design | 1743-8284 | unranked | 1 | 1 | 0 | 0 | 2022 |
| 1009 | International journal of systematic innovation | 2077-7973 | Q3 | 1 | 0 | 1 | 0 | 2022 |
| 1010 | International Journal of Telemedicine and Clinical Practices | 2052-8434 | unranked | 1 | 0 | 1 | 0 | 2017 |
| 1011 | International Journal of Theoretical Physics | 0020-7748 | Q3 | 1 | 1 | 0 | 0 | 2016 |
| 1012 | International Journal of Trust Management in Computing and Communications | 2048-8378 | unranked | 1 | 1 | 0 | 0 | 2017 |
| 1013 | International Journal of Wavelets Multiresolution and Information Processing | 0219-6913 | Q3 | 1 | 0 | 1 | 0 | 2024 |
| 1014 | International Journal of Web Based Communities | 1477-8394 | Q3 | 1 | 0 | 1 | 0 | 2016 |
| 1015 | International Journal of Wireless and Mobile Computing | 1741-1084 | Q4 | 1 | 1 | 0 | 0 | 2019 |
| 1016 | International Journal of Wireless Information Networks | 1068-9605 | Q4 | 1 | 0 | 1 | 0 | 2017 |
| 1017 | International Journal on Document Analysis and Recognition (IJDAR) | 1433-2825 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1018 | International Research Journal on Advanced Engineering Hub (IRJAEH) | 2584-2137 | unranked | 1 | 0 | 0 | 1 | 2025 |
| 1019 | International Review of Economics & Finance | 1059-0560 | Q1 | 1 | 0 | 1 | 0 | 2022 |
| 1020 | International Review on Public and Nonprofit Marketing | 1865-1984 | Q2 | 1 | 0 | 1 | 0 | 2023 |
| 1021 | IoT | 2624-831X | Q1 | 1 | 0 | 0 | 1 | 2025 |
| 1022 | Iran Journal of Computer Science | 2520-8438 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 1023 | Iranian journal of management studies | 2008-7055 | unranked | 1 | 1 | 0 | 0 | 2018 |
| 1024 | Iranian Journal of Science and Technology Transactions of Electrical Engineering | 2228-6179 | Q4 | 1 | 1 | 0 | 0 | 2019 |
| 1025 | ITEGAM- Journal of Engineering and Technology for Industrial Applications (ITEGAM-JETIA) | 2447-0228 | Q4 | 1 | 0 | 1 | 0 | 2026 |
| 1026 | IV | – | unranked | 1 | 0 | 0 | 1 | 2020 |
| 1027 | JMIR Formative Research | 2561-326X | Q2 | 1 | 0 | 0 | 1 | 2025 |
| 1028 | Jordan Journal of Mathematics and Statistics | 2075-7905 | Q3 | 1 | 0 | 1 | 0 | 2025 |
| 1029 | Journal des Anti-infectieux | 2210-6545 | Q4 | 1 | 1 | 0 | 0 | 2017 |
| 1030 | Journal of Advanced Dielectrics | 2010-135X | Q2 | 1 | 1 | 0 | 0 | 2018 |
| 1031 | Journal of Advanced Management Studies. | 3048-636X | unranked | 1 | 0 | 1 | 0 | 2025 |
| 1032 | Journal of Advanced Research in Production and Industrial Engineering | 2456-429X | unranked | 1 | 0 | 1 | 0 | 2019 |
| 1033 | Journal of Advances and Scholarly Researches in Allied Education | 2230-7540 | unranked | 1 | 0 | 1 | 0 | 2018 |
| 1034 | Journal of Agricultural Engineering | 1974-7071 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 1035 | Journal of Algebra and Its Applications | 0219-4988 | Q2 | 1 | 1 | 0 | 0 | 2020 |
| 1036 | Journal of Applied Analysis & Computation | 2156-907X | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 1037 | Journal of Applied and Computational Topology | 2367-1726 | Q1 | 1 | 0 | 0 | 1 | 2026 |
| 1038 | Journal of Applied Pharmaceutical Science | 2231-3354 | Q2 | 1 | 1 | 0 | 0 | 2017 |
| 1039 | Journal of Applied Philosophy | 0264-3758 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 1040 | Journal of Applied Physics | 0021-8979 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 1041 | Journal of Applied Security Research | 1936-1610 | Q3 | 1 | 0 | 0 | 1 | 2019 |
| 1042 | Journal of Artificial Intelligence Research | 1076-9757 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1043 | Journal of Asia Business Studies | 1558-7894 | Q2 | 1 | 1 | 0 | 0 | 2019 |
| 1044 | Journal of Atomic Molecular Condensate and Nano Physics | 2349-2716 | unranked | 1 | 0 | 1 | 0 | 2019 |
| 1045 | Journal of Behavioral Finance | 1520-8834 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 1046 | Journal of biology and nature | 2395-5376 | unranked | 1 | 0 | 1 | 0 | 2025 |
| 1047 | Journal of Biomedical Optics | 1083-3668 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1048 | Journal of Biosciences and Medicines | 2327-5081 | unranked | 1 | 1 | 0 | 0 | 2016 |
| 1049 | Journal of Business and Industrial Marketing | 0885-8624 | Q1 | 1 | 1 | 0 | 0 | 2020 |
| 1050 | Journal of Business Cycle Research | 2509-7962 | Q3 | 1 | 1 | 0 | 0 | 2021 |
| 1051 | Journal of chemical health risks | 2251-6719 | Q4 | 1 | 0 | 0 | 1 | 2026 |
| 1052 | Journal of Chemical Information and Modeling | 1549-9596 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 1053 | Journal of Clinical and Translational Research | 2382-6533 | unranked | 1 | 1 | 0 | 0 | 2022 |
| 1054 | Journal of Communications and Information Networks | 2096-1081 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 1055 | Journal of Comparative Policy Analysis Research and Practice | 1387-6988 | Q1 | 1 | 0 | 0 | 1 | 2025 |
| 1056 | Journal of Computational Biophysics and Chemistry | 2737-4165 | Q4 | 1 | 0 | 1 | 0 | 2022 |
| 1057 | Journal of Computational Design and Engineering | 2288-4300 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 1058 | Journal of Computational Social Science | 2432-2717 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1059 | Journal of Computer and System Sciences | 0022-0000 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1060 | Journal of Computer Languages | 2590-1184 | Q3 | 1 | 0 | 0 | 1 | 2024 |
| 1061 | Journal of Computer Virology and Hacking Techniques | 1772-9890 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1062 | Journal of Computers in Education | 2197-9987 | unranked | 1 | 0 | 0 | 1 | 2017 |
| 1063 | Journal of Conservative Dentistry and Endodontics | 2950-4708 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1064 | Journal of Cryptographic Engineering | 2190-8508 | Q3 | 1 | 0 | 1 | 0 | 2026 |
| 1065 | Journal of Cultural Cognitive Science | 2520-100X | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 1066 | Journal of Cultural Economy | 1753-0350 | Q1 | 1 | 0 | 0 | 1 | 2019 |
| 1067 | Journal of Cybersecurity Education Research and Practice | 2472-2707 | unranked | 1 | 1 | 0 | 0 | 2024 |
| 1068 | Journal of Decision System | 1246-0125 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1069 | Journal of Differential Equations | 0022-0396 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 1070 | Journal of Double Star Observations | 2572-4436 | unranked | 1 | 0 | 0 | 1 | 2025 |
| 1071 | Journal of Earth System Science | 0253-4126 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1072 | Journal of economic and administrative sciences. | 2054-6238 | unranked | 1 | 1 | 0 | 0 | 2021 |
| 1073 | Journal of Economic Surveys | 0950-0804 | Q1 | 1 | 1 | 0 | 0 | 2026 |
| 1074 | Journal of Economics and Finance | 1055-0925 | Q2 | 1 | 0 | 1 | 0 | 2024 |
| 1075 | Journal of Education for Business | 0883-2323 | Q2 | 1 | 0 | 1 | 0 | 2023 |
| 1076 | Journal of Electrical Engineering | 1335-3632 | Q3 | 1 | 1 | 0 | 0 | 2020 |
| 1077 | Journal of Electrical Engineering and Technology | 1975-0102 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1078 | Journal of Electroanalytical Chemistry | 1572-6657 | Q1 | 1 | 0 | 1 | 0 | 2016 |
| 1079 | Journal of Emerging Market Finance | 0972-6527 | Q3 | 1 | 0 | 0 | 1 | 2022 |
| 1080 | Journal of Emerging Technologies and Innovative Research | 2349-5162 | unranked | 1 | 1 | 0 | 0 | 2025 |
| 1081 | Journal of Engineering Mathematics | 0022-0833 | Q2 | 1 | 0 | 1 | 0 | 2021 |
| 1082 | Journal of Enterprise Information Management | 1741-0398 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1083 | Journal of Entrepreneurship in Emerging Economies | 2053-4604 | Q1 | 1 | 0 | 1 | 0 | 2021 |
| 1084 | Journal of environmental chemical engineering | 2213-2929 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1085 | Journal of Environmental Informatics Letters | 2663-6859 | Q4 | 1 | 0 | 1 | 0 | 2025 |
| 1086 | Journal of Eye Movement Research | 1995-8692 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 1087 | Journal of Fashion Marketing and Management | 1361-2026 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 1088 | Journal of Financial Services Marketing | 1363-0539 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1089 | Journal of Fluid Mechanics | 0022-1120 | Q1 | 1 | 0 | 0 | 1 | 2025 |
| 1090 | Journal of Food Measurement & Characterization | 2193-4126 | Q2 | 1 | 1 | 0 | 0 | 2018 |
| 1091 | Journal of Foodservice Business Research | 1537-8020 | Q2 | 1 | 0 | 1 | 0 | 2021 |
| 1092 | Journal of Forensic Sciences | 0022-1198 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1093 | Journal of Fractal Geometry Mathematics of Fractals and Related Topics | 2308-1309 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 1094 | Journal of Future Sustainability | 2816-8143 | unranked | 1 | 1 | 0 | 0 | 2025 |
| 1095 | Journal of Global Marketing | 0891-1762 | Q1 | 1 | 1 | 0 | 0 | 2026 |
| 1096 | Journal of Guidance Control and Dynamics | 0731-5090 | Q1 | 1 | 0 | 0 | 1 | 2020 |
| 1097 | Journal of Health Management | 0972-0634 | Q3 | 1 | 0 | 1 | 0 | 2019 |
| 1098 | Journal of Hospitality and Tourism Insights | 2514-9792 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 1099 | Journal of Hospitality and Tourism Technology | 1757-9880 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1100 | Journal of ICT Standardization | 2245-800X | unranked | 1 | 0 | 0 | 1 | 2016 |
| 1101 | Journal of Industrial and Engineering Chemistry | 1226-086X | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 1102 | Journal of Information and Optimization Sciences | 0252-2667 | unranked | 1 | 0 | 1 | 0 | 2020 |
| 1103 | Journal of Information Communication and Ethics in Society | 1477-996X | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1104 | Journal of Information Science | 0165-5515 | Q2 | 1 | 1 | 0 | 0 | 2016 |
| 1105 | Journal of Innovation & Knowledge | 2444-569X | Q1 | 1 | 0 | 0 | 1 | 2025 |
| 1106 | Journal of Institute of Science and Technology | 2467-9062 | unranked | 1 | 0 | 1 | 0 | 2018 |
| 1107 | Journal of Intelligence | 2079-3200 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 1108 | Journal of Intelligent & Robotic Systems | 0921-0296 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 1109 | Journal of Intelligent Information Systems | 0925-9902 | Q1 | 1 | 1 | 0 | 0 | 2017 |
| 1110 | Journal of Intelligent Manufacturing | 0956-5515 | Q1 | 1 | 0 | 1 | 0 | 2017 |
| 1111 | Journal of Interdisciplinary Mathematics | 0972-0502 | Q3 | 1 | 0 | 1 | 0 | 2022 |
| 1112 | Journal of International Crisis and Risk Communication Research | 2576-0017 | Q2 | 1 | 0 | 0 | 1 | 2025 |
| 1113 | Journal of International Entrepreneurship | 1570-7385 | Q1 | 1 | 0 | 1 | 0 | 2016 |
| 1114 | Journal of Islamic Finance | 2289-2109 | unranked | 1 | 1 | 0 | 0 | 2020 |
| 1115 | Journal of Knowledge Management | 1367-3270 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 1116 | Journal of Management Analytics | 2327-0012 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1117 | Journal of Marketing Analytics | 2050-3318 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1118 | Journal of Marketing Communications | 1352-7266 | Q1 | 1 | 0 | 1 | 0 | 2020 |
| 1119 | Journal of Materials Chemistry C | 2050-7526 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 1120 | Journal of materials research/Pratt's guide to venture capital sources | 0884-1616 | Q1 | 1 | 1 | 0 | 0 | 2019 |
| 1121 | Journal of Materials Science and Nanotechnology | 2348-9812 | unranked | 1 | 0 | 1 | 0 | 2018 |
| 1122 | Journal of Materials Science Materials in Engineering | 3004-8958 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1123 | Journal of Mathematical Analysis and Applications | 0022-247X | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 1124 | Journal of mathematical modeling | 2345-394X | Q4 | 1 | 0 | 1 | 0 | 2019 |
| 1125 | Journal of Mathematical Sciences & Computational Mathematics | 2644-3368 | unranked | 1 | 0 | 0 | 1 | 2020 |
| 1126 | Journal of Mechanical Science and Technology | 1738-494X | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1127 | Journal of Medical and Biological Engineering | 1609-0985 | Q3 | 1 | 1 | 0 | 0 | 2017 |
| 1128 | Journal of Microbial & Biochemical Technology | 1948-5948 | Q3 | 1 | 1 | 0 | 0 | 2018 |
| 1129 | Journal of Microelectromechanical Systems | 1057-7157 | Q1 | 1 | 1 | 0 | 0 | 2017 |
| 1130 | Journal of Micromechanics and Microengineering | 0960-1317 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1131 | Journal of Modelling in Management | 1746-5664 | Q2 | 1 | 0 | 1 | 0 | 2017 |
| 1132 | Journal of Modern Accounting and Auditing | 1548-6583 | unranked | 1 | 1 | 0 | 0 | 2019 |
| 1133 | Journal of Molecular Graphics and Modelling | 1093-3263 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1134 | Journal of Molecular Liquids | 0167-7322 | Q1 | 1 | 1 | 0 | 0 | 2020 |
| 1135 | Journal of Molecular Neuroscience | 0895-8696 | Q2 | 1 | 1 | 0 | 0 | 2020 |
| 1136 | Journal of Molecular Recognition | 0952-3499 | Q4 | 1 | 1 | 0 | 0 | 2021 |
| 1137 | Journal of Nanoparticle Research | 1388-0764 | Q2 | 1 | 0 | 0 | 1 | 2018 |
| 1138 | Journal of Nanophotonics | 1934-2608 | Q4 | 1 | 1 | 0 | 0 | 2025 |
| 1139 | Journal of Nanoscience Nanoengineering and Applications | 2231-1777 | unranked | 1 | 1 | 0 | 0 | 2018 |
| 1140 | Journal of Nepal Physical Society | 2392-473X | unranked | 1 | 0 | 1 | 0 | 2020 |
| 1141 | Journal of Non-Crystalline Solids | 0022-3093 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 1142 | Journal of Number Theory | 0022-314X | Q1 | 1 | 0 | 0 | 1 | 2016 |
| 1143 | Journal of Oilseeds Research | 0970-2776 | unranked | 1 | 0 | 1 | 0 | 2025 |
| 1144 | Journal of Online Trust and Safety | 2770-3142 | unranked | 1 | 0 | 0 | 1 | 2026 |
| 1145 | Journal of Open Innovation Technology Market and Complexity | 2199-8531 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1146 | Journal of Ovonic Research | 1584-9953 | Q3 | 1 | 1 | 0 | 0 | 2025 |
| 1147 | Journal of Parallel and Distributed Computing | 0743-7315 | Q1 | 1 | 0 | 0 | 1 | 2022 |
| 1148 | Journal of Peptide Science | 1075-2617 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 1149 | Journal of Physics Communications | 2399-6528 | Q3 | 1 | 1 | 0 | 0 | 2021 |
| 1150 | Journal of Plant Diseases and Protection | 1861-3829 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1151 | Journal of Propulsion Technology | 1001-4055 | Q3 | 1 | 0 | 0 | 1 | 2026 |
| 1152 | Journal of Proteome Research | 1535-3893 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1153 | Journal of Public Affairs | 1472-3891 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1154 | Journal of Quality Assurance in Hospitality & Tourism | 1528-008X | Q2 | 1 | 0 | 1 | 0 | 2020 |
| 1155 | Journal of Quality in Maintenance Engineering | 1355-2511 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1156 | Journal of Radio Electronics | 1684-1719 | unranked | 1 | 1 | 0 | 0 | 2021 |
| 1157 | Journal of Receptors and Signal Transduction | 1079-9893 | Q4 | 1 | 1 | 0 | 0 | 2020 |
| 1158 | Journal of Research in Engineering and Computer Sciences | 3049-7590 | unranked | 1 | 1 | 0 | 0 | 2023 |
| 1159 | Journal of Revenue and Pricing Management | 1476-6930 | Q3 | 1 | 1 | 0 | 0 | 2025 |
| 1160 | Journal of Science and Technology Policy Management | 2053-4620 | Q2 | 1 | 0 | 1 | 0 | 2022 |
| 1161 | Journal of Sensory Studies | 0887-8250 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 1162 | Journal of Service Theory and Practice | 2055-6225 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1163 | Journal of Social and Personal Relationships | 0265-4075 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1164 | Journal of Social Computing | 2688-5255 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 1165 | Journal of Solar Energy Engineering | 0199-6231 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1166 | Journal of Solid State Chemistry | 0022-4596 | Q2 | 1 | 0 | 1 | 0 | 2021 |
| 1167 | Journal of Statistics and Management Systems | 0972-0510 | unranked | 1 | 1 | 0 | 0 | 2020 |
| 1168 | Journal of Sustainable Finance & Investment | 2043-0795 | Q2 | 1 | 0 | 1 | 0 | 2020 |
| 1169 | Journal of Symbolic Computation | 0747-7171 | Q2 | 1 | 0 | 0 | 1 | 2016 |
| 1170 | Journal of Systems and Software | 0164-1212 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1171 | Journal of Systems Architecture | 1383-7621 | Q2 | 1 | 0 | 1 | 0 | 2016 |
| 1172 | Journal of Systems Science and Systems Engineering | 1004-3756 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1173 | Journal of Telecommunication Electronic and Computer Engineering (JTEC) | 2180-1843 | Q4 | 1 | 0 | 0 | 1 | 2018 |
| 1174 | Journal of Telecommunications and the Digital Economy | 2203-1693 | Q2 | 1 | 0 | 0 | 1 | 2025 |
| 1175 | Journal of the ACM | 0004-5411 | Q1 | 1 | 0 | 0 | 1 | 2020 |
| 1176 | Journal of the Australian Ceramic Society | 0004-881X | Q3 | 1 | 1 | 0 | 0 | 2025 |
| 1177 | Journal of the Franklin Institute | 0016-0032 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 1178 | Journal of the Korean Ceramic Society | 1229-7801 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1179 | Journal of the Science of Food and Agriculture | 0022-5142 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 1180 | Journal of Thermal Biology | 0306-4565 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1181 | Journal of Travel Medicine | 1195-1982 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1182 | Journal of Umm Al-Qura University for Applied Sciences | 1658-8185 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1183 | Journal of Vacuum Science & Technology B Nanotechnology and Microelectronics Materials Processing Measurement and Phenomena | 2166-2746 | Q2 | 1 | 1 | 0 | 0 | 2018 |
| 1184 | Journal \| MESA | – | unranked | 1 | 0 | 1 | 0 | 2021 |
| 1185 | JUCS - Journal of Universal Computer Science | 0948-695X | Q2 | 1 | 1 | 0 | 0 | 2021 |
| 1186 | Kuwait Journal of Science | 2307-4108 | Q2 | 1 | 0 | 1 | 0 | 2017 |
| 1187 | Langmuir | 0743-7463 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1188 | Law State and Telecommunications Review | 1984-8161 | Q3 | 1 | 0 | 0 | 1 | 2024 |
| 1189 | Learning Futures and Emerging Technologies | 2978-5812 | unranked | 1 | 0 | 1 | 0 | 2026 |
| 1190 | Library Herald | 0024-2292 | unranked | 1 | 0 | 1 | 0 | 2025 |
| 1191 | Linear and Multilinear Algebra | 0308-1087 | Q2 | 1 | 1 | 0 | 0 | 2020 |
| 1192 | Logistics | 2305-6290 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1193 | Machine Intelligence Research | 1476-8186 | Q2 | 1 | 0 | 1 | 0 | 2016 |
| 1194 | Machine Learning | 0885-6125 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 1195 | Machine Learning Science and Technology | 2632-2153 | Q1 | 1 | 0 | 0 | 1 | 2024 |
| 1196 | Macromolecular Symposia | 1022-1360 | Q3 | 1 | 1 | 0 | 0 | 2025 |
| 1197 | Management Decision | 0025-1747 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1198 | Management Insight - The Journal of Incisive Analysers | 0973-936X | unranked | 1 | 1 | 0 | 0 | 2018 |
| 1199 | Managerial and Decision Economics | 0143-6570 | Q3 | 1 | 1 | 0 | 0 | 2021 |
| 1200 | Managerial Finance | 0307-4358 | Q2 | 1 | 0 | 1 | 0 | 2024 |
| 1201 | Managing Sport and Leisure | 2375-0472 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1202 | MAPAN | 0970-3950 | Q3 | 1 | 1 | 0 | 0 | 2016 |
| 1203 | Materials Advances | 2633-5409 | Q1 | 1 | 1 | 1 | 0 | 2024 |
| 1204 | Materials Open | 2811-0862 | unranked | 1 | 0 | 1 | 0 | 2024 |
| 1205 | Materials Research Bulletin | 0025-5408 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 1206 | Materials Research Innovations | 1432-8917 | Q3 | 1 | 1 | 0 | 0 | 2025 |
| 1207 | Materials Today Electronics | 2772-9494 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1208 | Mathematical Biosciences | 0025-5564 | Q2 | 1 | 0 | 1 | 0 | 2018 |
| 1209 | Mathematical Modelling and Analysis | 1392-6292 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1210 | Measurement Science and Technology | 0957-0233 | Q2 | 1 | 0 | 0 | 1 | 2025 |
| 1211 | Measurement Sensors | 2665-9174 | Q3 | 1 | 1 | 0 | 0 | 2023 |
| 1212 | Measuring Business Excellence | 1368-3047 | Q2 | 1 | 0 | 1 | 0 | 2024 |
| 1213 | Medical Oncology | 1357-0560 | Q2 | 1 | 1 | 0 | 0 | 2023 |
| 1214 | Memories - Materials Devices Circuits and Systems | 2773-0646 | Q2 | 1 | 0 | 1 | 0 | 2023 |
| 1215 | Methods | 1046-2023 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 1216 | Microbiology | 1350-0872 | Q2 | 1 | 1 | 0 | 0 | 2017 |
| 1217 | Microelectronic Engineering | 0167-9317 | Q2 | 1 | 0 | 1 | 0 | 2018 |
| 1218 | Micron | 0968-4328 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1219 | Mikrotalasna revija | 1450-5835 | Q3 | 1 | 0 | 1 | 0 | 2024 |
| 1220 | MIS Quarterly | 0276-7783 | Q1 | 1 | 0 | 0 | 1 | 2016 |
| 1221 | Molecular Biology Reports | 0301-4851 | Q2 | 1 | 1 | 0 | 0 | 2019 |
| 1222 | Molecular BioSystems | 1742-2051 | Q1 | 1 | 1 | 0 | 0 | 2017 |
| 1223 | Molecular Simulation | 0892-7022 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1224 | MRS Advances | 2059-8521 | Q3 | 1 | 0 | 1 | 0 | 2021 |
| 1225 | Mycopathologia | 0301-486X | Q2 | 1 | 1 | 0 | 0 | 2017 |
| 1226 | NANO | 1793-2920 | Q3 | 1 | 0 | 1 | 0 | 2024 |
| 1227 | Nano Communication Networks | 1878-7789 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 1228 | Nano Express | 2632-959X | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 1229 | Nano-Structures & Nano-Objects | 2352-507X | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1230 | Nanotechnology for Environmental Engineering | 2365-6379 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1231 | Natural Hazards | 0921-030X | Q1 | 1 | 0 | 1 | 0 | 2019 |
| 1232 | Natural Language Processing Journal | 2949-7191 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1233 | Nature Genetics | 1061-4036 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1234 | Nature Human Behaviour | 2397-3374 | Q1 | 1 | 0 | 0 | 1 | 2026 |
| 1235 | Nature Reviews Psychology | 2731-0574 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 1236 | NeuroImage | 1053-8119 | Q1 | 1 | 0 | 0 | 1 | 2021 |
| 1237 | Neuroradiology | 0028-3940 | Q1 | 1 | 0 | 0 | 1 | 2016 |
| 1238 | New Astronomy | 1384-1076 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 1239 | New Journal of Chemistry | 0398-9836 | Q1 | 1 | 1 | 0 | 0 | 2020 |
| 1240 | New Mathematics and Natural Computation | 1793-0057 | Q3 | 1 | 0 | 1 | 0 | 2024 |
| 1241 | New Media & Society | 1461-4448 | Q1 | 1 | 0 | 0 | 1 | 2022 |
| 1242 | New Review of Information Networking | 1361-4576 | Q4 | 1 | 1 | 0 | 0 | 2019 |
| 1243 | Next Nanotechnology | 2949-8295 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 1244 | Next research. | 3050-4759 | unranked | 1 | 0 | 0 | 1 | 2025 |
| 1245 | Nonlinear Dynamics | 0924-090X | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1246 | npj Breast Cancer | 2374-4677 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1247 | Nucleic Acids Research | 0305-1048 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 1248 | OmniScience A Multi-disciplinary Journal | 2231-0398 | unranked | 1 | 1 | 0 | 0 | 2016 |
| 1249 | OncoTargets and Therapy | 1178-6930 | Q2 | 1 | 1 | 0 | 0 | 2016 |
| 1250 | Online Journal of Public Health Informatics | 1947-2579 | Q2 | 1 | 0 | 0 | 1 | 2025 |
| 1251 | Open Access Biostatistics & Bioinformatics | 2578-0247 | unranked | 1 | 1 | 0 | 0 | 2018 |
| 1252 | Open Journal of Social Sciences | 2327-5952 | unranked | 1 | 1 | 0 | 0 | 2024 |
| 1253 | Operations and Supply Chain Management An International Journal | 2579-9363 | Q3 | 1 | 0 | 1 | 0 | 2020 |
| 1254 | Operations Research Forum | 2662-2556 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 1255 | Optical and Quantum Electronics | 0306-8919 | Q2 | 1 | 0 | 1 | 0 | 2024 |
| 1256 | Optical Materials | 0925-3467 | Q1 | 1 | 1 | 0 | 0 | 2020 |
| 1257 | Optik | 0030-4026 | Q2 | 1 | 1 | 0 | 0 | 2021 |
| 1258 | Oriental Journal Of Chemistry | 0970-020X | unranked | 1 | 0 | 1 | 0 | 2025 |
| 1259 | Paladyn Journal of Behavioral Robotics | 2080-9778 | Q4 | 1 | 1 | 0 | 0 | 2016 |
| 1260 | Pattern Recognition | 0031-3203 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 1261 | Pharmacognosy Magazine | 0973-1296 | Q2 | 1 | 1 | 0 | 0 | 2017 |
| 1262 | Phosphorus, sulfur, and silicon and the related elements | 1026-7719 | Q4 | 1 | 1 | 0 | 0 | 2021 |
| 1263 | Phycology | 2673-9410 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1264 | Physica D Nonlinear Phenomena | 0167-2789 | Q1 | 1 | 0 | 1 | 0 | 2024 |
| 1265 | Planetary and Space Science | 0032-0633 | Q2 | 1 | 1 | 0 | 0 | 2021 |
| 1266 | Plant Science Today | 2348-1900 | Q4 | 1 | 1 | 0 | 0 | 2026 |
| 1267 | PLOS Digital Health | 2767-3170 | Q1 | 1 | 0 | 0 | 1 | 2022 |
| 1268 | Polymer | 0032-3861 | Q1 | 1 | 0 | 1 | 0 | 2020 |
| 1269 | Polymer Composites | 0272-8397 | Q2 | 1 | 1 | 0 | 0 | 2021 |
| 1270 | Polymer-Plastics Technology and Materials | 2574-0881 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1271 | Positivity | 1385-1292 | Q2 | 1 | 1 | 0 | 0 | 2021 |
| 1272 | Precision Agriculture | 1385-2256 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 1273 | Present Environment and Sustainable Development | 1843-5971 | unranked | 1 | 1 | 0 | 0 | 2021 |
| 1274 | Probiotics and Antimicrobial Proteins | 1867-1306 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1275 | Proceedings of the Institution of Mechanical Engineers Part O Journal of Risk and Reliability | 1748-006X | Q2 | 1 | 0 | 1 | 0 | 2021 |
| 1276 | Proceedings of the Romanian Academy Series A Mathematics Physics Technical Sciences Information Science | 1454-9069 | Q3 | 1 | 1 | 0 | 0 | 2024 |
| 1277 | Production Planning & Control | 0953-7287 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1278 | Progress in Artificial Intelligence | 2192-6352 | Q2 | 1 | 0 | 1 | 0 | 2018 |
| 1279 | Progress In Electromagnetics Research B | 1937-6472 | Q3 | 1 | 1 | 0 | 0 | 2023 |
| 1280 | Progress In Electromagnetics Research M | 1937-8726 | Q3 | 1 | 0 | 1 | 0 | 2022 |
| 1281 | Property Management | 0263-7472 | Q3 | 1 | 1 | 0 | 0 | 2026 |
| 1282 | Protein Science | 0961-8368 | Q1 | 1 | 1 | 0 | 0 | 2026 |
| 1283 | Public Organization Review | 1566-7170 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 1284 | Purushartha - A Journal of Management Ethics and Spirituality | 0975-024X | Q3 | 1 | 1 | 0 | 0 | 2017 |
| 1285 | Quaestiones Mathematicae | 1607-3606 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 1286 | Quality Education for All | 2976-9310 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1287 | Quantitative Biology | 2095-4689 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 1288 | Quantitative Finance and Economics | 2573-0134 | unranked | 1 | 0 | 1 | 0 | 2020 |
| 1289 | Queen Mary Journal of Intellectual Property | 2045-9807 | Q3 | 1 | 1 | 0 | 0 | 2016 |
| 1290 | Radiation effects and defects in solids | 1026-549X | Q3 | 1 | 1 | 0 | 0 | 2016 |
| 1291 | Radioelectronics and Communications Systems | 0735-2727 | Q3 | 1 | 0 | 0 | 1 | 2019 |
| 1292 | Recent Advances in Computer Science and Communications | 1874-4796 | Q4 | 1 | 1 | 0 | 0 | 2020 |
| 1293 | Recent Advances in Electrical & Electronic Engineering (Formerly Recent Patents on Electrical & Electronic Engineering) | 2352-0965 | Q3 | 1 | 0 | 1 | 0 | 2024 |
| 1294 | Recent Patents on Biotechnology | 1872-2083 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 1295 | Renewable and Sustainable Energy Reviews | 1364-0321 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1296 | Reproduction | 1470-1626 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1297 | Reproductive Toxicology | 0890-6238 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1298 | Research in Transportation Business & Management | 2210-5395 | Q1 | 1 | 0 | 1 | 0 | 2024 |
| 1299 | Review of Behavioral Economics | 2326-6198 | Q3 | 1 | 1 | 0 | 0 | 2026 |
| 1300 | Review of Behavioral Finance | 1940-5979 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1301 | Review of Regional Research | 0173-7600 | Q1 | 1 | 0 | 0 | 1 | 2025 |
| 1302 | Risk Management | 1460-3799 | Q2 | 1 | 1 | 0 | 0 | 2023 |
| 1303 | Risks | 2227-9091 | Q3 | 1 | 1 | 0 | 0 | 2019 |
| 1304 | Robotics | 2218-6581 | Q3 | 1 | 1 | 0 | 0 | 2018 |
| 1305 | Russian Journal of General Chemistry | 1070-3632 | Q4 | 1 | 1 | 0 | 0 | 2024 |
| 1306 | Russian Microelectronics | 1063-7397 | Q4 | 1 | 0 | 1 | 0 | 2026 |
| 1307 | SAGE Open | 2158-2440 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1308 | Science & Technology Indonesia | 2580-4391 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 1309 | Science of Computer Programming | 0167-6423 | Q3 | 1 | 1 | 0 | 0 | 2024 |
| 1310 | Scientific Data | 2052-4463 | Q1 | 1 | 0 | 0 | 1 | 2026 |
| 1311 | Scientific Phone Apps and Mobile Devices | 2364-4958 | unranked | 1 | 0 | 1 | 0 | 2017 |
| 1312 | SeMA Journal | 1575-9822 | Q2 | 1 | 0 | 1 | 0 | 2024 |
| 1313 | Semantic Web | 1570-0844 | Q1 | 1 | 1 | 0 | 0 | 2020 |
| 1314 | Semiconductors | 1063-7826 | Q3 | 1 | 0 | 1 | 0 | 2019 |
| 1315 | Sensor Review | 0260-2288 | Q3 | 1 | 1 | 0 | 0 | 2024 |
| 1316 | Service Oriented Computing and Applications | 1863-2386 | Q2 | 1 | 0 | 1 | 0 | 2026 |
| 1317 | Sexuality & Culture | 1095-5143 | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 1318 | SIAM Journal on Discrete Mathematics | 0895-4801 | Q1 | 1 | 0 | 0 | 1 | 2018 |
| 1319 | Small Methods | 2366-9608 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1320 | Smart Science | 2308-0477 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 1321 | Social Indicators Research | 0303-8300 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1322 | Social Responsibility Journal | 1747-1117 | Q2 | 1 | 0 | 1 | 0 | 2017 |
| 1323 | Social Sciences & Humanities Open | 2590-2911 | Q1 | 1 | 0 | 0 | 1 | 2025 |
| 1324 | Societal Impacts | 2949-6977 | unranked | 1 | 0 | 1 | 0 | 2025 |
| 1325 | Socio-Economic Planning Sciences | 0038-0121 | Q1 | 1 | 0 | 1 | 0 | 2021 |
| 1326 | Socius Sociological Research for a Dynamic World | 2378-0231 | unranked | 1 | 0 | 1 | 0 | 2016 |
| 1327 | Software Practice and Experience | 0038-0644 | Q2 | 1 | 1 | 0 | 0 | 2026 |
| 1328 | Solar Energy | 0038-092X | Q1 | 1 | 0 | 1 | 0 | 2023 |
| 1329 | Solar Energy Materials and Solar Cells | 0927-0248 | Q1 | 1 | 1 | 0 | 0 | 2022 |
| 1330 | South Asia Journal of South Asian Studies | 0085-6401 | Q1 | 1 | 0 | 0 | 1 | 2019 |
| 1331 | South Asian Journal of Business Studies | 2398-628X | Q1 | 1 | 0 | 1 | 0 | 2025 |
| 1332 | South Asian Journal of Human Resources Management | 2322-0937 | Q3 | 1 | 1 | 0 | 0 | 2018 |
| 1333 | Spectrochimica Acta Part A Molecular and Biomolecular Spectroscopy | 1386-1425 | Q1 | 1 | 0 | 0 | 1 | 2025 |
| 1334 | Sports Science & Health Advances | 2583-8296 | unranked | 1 | 0 | 0 | 1 | 2025 |
| 1335 | Structural Chemistry | 1040-0400 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 1336 | Studia Scientiarum Mathematicarum Hungarica | 0081-6906 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 1337 | Studies in Applied Mathematics | 0022-2526 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1338 | Studies in Indian Politics | 2321-0230 | Q2 | 1 | 0 | 0 | 1 | 2026 |
| 1339 | Summerhill | 0972-1452 | unranked | 1 | 0 | 1 | 0 | 2026 |
| 1340 | Supply Chain Forum an International Journal | 1624-6039 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1341 | Surface Review and Letters | 0218-625X | Q3 | 1 | 0 | 0 | 1 | 2025 |
| 1342 | Sustainability | 2071-1050 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1343 | Sustainable Chemistry and Pharmacy | 2352-5541 | Q2 | 1 | 0 | 1 | 0 | 2021 |
| 1344 | Sustainable Energy & Fuels | 2398-4902 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 1345 | Sustainable Futures | 2666-1888 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1346 | Swarm and Evolutionary Computation | 2210-6502 | Q1 | 1 | 1 | 0 | 0 | 2025 |
| 1347 | Symmetry | 2073-8994 | Q2 | 1 | 1 | 0 | 0 | 2018 |
| 1348 | Systems Science & Control Engineering | 2164-2583 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1349 | Technologies | 2227-7080 | unranked | 1 | 1 | 0 | 0 | 2017 |
| 1350 | Telematics and Informatics | 0736-5853 | Q1 | 1 | 0 | 1 | 0 | 2017 |
| 1351 | The AAG Review of Books | 2325-548X | unranked | 1 | 0 | 0 | 1 | 2018 |
| 1352 | The American Journal of Applied Sciences | 2689-0992 | unranked | 1 | 1 | 0 | 0 | 2023 |
| 1353 | The Astrophysical Journal | 0004-637X | Q1 | 1 | 0 | 1 | 0 | 2022 |
| 1354 | The Bombay Technologist | 0067-9925 | unranked | 1 | 0 | 0 | 1 | 2025 |
| 1355 | The European Physical Journal C | 1434-6044 | Q1 | 1 | 1 | 0 | 0 | 2023 |
| 1356 | The European Physical Journal E | 1292-8941 | Q3 | 1 | 0 | 0 | 1 | 2026 |
| 1357 | The International Journal of Advanced Manufacturing Technology | 0268-3768 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1358 | The International Journal of Human Resource Management | 0958-5192 | Q1 | 1 | 1 | 0 | 0 | 2021 |
| 1359 | The International Journal of Logistics Management | 0957-4093 | Q1 | 1 | 0 | 1 | 0 | 2021 |
| 1360 | The Journal of Academic Librarianship | 0099-1333 | Q1 | 1 | 0 | 1 | 0 | 2022 |
| 1361 | The Journal of Chemical Physics | 0021-9606 | Q1 | 1 | 1 | 0 | 0 | 2024 |
| 1362 | The Journal of Microbiology | 1225-8873 | Q2 | 1 | 1 | 0 | 0 | 2022 |
| 1363 | The Journal of Physical Chemistry B | 1520-5207 | Q1 | 1 | 0 | 0 | 1 | 2020 |
| 1364 | The Singapore Economic Review | 0217-5908 | Q3 | 1 | 1 | 0 | 0 | 2020 |
| 1365 | Theoretical and Applied Fracture Mechanics | 0167-8442 | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1366 | Theoretical Chemistry Accounts | 1432-2234 | Q3 | 1 | 0 | 0 | 1 | 2018 |
| 1367 | Theory of Computing Systems | 0025-5661 | Q3 | 1 | 0 | 0 | 1 | 2021 |
| 1368 | Tissue Engineering and Regenerative Medicine | 1738-2696 | Q3 | 1 | 1 | 0 | 0 | 2017 |
| 1369 | Tourism & Management Studies | 2182-8458 | Q2 | 1 | 0 | 1 | 0 | 2023 |
| 1370 | Traitement du signal | 0765-0019 | Q3 | 1 | 1 | 0 | 0 | 2022 |
| 1371 | Transactions in GIS | 1361-1682 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 1372 | Transactions of Indian National Academy of Engineering | 2662-5415 | unranked | 1 | 1 | 0 | 0 | 2020 |
| 1373 | Transactions on Electrical and Electronic Materials | 1229-7607 | Q2 | 1 | 1 | 0 | 0 | 2025 |
| 1374 | Transportation Planning and Technology | 0308-1060 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 1375 | Transportation Research Record Journal of the Transportation Research Board | 0361-1981 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 1376 | Tribology International | 0301-679X | Q1 | 1 | 0 | 1 | 0 | 2026 |
| 1377 | Universal Access in the Information Society | 1615-5289 | Q2 | 1 | 1 | 0 | 0 | 2023 |
| 1378 | Universal Journal of Catalysis Science | 2972-4635 | unranked | 1 | 1 | 0 | 0 | 2023 |
| 1379 | Vikalpa The Journal for Decision Makers | 0256-0909 | Q3 | 1 | 0 | 0 | 1 | 2025 |
| 1380 | Vinayasādhana | 0976-0946 | unranked | 1 | 0 | 0 | 1 | 2026 |
| 1381 | Vision Research | 0042-6989 | Q2 | 1 | 1 | 0 | 0 | 2024 |
| 1382 | Waste Management | 0956-053X | Q1 | 1 | 0 | 1 | 0 | 2019 |
| 1383 | Waves in Random and Complex Media | 1745-5030 | Q2 | 1 | 0 | 1 | 0 | 2022 |
| 1384 | Wellcome Open Research | 2398-502X | Q1 | 1 | 0 | 0 | 1 | 2020 |
| 1385 | Wiley Interdisciplinary Reviews Data Mining and Knowledge Discovery | 1942-4787 | Q1 | 1 | 0 | 0 | 1 | 2023 |
| 1386 | Wireless Communications and Mobile Computing | 1530-8669 | Q2 | 1 | 0 | 1 | 0 | 2022 |
| 1387 | Working with Older People | 1366-3666 | Q3 | 1 | 0 | 1 | 0 | 2022 |
| 1388 | World Journal of Advanced Research and Reviews | 2581-9615 | unranked | 1 | 1 | 0 | 0 | 2025 |
| 1389 | World Review of Science Technology and Sustainable Development | 1741-2234 | Q3 | 1 | 0 | 1 | 0 | 2017 |
| 1390 | World Scientific News | 2392-2192 | unranked | 1 | 0 | 1 | 0 | 2019 |
| 1391 | WSEAS TRANSACTIONS ON BIOLOGY AND BIOMEDICINE | 1109-9518 | Q4 | 1 | 0 | 1 | 0 | 2024 |
| 1392 | X-Ray Spectrometry | 0049-8246 | Q3 | 1 | 1 | 0 | 0 | 2023 |
| 1393 | ZAMM ‐ Journal of Applied Mathematics and Mechanics / Zeitschrift für Angewandte Mathematik und Mechanik | 0044-2267 | Q2 | 1 | 0 | 1 | 0 | 2025 |
| 1394 | Zeitschrift für Naturforschung A | 0340-4811 | Q3 | 1 | 0 | 1 | 0 | 2025 |

## Appendix B — Conferences and proceedings in the dataset

558 named conference venues (proceedings, conference series and proceedings book series such as LNCS / CCIS), 3,042 conference papers. 480 further conference papers have no venue name in OpenAlex. Columns as above; rank = CORE ICORE2026 rank where matched.

| # | Conference / proceedings | CORE rank | Papers | IIITA | ABV | IIITB | Years |
|---|---|---|---|---|---|---|---|
| 1 | Lecture notes in computer science | unranked | 189 | 64 | 15 | 111 | 2016–2026 |
| 2 | Communications in computer and information science | unranked | 118 | 71 | 21 | 26 | 2016–2026 |
| 3 | Lecture notes in networks and systems | unranked | 96 | 56 | 30 | 10 | 2017–2026 |
| 4 | Advances in intelligent systems and computing | unranked | 86 | 46 | 34 | 7 | 2016–2023 |
| 5 | IEEE Conference on Information and Communication Technology (CICT) | unranked | 64 | 39 | 25 | 0 | 2019–2023 |
| 6 | IEEE Uttar Pradesh Section International Conference on Electrical, Electronics and Computer Engineering (UPCON) | unranked | 63 | 55 | 8 | 0 | 2018–2025 |
| 7 | Lecture notes in electrical engineering | unranked | 56 | 34 | 16 | 6 | 2019–2026 |
| 8 | IEEE International Conference on Electronics, Computing and Communication Technologies (CONECCT) | unranked | 55 | 4 | 1 | 50 | 2018–2026 |
| 9 | IEEE India Council International Conference (INDICON) | unranked | 50 | 41 | 3 | 6 | 2017–2025 |
| 10 | IEEE Region 10 Conference (TENCON) | C | 48 | 28 | 11 | 11 | 2016–2025 |
| 11 | IEEE International Conference on Interdisciplinary Approaches in Technology and Management for Social Innovation (IATMSI) | unranked | 46 | 1 | 44 | 2 | 2024–2026 |
| 12 | International Conference on Computing, Communication and Networking Technologies (ICCCNT) | unranked | 43 | 29 | 10 | 4 | 2017–2024 |
| 13 | Conference on Information and Communication Technology (CICT) | unranked | 37 | 18 | 18 | 2 | 2017–2021 |
| 14 | IEEE International Conference on Advanced Networks and Telecommunications Systems | unranked | 29 | 7 | 13 | 9 | 2017–2025 |
| 15 | Materials Today Proceedings | unranked | 29 | 4 | 25 | 0 | 2016–2023 |
| 16 | AIP conference proceedings | unranked | 26 | 4 | 22 | 0 | 2016–2025 |
| 17 | International Symposium on Quality Electronic Design (ISQED) | unranked | 25 | 0 | 0 | 25 | 2021–2026 |
| 18 | International Conference on VLSI Design and International Conference on Embedded Systems (VLSID) | unranked | 24 | 2 | 4 | 18 | 2016–2025 |
| 19 | IEEE International Conference on Computer Vision and Machine Intelligence (CVMI) | unranked | 23 | 7 | 17 | 0 | 2023–2025 |
| 20 | International Conference on Bioinformatics and Systems Biology (BSB) | unranked | 22 | 22 | 0 | 0 | 2016–2018 |
| 21 | IEEE International Geoscience and Remote Sensing Symposium (IGARSS) | C | 20 | 11 | 1 | 8 | 2017–2025 |
| 22 | Procedia Computer Science | unranked | 20 | 12 | 5 | 3 | 2016–2026 |
| 23 | IEEE Bombay Section Signature Conference (IBSSC) | unranked | 19 | 1 | 18 | 0 | 2021 |
| 24 | Innovations in Software Engineering Conference (ISEC) | unranked | 18 | 0 | 8 | 10 | 2017–2026 |
| 25 | International Symposium on VLSI Design and Test (VDAT) | unranked | 18 | 6 | 7 | 5 | 2016–2026 |
| 26 | ACM Great Lakes Symposium on VLSI (GLSVLSI) | unranked | 17 | 0 | 0 | 17 | 2021–2026 |
| 27 | IEEE India Geoscience and Remote Sensing Symposium (InGARSS) | unranked | 15 | 7 | 1 | 7 | 2020–2025 |
| 28 | IEEE International Symposium on Circuits and Systems proceedings | C | 15 | 0 | 0 | 15 | 2022–2026 |
| 29 | Smart innovation, systems and technologies | unranked | 15 | 5 | 5 | 5 | 2016–2026 |
| 30 | IEEE Region 10 Symposium (TENSYMP) | C | 14 | 7 | 2 | 5 | 2016–2024 |
| 31 | IEEE Wireless Communications and Networking Conference | B | 14 | 0 | 0 | 14 | 2018–2026 |
| 32 | IFIP advances in information and communication technology | unranked | 14 | 1 | 0 | 13 | 2017–2026 |
| 33 | International Conference on Electrical Engineering, Computer Science and Informatics (EECSI) | unranked | 14 | 14 | 0 | 0 | 2019–2024 |
| 34 | International Conference on Signal Processing and Communications (SPCOM) | unranked | 14 | 3 | 1 | 11 | 2016–2026 |
| 35 | International Conference on Signal Processing and Integrated Networks (SPIN) | unranked | 14 | 9 | 4 | 1 | 2016–2021 |
| 36 | National Conference on Communications | unranked | 14 | 3 | 2 | 9 | 2017–2026 |
| 37 | OITS International Conference on Information Technology (OCIT) | unranked | 14 | 11 | 2 | 1 | 2021–2025 |
| 38 | IEEE International Symposium on Smart Electronic Systems (iSES) | unranked | 12 | 10 | 0 | 2 | 2018–2024 |
| 39 | International Conference on Advances in Computing, Communications and Informatics (ICACCI) | unranked | 12 | 5 | 2 | 5 | 2016–2018 |
| 40 | International Conference on Communication Systems & Networks (COMSNETS) | unranked | 12 | 2 | 2 | 8 | 2019–2024 |
| 41 | IEEE Consumer Communications & Networking Conference (CCNC) | B | 11 | 0 | 0 | 11 | 2018–2024 |
| 42 | IEEE International Conference on Bioinformatics and Biomedicine (BIBM) | unranked | 11 | 1 | 9 | 1 | 2016–2025 |
| 43 | International Conference on Wireless Communications, Signal Processing and Networking (WiSPNET) | unranked | 11 | 5 | 2 | 4 | 2016–2019 |
| 44 | Proceedings of the Annual International Conference of the IEEE Engineering in Medicine and Biology Society | unranked | 11 | 0 | 0 | 11 | 2020–2023 |
| 45 | IEEE India Council International Subsections Conference (INDISCON) | unranked | 10 | 7 | 1 | 2 | 2021–2025 |
| 46 | IEEE International Conference on Computational Intelligence and Communication Networks (CICN) | unranked | 10 | 5 | 5 | 0 | 2024–2026 |
| 47 | IEEE Microwaves, Antennas, and Propagation Conference (MAPCON) | unranked | 10 | 5 | 5 | 0 | 2022–2025 |
| 48 | Lecture notes on data engineering and communications technologies | unranked | 10 | 7 | 2 | 1 | 2018–2026 |
| 49 | Adaptive Agents and Multi-Agents Systems | unranked | 9 | 0 | 1 | 8 | 2017–2024 |
| 50 | Algorithms for intelligent systems | unranked | 9 | 4 | 5 | 0 | 2019–2023 |
| 51 | IEEE International Conference on Emerging Electronics (ICEE) | unranked | 9 | 7 | 0 | 2 | 2022–2025 |
| 52 | IEEE International Conference on Nanotechnology (IEEE-NANO) | unranked | 9 | 4 | 2 | 3 | 2017–2023 |
| 53 | IEEE Vehicular Technology Conference | B | 9 | 3 | 2 | 4 | 2019–2025 |
| 54 | Euromicro Conference on Digital System Design (DSD) | C | 8 | 0 | 0 | 8 | 2021–2025 |
| 55 | IEEE 5G World Forum (5GWF) | unranked | 8 | 0 | 0 | 8 | 2020–2021 |
| 56 | IEEE Computer Society Annual Symposium on VLSI | unranked | 8 | 2 | 0 | 6 | 2016–2025 |
| 57 | IEEE India Conference | unranked | 8 | 0 | 0 | 8 | 2016 |
| 58 | IEEE International Conference for Convergence in Technology (I2CT) | unranked | 8 | 2 | 5 | 1 | 2019–2023 |
| 59 | IEEE International Symposium on Nanoelectronic and Information Systems (iNIS) | unranked | 8 | 0 | 7 | 1 | 2016–2017 |
| 60 | IEEE Workshop on Recent Advances in Photonics (WRAP) | unranked | 8 | 8 | 0 | 0 | 2023 |
| 61 | International Conference for Convergence in Technology (I2CT) | unranked | 8 | 1 | 3 | 4 | 2017–2021 |
| 62 | International Conference on Computer Communication and Informatics (ICCCI) | unranked | 8 | 2 | 3 | 3 | 2016–2021 |
| 63 | Joint International Conference on Data Science & Management of Data (CODS-COMAD) | unranked | 8 | 0 | 0 | 8 | 2022–2024 |
| 64 | Proceedings - International Conference on Image Processing | B | 8 | 2 | 0 | 6 | 2021–2025 |
| 65 | IEEE International Symposium on Biomedical Imaging (ISBI) | unranked | 7 | 0 | 1 | 6 | 2022–2026 |
| 66 | International Conference for Emerging Technology (INCET) | unranked | 7 | 5 | 2 | 0 | 2020–2024 |
| 67 | Proceedings of IEEE Sensors/Proceedings of IEEE Sensors ... | unranked | 7 | 3 | 1 | 3 | 2018–2025 |
| 68 | 2022 IEEE International Conference on Signal Processing and Communications (SPCOM) | unranked | 6 | 0 | 0 | 6 | 2022 |
| 69 | Asian Conference on Innovation in Technology (ASIANCON) | unranked | 6 | 4 | 2 | 0 | 2021–2023 |
| 70 | CHI Conference on Human Factors in Computing Systems | unranked | 6 | 0 | 0 | 6 | 2017–2025 |
| 71 | IEEE Congress on Evolutionary Computation (CEC) | B | 6 | 6 | 0 | 0 | 2016–2024 |
| 72 | IEEE Future Networks World Forum (FNWF) | unranked | 6 | 0 | 0 | 6 | 2025 |
| 73 | IEEE International Black Sea Conference on Communications and Networking | unranked | 6 | 5 | 0 | 1 | 2020–2025 |
| 74 | IEEE International Conference on Acoustics Speech and Signal Processing | unranked | 6 | 4 | 0 | 2 | 2021–2026 |
| 75 | IEEE International Conference on Electronics, Circuits and Systems (ICECS) | unranked | 6 | 1 | 0 | 5 | 2022–2024 |
| 76 | IEEE International Conference on Industrial and Information Systems (ICIIS) | unranked | 6 | 3 | 3 | 0 | 2017–2026 |
| 77 | IEEE International Students' Conference on Electrical, Electronics and Computer Science (SCEECS) | unranked | 6 | 2 | 4 | 0 | 2018–2026 |
| 78 | IEEE International Symposium on Personal, Indoor and Mobile Radio Communications (PIMRC) | B | 6 | 0 | 3 | 3 | 2022–2026 |
| 79 | Indian Control Conference | unranked | 6 | 1 | 0 | 5 | 2019–2025 |
| 80 | International Conference for Advancement in Technology (ICONAT) | unranked | 6 | 2 | 4 | 0 | 2022 |
| 81 | International Conference on AI-ML Systems (AIMLSystems) | unranked | 6 | 0 | 0 | 6 | 2022–2024 |
| 82 | International Conference on Cloud Computing, Data Science & Engineering (Confluence) | unranked | 6 | 2 | 4 | 0 | 2018–2023 |
| 83 | International Conference on Theory and Practice of Electronic Governance | unranked | 6 | 0 | 0 | 6 | 2017–2023 |
| 84 | Lecture notes in energy | unranked | 6 | 6 | 0 | 0 | 2023 |
| 85 | ACM International Conference on Multimodal Interaction (ICMI) | B | 5 | 0 | 0 | 5 | 2016–2018 |
| 86 | European Signal Processing Conference (EUSIPCO) | unranked | 5 | 0 | 0 | 5 | 2019–2022 |
| 87 | Frontiers in Optics + Laser Science (FiO, LS) | unranked | 5 | 5 | 0 | 0 | 2020–2022 |
| 88 | IEEE International Conference on Communication Systems and Network Technologies (CSNT) | unranked | 5 | 3 | 2 | 0 | 2023–2026 |
| 89 | IEEE International India Geoscience and Remote Sensing Symposium (InGARSS) | unranked | 5 | 1 | 0 | 4 | 2021 |
| 90 | International Conference on Distributed Computing and Networking (ICDCN) | unranked | 5 | 3 | 0 | 2 | 2017–2025 |
| 91 | International Conference on Information and Communication Technologies and Development (ICTD) | C | 5 | 0 | 0 | 5 | 2016–2020 |
| 92 | International Conference on Intelligent Computing and Control Systems (ICICCS) | unranked | 5 | 3 | 2 | 0 | 2017–2018 |
| 93 | International Conference on Microwave, Antenna and Communication (MAC) | unranked | 5 | 0 | 5 | 0 | 2023–2025 |
| 94 | International Joint Conference on Biomedical Engineering Systems and Technologies (BIOSTEC) | unranked | 5 | 0 | 0 | 5 | 2019–2026 |
| 95 | Proceedings of the AAAI Conference on Artificial Intelligence | A* | 5 | 1 | 2 | 2 | 2019–2026 |
| 96 | ACM Web Science Conference (WebSci) | unranked | 4 | 0 | 0 | 4 | 2021 |
| 97 | Globecom | unranked | 4 | 1 | 0 | 3 | 2018–2025 |
| 98 | IEEE Asia Pacific Conference on Circuits and Systems (APCCAS) | unranked | 4 | 2 | 1 | 1 | 2020–2023 |
| 99 | IEEE Asia-Pacific Microwave Conference (APMC) | unranked | 4 | 3 | 0 | 1 | 2017–2024 |
| 100 | IEEE Guwahati Subsection Conference (GCON) | unranked | 4 | 0 | 4 | 0 | 2025–2026 |
| 101 | IEEE International Advance Computing Conference | unranked | 4 | 1 | 3 | 0 | 2017–2018 |
| 102 | IEEE International Conference on Big Data (BigData) | B | 4 | 2 | 0 | 2 | 2020–2024 |
| 103 | IEEE International Conference on Computing, Communication and Automation (ICCCA) | unranked | 4 | 1 | 3 | 0 | 2025 |
| 104 | IEEE International Conference on Computing, Power and Communication Technologies (IC2PCT) | unranked | 4 | 0 | 4 | 0 | 2020–2024 |
| 105 | IEEE International Symposium on Embedded Multicore/Many-core Systems-on-Chip (MCSoC) | unranked | 4 | 2 | 0 | 2 | 2021–2022 |
| 106 | IEEE Silchar Subsection Conference (SILCON) | unranked | 4 | 4 | 1 | 0 | 2022–2023 |
| 107 | International Conference on Computational Techniques in Information and Communication Technologies | unranked | 4 | 1 | 3 | 0 | 2016 |
| 108 | International Conference on Emerging Techniques in Computational Intelligence (ICETCI) | unranked | 4 | 1 | 3 | 0 | 2025–2026 |
| 109 | International Conference on Image Information Processing (ICIIP) | unranked | 4 | 2 | 0 | 2 | 2017–2023 |
| 110 | International Conference on Information Systems and Computer Networks (ISCON) | unranked | 4 | 3 | 1 | 0 | 2019–2023 |
| 111 | INTERNATIONAL CONFERENCE ON MULTIMODAL INTERACTION | B | 4 | 0 | 0 | 4 | 2020–2026 |
| 112 | International Conference on Parallel, Distributed and Grid Computing (PDGC) | unranked | 4 | 3 | 1 | 1 | 2016–2020 |
| 113 | International Conference Radioelektronika | unranked | 4 | 2 | 1 | 1 | 2024–2025 |
| 114 | International Electrical Engineering Congress (iEECON) | unranked | 4 | 4 | 0 | 0 | 2026 |
| 115 | International Joint Conference on Computer Vision, Imaging and Computer Graphics Theory and Applications (VISIGRAPP) | unranked | 4 | 1 | 1 | 2 | 2020–2025 |
| 116 | IOP Conference Series Materials Science and Engineering | unranked | 4 | 0 | 4 | 0 | 2021–2022 |
| 117 | Journal of Physics Conference Series | unranked | 4 | 2 | 2 | 0 | 2021–2023 |
| 118 | Lecture notes of the Institute for Computer Sciences, Social Informatics and Telecommunications Engineering | unranked | 4 | 2 | 0 | 2 | 2018–2024 |
| 119 | 2020 IEEE International Systems Conference (SysCon) | unranked | 3 | 0 | 0 | 3 | 2022–2026 |
| 120 | 2022 IEEE 18th International Conference on Automation Science and Engineering (CASE) | unranked | 3 | 2 | 0 | 1 | 2020–2022 |
| 121 | ACM SIGCAS Conference on Computing and Sustainable Societies (COMPASS) | C | 3 | 0 | 0 | 3 | 2019–2020 |
| 122 | ACM Symposium on Principles of Distributed Computing (PODC) | A* | 3 | 0 | 0 | 3 | 2018–2026 |
| 123 | ACM/SIGAPP Symposium on Applied Computing (SAC) | unranked | 3 | 0 | 0 | 3 | 2022–2026 |
| 124 | Advanced Materials Proceedings | unranked | 3 | 2 | 1 | 0 | 2016–2018 |
| 125 | IEEE Applied Electromagnetics Conference | unranked | 3 | 3 | 0 | 1 | 2017 |
| 126 | IEEE Applied Sensing Conference (APSCON) | unranked | 3 | 1 | 0 | 2 | 2023–2026 |
| 127 | IEEE Conference on Control Technology and Applications (CCTA) | unranked | 3 | 0 | 0 | 3 | 2019–2022 |
| 128 | IEEE Intelligent Vehicles Symposium | B | 3 | 0 | 1 | 2 | 2018–2026 |
| 129 | IEEE International Conference on High Performance Computing, Data and Analytics Workshop (HiPCW) | unranked | 3 | 1 | 0 | 2 | 2024–2025 |
| 130 | IEEE International Conference on Multimedia Big Data | unranked | 3 | 2 | 0 | 1 | 2020 |
| 131 | IEEE International Conference on Signal Processing, Informatics, Communication and Energy Systems (SPICES) | unranked | 3 | 1 | 1 | 1 | 2017–2024 |
| 132 | IEEE International Requirements Engineering Conference (RE) | A | 3 | 0 | 2 | 1 | 2020–2025 |
| 133 | IEEE International System-on-Chip Conference (SOCC) | unranked | 3 | 0 | 0 | 3 | 2024–2025 |
| 134 | IEEE International Ultrasonics Symposium | unranked | 3 | 3 | 0 | 0 | 2016–2023 |
| 135 | IEEE International Workshop on Machine Learning for Signal Processing (MLSP) | unranked | 3 | 0 | 0 | 3 | 2023 |
| 136 | IEEE Mediterranean Electrotechnical Conference (MELECON) | unranked | 3 | 1 | 0 | 2 | 2022–2024 |
| 137 | IEEE Uttar Pradesh Section International Conference on Electrical, Computer and Electronics (UPCON) | unranked | 3 | 2 | 0 | 2 | 2017 |
| 138 | Indian Conference on Computer Vision, Graphics and Image Processing | unranked | 3 | 0 | 0 | 3 | 2018–2021 |
| 139 | International Computer Science and Engineering Conference | unranked | 3 | 3 | 0 | 0 | 2023 |
| 140 | International conference natural language processing | B | 3 | 2 | 1 | 0 | 2016–2017 |
| 141 | International Conference on Advances in Electrical, Computing, Communication and Sustainable Technologies (ICAECT) | unranked | 3 | 3 | 0 | 0 | 2021–2024 |
| 142 | International Conference on Blockchain Computing and Applications (BCCA) | unranked | 3 | 3 | 0 | 0 | 2021–2023 |
| 143 | International Conference on Computational Intelligence & Communication Technology (CICT) | unranked | 3 | 2 | 1 | 0 | 2016–2018 |
| 144 | International Conference on Computational Intelligence and Communication Technologies (CCICT) | unranked | 3 | 0 | 3 | 0 | 2021–2022 |
| 145 | International Conference on Computer and Automation Engineering | unranked | 3 | 1 | 0 | 2 | 2023–2024 |
| 146 | International Conference on Consumer Electronics | unranked | 3 | 1 | 0 | 2 | 2018–2026 |
| 147 | International Conference on Developments in eSystems Engineering (DeSE) | C | 3 | 0 | 3 | 0 | 2016–2020 |
| 148 | International Conference on Information Networking | unranked | 3 | 1 | 1 | 1 | 2017–2019 |
| 149 | International Conference on Intelligent Computing, Instrumentation and Control Technologies (ICICICT) | unranked | 3 | 3 | 0 | 0 | 2022 |
| 150 | International Conference on Intelligent Technologies (CONIT) | unranked | 3 | 1 | 2 | 0 | 2021–2022 |
| 151 | International Conference on Internet of Things: Systems, Management and Security (IOTSMS) | unranked | 3 | 3 | 0 | 0 | 2023–2024 |
| 152 | International Conference on Smart Computing and Communications (ICSCC) | unranked | 3 | 3 | 0 | 0 | 2023 |
| 153 | International Joint Conference on Artificial Intelligence | A* | 3 | 0 | 0 | 3 | 2019–2023 |
| 154 | International SoC Design Conference | unranked | 3 | 0 | 0 | 3 | 2020–2021 |
| 155 | International Symposium on Embedded Computing and System Design (ISED) | unranked | 3 | 0 | 0 | 3 | 2016–2019 |
| 156 | International Workshop on Semantic Evaluation (SemEval) | unranked | 3 | 2 | 1 | 0 | 2021–2024 |
| 157 | Proceedings - IEEE International Conference on Robotics and Automation/Proceedings | A* | 3 | 1 | 0 | 2 | 2016–2023 |
| 158 | Proceedings - International Conference on Tools with Artificial Intelligence, TAI | unranked | 3 | 0 | 1 | 2 | 2024–2025 |
| 159 | Proceedings of the AAAI/ACM Conference on AI Ethics and Society | C | 3 | 0 | 0 | 3 | 2025 |
| 160 | Proceedings of the IEEE National Radar Conference | unranked | 3 | 0 | 0 | 3 | 2021–2023 |
| 161 | Springer proceedings in physics | unranked | 3 | 1 | 2 | 0 | 2019–2022 |
| 162 | Studies in autonomic, data-driven and industrial computing | unranked | 3 | 2 | 0 | 1 | 2024 |
| 163 | URSI Asia-Pacific Radio Science Conference | unranked | 3 | 3 | 0 | 0 | 2016–2019 |
| 164 | 2006 14th Mediterranean Conference on Control and Automation | unranked | 2 | 2 | 0 | 0 | 2022 |
| 165 | 2022 IEEE 72nd Electronic Components and Technology Conference (ECTC) | unranked | 2 | 0 | 1 | 1 | 2017–2020 |
| 166 | ACM Conference on Computer-Supported Cooperative Work and Social Computing (CSCW) | unranked | 2 | 0 | 0 | 2 | 2021–2022 |
| 167 | ACM International Conference on Information and Knowledge Management (CIKM) | A | 2 | 0 | 0 | 2 | 2023–2025 |
| 168 | ACM Symposium on Applied Computing | C | 2 | 0 | 0 | 2 | 2021 |
| 169 | Annals of Computer Science and Information Systems | unranked | 2 | 2 | 0 | 0 | 2017–2020 |
| 170 | Asia and South Pacific Design Automation Conference (ASP-DAC) | B | 2 | 0 | 0 | 2 | 2024–2025 |
| 171 | Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL) | unranked | 2 | 1 | 1 | 0 | 2025 |
| 172 | Conference of the Oriental COCOSDA International Committee for the Co-ordination and Standardisation of Speech Databases and Assessment Techniques (O-COCOSDA) | unranked | 2 | 2 | 0 | 0 | 2023 |
| 173 | Conference on Lasers and Electro-Optics Pacific Rim (CLEO-PR) | unranked | 2 | 2 | 0 | 0 | 2022 |
| 174 | Conference proceedings | unranked | 2 | 1 | 0 | 1 | 2016 |
| 175 | Conference record | unranked | 2 | 0 | 2 | 0 | 2023–2025 |
| 176 | Conference record of the IEEE Photovoltaic Specialists Conference | unranked | 2 | 2 | 0 | 0 | 2017–2019 |
| 177 | Devices for Integrated Circuit (DevIC) | unranked | 2 | 2 | 0 | 0 | 2021–2025 |
| 178 | Educational Data Mining | B | 2 | 0 | 0 | 2 | 2017–2019 |
| 179 | Extended Abstracts of the CHI Conference on Human Factors in Computing Systems (CHI EA) | unranked | 2 | 1 | 0 | 1 | 2021–2025 |
| 180 | IAPR Asian Conference on Pattern Recognition (ACPR) | unranked | 2 | 0 | 0 | 2 | 2017 |
| 181 | IEEE ... International Conference on Cloud Computing | B | 2 | 0 | 1 | 1 | 2022 |
| 182 | IEEE Conference on Artificial Intelligence (CAI) | A* | 2 | 2 | 0 | 0 | 2024–2026 |
| 183 | IEEE Conference on Computational Intelligence in Bioinformatics and Computational Biology (CIBCB) | C | 2 | 1 | 0 | 1 | 2016–2021 |
| 184 | IEEE Dallas Circuits and Systems Conference (DCAS) | unranked | 2 | 0 | 0 | 2 | 2026 |
| 185 | IEEE Design Methodologies Conference (DMC) | unranked | 2 | 0 | 0 | 2 | 2024–2025 |
| 186 | IEEE Electrical Design of Advanced Packaging and Systems Symposium (EDAPS) | unranked | 2 | 0 | 2 | 0 | 2020–2023 |
| 187 | IEEE Electronics Packaging Technology Conference (EPTC) | unranked | 2 | 0 | 2 | 0 | 2020–2025 |
| 188 | IEEE Global Conference for Advancement in Technology (GCAT) | unranked | 2 | 1 | 0 | 1 | 2022–2025 |
| 189 | IEEE Global Conference on Consumer Electronics (GCCE) | unranked | 2 | 2 | 0 | 0 | 2019–2025 |
| 190 | IEEE Globecom Workshops (GC Wkshps) | unranked | 2 | 0 | 0 | 2 | 2023–2025 |
| 191 | IEEE Indian Conference on Antennas and Propagation (InCAP) | unranked | 2 | 2 | 0 | 0 | 2019–2021 |
| 192 | IEEE Information Theory Workshop (ITW) | unranked | 2 | 0 | 0 | 2 | 2021 |
| 193 | IEEE International Conference of Electron Devices Society Kolkata Chapter (EDKCON) | unranked | 2 | 2 | 0 | 0 | 2022 |
| 194 | IEEE International Conference on Advanced Learning Technologies (ICALT) | B | 2 | 0 | 0 | 2 | 2018–2026 |
| 195 | IEEE International Conference on Advanced Video and Signal Based Surveillance (AVSS) | B | 2 | 2 | 0 | 0 | 2021 |
| 196 | IEEE International Conference on Big Data and Smart Computing (BigComp) | unranked | 2 | 0 | 0 | 2 | 2024 |
| 197 | IEEE International Conference on Contemporary Computing and Communications (InC4) | unranked | 2 | 0 | 1 | 1 | 2023–2024 |
| 198 | IEEE International Conference on Electro Information Technology | unranked | 2 | 0 | 0 | 2 | 2017 |
| 199 | IEEE International Conference on Machine Learning and Applications (ICMLA) | C | 2 | 1 | 0 | 1 | 2017–2020 |
| 200 | IEEE International Conference on MOOCs, Innovation and Technology in Education (MITE) | unranked | 2 | 0 | 0 | 2 | 2016 |
| 201 | IEEE International Conference on Recent Trends in Electronics, Information & Communication Technology | unranked | 2 | 1 | 0 | 1 | 2016 |
| 202 | IEEE International Conference on Robot and Human Interactive Communication (RO-MAN) | B | 2 | 1 | 0 | 1 | 2023 |
| 203 | IEEE International Conference on Semantic Computing (ICSC) | unranked | 2 | 0 | 0 | 2 | 2021–2023 |
| 204 | IEEE International Conference on Simulation, Modeling, and Programming for Autonomous Robots (SIMPAR) | unranked | 2 | 2 | 0 | 0 | 2018 |
| 205 | IEEE International Conference on Smart Computing | B | 2 | 2 | 0 | 1 | 2018–2019 |
| 206 | IEEE International Conference on Sustainable Energy and Future Electric Transportation (SEFET) | unranked | 2 | 1 | 1 | 0 | 2023–2025 |
| 207 | IEEE International Conference on Technology, Engineering, Management for Societal Impact using Marketing, Entrepreneurship and Talent (TEMSMET) | unranked | 2 | 0 | 2 | 0 | 2025 |
| 208 | IEEE International Parallel and Distributed Processing Symposium Workshops (IPDPSW) | unranked | 2 | 0 | 0 | 2 | 2017–2024 |
| 209 | IEEE Latin America Symposium on Circuits and Systems (LASCAS) | unranked | 2 | 0 | 0 | 2 | 2023 |
| 210 | IEEE Latin-American Conference on Communications | unranked | 2 | 2 | 0 | 0 | 2020 |
| 211 | IEEE Region Humanitarian Technology Conference | unranked | 2 | 0 | 1 | 1 | 2021–2024 |
| 212 | IEEE Students Conference on Engineering and Systems (SCES) | unranked | 2 | 2 | 0 | 0 | 2019 |
| 213 | IEEE Symposium Series on Computational Intelligence (SSCI) | unranked | 2 | 0 | 0 | 2 | 2018–2022 |
| 214 | IEEE Technology & Engineering Management Conference (TEMSCON) | unranked | 2 | 1 | 0 | 1 | 2017–2020 |
| 215 | IEEE World AI IoT Congress (AIIoT) | unranked | 2 | 2 | 0 | 0 | 2022 |
| 216 | IEEE World Conference on Applied Intelligence and Computing (AIC) | unranked | 2 | 1 | 1 | 0 | 2022 |
| 217 | IEEE World Forum on Internet of Things (WF-IoT) | unranked | 2 | 0 | 0 | 2 | 2019–2021 |
| 218 | IFAC-PapersOnLine | unranked | 2 | 0 | 0 | 2 | 2016–2023 |
| 219 | India Software Engineering Conference | unranked | 2 | 0 | 0 | 2 | 2016 |
| 220 | International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR) | A* | 2 | 0 | 1 | 1 | 2021–2024 |
| 221 | International Conference on Advanced Communication Technologies and Networking (CommNet) | unranked | 2 | 2 | 0 | 0 | 2021–2023 |
| 222 | International Conference on Advanced Computing and Communication Systems (ICACCS) | unranked | 2 | 1 | 1 | 0 | 2021–2024 |
| 223 | International Conference on Advances in Computing and Communication Engineering | unranked | 2 | 0 | 1 | 1 | 2016–2018 |
| 224 | International Conference on Affective Computing and Intelligent Interaction Workshops and Demos (ACIIW) | unranked | 2 | 0 | 0 | 2 | 2017–2026 |
| 225 | International Conference on Artificial Intelligence for Innovations in Healthcare Industries (ICAIIHI) | unranked | 2 | 0 | 2 | 0 | 2023 |
| 226 | International Conference on Artificial Intelligence in Information and Communication (ICAIIC) | unranked | 2 | 0 | 0 | 2 | 2021–2023 |
| 227 | International Conference on Automation, Robotics and Applications | unranked | 2 | 0 | 0 | 2 | 2023–2024 |
| 228 | International Conference on Circuits, Power and Intelligent Systems (CCPIS) | unranked | 2 | 0 | 2 | 0 | 2025 |
| 229 | International Conference on Computing for Sustainable Global Development | unranked | 2 | 2 | 0 | 0 | 2020–2026 |
| 230 | International Conference on Computing, Communication and Automation | unranked | 2 | 2 | 0 | 0 | 2017 |
| 231 | International Conference on Contemporary Computing | unranked | 2 | 1 | 1 | 0 | 2017–2019 |
| 232 | International Conference on Control, Automation and Robotics (ICCAR) | unranked | 2 | 2 | 1 | 0 | 2020–2026 |
| 233 | International Conference on Control, Automation and Systems (ICCAS) | unranked | 2 | 0 | 0 | 2 | 2025 |
| 234 | International Conference on Devices, Circuits and Systems (ICDCS) | unranked | 2 | 1 | 1 | 0 | 2016–2018 |
| 235 | International Conference on Electrical, Computer and Communication Technologies (ICECCT) | unranked | 2 | 0 | 1 | 1 | 2017–2019 |
| 236 | International Conference on Electrical, Computer and Energy Technologies (ICECET) | unranked | 2 | 1 | 1 | 0 | 2021–2026 |
| 237 | International Conference on Electrical, Electronics, Communication, Computer Technologies and Optimization Techniques (ICEECCOT) | unranked | 2 | 2 | 0 | 0 | 2021 |
| 238 | International Conference on Emerging Systems and Intelligent Computing (ESIC) | unranked | 2 | 0 | 2 | 0 | 2025 |
| 239 | International Conference on Engineering and Emerging Technologies (ICEET) | unranked | 2 | 1 | 0 | 1 | 2022–2024 |
| 240 | International Conference on Future Internet of Things and Cloud (FiCloud) | unranked | 2 | 0 | 0 | 2 | 2021 |
| 241 | International Conference on I-SMAC (IoT in Social, Mobile, Analytics and Cloud) (I-SMAC) | unranked | 2 | 0 | 1 | 1 | 2019–2024 |
| 242 | International Conference on Information Technologies (InfoTech) | unranked | 2 | 2 | 0 | 0 | 2023 |
| 243 | International Conference on Intelligent Communication and Computational Techniques (ICCT) | unranked | 2 | 1 | 0 | 1 | 2019–2023 |
| 244 | International Conference on Intelligent Systems and Control | unranked | 2 | 0 | 1 | 1 | 2016–2017 |
| 245 | International Conference on Intelligent Systems and Embedded Design (ISED) | unranked | 2 | 1 | 1 | 0 | 2025 |
| 246 | International Conference on Intelligent Systems, Metaheuristics & Swarm Intelligence (ISMSI) | unranked | 2 | 0 | 2 | 0 | 2024–2026 |
| 247 | International Conference on Inventive Computation Technologies (ICICT) | unranked | 2 | 1 | 1 | 0 | 2021–2026 |
| 248 | International Conference on Inventive Research in Computing Applications (ICIRCA) | unranked | 2 | 2 | 0 | 0 | 2022 |
| 249 | International Conference on Issues and Challenges in Intelligent Computing Techniques | unranked | 2 | 0 | 2 | 0 | 2019 |
| 250 | International Conference on Machine Intelligence for GeoAnalytics and Remote Sensing (MIGARS) | unranked | 2 | 1 | 0 | 1 | 2024–2026 |
| 251 | International Conference on Optical MEMS and Nanophotonics | unranked | 2 | 2 | 0 | 0 | 2024 |
| 252 | International Conference on Research in Computational Intelligence and Communication Networks (ICRCICN) | unranked | 2 | 1 | 1 | 0 | 2016–2025 |
| 253 | International Conference on Smart Applications, Communications and Networking (SmartNets) | unranked | 2 | 0 | 0 | 2 | 2024–2026 |
| 254 | International Conference on Trends in Electronics and Informatics (ICOEI) | unranked | 2 | 2 | 0 | 0 | 2019–2021 |
| 255 | International Conference on Trends in Quantum Computing and Emerging Business Technologies (TQCEBT) | unranked | 2 | 2 | 0 | 0 | 2026 |
| 256 | International Joint Conference on Computational Intelligence | C | 2 | 0 | 0 | 2 | 2022–2023 |
| 257 | International Joint Conference on Knowledge Discovery, Knowledge Engineering and Knowledge Management | C | 2 | 0 | 0 | 2 | 2022–2025 |
| 258 | International Technical Conference on Circuits/Systems, Computers and Communications (ITC-CSCC) | unranked | 2 | 2 | 0 | 0 | 2021–2022 |
| 259 | Lecture notes in computational vision and biomechanics | unranked | 2 | 0 | 2 | 0 | 2017 |
| 260 | Lecture notes in educational technology | unranked | 2 | 1 | 0 | 1 | 2024–2025 |
| 261 | Lecture notes in intelligent transportation and infrastructure | unranked | 2 | 2 | 0 | 0 | 2025 |
| 262 | Leibniz international proceedings in informatics | unranked | 2 | 0 | 0 | 2 | 2020–2026 |
| 263 | Open Conference Proceedings | unranked | 2 | 2 | 0 | 0 | 2024–2025 |
| 264 | OPJU International Technology Conference on Smart Computing for Innovation and Advancement in Industry (OTCON) | unranked | 2 | 1 | 1 | 0 | 2025–2026 |
| 265 | Proceedings - Asia Pacific Software Engineering Conference/Proceedings | unranked | 2 | 0 | 2 | 0 | 2019–2022 |
| 266 | Proceedings of SPIE, the International Society for Optical Engineering/Proceedings of SPIE | unranked | 2 | 1 | 0 | 1 | 2017 |
| 267 | Proceedings, IEEE International Conference on Computer Design/Proceedings - IEEE International Conference on Computer Design | C | 2 | 0 | 0 | 2 | 2022–2023 |
| 268 | Proceedings/Proceedings of the ... International Conference on Software Engineering and Knowledge Engineering | C | 2 | 1 | 0 | 1 | 2022–2023 |
| 269 | Springer proceedings in business and economics | unranked | 2 | 2 | 0 | 0 | 2017–2025 |
| 270 | Springer proceedings in mathematics & statistics | unranked | 2 | 2 | 0 | 0 | 2023 |
| 271 | Student Research Workshop .../Proceedings of the Student Research Workshop ... | unranked | 2 | 0 | 0 | 2 | 2021 |
| 272 | Studies in computational intelligence | unranked | 2 | 1 | 0 | 1 | 2016–2018 |
| 273 | URSI Regional Conference on Radio Science (URSI-RCRS) | unranked | 2 | 2 | 0 | 0 | 2020 |
| 274 | Workshop on Recent Advances in Photonics (WRAP) | unranked | 2 | 2 | 0 | 0 | 2019–2022 |
| 275 | 2016 SAI Computing Conference (SAI) | unranked | 1 | 0 | 1 | 0 | 2016 |
| 276 | 2022 IEEE 20th International Conference on Industrial Informatics (INDIN) | C | 1 | 0 | 1 | 0 | 2024 |
| 277 | ACM Conference on Fairness, Accountability, and Transparency (FAccT) | unranked | 1 | 0 | 0 | 1 | 2026 |
| 278 | ACM International Conference on Intelligent Virtual Agents (IVA) | B | 1 | 0 | 0 | 1 | 2020 |
| 279 | ACM International Conference on PErvasive Technologies Related to Assistive Environments (PETRA) | unranked | 1 | 0 | 0 | 1 | 2019 |
| 280 | ACM International Conference on Web Search and Data Mining (WSDM) | A | 1 | 0 | 0 | 1 | 2019 |
| 281 | ACM SIGCAS/SIGCHI Conference on Computing and Sustainable Societies (COMPASS) | C | 1 | 0 | 0 | 1 | 2022 |
| 282 | ACM Symposium on Eye Tracking Research and Applications (ETRA) | B | 1 | 0 | 0 | 1 | 2025 |
| 283 | ACM Web Conference (WWW) | unranked | 1 | 1 | 0 | 0 | 2026 |
| 284 | ACM/SPEC International Conference on Performance Engineering (ICPE) | B | 1 | 0 | 0 | 1 | 2026 |
| 285 | Advances in Robotics - International Conference of The Robotics Society (AIR) | unranked | 1 | 1 | 0 | 0 | 2023 |
| 286 | Allerton Conference on Communication, Control, and Computing | unranked | 1 | 0 | 0 | 1 | 2023 |
| 287 | Americas Conference on Information Systems | unranked | 1 | 0 | 0 | 1 | 2021 |
| 288 | Annual Meeting of the Association for Computational Linguistics (ACL) | A* | 1 | 1 | 0 | 0 | 2026 |
| 289 | Applied Networking Research Workshop (ANRW) | unranked | 1 | 1 | 0 | 0 | 2026 |
| 290 | Asia-Pacific Conference on Intelligent Robot Systems (ACIRS) | unranked | 1 | 1 | 0 | 0 | 2018 |
| 291 | Asian Conference on Machine Learning | C | 1 | 0 | 0 | 1 | 2020 |
| 292 | BlackboxNLP Workshop on Analyzing and Interpreting Neural Networks for NLP (BlackboxNLP) | unranked | 1 | 0 | 0 | 1 | 2022 |
| 293 | CHI Conference on Human Factors in Computing Systems Extended Abstracts | unranked | 1 | 1 | 0 | 0 | 2022 |
| 294 | Clinical Natural Language Processing Workshop (ClinicalNLP) | unranked | 1 | 0 | 0 | 1 | 2023 |
| 295 | Companion Publication of the International Conference on Multimodal Interaction (ICMI Companion) | unranked | 1 | 0 | 0 | 1 | 2021 |
| 296 | Computer Science and Electronic Engineering Conference | unranked | 1 | 0 | 1 | 0 | 2016 |
| 297 | Conference of the European Chapter of the Association for Computational Linguistics | unranked | 1 | 1 | 0 | 0 | 2026 |
| 298 | Conference on Lasers and Electro-Optics | unranked | 1 | 1 | 0 | 0 | 2022 |
| 299 | Conference on Management of Data | unranked | 1 | 0 | 0 | 1 | 2016 |
| 300 | Conference on Robots and Vision (CRV) | unranked | 1 | 0 | 0 | 1 | 2023 |
| 301 | Data-intensive research | unranked | 1 | 0 | 1 | 0 | 2024 |
| 302 | Distributed Simulation and Real-Time Applications | unranked | 1 | 0 | 0 | 1 | 2018 |
| 303 | Electronic Imaging | unranked | 1 | 0 | 0 | 1 | 2023 |
| 304 | Empirical Methods in Natural Language Processing | A* | 1 | 0 | 0 | 1 | 2021 |
| 305 | European Conference on e-Learning | unranked | 1 | 0 | 0 | 1 | 2026 |
| 306 | European Control Conference (ECC) | unranked | 1 | 0 | 0 | 1 | 2021 |
| 307 | European Microwave Conference (EuMC) | unranked | 1 | 1 | 0 | 0 | 2016 |
| 308 | Green energy and technology | unranked | 1 | 1 | 0 | 0 | 2024 |
| 309 | IEEE ... International Conference on Data Mining workshops | unranked | 1 | 0 | 0 | 1 | 2018 |
| 310 | IEEE Annual Computers, Software, and Applications Conference (COMPSAC) | B | 1 | 1 | 0 | 0 | 2024 |
| 311 | IEEE Automatic Speech Recognition and Understanding Workshop (ASRU) | unranked | 1 | 0 | 0 | 1 | 2019 |
| 312 | IEEE Bangalore Humanitarian Technology Conference (B-HTC) | unranked | 1 | 0 | 0 | 1 | 2025 |
| 313 | IEEE Conference on Electrical Performance of Electronic Packaging and Systems (EPEPS) | unranked | 1 | 0 | 1 | 0 | 2020 |
| 314 | IEEE Conference on Service-Oriented Computing and Applications (SOCA) | unranked | 1 | 0 | 0 | 1 | 2018 |
| 315 | IEEE Conference on Standards for Communications and Networking | unranked | 1 | 0 | 1 | 0 | 2024 |
| 316 | IEEE Distributed Computing, VLSI, Electrical Circuits and Robotics (DISCOVER) | unranked | 1 | 0 | 0 | 1 | 2016 |
| 317 | IEEE Electron Devices Technology & Manufacturing Conference (EDTM) | unranked | 1 | 1 | 0 | 0 | 2024 |
| 318 | IEEE Gaming, Entertainment, and Media Conference (GEM) | unranked | 1 | 0 | 0 | 1 | 2023 |
| 319 | IEEE Global Conference on Computing, Power and Communication Technologies (GlobConPT) | unranked | 1 | 0 | 1 | 0 | 2022 |
| 320 | IEEE IAS Global Conference on Emerging Technologies (GlobConET) | unranked | 1 | 1 | 0 | 0 | 2022 |
| 321 | IEEE Industrial Electronics and Applications Conference (IEACon) | unranked | 1 | 0 | 1 | 0 | 2023 |
| 322 | IEEE International Carnahan Conference on Security Technology (ICCST) | unranked | 1 | 1 | 0 | 0 | 2023 |
| 323 | IEEE International Colloquium on Signal Processing & Its Applications (CSPA) | unranked | 1 | 0 | 0 | 1 | 2018 |
| 324 | IEEE International Conference Nanomaterials: Applications & Properties (NAP) | unranked | 1 | 0 | 1 | 0 | 2020 |
| 325 | IEEE International Conference on Advanced Computing (IACC) | unranked | 1 | 1 | 0 | 0 | 2016 |
| 326 | IEEE International Conference on Application of Information and Communication Technologies (AICT) | unranked | 1 | 0 | 1 | 0 | 2020 |
| 327 | IEEE International Conference on Artificial Intelligence and Virtual Reality (AIVR) | unranked | 1 | 0 | 0 | 1 | 2022 |
| 328 | IEEE International Conference on Artificial Intelligence Circuits and Systems (AICAS) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 329 | IEEE International Conference on Biometrics: Theory, Applications and Systems (BTAS) | unranked | 1 | 0 | 1 | 0 | 2019 |
| 330 | IEEE International Conference on Blockchain (Blockchain) | unranked | 1 | 1 | 0 | 0 | 2020 |
| 331 | IEEE International Conference on Cloud Computing in Emerging Markets (CCEM) | unranked | 1 | 1 | 0 | 0 | 2020 |
| 332 | IEEE International Conference on Cloud Computing Technology and Science | C | 1 | 1 | 0 | 0 | 2019 |
| 333 | IEEE International Conference on Communication, Networks and Satellite (COMNETSAT) | unranked | 1 | 1 | 0 | 0 | 2020 |
| 334 | IEEE International Conference on Communications workshops | unranked | 1 | 0 | 0 | 1 | 2018 |
| 335 | IEEE International Conference on Cybernetics, Cognition and Machine Learning Applications (ICCCMLA) | unranked | 1 | 0 | 1 | 0 | 2022 |
| 336 | IEEE International Conference on Emerging Technologies and Factory Automation (ETFA) | C | 1 | 0 | 0 | 1 | 2019 |
| 337 | IEEE International Conference on Enabling Technologies: Infrastructure for Collaborative Enterprises (WETICE) | C | 1 | 1 | 0 | 0 | 2019 |
| 338 | IEEE International Conference on Engineering and Technology | unranked | 1 | 0 | 1 | 0 | 2016 |
| 339 | IEEE International Conference on Industrial Cyber-Physical Systems (ICPS) | unranked | 1 | 0 | 0 | 1 | 2022 |
| 340 | IEEE International Conference on Industrial Engineering and Applications (ICIEA) | unranked | 1 | 1 | 0 | 0 | 2020 |
| 341 | IEEE International Conference on Industrial Technology (ICIT) | unranked | 1 | 0 | 0 | 1 | 2017 |
| 342 | IEEE International Conference on Intelligent Transportation Systems (ITSC) | unranked | 1 | 1 | 0 | 0 | 2022 |
| 343 | IEEE International Conference on Internet of Things and Intelligence Systems (IoTaIS) | unranked | 1 | 0 | 0 | 1 | 2022 |
| 344 | IEEE International Conference on Mechatronics and Automation (ICMA) | unranked | 1 | 0 | 0 | 1 | 2020 |
| 345 | IEEE International Conference on Mobile Ad-Hoc and Smart Systems (MASS) | B | 1 | 0 | 1 | 0 | 2021 |
| 346 | IEEE International Conference on Mobile Networks and Wireless Communications (ICMNWC) | C | 1 | 1 | 0 | 0 | 2021 |
| 347 | IEEE International Conference on Multimedia & Expo Workshops (ICMEW) | unranked | 1 | 0 | 0 | 1 | 2016 |
| 348 | IEEE International Conference on Multimedia and Expo (ICME) | A | 1 | 1 | 0 | 0 | 2022 |
| 349 | IEEE International Conference on Nano/Micro Engineered and Molecular Systems | unranked | 1 | 0 | 0 | 1 | 2019 |
| 350 | IEEE International Conference on Network Softwarization (NetSoft) | B | 1 | 0 | 0 | 1 | 2026 |
| 351 | IEEE International Conference on Omni-layer Intelligent Systems (COINS) | unranked | 1 | 1 | 0 | 0 | 2022 |
| 352 | IEEE International Conference on Pervasive Computing and Communications Workshops and other Affiliated Events (PerCom Workshops) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 353 | IEEE International Conference on Photonics | unranked | 1 | 1 | 0 | 0 | 2020 |
| 354 | IEEE International Conference on Power Electronics, Drives and Energy Systems | unranked | 1 | 0 | 1 | 0 | 2024 |
| 355 | IEEE International Conference on Power Electronics, Intelligent Control and Energy Systems | unranked | 1 | 0 | 1 | 0 | 2016 |
| 356 | IEEE International Conference on Robotic Computing (IRC) | unranked | 1 | 1 | 0 | 0 | 2020 |
| 357 | IEEE International Conference on Sensors and Nanotechnology (SENNANO) | unranked | 1 | 1 | 0 | 0 | 2019 |
| 358 | IEEE International Conference on Signal Processing, Communications and Computing (ICSPCC) | unranked | 1 | 1 | 0 | 0 | 2016 |
| 359 | IEEE International Conference on Smart Cloud (SmartCloud) | unranked | 1 | 0 | 0 | 1 | 2018 |
| 360 | IEEE International Conference on Smart Energy Grid Engineering (SEGE) | unranked | 1 | 1 | 0 | 0 | 2024 |
| 361 | IEEE International Conference on Smart Technologies for Power, Energy and Control (STPEC) | unranked | 1 | 0 | 1 | 0 | 2025 |
| 362 | IEEE International Conference on Software Analysis, Evolution and Reengineering (SANER) | A | 1 | 1 | 0 | 0 | 2026 |
| 363 | IEEE International Conference on Teaching, Assessment, and Learning for Engineering | unranked | 1 | 0 | 0 | 1 | 2018 |
| 364 | IEEE International Conference on Technology for Education (T4E) | unranked | 1 | 0 | 0 | 1 | 2016 |
| 365 | IEEE International Conference on Vehicular Electronics and Safety (ICVES) | unranked | 1 | 0 | 0 | 1 | 2019 |
| 366 | IEEE International Conference on Visual Communications and Image Processing (VCIP) | C | 1 | 0 | 0 | 1 | 2025 |
| 367 | IEEE International IOT, Electronics and Mechatronics Conference (IEMTRONICS) | unranked | 1 | 0 | 0 | 1 | 2021 |
| 368 | IEEE International Joint Conference on Biometrics (IJCB) | B | 1 | 0 | 1 | 0 | 2022 |
| 369 | IEEE International Power and Renewable Energy Conference (IPRECON) | unranked | 1 | 0 | 1 | 0 | 2022 |
| 370 | IEEE International Symposium on Information Theory (ISIT) | B | 1 | 0 | 0 | 1 | 2022 |
| 371 | IEEE International Symposium on Software Reliability Engineering Workshops (ISSREW) | unranked | 1 | 0 | 0 | 1 | 2017 |
| 372 | IEEE International Symposium on Sustainable Energy, Signal Processing and Cyber Security (iSSSC) | unranked | 1 | 1 | 0 | 0 | 2020 |
| 373 | IEEE International Symposium on the Physical and Failure Analysis of Integrated Circuits (IPFA) | unranked | 1 | 0 | 0 | 1 | 2020 |
| 374 | IEEE International Workshop on Multimedia Signal Processing (MMSP) | unranked | 1 | 0 | 0 | 1 | 2021 |
| 375 | IEEE International Workshop on Signal Processing Advances in Wireless Communications (SPAWC) | unranked | 1 | 0 | 0 | 1 | 2021 |
| 376 | IEEE Latin American Electron Devices Conference (LAEDC) | unranked | 1 | 0 | 1 | 0 | 2024 |
| 377 | IEEE MTT-S International Conference on Numerical Electromagnetic and Multiphysics Modeling and Optimization | unranked | 1 | 0 | 1 | 0 | 2023 |
| 378 | IEEE MTT-S International Microwave and RF Conference (IMaRC) | unranked | 1 | 1 | 0 | 0 | 2018 |
| 379 | IEEE Nanotechnology Materials and Devices Conference (NMDC) | unranked | 1 | 0 | 1 | 0 | 2017 |
| 380 | IEEE Nordic Circuits and Systems Conference (NorCAS) | unranked | 1 | 0 | 0 | 1 | 2022 |
| 381 | IEEE Optoelectronics Global Conference (OGC) | unranked | 1 | 1 | 0 | 0 | 2021 |
| 382 | IEEE Power & Energy Society Innovative Smart Grid Technologies Conference (ISGT) | unranked | 1 | 0 | 0 | 1 | 2024 |
| 383 | IEEE Pune Section International Conference (PuneCon) | unranked | 1 | 1 | 0 | 0 | 2020 |
| 384 | IEEE Swiss Conference on Data Science (SDS) | unranked | 1 | 0 | 0 | 1 | 2024 |
| 385 | IEEE Uttar Pradesh Section International Conference on Electrical, Computer and Electronics Engineering (UPCON) | unranked | 1 | 1 | 0 | 0 | 2016 |
| 386 | IEEE Wireless Communications and Networking Conference Workshops (WCNCW) | unranked | 1 | 0 | 0 | 1 | 2020 |
| 387 | IEEE Workshop on Signal and Power Integrity | unranked | 1 | 0 | 1 | 0 | 2020 |
| 388 | IEEE World Engineering Education Conference (EDUNINE) | unranked | 1 | 0 | 0 | 1 | 2023 |
| 389 | IEEE/ACIS International Conference on Computer and Information Science (ICIS) | C | 1 | 1 | 0 | 0 | 2018 |
| 390 | IEEE/ACM International Symposium on Cluster, Cloud and Internet Computing (CCGrid) | B | 1 | 0 | 0 | 1 | 2023 |
| 391 | IEEE/ACM International Symposium on Low Power Electronics and Design (ISLPED) | A | 1 | 0 | 0 | 1 | 2025 |
| 392 | IEEE/AIAA Digital Avionics Systems Conference (DASC) | unranked | 1 | 0 | 0 | 1 | 2017 |
| 393 | IEEE/CVF Winter Conference on Applications of Computer Vision (WACV) | A | 1 | 1 | 0 | 0 | 2023 |
| 394 | IEEE/CVF Winter Conference on Applications of Computer Vision Workshops (WACVW) | unranked | 1 | 0 | 0 | 1 | 2026 |
| 395 | IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS) | A | 1 | 0 | 0 | 1 | 2016 |
| 396 | IEEE/SICE International Symposium on System Integration (SII) | unranked | 1 | 0 | 0 | 1 | 2025 |
| 397 | INCOSE International Symposium | unranked | 1 | 0 | 0 | 1 | 2017 |
| 398 | Innovations in Power and Advanced Computing Technologies (i-PACT) | unranked | 1 | 1 | 0 | 0 | 2019 |
| 399 | International ACM Conference on Modeling, Analysis and Simulation of Wireless and Mobile Systems (MSWiM) | A | 1 | 1 | 0 | 0 | 2022 |
| 400 | International ACM SIGACCESS Conference on Computers and Accessibility (ASSETS) | A | 1 | 0 | 0 | 1 | 2024 |
| 401 | International Carnahan Conference on Security Technology | unranked | 1 | 0 | 1 | 0 | 2019 |
| 402 | International Conference Electronics | unranked | 1 | 0 | 1 | 0 | 2023 |
| 403 | International Conference on Advance Computing and Innovative Technologies in Engineering (ICACITE) | unranked | 1 | 0 | 1 | 0 | 2023 |
| 404 | International Conference on Advanced Composite Materials in Bridges and Structures (ACMBS) | unranked | 1 | 0 | 0 | 1 | 2026 |
| 405 | International Conference on Advanced Research in Computing (ICARC) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 406 | International Conference on Advanced Technologies for Communications | unranked | 1 | 0 | 0 | 1 | 2024 |
| 407 | International Conference on Advances in Computing, Communication & Automation (ICACCA) | unranked | 1 | 0 | 1 | 0 | 2017 |
| 408 | International Conference on Advances in Computing, Communication and Control (ICAC3) | unranked | 1 | 0 | 1 | 0 | 2019 |
| 409 | International Conference on Advances in Computing, Communication Control and Networking (ICAC3N) | unranked | 1 | 1 | 0 | 0 | 2021 |
| 410 | International Conference on Advances in Intelligent Computing and Applications (AICAPS) | unranked | 1 | 0 | 1 | 0 | 2023 |
| 411 | International Conference on Algorithms, Computing and Artificial Intelligence (ACAI) | unranked | 1 | 0 | 1 | 0 | 2018 |
| 412 | International Conference on Algorithms, Methodology, Models and Applications in Emerging Technologies (ICAMMAET) | unranked | 1 | 0 | 0 | 1 | 2017 |
| 413 | International Conference on Artificial Intelligence and Machine Vision (AIMV) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 414 | International Conference on Artificial Intelligence and Signal Processing (AISP) | unranked | 1 | 1 | 0 | 0 | 2024 |
| 415 | International Conference on Artificial Intelligence and Smart Energy (ICAIS) | unranked | 1 | 1 | 0 | 0 | 2022 |
| 416 | International Conference on Artificial Intelligence, Computer, Data Sciences and Applications (ACDSA) | unranked | 1 | 0 | 1 | 0 | 2026 |
| 417 | International Conference on Augmented Intelligence and Sustainable Systems (ICAISS) | unranked | 1 | 0 | 1 | 0 | 2022 |
| 418 | International Conference on Automatic Face and Gesture Recognition | B | 1 | 0 | 0 | 1 | 2020 |
| 419 | International Conference on Availability, Reliability and Security (ARES) | B | 1 | 0 | 0 | 1 | 2022 |
| 420 | International Conference on Business and Industrial Research (ICBIR) | unranked | 1 | 0 | 0 | 1 | 2025 |
| 421 | International Conference on Circuits, Systems and Simulation (ICCSS) | unranked | 1 | 0 | 0 | 1 | 2026 |
| 422 | International Conference on Cloud Computing and Services Science | C | 1 | 1 | 0 | 0 | 2023 |
| 423 | International Conference on Communication Information and Computing Technology (ICCICT) | unranked | 1 | 1 | 0 | 0 | 2021 |
| 424 | International Conference on Communication Systems and Network Technologies | unranked | 1 | 0 | 1 | 0 | 2018 |
| 425 | International Conference on Communication, Computing and Industry 4.0 (C2I4) | unranked | 1 | 1 | 0 | 0 | 2020 |
| 426 | International Conference on Communication, Control and Intelligent Systems (CCIS) | unranked | 1 | 1 | 0 | 0 | 2024 |
| 427 | International Conference on Communication, Security and Artificial Intelligence (ICCSAI) | unranked | 1 | 0 | 1 | 0 | 2025 |
| 428 | International Conference on Compilers, Architecture, and Synthesis for Embedded Systems (CASES) | unranked | 1 | 1 | 0 | 0 | 2022 |
| 429 | International Conference on Computational Biology and Bioinformatics (ICCBB) | unranked | 1 | 0 | 1 | 0 | 2017 |
| 430 | International Conference on Computational Performance Evaluation (ComPE) | unranked | 1 | 0 | 1 | 0 | 2021 |
| 431 | International Conference on Computational Science and Computational Intelligence (CSCI) | unranked | 1 | 1 | 0 | 0 | 2016 |
| 432 | International Conference on Computational Science and Its Applications | C | 1 | 0 | 0 | 1 | 2017 |
| 433 | International Conference on Compute and Data Analysis (ICCDA) | unranked | 1 | 0 | 1 | 0 | 2017 |
| 434 | International Conference on Computer and Communication Technology | unranked | 1 | 1 | 0 | 0 | 2017 |
| 435 | International Conference on Computer Technologies (ICCTech) | unranked | 1 | 0 | 0 | 1 | 2023 |
| 436 | International Conference on Computer Technology Applications (ICCTA) | unranked | 1 | 0 | 0 | 1 | 2022 |
| 437 | International Conference on Computing and Artificial Intelligence (ICCAI) | unranked | 1 | 1 | 0 | 0 | 2024 |
| 438 | International Conference on Computing and Pattern Recognition (ICCPR) | unranked | 1 | 1 | 0 | 0 | 2023 |
| 439 | International Conference on Computing Methodologies and Communication (ICCMC) | unranked | 1 | 1 | 0 | 0 | 2019 |
| 440 | International Conference on Computing, Communication, and Intelligent Systems (ICCCIS) | unranked | 1 | 0 | 1 | 0 | 2021 |
| 441 | International Conference on Control and Automation | unranked | 1 | 1 | 0 | 0 | 2018 |
| 442 | International Conference on Control and Robotics Engineering (ICCRE) | unranked | 1 | 1 | 0 | 0 | 2023 |
| 443 | International Conference on Control, Automation and Information Sciences (ICCAIS) | unranked | 1 | 0 | 1 | 0 | 2025 |
| 444 | International Conference on Control, Communication and Computing (ICCC) | unranked | 1 | 0 | 0 | 1 | 2025 |
| 445 | International Conference on Control, Computing, Communication and Materials (ICCCCM) | unranked | 1 | 0 | 1 | 0 | 2024 |
| 446 | International Conference on Data Science, Agents & Artificial Intelligence (ICDSAAI) | unranked | 1 | 1 | 0 | 0 | 2022 |
| 447 | International Conference on Disruptive Technologies (ICDT) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 448 | International conference on economics & development/Asian journal of public health | unranked | 1 | 1 | 0 | 0 | 2017 |
| 449 | International Conference on Electrical Engineering/Electronics, Computer, Telecommunications and Information Technology (ECTI-CON) | unranked | 1 | 0 | 1 | 0 | 2016 |
| 450 | International Conference on Electrical, Computer, Communications and Mechatronics Engineering (ICECCME) | unranked | 1 | 1 | 0 | 0 | 2021 |
| 451 | International Conference on Electronics and Sustainable Communication Systems (ICESC) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 452 | International Conference on Electronics, Communication and Aerospace Technology (ICECA) | unranked | 1 | 0 | 0 | 1 | 2023 |
| 453 | International Conference on Emerging Frontiers in Electrical and Electronic Technologies (ICEFEET) | unranked | 1 | 0 | 1 | 0 | 2020 |
| 454 | International Conference on Emerging Trends in Information Technology and Engineering (ICETITE) | unranked | 1 | 0 | 0 | 1 | 2024 |
| 455 | International Conference on Engineering and Telecommunication (EnT) | unranked | 1 | 1 | 0 | 0 | 2019 |
| 456 | International Conference on Engineering, Applied Sciences, and Technology (ICEAST) | unranked | 1 | 1 | 0 | 0 | 2018 |
| 457 | International Conference on Evaluation and Assessment in Software Engineering (EASE) | A | 1 | 1 | 0 | 0 | 2025 |
| 458 | International Conference on Field-Programmable Technology (FPT) | unranked | 1 | 0 | 0 | 1 | 2024 |
| 459 | International Conference on Geographical Information Systems Theory, Applications and Management (GISTAM) | unranked | 1 | 0 | 0 | 1 | 2021 |
| 460 | International Conference on Human System Interaction (HSI) | C | 1 | 0 | 1 | 0 | 2022 |
| 461 | International Conference on Image Processing Theory, Tools and Applications (IPTA) | unranked | 1 | 0 | 0 | 1 | 2017 |
| 462 | International Conference on Information and Communication Technology for Competitive Strategies (ICTCS) | unranked | 1 | 1 | 0 | 0 | 2016 |
| 463 | International Conference on Information and Computer Technologies (ICICT) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 464 | International Conference on Information, Communication, Instrumentation and Control (ICICIC) | unranked | 1 | 0 | 0 | 1 | 2017 |
| 465 | International Conference on Innovation and Intelligence for Informatics, Computing, and Technologies (3ICT) | unranked | 1 | 1 | 0 | 0 | 2022 |
| 466 | International Conference on Innovations in Electronics, Signal Processing and Communication (IESC) | unranked | 1 | 0 | 0 | 1 | 2017 |
| 467 | International Conference on Innovative Data Communication Technologies and Application (ICIDCA) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 468 | International Conference on Innovative Practices in Technology and Management (ICIPTM) | unranked | 1 | 0 | 1 | 0 | 2024 |
| 469 | International Conference on Innovative Sustainable Computational Technologies (CISCT) | unranked | 1 | 0 | 1 | 0 | 2023 |
| 470 | International Conference on Intelligent and Innovative Technologies in Computing, Electrical and Electronics (IITCEE) | unranked | 1 | 0 | 0 | 1 | 2023 |
| 471 | International Conference on Intelligent Data Communication Technologies and Internet of Things (IDCIoT) | unranked | 1 | 0 | 0 | 1 | 2024 |
| 472 | International Conference on Intelligent Systems, Advanced Computing and Communication (ISACC) | unranked | 1 | 1 | 0 | 0 | 2023 |
| 473 | International Conference on Internet of Things, Big Data and Security (IoTBDS) | C | 1 | 0 | 0 | 1 | 2025 |
| 474 | International Conference on Inventive Systems and Control (ICISC) | unranked | 1 | 1 | 0 | 0 | 2018 |
| 475 | International Conference on IoT, Communication and Automation Technology (ICICAT) | unranked | 1 | 0 | 1 | 0 | 2023 |
| 476 | International Conference on Knowledge and Smart Technology | unranked | 1 | 0 | 1 | 0 | 2024 |
| 477 | International Conference on Machine Learning and Soft Computing (ICMLSC) | unranked | 1 | 0 | 0 | 1 | 2024 |
| 478 | International Conference on Machine Learning Technologies (ICMLT) | unranked | 1 | 0 | 1 | 0 | 2026 |
| 479 | International Conference on Methods and Models in Automation and Robotics | unranked | 1 | 1 | 0 | 0 | 2024 |
| 480 | International Conference on Microelectronics, Computing and Communications | unranked | 1 | 0 | 1 | 0 | 2016 |
| 481 | International Conference on Microwave and Photonics | unranked | 1 | 0 | 1 | 0 | 2018 |
| 482 | International Conference on Mobile and Ubiquitous Multimedia (MUM) | B | 1 | 0 | 0 | 1 | 2018 |
| 483 | International Conference on Multimedia, Signal Processing and Communication Technologies (IMPACT) | unranked | 1 | 1 | 0 | 1 | 2017 |
| 484 | International Conference on Networking, Systems and Security (NSysS) | unranked | 1 | 0 | 0 | 1 | 2023 |
| 485 | International Conference on Parallel and Distributed Computing, Applications and Technologies (PDCAT) | C | 1 | 1 | 0 | 0 | 2016 |
| 486 | International Conference on Pattern Recognition Applications and Methods | C | 1 | 0 | 1 | 0 | 2025 |
| 487 | International Conference on Power Energy, Environment and Intelligent Control (PEEIC) | unranked | 1 | 1 | 0 | 0 | 2019 |
| 488 | International Conference on Power, Control & Embedded Systems (ICPCES) | unranked | 1 | 1 | 0 | 0 | 2017 |
| 489 | International Conference on Power, Control and Computing Technologies (ICPC2T) | unranked | 1 | 0 | 1 | 0 | 2025 |
| 490 | International Conference on Quantum Communications, Networking, and Computing (QCNC) | unranked | 1 | 0 | 0 | 1 | 2026 |
| 491 | International Conference on Recent Advances in Information Technology | unranked | 1 | 0 | 1 | 0 | 2025 |
| 492 | International Conference on Recent Innovations in Signal Processing and Embedded Systems (RISE) | unranked | 1 | 1 | 0 | 0 | 2017 |
| 493 | International Conference on Recent Trends in Information Technology | unranked | 1 | 0 | 1 | 0 | 2016 |
| 494 | International Conference on Recent Trends in Microelectronics, Automation, Computing and Communications Systems (ICMACC) | unranked | 1 | 1 | 0 | 0 | 2022 |
| 495 | International Conference on Secure Cyber Computing and Communication (ICSCCC) | unranked | 1 | 0 | 1 | 0 | 2018 |
| 496 | International Conference on Secure Cyber Computing and Communications (ICSCCC) | unranked | 1 | 0 | 1 | 0 | 2021 |
| 497 | International Conference on Security and Cryptography | unranked | 1 | 0 | 1 | 0 | 2022 |
| 498 | International Conference on Self Sustainable Artificial Intelligence Systems (ICSSAS) | unranked | 1 | 0 | 1 | 0 | 2024 |
| 499 | International Conference on Signal and Information Processing | unranked | 1 | 1 | 0 | 0 | 2022 |
| 500 | International Conference on Signal Processing and Multimedia Applications | unranked | 1 | 0 | 0 | 1 | 2021 |
| 501 | International Conference on Signal Processing, Communication, Power and Embedded System (SCOPES) | unranked | 1 | 0 | 0 | 1 | 2016 |
| 502 | International Conference on Smart Electronics and Communication (ICOSEC) | unranked | 1 | 0 | 1 | 0 | 2020 |
| 503 | International Conference on Smart Generation Computing, Communication and Networking (SMART GENCON) | unranked | 1 | 1 | 0 | 0 | 2021 |
| 504 | International Conference on Smart Grid and Smart Cities (ICSGSC) | unranked | 1 | 1 | 0 | 0 | 2021 |
| 505 | International Conference On Smart Technologies For Smart Nation (SmartTechCon) | unranked | 1 | 0 | 0 | 1 | 2017 |
| 506 | International Conference on Soft Computing & Machine Intelligence (ISCMI) | unranked | 1 | 0 | 1 | 0 | 2021 |
| 507 | International Conference on Sustainable Communication Networks and Application (ICSCNA) | unranked | 1 | 0 | 1 | 0 | 2024 |
| 508 | International Conference on Sustainable Computing and Smart Systems (ICSCSS) | unranked | 1 | 0 | 1 | 0 | 2025 |
| 509 | International Conference on the Internet of Things (IoT) | unranked | 1 | 1 | 0 | 0 | 2024 |
| 510 | International Conference on UK-China Emerging Technologies (UCET) | unranked | 1 | 1 | 0 | 0 | 2020 |
| 511 | International Conference on Web Research (ICWR) | unranked | 1 | 0 | 1 | 0 | 2026 |
| 512 | International Electronic Conference on Agronomy (IECAG) | unranked | 1 | 1 | 0 | 0 | 2026 |
| 513 | International Joint Conference on e-Business and Telecommunications (ICETE) | unranked | 1 | 1 | 0 | 0 | 2017 |
| 514 | International Scientific Conference on Information Technology and Management Science of Riga Technical University (ITMS) | unranked | 1 | 1 | 0 | 0 | 2021 |
| 515 | International Symposium on Computational and Business Intelligence (ISCBI) | unranked | 1 | 0 | 1 | 0 | 2016 |
| 516 | International Symposium on Innovative Approaches in Smart Technologies (ISAS) | unranked | 1 | 0 | 1 | 0 | 2024 |
| 517 | International Symposium on Intelligent Signal Processing and Communication Systems (ISPACS) | unranked | 1 | 1 | 0 | 0 | 2018 |
| 518 | International Symposium on Modeling and Optimization in Mobile, Ad Hoc, and Wireless Networks (WiOpt) | B | 1 | 0 | 0 | 1 | 2025 |
| 519 | International Symposium on Networks, Computers and Communications (ISNCC) | C | 1 | 0 | 0 | 1 | 2021 |
| 520 | International Telecommunications Conference (ITC-Egypt) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 521 | International VLSI Symposium on Technology, Systems and Applications (VLSI-TSA) | unranked | 1 | 0 | 0 | 1 | 2026 |
| 522 | International Workshop on Acoustic Signal Enhancement | unranked | 1 | 0 | 1 | 0 | 2024 |
| 523 | International Workshop on Variable Structure Systems | unranked | 1 | 0 | 0 | 1 | 2018 |
| 524 | Interspeech (USB) | A | 1 | 0 | 0 | 1 | 2018 |
| 525 | IOP Conference Series Earth and Environmental Science | unranked | 1 | 1 | 0 | 0 | 2017 |
| 526 | Joint Conference on Lexical and Computational Semantics | unranked | 1 | 1 | 0 | 0 | 2016 |
| 527 | Lecture notes in business information processing | unranked | 1 | 1 | 0 | 0 | 2024 |
| 528 | Materials science forum | unranked | 1 | 1 | 0 | 0 | 2020 |
| 529 | MIPRO ICT and Electronics Convention (MIPRO) | unranked | 1 | 1 | 0 | 0 | 2023 |
| 530 | Multidisciplinary International Social Networks Conference (MISNC) | unranked | 1 | 1 | 0 | 0 | 2017 |
| 531 | National Power Systems Conference | unranked | 1 | 0 | 1 | 0 | 2016 |
| 532 | Odisha International Conference on Electrical Power Engineering, Communication and Computing Technology (ODICON) | unranked | 1 | 0 | 1 | 0 | 2026 |
| 533 | Optica Sensing Congress | unranked | 1 | 1 | 0 | 0 | 2025 |
| 534 | Proceedings - Asian Test Symposium/Proceedings | unranked | 1 | 1 | 0 | 0 | 2024 |
| 535 | Proceedings - Euromicro Workshop on Parallel and Distributed Processing/Proceedings | unranked | 1 | 0 | 0 | 1 | 2020 |
| 536 | Proceedings - IEEE Aerospace Conference | unranked | 1 | 0 | 0 | 1 | 2022 |
| 537 | Proceedings of ... IEEE International Conference on Fuzzy Systems | B | 1 | 0 | 1 | 0 | 2025 |
| 538 | Proceedings of MOL2NET'22, Conference on Molecular, Biomedical &amp; Computational Sciences and Engineering, 8th ed. - MOL2NET: FROM MOLECULES TO NETWORKS | unranked | 1 | 0 | 0 | 1 | 2022 |
| 539 | Proceedings of the ... ACM International Conference on Information & Knowledge Management | A | 1 | 0 | 0 | 1 | 2022 |
| 540 | Proceedings of the ... Annual Hawaii International Conference on System Sciences/Proceedings of the Annual Hawaii International Conference on System Sciences | unranked | 1 | 0 | 0 | 1 | 2023 |
| 541 | Proceedings of the ... International Florida Artificial Intelligence Research Society Conference | unranked | 1 | 0 | 1 | 0 | 2023 |
| 542 | Proceedings of the 2022 Fourteenth International Conference on Contemporary Computing | unranked | 1 | 1 | 0 | 0 | 2022 |
| 543 | Proceedings of the IEEE Conference on Decision & Control, including the Symposium on Adaptive Processes | unranked | 1 | 0 | 0 | 1 | 2023 |
| 544 | SAE technical papers on CD-ROM/SAE technical paper series | unranked | 1 | 0 | 1 | 0 | 2017 |
| 545 | SIGGRAPH Asia Posters | unranked | 1 | 0 | 0 | 1 | 2024 |
| 546 | SPIE Medical Imaging: Biomedical Applications in Molecular, Structural, and Functional Imaging | unranked | 1 | 0 | 0 | 1 | 2018 |
| 547 | SPIE Medical Imaging: Image Processing | unranked | 1 | 0 | 0 | 1 | 2021 |
| 548 | Springer proceedings in complexity | unranked | 1 | 0 | 0 | 1 | 2018 |
| 549 | Springer Proceedings in Materials | unranked | 1 | 0 | 1 | 0 | 2025 |
| 550 | Studies in classification, data analysis, and knowledge organization | unranked | 1 | 1 | 0 | 0 | 2025 |
| 551 | Sustainable civil infrastructures | unranked | 1 | 0 | 0 | 1 | 2024 |
| 552 | Symposium on Applied Computing | C | 1 | 0 | 0 | 1 | 2017 |
| 553 | The Sixteenth Marcel Grossmann Meeting | unranked | 1 | 1 | 0 | 0 | 2023 |
| 554 | Transportation research procedia | unranked | 1 | 1 | 0 | 0 | 2020 |
| 555 | Workshop on Biomedical Language Processing (BioNLP) | unranked | 1 | 0 | 0 | 1 | 2025 |
| 556 | Workshop on Speech, Vision, and Language Technologies for Dravidian Languages (DravidianLangTech) | unranked | 1 | 1 | 0 | 0 | 2025 |
| 557 | World Conference on Smart Trends in Systems, Security and Sustainability (WorldS4) | unranked | 1 | 0 | 1 | 0 | 2020 |
| 558 | The international archives of the photogrammetry, remote sensing and spatial information sciences/International archives of the photogrammetry, remote sensing and spatial information sciences | unranked | 1 | 0 | 0 | 1 | 2024 |
