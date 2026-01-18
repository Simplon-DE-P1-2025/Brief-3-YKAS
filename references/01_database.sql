-- ============================================================
-- 01_schema.sql — Schéma FINAL (PostgreSQL v10)
-- Ordre: ENUM → Dimensions → Tables métier → Index
-- Compatible Docker / Render / Local
-- ============================================================

-- -------------------------------
-- 0) ENUM calendaires (1x)
-- -------------------------------
DROP TYPE IF EXISTS mois_francais CASCADE;
CREATE TYPE mois_francais AS enum(
  'Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août',
  'Septembre','Octobre','Novembre','Décembre'
);

DROP TYPE IF EXISTS jours_semaine_francais CASCADE;
CREATE TYPE jours_semaine_francais AS enum(
  'Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'
);

DROP TYPE IF EXISTS phase_journee CASCADE;
CREATE TYPE phase_journee AS enum('matinée','déjeuner','après-midi','nuit');

-- ----------------------------------------------------------------------
-- 1) Création des tables de dimensions (dim_*) (vides)
-- ----------------------------------------------------------------------
DROP TABLE IF EXISTS public.dim_temps CASCADE;
DROP TABLE IF EXISTS public.dim_maree_port CASCADE;
DROP TABLE IF EXISTS public.dim_maree_categorie CASCADE;
DROP TABLE IF EXISTS public.dim_prefecture_maritime CASCADE;

DROP TABLE IF EXISTS public.dim_type_flotteur CASCADE;
DROP TABLE IF EXISTS public.dim_categorie_flotteur CASCADE;
DROP TABLE IF EXISTS public.dim_resultat_flotteur CASCADE;
DROP TABLE IF EXISTS public.dim_pavillon CASCADE;

DROP TABLE IF EXISTS public.dim_resultat_humain CASCADE;
DROP TABLE IF EXISTS public.dim_categorie_personne CASCADE;

DROP TABLE IF EXISTS public.dim_categorie_evenement CASCADE;
DROP TABLE IF EXISTS public.dim_evenement CASCADE;
DROP TABLE IF EXISTS public.dim_cross CASCADE;
DROP TABLE IF EXISTS public.dim_qui_alerte CASCADE;
DROP TABLE IF EXISTS public.dim_moyen_alerte CASCADE;

