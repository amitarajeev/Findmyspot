# app/utils.py
from pathlib import Path
import pandas as pd
import re

BASE_DIR = Path(__file__).resolve().parent.parent
VEHICLE_DATA_PATH = BASE_DIR / "data" / "victoria_vehicle_registration_cleaned.xlsx"
POPULATION_DATA_PATH = BASE_DIR / "data" / "melbourne_population_cleaned_new.xlsx"


def _detect_available_years(columns):
    """
    Detect available years from column names.
    Supports formats like '2016', '2016.0', etc.
    Returns a sorted list of integers.
    """
    years = []
    for c in columns:
        s = str(c).strip()
        if s.replace(".", "", 1).isdigit():
            try:
                years.append(int(float(s)))
            except:
                pass
    return sorted(set(years))


def _promote_first_row_as_header_if_years(raw: pd.DataFrame) -> pd.DataFrame:
    """
    If the first row appears to contain years (>= 2 four-digit numbers),
    promote it to the header row.  
    Set the first column name as 'Vehicle_Type' and the last column as 'State' (if present).
    """
    first = raw.iloc[0].tolist()
    first_years = []
    for v in first:
        s = str(v).strip()
        if s.isdigit() and len(s) == 4:
            first_years.append(int(s))

    if len(first_years) >= 2:
        new_header = raw.iloc[0].tolist()
        df = raw.iloc[1:].copy()
        new_header[0] = "Vehicle_Type"
        if len(new_header) >= 5:
            new_header[-1] = "State"
        df.columns = [str(c).strip() for c in new_header]
        return df

    # Fallback: Do not promote, but attempt to rename columns if old-style headers like 'Unnamed' or 'Year' exist
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    if any("Unnamed" in c or c.lower() == "year" for c in df.columns):
        hdr = df.iloc[0].tolist()
        renamed = []
        for i, c in enumerate(df.columns):
            s = str(hdr[i]).strip()
            if s.isdigit() and len(s) == 4:
                renamed.append(s)
            elif i == 0:
                renamed.append("Vehicle_Type")
            elif i == len(df.columns) - 1:
                renamed.append("State")
            else:
                renamed.append(c)
        df = df.iloc[1:].copy()
        df.columns = renamed
    return df


def get_vehicle_growth_data(start_year: int = 2016, end_year: int = 2021, mode: str | None = None):
    """
    Prepare vehicle registration growth data.

    Parameter validation:
      - start_year and end_year must be integers with start_year <= end_year.
      - Requested range must overlap with available years.

    Modes:
      - 'by_type' (default): Return registrations by vehicle type.
      - 'total': Return only total registrations (if TOTAL row exists, use it; otherwise sum all types).

    If mode is not passed directly, will attempt to read 'mode' from Flask request args.

    Returns:
      dict containing data, years, source, mode, available_years.
    """
    # Attempt to get mode from Flask request args if not explicitly provided
    if mode is None:
        try:
            from flask import request
            mode = request.args.get("mode", default="by_type", type=str)
        except Exception:
            mode = "by_type"
    mode = (mode or "by_type").lower()
    if mode not in ("by_type", "total"):
        raise ValueError("mode must be 'by_type' or 'total'.")

    # Validate parameters
    if not (isinstance(start_year, int) and isinstance(end_year, int)):
        raise ValueError("start and end must be integers.")
    if start_year > end_year:
        raise ValueError("start must be <= end.")

    # Load and fix headers
    raw = pd.read_excel(VEHICLE_DATA_PATH)
    df = _promote_first_row_as_header_if_years(raw)

    # Determine available years
    avail_years = _detect_available_years(df.columns)
    if not avail_years:
        raise ValueError("No numeric year columns detected in vehicle data.")
    selected_years = [y for y in avail_years if start_year <= y <= end_year]
    if not selected_years:
        raise ValueError(
            f"No data in requested range [{start_year}, {end_year}]. Available years: {avail_years}"
        )

    veh_col = "Vehicle_Type" if "Vehicle_Type" in df.columns else df.columns[0]
    df = df[[veh_col] + [str(y) for y in selected_years]].copy()

    if mode == "total":
        # Option 1: Use TOTAL row if available
        total_row = df[df[veh_col].astype(str).str.contains("total", case=False, na=False)]
        if not total_row.empty:
            row = total_row.iloc[0]
            sums = {}
            for y in selected_years:
                v = row.get(str(y))
                if pd.notna(v):
                    try:
                        sums[str(y)] = int(str(v).replace(",", ""))
                    except:
                        try:
                            sums[str(y)] = int(float(str(v).replace(",", "")))
                        except:
                            pass
        else:
            # Option 2: Sum all types for each year
            sums = {}
            for y in selected_years:
                col = str(y)
                s = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce").sum(min_count=1)
                if pd.notna(s):
                    sums[str(y)] = int(s)

        return {
            "data": [{"vehicle_type": "TOTAL MOTOR VEHICLES", "registrations": sums}],
            "years": [str(y) for y in selected_years],
            "source": "https://www.abs.gov.au/statistics/industry/tourism-and-transport/motor-vehicle-census-australia/latest-release",
            "mode": "total",
            "available_years": avail_years,
        }

    # Default: Return by type
    out = []
    for _, r in df.iterrows():
        name = str(r[veh_col]).strip()
        if not name or name.lower() == "nan":
            continue
        vals = {}
        for y in selected_years:
            v = r.get(str(y))
            if pd.notna(v):
                try:
                    vals[str(y)] = int(str(v).replace(",", ""))
                except:
                    try:
                        vals[str(y)] = int(float(str(v).replace(",", "")))
                    except:
                        pass
        if vals:
            out.append({"vehicle_type": name, "registrations": vals})

    return {
        "data": out,
        "years": [str(y) for y in selected_years],
        "source": "https://www.abs.gov.au/statistics/industry/tourism-and-transport/motor-vehicle-census-australia/latest-release",
        "mode": "by_type",
        "available_years": avail_years,
    }


