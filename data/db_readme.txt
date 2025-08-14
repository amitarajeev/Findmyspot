FindMySpot Database Schema

This repository contains the PostgreSQL database schema for the FindMySpot project, a parking and traffic data platform integrating parking bay information, sensor data, population statistics, and vehicle registrations in Victoria, Australia.

Contents

schema.sql — The full PostgreSQL schema export (--schema-only), including:

Tables

Views

Functions

Sequences

Indexes

Foreign key constraints

Database Structure

The schema defines the following key components:

1. Core Parking Data
Table	Description
parking_bay	Metadata for each parking bay: location, street segment, zone ID, coordinates, timestamps.
parking_zone	Parking zone definitions.
street_segment	Street segment metadata (on_street, street_from, street_to).
zone_street_link	Mapping between zones and street segments.
2. Sensor Data
Table	Description
bay_sensor	Time-series data from parking sensors: bay ID, zone number, status, timestamps, coordinates.
3. Signage
Table	Description
sign_plate	Parking restriction signs linked to zones, with time/day restrictions.
4. External Data
Table	Description
population_raw	Raw population figures by region (2001–2021).
vehicle_registration_vic	Annual vehicle registration data by state, type, and year.
5. Views
View	Description
population_stats	Year-by-year population values unpivoted from population_raw.
v_bay_with_zone	Parking bay + street segment details.
v_sensor_latest	Latest sensor reading per bay.
v_bay_with_latest_status	Parking bay with street + latest sensor status.
6. Functions
Function	Purpose
infer_zone_by_neighbors(radius_km, k)	Infers missing zone_id values for bays by looking at the k nearest neighbors within a radius.
🚀 How to Use
1. Create the Database
createdb findmyspot

2. Import the Schema
psql -U your_username -d findmyspot -f schema.sql

3. (Optional) Populate Data

The schema does not include data — you will need to insert or import your own datasets matching the table definitions.

Example Connection String
$Env:PGPASSWORD = "dtVD7Dqn587EVoWrZAWfUsvEVsxCOK35"
psql -h dpg-d2e5l249c44c73ef17j0-a.singapore-postgres.render.com `
     -p 5432 `
     -U findmyspot_user `
     -d findmyspot
