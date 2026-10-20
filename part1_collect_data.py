"""
DPCN 2026 - Group 10 - Part 1: Data Collection (OpenAlex)
==========================================================
Downloads everything the later steps need and stores it in ./cache/:

  1. works.json.gz                 all works 2016-2026 of
                                   IIIT Allahabad    (OpenAlex I26072440  | ROR 03rgjt374)
                                   ABV-IIITM Gwalior (OpenAlex I9747756   | ROR 008b3ap06)
                                   IIIT Bangalore    (OpenAlex I181514455 | ROR 05h9eqy10)
  2. inflow_citing_works.json.gz   works with an Indian affiliation that CITE our
                                   papers   (citation in-flow, cited_by_indian_inst)
  3. outflow_cited_works.json.gz   works with an Indian affiliation that our papers
                                   CITE     (citation out-flow, cites_indian_inst)

Steps 2-3 query OpenAlex with batched filters (100 work IDs per request,
`cites:` / `cited_by:` + `authorships.institutions.country_code:IN`), which
needs ~500 requests instead of resolving 200k+ references one by one.

OpenAlex budget: without an API key the API allows ~1000 requests/day per IP.
Every step is cached and resumable - if the budget runs out, just re-run the
script the next day.  Set OPENALEX_API_KEY to use a personal (larger) budget.

Usage:
    python part1_collect_data.py            # fetch / resume
    python part1_collect_data.py --refresh  # re-download works (keeps flows)
Next:
    python part1b_enrich_data.py
"""

import hashlib
import sys

import group10_common as C

BATCH = 100       # OpenAlex allows up to 100 OR-ed values in one filter

WORK_FIELDS = ("id,doi,display_name,publication_year,type,primary_location,locations,"
               "authorships,cited_by_count,counts_by_year,referenced_works,primary_topic,"
               "is_retracted,open_access")


# ─────────────────────────────────────────────
# 1. WORKS
# ─────────────────────────────────────────────

def fetch_works(oa, refresh=False):
    cache = C.load_json_gz(C.WORKS_CACHE, {"done_institutions": [], "works": {}})
    if refresh:
        cache = {"done_institutions": [], "works": {}}
    works = cache["works"]
    for inst, (inst_id, _) in C.INSTITUTIONS.items():
        if inst_id in cache["done_institutions"]:
            print(f"  {inst}: cached")
            continue
        print(f"  {inst}: downloading ...")
        n = 0
        flt = f"authorships.institutions.id:{inst_id},publication_year:{C.START_YEAR}-{C.END_YEAR}"
        for w in oa.paginate("works", {"filter": flt, "select": WORK_FIELDS}):
            cw = C.compact_work(w)
            prev = works.get(cw["id"], {})
            cw["found_via"] = sorted(set(prev.get("found_via", [])) | {inst_id})
            works[cw["id"]] = cw
            n += 1
            if n % 1000 == 0:
                print(f"    {n} works ...")
        cache["done_institutions"].append(inst_id)
        C.save_json_gz(cache, C.WORKS_CACHE)
        print(f"    {n} works (requests used so far: {oa.calls})")

    # Works whose (100-capped) author list hides our author and that were
    # cached without `found_via`: ask OpenAlex which institution matched.
    hidden = [wid for wid, w in works.items()
              if not C.our_institutions_on(w)]
    if hidden:
        print(f"  Resolving institution membership for {len(hidden)} truncated-author works ...")
        for inst, (inst_id, _) in C.INSTITUTIONS.items():
            for i in range(0, len(hidden), 100):
                ids = "|".join(hidden[i:i + 100])
                data = oa.get("works", {"filter": f"openalex:{ids},authorships.institutions.id:{inst_id}",
                                        "select": "id", "per_page": 100})
                for r in data.get("results", []):
                    w = works[C.short_id(r["id"])]
                    w["found_via"] = sorted(set(w.get("found_via", [])) | {inst_id})
        C.save_json_gz(cache, C.WORKS_CACHE)
    return works


# ─────────────────────────────────────────────
# 2/3. CITATION FLOWS
# ─────────────────────────────────────────────

def batch_key(ids):
    return hashlib.sha1("|".join(ids).encode()).hexdigest()[:16]


