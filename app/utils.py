import pandas as pd
import os

# Define the path to the dataset
VEHICLE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'victoria_vehicle_registration_cleaned.xlsx')
def get_vehicle_growth_data(start_year=2016, end_year=2018):
    # Load the Excel file, skip first 2 rows, and assign proper column names
    df = pd.read_excel(VEHICLE_DATA_PATH, skiprows=2, header=None)
    df.columns = ["vehicle_type", 2016, 2017, 2018, "region"]

    # Select only the relevant year columns
    selected_years = [y for y in [2016, 2017, 2018] if start_year <= y <= end_year]

    result = []

    # Build structured data: each vehicle type and its yearly registrations
    for _, row in df.iterrows():
        vehicle_type = row["vehicle_type"]
        yearly_counts = {str(year): int(row[year]) for year in selected_years if pd.notna(row[year])}

        result.append({
            "vehicle_type": vehicle_type,
            "registrations": yearly_counts
        })

    return {
        "data": result,
        "years": [str(y) for y in selected_years],
        "source": "https://www.abs.gov.au/statistics/industry/tourism-and-transport/motor-vehicle-census-australia/latest-release"
    }


POPULATION_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'melbourne_population_cleaned_new.xlsx')

def get_population_growth_data(start_year=2015, end_year=2021, region=None):
    # Read with multi-header (first two rows)
    df = pd.read_excel(POPULATION_DATA_PATH, header=[0, 1])

    # Rename the first column to 'region' for easier access
    df.columns = ['region' if (i == 0) else col for i, col in enumerate(df.columns)]
    
    # Now, all year columns are multiindex, region is a string
    # Select columns where first level is a year and second is 'no.'
    year_cols = [col for col in df.columns if isinstance(col, tuple) 
                 and str(col[0]).isdigit() and 1900 < int(col[0]) < 2100 
                 and col[1].strip().lower() == 'no.']

    # Filter year columns within range
    selected_years = [col for col in year_cols if start_year <= int(col[0]) <= end_year]
    
    # Optionally filter by region
    if region:
        df = df[df['region'].str.lower() == region.lower()]
    
    data = []
    for _, row in df.iterrows():
        region_name = row['region']
        yearly_data = {str(col[0]): int(row[col]) for col in selected_years if pd.notna(row[col])}
        
        if yearly_data:
            # Trend calculation
            years_sorted = sorted(yearly_data.keys())
            start_val = yearly_data.get(years_sorted[0])
            end_val = yearly_data.get(years_sorted[-1])
            if start_val is not None and end_val is not None:
                diff = end_val - start_val
                trend = f"Increased by {diff}" if diff > 0 else f"Decreased by {abs(diff)}"
            else:
                trend = "Trend data unavailable"
            data.append({
                "region": region_name,
                "population": {y: yearly_data[y] for y in years_sorted},
                "trend": trend
            })

    return {
        "data": data,
        "years": [str(col[0]) for col in selected_years],
        "source": "https://www.abs.gov.au/statistics/people/population/regional-population/2021"
    }