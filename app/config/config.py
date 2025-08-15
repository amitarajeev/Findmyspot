import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LocationIQ
    LOCATIONIQ_API_KEY = os.getenv("VITE_LOCATIONIQ_API_KEY", "pk.c9228d44132bed501f2cab0dc3c6e783")

    # Paths to data files (inside /data)
    POPULATION_DATA = os.path.join("E:/Monash/Semester 4/FIT5120/Onboarding_Project/findmyspot/data/melbourne_population_cleaned_new.xlsx")
    VEHICLE_DATA = os.path.join("E:/Monash/Semester 4/FIT5120/Onboarding_Project/findmyspot/data/victoria_vehicle_registration_cleaned.xlsx")
    PARKING_BAYS_DATA = os.path.join("E:/Monash/Semester 4/FIT5120/Onboarding_Project/findmyspot/data/on_street_parking_bays_cleaned.xlsx")
    BAY_SENSORS_DATA = os.path.join("E:/Monash/Semester 4/FIT5120/Onboarding_Project/findmyspot/data/on_street_parking_bay_sensors_cleaned.csv")
    PARKING_ZONES_DATA = os.path.join("E:/Monash/Semester 4/FIT5120/Onboarding_Project/findmyspot/data/parking_zones_linked_to_street_segments_cleaned.csv")
    SIGN_PLATES_DATA = os.path.join("E:/Monash/Semester 4/FIT5120/Onboarding_Project/findmyspot/data/sign_plates_located_in_each_parking_zone_cleaned.csv")

    # Paths inside /app
    ZONE_LOCATIONS_PATH = os.path.join("E:/Monash/Semester 4/FIT5120/Onboarding_Project/findmyspot/app/config/zone_locations.json")
    ML_MODEL_PATH = os.path.join("E:/Monash/Semester 4/FIT5120/Onboarding_Project/findmyspot/app/ml_model/findmyspot_model.pth")