def compact_flow_work(w, corpus_ids=None):
    insts = {}
    for a in w.get("authorships") or []:
        for i in a.get("institutions") or []:
            if i.get("country_code") == "IN":
                ci = C.compact_institution(i)
                insts[ci["id"]] = {"name": ci["name"], "type": ci["type"]}
    out = {
        "id": C.short_id(w.get("id")),
        "doi": C.normalize_doi(w.get("doi")),
        "title": w.get("display_name") or "",
        "year": w.get("publication_year"),
        "cited_by_count": w.get("cited_by_count") or 0,
        "insts": insts,
    }
    if corpus_ids is not None:
        out["cites"] = sorted({C.short_id(r) for r in w.get("referenced_works") or []} & corpus_ids)
    return out


def fetch_flow(oa, path, ids, filter_name, select, corpus_ids=None, label=""):
    cache = C.load_json_gz(path, {"done": [], "works": {}})
    done = set(cache["done"])
    batches = [ids[i:i + BATCH] for i in range(0, len(ids), BATCH)]
    todo = [b for b in batches if batch_key(b) not in done]
    print(f"  {label}: {len(batches)} batches, {len(batches) - len(todo)} cached, {len(todo)} to fetch")
    try:
        for k, b in enumerate(todo, 1):
            flt = f"{filter_name}:{'|'.join(b)},authorships.institutions.country_code:IN"
            for w in oa.paginate("works", {"filter": flt, "select": select}):
                cw = compact_flow_work(w, corpus_ids)
                prev = cache["works"].get(cw["id"])
                if prev and "cites" in prev:
                    cw["cites"] = sorted(set(prev["cites"]) | set(cw["cites"]))
                cache["works"][cw["id"]] = cw
            cache["done"].append(batch_key(b))
            if k % 5 == 0 or k == len(todo):
                C.save_json_gz(cache, path)
                print(f"    batch {k}/{len(todo)} | works: {len(cache['works'])} | "
                      f"requests used: {oa.calls} | budget left: {oa.remaining}")
    finally:
        C.save_json_gz(cache, path)
    return cache


def main():
    print("=" * 65)
    print(" DPCN 2026 - Group 10 - Part 1: Data Collection (OpenAlex)")
    print("=" * 65)
    oa = C.OpenAlex()
    refresh = "--refresh" in sys.argv

    try:
        print("\n[1/3] Works per institution")
        works = fetch_works(oa, refresh)
        print(f"  Unique works cached: {len(works)}")

        scimago = C.Scimago()
        corpus, excluded, aliases = C.select_corpus(works, scimago)
        print(f"  Corpus after type filter + dedup: {len(corpus)} works "
              f"({len(aliases)} other versions mapped to them)")
        for reason, n in excluded.most_common():
            print(f"    excluded {n:5d}  {reason}")
        corpus_ids = sorted(corpus)

        print("\n[2/3] Citation in-flow (Indian works citing our papers)")
        # include the other versions: citations to a preprint/repository copy
        # are credited to the canonical paper later (part2)
        targets = sorted(set(corpus_ids) | set(aliases))
        cited = [w for w in targets if works[w]["cited_by_count"] > 0]
        fetch_flow(oa, C.INFLOW_CACHE, cited, "cites",
                   "id,doi,display_name,publication_year,cited_by_count,referenced_works,authorships",
                   corpus_ids=set(targets), label="in-flow")

        print("\n[3/3] Citation out-flow (Indian works cited by our papers)")
        citing = [w for w in corpus_ids if works[w]["refs"]]
        fetch_flow(oa, C.OUTFLOW_CACHE, citing, "cited_by",
                   "id,doi,display_name,publication_year,cited_by_count,authorships",
                   label="out-flow")
    except C.BudgetExhausted as e:
        print(f"\n  STOPPED: {e}.")
        print("  Progress is cached - re-run this script tomorrow (or set OPENALEX_API_KEY).")
        sys.exit(2)

    print(f"\n  OpenAlex requests this run: {oa.calls} | budget left today: {oa.remaining}")
    print("=" * 65)
    print(" Part 1 complete. Next: python part1b_enrich_data.py")
    print("=" * 65)


if __name__ == "__main__":
    main()