def get_population_growth_data(start_year: int = 2015, end_year: int = 2021, region: str | None = None):
    """
    Prepare population growth data (supports exact and partial matches for 'region').

    Parameter validation:
      - start_year and end_year must be integers with start_year <= end_year.
      - Requested range must overlap with available years.

    Returns:
      dict containing data, years, matched_regions, available_years, source.
    """
    # Validate parameters
    if not (isinstance(start_year, int) and isinstance(end_year, int)):
        raise ValueError("start and end must be integers.")
    if start_year > end_year:
        raise ValueError("start must be <= end.")

    wide = pd.read_excel(POPULATION_DATA_PATH)
    wide.columns = [str(c).strip() for c in wide.columns]

    # Drop first row if it contains unit info (e.g., 'no.')
    if str(wide.iloc[0, 1]).strip().lower() == "no.":
        wide = wide.iloc[1:].reset_index(drop=True)

    # Identify region column
    region_col = "Region" if "Region" in wide.columns else next(
        (c for c in wide.columns if any(k in c.lower() for k in ["region", "area", "suburb"])), None
    )
    if not region_col:
        raise ValueError("No region-like column found in population data.")

    # Determine available years
    avail_years = [int(y) for y in wide.columns if str(y).isdigit()]
    avail_years = sorted(set(avail_years))
    if not avail_years:
        raise ValueError("No numeric year columns detected in population data.")

    selected_years = [y for y in avail_years if start_year <= y <= end_year]
    if not selected_years:
        raise ValueError(
            f"No data in requested range [{start_year}, {end_year}]. Available years: {avail_years}"
        )

    # Convert wide format to long format
    long = wide.melt(
        id_vars=[region_col],
        value_vars=[str(y) for y in selected_years],
        var_name="Year",
        value_name="Population",
    )
    long["Year"] = pd.to_numeric(long["Year"], errors="coerce").astype("Int64")
    long["Population"] = pd.to_numeric(long["Population"], errors="coerce")

    matched_regions = None
    if region:
        # First try exact match
        exact = long[long[region_col].astype(str).str.strip().str.casefold() == region.strip().casefold()]
        if exact.empty:
            # Then try partial match (case-insensitive)
            mask = long[region_col].astype(str).str.contains(re.escape(region), case=False, na=False)
            sub = long[mask]
            matched_regions = sorted(sub[region_col].dropna().astype(str).unique().tolist())
            long = sub
        else:
            matched_regions = sorted(exact[region_col].dropna().astype(str).unique().tolist())
            long = exact

    # Aggregate by year
    s = long.groupby("Year", dropna=True)["Population"].sum(min_count=1).reset_index()
    s = s.dropna(subset=["Population"])

    if s.empty:
        return {
            "data": [{"region": region if region else "All Regions", "population": {}, "trend": "Trend data unavailable"}],
            "years": [],
            "matched_regions": matched_regions or [],
            "available_years": avail_years,
            "source": "https://www.abs.gov.au/statistics/people/population/regional-population/2021",
        }

    data_obj = {
        "region": region if region else "All Regions",
        "population": {str(int(r["Year"])): int(r["Population"]) for _, r in s.iterrows()},
        "trend": (
            f"Increased by {int(s.iloc[-1]['Population'] - s.iloc[0]['Population'])}" if len(s) >= 2 else "Trend data unavailable"
        ),
    }

    return {
        "data": [data_obj],
        "years": [str(y) for y in sorted(s["Year"].astype(int).tolist())],
        "matched_regions": matched_regions or (["All Regions"] if not region else []),
        "available_years": avail_years,
        "source": "https://www.abs.gov.au/statistics/people/population/regional-population/2021",
    }