DROP TABLE IF EXISTS public.dim_system_source CASCADE;
DROP TABLE IF EXISTS public.dim_vent_direction_categorie CASCADE;
DROP TABLE IF EXISTS public.dim_type_operation CASCADE;
CREATE TABLE public.dim_type_operation (
  type_operation_id bigserial PRIMARY KEY,
  label varchar(10) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_vent_direction_categorie (
  vent_direction_categorie_id bigserial PRIMARY KEY,
  label varchar(20) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_system_source (
  system_source_id bigserial PRIMARY KEY,
  code varchar(50) NOT NULL UNIQUE,
  label varchar(100),
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_cross (
  cross_id bigserial PRIMARY KEY,
  label varchar(50) NOT NULL UNIQUE,
  annee_debut smallint,
  annee_fin varchar(15),
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_evenement (
  evenement_id bigserial PRIMARY KEY,
  label varchar(200) NOT NULL UNIQUE,
  present_secmar boolean,
  present_seamis boolean,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_categorie_evenement (
  categorie_evenement_id bigserial PRIMARY KEY,
  label varchar(80) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_moyen_alerte (
  moyen_alerte_id bigserial PRIMARY KEY,
  label varchar(200) NOT NULL UNIQUE,
  present_secmar boolean,
  present_seamis boolean,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_qui_alerte (
  qui_alerte_id bigserial PRIMARY KEY,
  label varchar(200) NOT NULL UNIQUE,
  present_secmar boolean,
  present_seamis boolean,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_categorie_personne (
  categorie_personne_id bigserial PRIMARY KEY,
  label varchar(80) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_resultat_humain (
  resultat_humain_id bigserial PRIMARY KEY,
  label varchar(120) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_pavillon (
  pavillon_id bigserial PRIMARY KEY,
  label varchar(30) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_resultat_flotteur (
  resultat_flotteur_id bigserial PRIMARY KEY,
  label varchar(120) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_categorie_flotteur (
  categorie_flotteur_id bigserial PRIMARY KEY,
  label varchar(50) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_type_flotteur (
  type_flotteur_id bigserial PRIMARY KEY,
  label varchar(120) NOT NULL UNIQUE,
  present_secmar boolean,
  present_seamis boolean,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_prefecture_maritime (
  prefecture_maritime_id bigserial PRIMARY KEY,
  label varchar(30) NOT NULL UNIQUE
);
CREATE TABLE public.dim_maree_categorie (
  maree_categorie_id bigserial PRIMARY KEY,
  label varchar(20) NOT NULL UNIQUE
);

CREATE TABLE public.dim_maree_port (
  maree_port_id bigserial PRIMARY KEY,
  label varchar(120) NOT NULL UNIQUE,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE public.dim_temps (
  temps_id bigserial PRIMARY KEY,
  date date NOT NULL,
  annee smallint NOT NULL,
  mois smallint NOT NULL,
  jour smallint NOT NULL,
  mois_texte mois_francais NOT NULL,
  semaine smallint NOT NULL,
  annee_semaine varchar(7) NOT NULL,
  jour_semaine jours_semaine_francais NOT NULL,
  est_weekend boolean NOT NULL,
  est_jour_ferie boolean NOT NULL,
  est_vacances_scolaires boolean,
  phase_journee phase_journee,
  CONSTRAINT uq_dim_temps UNIQUE (date, phase_journee),
  CONSTRAINT chk_dim_temps_mois CHECK (mois BETWEEN 1 AND 12),
  CONSTRAINT chk_dim_temps_jour CHECK (jour BETWEEN 1 AND 31),
  CONSTRAINT chk_dim_temps_semaine CHECK (semaine BETWEEN 1 AND 53)
);

-- --------------------------------------------------------
-- 2) Création des tables métier (4) (vides)
-- --------------------------------------------------------
DROP TABLE IF EXISTS public.operations_stats CASCADE;
DROP TABLE IF EXISTS public.resultats_humain CASCADE;
DROP TABLE IF EXISTS public.flotteurs CASCADE;
DROP TABLE IF EXISTS public.operations CASCADE;

CREATE TABLE public.operations (
  operation_id bigint PRIMARY KEY,

  type_operation_id bigint REFERENCES public.dim_type_operation(type_operation_id),
  pourquoi_alerte varchar(50),

  moyen_alerte_id bigint NOT NULL REFERENCES public.dim_moyen_alerte(moyen_alerte_id),
  qui_alerte_id bigint NOT NULL REFERENCES public.dim_qui_alerte(qui_alerte_id),
  categorie_qui_alerte varchar(100) NOT NULL,

  cross_id bigint NOT NULL REFERENCES public.dim_cross(cross_id),
  departement varchar(100),
  est_metropolitain boolean,

  evenement_id bigint NOT NULL REFERENCES public.dim_evenement(evenement_id),
  categorie_evenement_id bigint NOT NULL REFERENCES public.dim_categorie_evenement(categorie_evenement_id),

  autorite varchar(100) NOT NULL,
  seconde_autorite varchar(100),
  zone_responsabilite varchar(50) NOT NULL,

  latitude numeric(7,4),
  longitude numeric(7,4),

  vent_direction smallint,
  vent_direction_categorie_id bigint REFERENCES public.dim_vent_direction_categorie(vent_direction_categorie_id),

  vent_force smallint,
  mer_force smallint,

  date_heure_reception_alerte timestamp with time zone NOT NULL,
  date_heure_fin_operation timestamp with time zone NOT NULL,

  numero_sitrep smallint NOT NULL,
  cross_sitrep varchar(50) NOT NULL,
  fuseau_horaire varchar(25) NOT NULL,

  system_source_id bigint REFERENCES public.dim_system_source(system_source_id),

  CONSTRAINT chk_latitude_range CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90)),
  CONSTRAINT chk_longitude_range CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180)),
  CONSTRAINT chk_dates_coherentes CHECK (date_heure_fin_operation >= date_heure_reception_alerte),
  CONSTRAINT chk_vent_dir_range CHECK (vent_direction IS NULL OR (vent_direction BETWEEN 0 AND 360)),
  CONSTRAINT chk_vent_force_range CHECK (vent_force IS NULL OR (vent_force BETWEEN 0 AND 12)),
  CONSTRAINT chk_mer_force_range CHECK (mer_force IS NULL OR (mer_force BETWEEN 0 AND 9)),
  CONSTRAINT chk_numero_sitrep_min CHECK (numero_sitrep >= 1)
);

CREATE TABLE public.flotteurs (
  flotteur_id bigserial PRIMARY KEY,
  operation_id bigint NOT NULL REFERENCES public.operations(operation_id) ON DELETE CASCADE,
  numero_ordre smallint,
  pavillon_id bigint REFERENCES public.dim_pavillon(pavillon_id),
  resultat_flotteur_id bigint NOT NULL REFERENCES public.dim_resultat_flotteur(resultat_flotteur_id),
  type_flotteur_id bigint NOT NULL REFERENCES public.dim_type_flotteur(type_flotteur_id),
  categorie_flotteur_id bigint NOT NULL REFERENCES public.dim_categorie_flotteur(categorie_flotteur_id),
  numero_immatriculation varchar(40)
);

CREATE TABLE public.resultats_humain (
  resultat_humain_row_id bigserial PRIMARY KEY,
  operation_id bigint NOT NULL REFERENCES public.operations(operation_id) ON DELETE CASCADE,
  categorie_personne_id bigint NOT NULL REFERENCES public.dim_categorie_personne(categorie_personne_id),
  resultat_humain_id bigint NOT NULL REFERENCES public.dim_resultat_humain(resultat_humain_id),
  nombre smallint NOT NULL,
  dont_nombre_blesse smallint NOT NULL,
  CONSTRAINT chk_res_humain_nonneg CHECK (nombre >= 0 AND dont_nombre_blesse >= 0),
  CONSTRAINT chk_blesse_leq_nombre CHECK (dont_nombre_blesse <= nombre)
);

CREATE TABLE public.operations_stats (
  operation_id bigint PRIMARY KEY REFERENCES public.operations(operation_id) ON DELETE CASCADE,
  temps_id bigint NOT NULL REFERENCES public.dim_temps(temps_id),

  concerne_plongee boolean NOT NULL,
  distance_cote_metres int,
  distance_cote_milles_nautiques numeric(6,2),

  est_dans_stm boolean NOT NULL,
  nom_stm varchar(50),
  est_dans_dst boolean NOT NULL,
  nom_dst varchar(50),

  maree_port_id bigint REFERENCES public.dim_maree_port(maree_port_id),
  maree_coefficient smallint,
  maree_categorie_id bigint REFERENCES public.dim_maree_categorie(maree_categorie_id),
  prefecture_maritime_id bigint REFERENCES public.dim_prefecture_maritime(prefecture_maritime_id),

  -- -----------------------------
  -- Indicateurs clés (KPI)
  -- -----------------------------
  nombre_personnes_blessees smallint NOT NULL,
  nombre_personnes_assistees smallint NOT NULL,
  nombre_personnes_decedees smallint NOT NULL,
  nombre_personnes_decedees_accidentellement smallint NOT NULL,
  nombre_personnes_decedees_naturellement smallint NOT NULL,
  nombre_personnes_disparues smallint NOT NULL,
  nombre_personnes_impliquees_dans_fausse_alerte smallint NOT NULL,
  nombre_personnes_retrouvees smallint NOT NULL,
  nombre_personnes_secourues smallint NOT NULL,
  nombre_personnes_tirees_daffaire_seule smallint NOT NULL,
  nombre_personnes_tous_deces smallint NOT NULL,
  nombre_personnes_tous_deces_ou_disparues smallint NOT NULL,
  nombre_personnes_impliquees smallint NOT NULL,

  nombre_personnes_blessees_sans_clandestins smallint NOT NULL,
  nombre_personnes_assistees_sans_clandestins smallint NOT NULL,
  nombre_personnes_decedees_sans_clandestins smallint NOT NULL,
  nombre_personnes_decedees_accidentellement_sans_clandestins smallint NOT NULL,
  nombre_personnes_decedees_naturellement_sans_clandestins smallint NOT NULL,
  nombre_personnes_disparues_sans_clandestins smallint NOT NULL,
  nombre_personnes_impliquees_dans_fausse_alerte_sans_clandestins smallint NOT NULL,
  nombre_personnes_retrouvees_sans_clandestins smallint NOT NULL,
  nombre_personnes_secourues_sans_clandestins smallint NOT NULL,
  nombre_personnes_tirees_daffaire_seule_sans_clandestins smallint NOT NULL,
  nombre_personnes_tous_deces_sans_clandestins smallint NOT NULL,
  nombre_personnes_tous_deces_ou_disparues_sans_clandestins smallint NOT NULL,
  nombre_personnes_impliquees_sans_clandestins smallint NOT NULL,

  nombre_flotteurs_commerce_impliques smallint NOT NULL,
  nombre_flotteurs_peche_impliques smallint NOT NULL,
  nombre_flotteurs_plaisance_impliques smallint NOT NULL,
  nombre_flotteurs_loisirs_nautiques_impliques smallint NOT NULL,
  nombre_aeronefs_impliques smallint NOT NULL,
  nombre_flotteurs_autre_impliques smallint NOT NULL,
  nombre_flotteurs_annexe_impliques smallint NOT NULL,
  nombre_flotteurs_autre_loisir_nautique_impliques smallint NOT NULL,
  nombre_flotteurs_canoe_kayak_aviron_impliques smallint NOT NULL,
  nombre_flotteurs_engin_de_plage_impliques smallint NOT NULL,
  nombre_flotteurs_kitesurf_impliques smallint NOT NULL,
  nombre_flotteurs_plaisance_voile_legere_impliques smallint NOT NULL,
  nombre_flotteurs_plaisance_a_moteur_moins_8m_impliques smallint NOT NULL,
  nombre_flotteurs_plaisance_a_moteur_plus_8m_impliques smallint NOT NULL,
  nombre_flotteurs_plaisance_a_voile_impliques smallint NOT NULL,
  nombre_flotteurs_planche_a_voile_impliques smallint NOT NULL,
  nombre_flotteurs_ski_nautique_impliques smallint NOT NULL,
  nombre_flotteurs_surf_impliques smallint NOT NULL,
  nombre_flotteurs_vehicule_nautique_a_moteur_impliques smallint NOT NULL,

  sans_flotteur_implique boolean NOT NULL,

  CONSTRAINT chk_stats_distances_nonneg CHECK (
    (distance_cote_metres IS NULL OR distance_cote_metres >= 0)
    AND (distance_cote_milles_nautiques IS NULL OR distance_cote_milles_nautiques >= 0)
  ),
  CONSTRAINT chk_maree_coeff_range CHECK (
    maree_coefficient IS NULL OR (maree_coefficient BETWEEN 20 AND 120)
  )
);
-- -------------------------
-- 3) Indexes
-- -------------------------
CREATE INDEX IF NOT EXISTS idx_dim_temps_date ON public.dim_temps(date);

CREATE INDEX IF NOT EXISTS idx_operations_cross_id ON public.operations(cross_id);
CREATE INDEX IF NOT EXISTS idx_operations_evenement_id ON public.operations(evenement_id);
CREATE INDEX IF NOT EXISTS idx_operations_moyen_alerte_id ON public.operations(moyen_alerte_id);
CREATE INDEX IF NOT EXISTS idx_operations_qui_alerte_id ON public.operations(qui_alerte_id);
CREATE INDEX IF NOT EXISTS idx_operations_date_reception ON public.operations(date_heure_reception_alerte);
CREATE INDEX IF NOT EXISTS idx_operations_date_fin ON public.operations(date_heure_fin_operation);

CREATE INDEX IF NOT EXISTS idx_flotteurs_operation_id ON public.flotteurs(operation_id);
CREATE INDEX IF NOT EXISTS idx_res_humain_operation_id ON public.resultats_humain(operation_id);
CREATE INDEX IF NOT EXISTS idx_operations_stats_temps_id ON public.operations_stats(temps_id);

-- ---------------------------------------------
-- 4) Données d’initialisation (seeds)
-- ---------------------------------------------
INSERT INTO public.dim_system_source(code, label)
VALUES ('secmarweb','SECMAR Web'), ('seamis_json','SeaMIS JSON')
ON CONFLICT (code) DO NOTHING;

INSERT INTO public.dim_pavillon(label)
VALUES ('Étranger'), ('Français')
ON CONFLICT (label) DO NOTHING;

