"""Build docs/data.js for the interactive map from ../results and the course data.

Usage (from the repo root):
    python docs/build_data.py

ZIP-level numbers follow the notebook's preprocessing: 0–5 supply is infant + toddler +
preschool capacity, 5–12 population is the 5–9 bucket plus half of 10–14, and a ZIP is
high-demand if its employment rate is at least 60% or its average income is $60,000 or less.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Optimization project 1" / "ChildCareDeserts_Data"
RESULTS = ROOT / "results"
OUT = ROOT / "docs" / "data.js"


def zips(df, col="zipcode"):
    df[col] = df[col].astype(str).str.zfill(5)
    return df


def main():
    fac = zips(pd.read_csv(DATA / "child_care_regulated.csv"), "zip_code").rename(columns={"zip_code": "zipcode"})
    pop = zips(pd.read_csv(DATA / "population.csv"))
    inc = zips(pd.read_csv(DATA / "avg_individual_income.csv").rename(columns={"ZIP code": "zipcode"}))
    emp = zips(pd.read_csv(DATA / "employment_rate.csv"))
    cand = zips(pd.read_csv(DATA / "potential_locations.csv"))
    new = zips(pd.read_csv(RESULTS / "part2_new_facilities.csv"))
    exp = zips(pd.read_csv(RESULTS / "part2_expansions.csv"))

    fac["e5"] = fac[["infant_capacity", "toddler_capacity", "preschool_capacity"]].sum(axis=1)
    fac["e12"] = fac["e5"] + fac["school_age_capacity"]
    exp["x12"] = exp[["seg1", "seg2", "seg3"]].sum(axis=1)
    new["n12"] = new["size"].map({"S": 100, "M": 200, "L": 400})

    z = pop[["zipcode"]].copy()
    z["p5"] = pop["-5"]
    z["p12"] = pop["-5"] + pop["5-9"] + 0.5 * pop["10-14"]
    z = z.merge(inc[["zipcode", "average income"]], on="zipcode", how="left")
    z = z.merge(emp[["zipcode", "employment rate"]], on="zipcode", how="left")
    z["hd"] = ((z["employment rate"] >= 0.60) | (z["average income"] <= 60000)).astype(int)
    z = z.merge(fac.groupby("zipcode")[["e12", "e5"]].sum(), on="zipcode", how="left")
    z = z.merge(exp.groupby("zipcode").agg(x12=("x12", "sum"), x5=("slots_0_5", "sum"),
                                           nx=("facility_id", "count")), on="zipcode", how="left")
    z = z.merge(new.groupby("zipcode").agg(n12=("n12", "sum"), n5=("slots_0_5", "sum")), on="zipcode", how="left")
    counts = new.pivot_table(index="zipcode", columns="size", values="site_id", aggfunc="count")
    z = z.merge(counts.reindex(columns=["S", "M", "L"]), on="zipcode", how="left")

    # Place each ZIP at the mean of its candidate sites, falling back to its facilities
    cent = cand.groupby("zipcode")[["latitude", "longitude"]].mean()
    cent = cent.combine_first(fac.groupby("zipcode")[["latitude", "longitude"]].mean())
    z = z.merge(cent, on="zipcode", how="left")
    z = z.fillna({c: 0 for c in ["e12", "e5", "x12", "x5", "nx", "n12", "n5", "S", "M", "L"]})

    zip_rows = [
        [r.zipcode, round(r.latitude, 4) if pd.notna(r.latitude) else None,
         round(r.longitude, 4) if pd.notna(r.longitude) else None, int(r.hd),
         round(r.p12, 1), int(r.p5), int(r.e12), int(r.e5), round(r.x12, 1), round(r.x5, 1),
         int(r.nx), int(r.n12), round(r.n5, 1), int(r.S), int(r.M), int(r.L)]
        for r in z.itertuples()
    ]
    zip_index = {row[0]: i for i, row in enumerate(zip_rows)}
    sites = [[round(r.lat, 5), round(r.lon, 5), "SML".index(r.size), zip_index[r.zipcode]]
             for r in new.itertuples()]
    existing = fac.dropna(subset=["latitude", "longitude"])
    existing = [[round(a, 4), round(b, 4)] for a, b in zip(existing.latitude, existing.longitude)]

    payload = {
        "zipFields": ["zip", "lat", "lon", "highDemand", "pop0_12", "pop0_5", "exist0_12", "exist0_5",
                      "expand0_12", "expand0_5", "nExpanded", "new0_12", "new0_5", "nS", "nM", "nL"],
        "zips": zip_rows,
        "sites": sites,
        "existing": existing,
    }
    OUT.write_text("window.DATA = " + json.dumps(payload, separators=(",", ":")) + ";\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(zip_rows)} ZIPs, {len(sites)} sites, "
          f"{len(existing)} existing, {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
