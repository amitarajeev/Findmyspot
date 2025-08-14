--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Debian 17.5-1.pgdg120+1)
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: infer_zone_by_neighbors(double precision, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.infer_zone_by_neighbors(radius_km double precision DEFAULT 0.2, k integer DEFAULT 5) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE affected integer;
BEGIN
  WITH params AS (SELECT radius_km AS radius_km, k AS k),
  missing AS (
    SELECT bay_id, latitude, longitude
    FROM parking_bay
    WHERE zone_id IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL
  ),
  neighbors AS (
    SELECT m.bay_id AS target_bay, p.bay_id AS neighbor_bay, p.zone_id,
           6371 * 2 * ASIN(
             SQRT(
               POWER(SIN(RADIANS(p.latitude  - m.latitude)/2), 2) +
               COS(RADIANS(m.latitude)) * COS(RADIANS(p.latitude)) *
               POWER(SIN(RADIANS(p.longitude - m.longitude)/2), 2)
             )
           ) AS dist_km
    FROM missing m
    JOIN parking_bay p ON p.zone_id IS NOT NULL AND p.latitude IS NOT NULL AND p.longitude IS NOT NULL
  ),
  within AS (
    SELECT n.*, p.radius_km,
           ROW_NUMBER() OVER (PARTITION BY target_bay ORDER BY dist_km ASC) AS rn
    FROM neighbors n JOIN params p ON n.dist_km <= p.radius_km
  ),
  topk AS (SELECT * FROM within WHERE rn <= (SELECT k FROM params)),
  vote AS (
    SELECT target_bay, zone_id, COUNT(*) AS votes, MIN(dist_km) AS min_dist
    FROM topk GROUP BY target_bay, zone_id
  ),
  pick AS (
    SELECT target_bay, zone_id
    FROM (
      SELECT target_bay, zone_id, votes, min_dist,
             ROW_NUMBER() OVER (PARTITION BY target_bay ORDER BY votes DESC, min_dist ASC) AS rnk
      FROM vote
    ) x WHERE rnk = 1
  )
  UPDATE parking_bay pb
  SET zone_id = p.zone_id
  FROM pick p
  WHERE pb.bay_id = p.target_bay
    AND pb.zone_id IS NULL
  RETURNING 1 INTO affected;

  GET DIAGNOSTICS affected = ROW_COUNT;
  RETURN affected;
END $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bay_sensor; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bay_sensor (
    sensor_id bigint NOT NULL,
    bay_id text,
    zone_number text,
    status_description text,
    status_timestamp_raw text,
    lastupdated_raw text,
    latitude numeric(9,6),
    longitude numeric(9,6),
    location_raw text,
    status_timestamp_ts timestamp with time zone,
    last_updated_ts timestamp with time zone
);


--
-- Name: bay_sensor_sensor_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bay_sensor_sensor_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bay_sensor_sensor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bay_sensor_sensor_id_seq OWNED BY public.bay_sensor.sensor_id;


--
-- Name: parking_bay; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parking_bay (
    bay_id text NOT NULL,
    street_segment_id bigint,
    road_segment_desc text,
    latitude numeric(9,6),
    longitude numeric(9,6),
    location_raw text,
    last_updated_raw text,
    zone_id text,
    last_updated_ts timestamp with time zone
);


--
-- Name: parking_zone; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parking_zone (
    zone_id text NOT NULL,
    zone_name text
);


--
-- Name: population_raw; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.population_raw (
    region text,
    area_km2 numeric(12,4),
    y2001 text,
    y2002 text,
    y2003 text,
    y2004 text,
    y2005 text,
    y2006 text,
    y2007 text,
    y2008 text,
    y2009 text,
    y2010 text,
    y2011 text,
    y2012 text,
    y2013 text,
    y2014 text,
    y2015 text,
    y2016 text,
    y2017 text,
    y2018 text,
    y2019 text,
    y2020 text,
    y2021 text
);


--
-- Name: population_stats; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.population_stats AS
 SELECT population_raw.region,
    2001 AS year,
    (NULLIF(population_raw.y2001, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2001 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2002 AS year,
    (NULLIF(population_raw.y2002, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2002 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2003 AS year,
    (NULLIF(population_raw.y2003, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2003 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2004 AS year,
    (NULLIF(population_raw.y2004, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2004 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2005 AS year,
    (NULLIF(population_raw.y2005, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2005 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2006 AS year,
    (NULLIF(population_raw.y2006, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2006 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2007 AS year,
    (NULLIF(population_raw.y2007, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2007 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2008 AS year,
    (NULLIF(population_raw.y2008, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2008 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2009 AS year,
    (NULLIF(population_raw.y2009, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2009 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2010 AS year,
    (NULLIF(population_raw.y2010, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2010 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2011 AS year,
    (NULLIF(population_raw.y2011, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2011 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2012 AS year,
    (NULLIF(population_raw.y2012, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2012 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2013 AS year,
    (NULLIF(population_raw.y2013, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2013 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2014 AS year,
    (NULLIF(population_raw.y2014, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2014 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2015 AS year,
    (NULLIF(population_raw.y2015, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2015 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2016 AS year,
    (NULLIF(population_raw.y2016, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2016 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2017 AS year,
    (NULLIF(population_raw.y2017, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2017 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2018 AS year,
    (NULLIF(population_raw.y2018, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2018 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2019 AS year,
    (NULLIF(population_raw.y2019, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2019 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2020 AS year,
    (NULLIF(population_raw.y2020, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2020 IS NOT NULL)
UNION ALL
 SELECT population_raw.region,
    2021 AS year,
    (NULLIF(population_raw.y2021, ''::text))::integer AS population
   FROM public.population_raw
  WHERE (population_raw.y2021 IS NOT NULL);


--
-- Name: sign_plate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sign_plate (
    sign_id bigint NOT NULL,
    zone_id text NOT NULL,
    restriction_days text,
    time_restrictions_start text,
    time_restrictions_finish text,
    restriction_display text
);


--
-- Name: sign_plate_sign_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sign_plate_sign_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sign_plate_sign_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sign_plate_sign_id_seq OWNED BY public.sign_plate.sign_id;


--
-- Name: street_segment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.street_segment (
    street_segment_id bigint NOT NULL,
    on_street text,
    street_from text,
    street_to text
);


--
-- Name: v_bay_with_zone; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_bay_with_zone AS
 SELECT b.bay_id,
    b.street_segment_id,
    b.zone_id,
    b.latitude,
    b.longitude,
    b.last_updated_ts,
    s.on_street,
    s.street_from,
    s.street_to
   FROM (public.parking_bay b
     LEFT JOIN public.street_segment s ON ((s.street_segment_id = b.street_segment_id)));


--
-- Name: v_sensor_latest; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_sensor_latest AS
 SELECT DISTINCT ON (bay_id) bay_id,
    zone_number,
    status_description,
    status_timestamp_ts,
    last_updated_ts,
    location_raw
   FROM public.bay_sensor
  WHERE (status_timestamp_ts IS NOT NULL)
  ORDER BY bay_id, status_timestamp_ts DESC NULLS LAST;


--
-- Name: v_bay_with_latest_status; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_bay_with_latest_status AS
 SELECT b.bay_id,
    b.street_segment_id,
    b.zone_id,
    b.latitude,
    b.longitude,
    b.last_updated_ts,
    b.on_street,
    b.street_from,
    b.street_to,
    sl.status_description,
    sl.status_timestamp_ts
   FROM (public.v_bay_with_zone b
     LEFT JOIN public.v_sensor_latest sl USING (bay_id));


--
-- Name: vehicle_registration_vic; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vehicle_registration_vic (
    reg_id bigint NOT NULL,
    state text NOT NULL,
    vehicle_type text NOT NULL,
    year smallint NOT NULL,
    vehicle_count integer NOT NULL
);


--
-- Name: vehicle_registration_vic_reg_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vehicle_registration_vic_reg_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vehicle_registration_vic_reg_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vehicle_registration_vic_reg_id_seq OWNED BY public.vehicle_registration_vic.reg_id;


--
-- Name: zone_street_link; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.zone_street_link (
    zone_id text NOT NULL,
    street_segment_id bigint NOT NULL
);


--
-- Name: bay_sensor sensor_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bay_sensor ALTER COLUMN sensor_id SET DEFAULT nextval('public.bay_sensor_sensor_id_seq'::regclass);


--
-- Name: sign_plate sign_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_plate ALTER COLUMN sign_id SET DEFAULT nextval('public.sign_plate_sign_id_seq'::regclass);


--
-- Name: vehicle_registration_vic reg_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicle_registration_vic ALTER COLUMN reg_id SET DEFAULT nextval('public.vehicle_registration_vic_reg_id_seq'::regclass);


--
-- Name: bay_sensor bay_sensor_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bay_sensor
    ADD CONSTRAINT bay_sensor_pkey PRIMARY KEY (sensor_id);


--
-- Name: parking_bay parking_bay_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parking_bay
    ADD CONSTRAINT parking_bay_pkey PRIMARY KEY (bay_id);


--
-- Name: parking_zone parking_zone_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parking_zone
    ADD CONSTRAINT parking_zone_pkey PRIMARY KEY (zone_id);


--
-- Name: sign_plate sign_plate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_plate
    ADD CONSTRAINT sign_plate_pkey PRIMARY KEY (sign_id);


--
-- Name: street_segment street_segment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.street_segment
    ADD CONSTRAINT street_segment_pkey PRIMARY KEY (street_segment_id);


--
-- Name: vehicle_registration_vic vehicle_registration_vic_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicle_registration_vic
    ADD CONSTRAINT vehicle_registration_vic_pkey PRIMARY KEY (reg_id);


--
-- Name: vehicle_registration_vic vehicle_registration_vic_state_vehicle_type_year_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vehicle_registration_vic
    ADD CONSTRAINT vehicle_registration_vic_state_vehicle_type_year_key UNIQUE (state, vehicle_type, year);


--
-- Name: zone_street_link zone_street_link_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_street_link
    ADD CONSTRAINT zone_street_link_pkey PRIMARY KEY (zone_id, street_segment_id);


--
-- Name: ix_bay_street; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bay_street ON public.parking_bay USING btree (street_segment_id);


--
-- Name: ix_bay_zone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bay_zone ON public.parking_bay USING btree (zone_id);


--
-- Name: ix_sensor_bay; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sensor_bay ON public.bay_sensor USING btree (bay_id);


--
-- Name: ix_sensor_bay_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sensor_bay_time ON public.bay_sensor USING btree (bay_id, status_timestamp_ts DESC);


--
-- Name: ix_sensor_zone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sensor_zone ON public.bay_sensor USING btree (zone_number);


--
-- Name: ix_sign_zone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sign_zone ON public.sign_plate USING btree (zone_id);


--
-- Name: ix_vic_reg_year_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vic_reg_year_type ON public.vehicle_registration_vic USING btree (year, vehicle_type);


--
-- Name: bay_sensor bay_sensor_bay_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bay_sensor
    ADD CONSTRAINT bay_sensor_bay_id_fkey FOREIGN KEY (bay_id) REFERENCES public.parking_bay(bay_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: parking_bay fk_parking_bay_zone; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parking_bay
    ADD CONSTRAINT fk_parking_bay_zone FOREIGN KEY (zone_id) REFERENCES public.parking_zone(zone_id);


--
-- Name: parking_bay parking_bay_street_segment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parking_bay
    ADD CONSTRAINT parking_bay_street_segment_id_fkey FOREIGN KEY (street_segment_id) REFERENCES public.street_segment(street_segment_id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: sign_plate sign_plate_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sign_plate
    ADD CONSTRAINT sign_plate_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.parking_zone(zone_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: zone_street_link zone_street_link_street_segment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_street_link
    ADD CONSTRAINT zone_street_link_street_segment_id_fkey FOREIGN KEY (street_segment_id) REFERENCES public.street_segment(street_segment_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: zone_street_link zone_street_link_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_street_link
    ADD CONSTRAINT zone_street_link_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.parking_zone(zone_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

