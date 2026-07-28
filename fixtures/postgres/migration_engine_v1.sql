--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg120+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg120+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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

CREATE SCHEMA public;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version integer NOT NULL,
    checksum text NOT NULL,
    applied_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT schema_migrations_checksum_check CHECK ((checksum ~ '^[0-9a-f]{64}$'::text)),
    CONSTRAINT schema_migrations_version_check CHECK ((version >= 1))
);


--
-- Name: strata_migration_sentinel; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.strata_migration_sentinel (
    singleton boolean DEFAULT true NOT NULL,
    message text NOT NULL,
    CONSTRAINT strata_migration_sentinel_singleton_check CHECK (singleton)
);


--
-- Data for Name: schema_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.schema_migrations VALUES (1, '3110ca52ef12fea7826b33d5ccc580cdbc1d46559770b5a51b20396ad60b51e8', '2026-07-27 23:30:00+00');


--
-- Data for Name: strata_migration_sentinel; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.strata_migration_sentinel VALUES (true, 'migration engine ready');


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: strata_migration_sentinel strata_migration_sentinel_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.strata_migration_sentinel
    ADD CONSTRAINT strata_migration_sentinel_pkey PRIMARY KEY (singleton);


--
-- PostgreSQL database dump complete
--
