-- 02_schéma.sql — Mapping (TEMP + COPY) — Postgres v10
-- Ordre de création des tables : operations → flotteurs → resultats_humain → operations_stats

-- ============================================================
-- A) Création de la table TEMP --> OPERATIONS 
-- CSV: operations.csv 
-- ============================================================

CREATE TEMP TABLE tmp_operations_brut (
  operation_id text,
  type_operation text,
  pourquoi_alerte text,
  moyen_alerte text,
  qui_alerte text,
  categorie_qui_alerte text,
  cross text,
  departement text,
  est_metropolitain text,
  evenement text,
  categorie_evenement text,
  autorite text,
  seconde_autorite text,
  zone_responsabilite text,
  latitude text,
  longitude text,
  vent_direction text,
  vent_direction_categorie text,
  vent_force text,
  mer_force text,
  date_heure_reception_alerte text,
  date_heure_fin_operation text,
  numero_sitrep text,
  cross_sitrep text,
  fuseau_horaire text,
  systeme_source text
);


-- Import des données brutes dans la table temporaire `tmp_operations_brut`
-- à partir du fichier CSV situé dans le répertoire du serveur Postgres.
-- Le fichier contient une ligne d'en-têtes.


COPY tmp_operations_brut FROM '/data/operations.csv' WITH (FORMAT csv, HEADER true);

-- --------------------------------------------
-- Alimenter les tables de dimensions
-- --------------------------------------------
INSERT INTO public.dim_type_operation(label)
SELECT DISTINCT type_operation
FROM tmp_operations_brut
WHERE type_operation IS NOT NULL AND type_operation <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_moyen_alerte(label)
SELECT DISTINCT moyen_alerte
FROM tmp_operations_brut
WHERE moyen_alerte IS NOT NULL AND moyen_alerte <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_qui_alerte(label)
SELECT DISTINCT qui_alerte
FROM tmp_operations_brut
WHERE qui_alerte IS NOT NULL AND qui_alerte <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_cross(label)
SELECT DISTINCT cross
FROM tmp_operations_brut
WHERE cross IS NOT NULL AND cross <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_evenement(label)
SELECT DISTINCT evenement
FROM tmp_operations_brut
WHERE evenement IS NOT NULL AND evenement <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_categorie_evenement(label)
SELECT DISTINCT categorie_evenement
FROM tmp_operations_brut
WHERE categorie_evenement IS NOT NULL AND categorie_evenement <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_vent_direction_categorie(label)
SELECT DISTINCT vent_direction_categorie
FROM tmp_operations_brut
WHERE vent_direction_categorie IS NOT NULL AND vent_direction_categorie <> ''
ON CONFLICT (label) DO NOTHING;

-- système source: stockage dans code

INSERT INTO public.dim_system_source(code)
SELECT DISTINCT systeme_source
FROM tmp_operations_brut
WHERE systeme_source IS NOT NULL AND systeme_source <> ''
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------
-- Alimenter la table métier (mapping label -> id)
-- ---------------------------------------------------------------
INSERT INTO public.operations (
  operation_id,
  type_operation_id,
  pourquoi_alerte,
  moyen_alerte_id,
  qui_alerte_id,
  categorie_qui_alerte,
  cross_id,
  departement,
  est_metropolitain,
  evenement_id,
  categorie_evenement_id,
  autorite,
  seconde_autorite,
  zone_responsabilite,
  latitude,
  longitude,
  vent_direction,
  vent_direction_categorie_id,
  vent_force,
  mer_force,
  date_heure_reception_alerte,
  date_heure_fin_operation,
  numero_sitrep,
  cross_sitrep,
  fuseau_horaire,
  system_source_id
)
SELECT
  o.operation_id::bigint,
  dto.type_operation_id,
  NULLIF(o.pourquoi_alerte,''),
  dma.moyen_alerte_id,
  dqa.qui_alerte_id,
  o.categorie_qui_alerte,
  dc.cross_id,
  NULLIF(o.departement,''),
  NULLIF(o.est_metropolitain,'')::boolean,
  dev.evenement_id,
  dce.categorie_evenement_id,
  o.autorite,
  NULLIF(o.seconde_autorite,''),
  o.zone_responsabilite,
  NULLIF(o.latitude,'')::numeric,
  NULLIF(o.longitude,'')::numeric,
  NULLIF(o.vent_direction,'')::smallint,
  dvd.vent_direction_categorie_id,
  NULLIF(o.vent_force,'')::smallint,
  NULLIF(o.mer_force,'')::smallint,
  o.date_heure_reception_alerte::timestamptz,
  o.date_heure_fin_operation::timestamptz,
  o.numero_sitrep::smallint,
  o.cross_sitrep,
  o.fuseau_horaire,
  dss.system_source_id
FROM tmp_operations_brut o
LEFT JOIN public.dim_type_operation dto ON dto.label = o.type_operation
JOIN public.dim_moyen_alerte dma ON dma.label = o.moyen_alerte
JOIN public.dim_qui_alerte dqa ON dqa.label = o.qui_alerte
JOIN public.dim_cross dc ON dc.label = o.cross
JOIN public.dim_evenement dev ON dev.label = o.evenement
JOIN public.dim_categorie_evenement dce ON dce.label = o.categorie_evenement
LEFT JOIN public.dim_vent_direction_categorie dvd ON dvd.label = o.vent_direction_categorie
LEFT JOIN public.dim_system_source dss ON dss.code = o.systeme_source;

-- (Optionnel) pour supprimer la temp table en fin de chargement
-- DROP TABLE IF EXISTS tmp_operations_brut;

-- ============================================================
-- B) Création de la table TEMP --> FLOTTTEURS 
-- CSV: operation_id, pavillon, resultat_flotteur, type_flotteur,
--      categorie_flotteur, numero_immatriculation, numero_ordre
-- ============================================================

CREATE TEMP TABLE tmp_flotteurs_brut (
  operation_id text,
  pavillon text,
  resultat_flotteur text,
  type_flotteur text,
  categorie_flotteur text,
  numero_immatriculation text,
  numero_ordre text
);

-- Import des données brutes dans la table temporaire `tmp_flotteurs_brut`

COPY tmp_flotteurs_brut FROM '/data/flotteurs.csv' WITH (FORMAT csv, HEADER true);

-- --------------------------------------------
-- Alimenter les tables de dimensions
-- --------------------------------------------
INSERT INTO public.dim_pavillon(label)
SELECT DISTINCT pavillon FROM tmp_flotteurs_brut
WHERE pavillon IS NOT NULL AND pavillon <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_resultat_flotteur(label)
SELECT DISTINCT resultat_flotteur FROM tmp_flotteurs_brut
WHERE resultat_flotteur IS NOT NULL AND resultat_flotteur <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_type_flotteur(label)
SELECT DISTINCT type_flotteur FROM tmp_flotteurs_brut
WHERE type_flotteur IS NOT NULL AND type_flotteur <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_categorie_flotteur(label)
SELECT DISTINCT categorie_flotteur FROM tmp_flotteurs_brut
WHERE categorie_flotteur IS NOT NULL AND categorie_flotteur <> ''
ON CONFLICT (label) DO NOTHING;

-- ---------------------------------------------------------------
-- Alimenter la table métier (mapping label -> id)
-- ---------------------------------------------------------------
INSERT INTO public.flotteurs (
  operation_id,
  numero_ordre,
  pavillon_id,
  resultat_flotteur_id,
  type_flotteur_id,
  categorie_flotteur_id,
  numero_immatriculation
)
SELECT
  f.operation_id::bigint,
  NULLIF(f.numero_ordre,'')::smallint,
  dp.pavillon_id,
  drf.resultat_flotteur_id,
  dtf.type_flotteur_id,
  dcf.categorie_flotteur_id,
  NULLIF(f.numero_immatriculation,'')
FROM tmp_flotteurs_brut f
JOIN public.operations o ON o.operation_id = f.operation_id::bigint
LEFT JOIN public.dim_pavillon dp ON dp.label = f.pavillon
JOIN public.dim_resultat_flotteur drf ON drf.label = f.resultat_flotteur
JOIN public.dim_type_flotteur dtf ON dtf.label = f.type_flotteur
JOIN public.dim_categorie_flotteur dcf ON dcf.label = f.categorie_flotteur;

-- ============================================================
-- C) Création de la table TEMP  RESULTATS_HUMAIN 
-- CSV: operation_id, categorie_personne, resultat_humain, nombre, dont_nombre_blesse
-- ============================================================

CREATE TEMP TABLE tmp_resultats_humain_brut (
  operation_id text,
  categorie_personne text,
  resultat_humain text,
  nombre text,
  dont_nombre_blesse text
);

-- Import des données brutes dans la table temporaire `tmp_resultats_humain_brut`

COPY tmp_resultats_humain_brut FROM '/data/resultats_humain.csv' WITH (FORMAT csv, HEADER true);

-- --------------------------------------------
-- Alimenter les tables de dimensions
-- --------------------------------------------
INSERT INTO public.dim_categorie_personne(label)
SELECT DISTINCT categorie_personne FROM tmp_resultats_humain_brut
WHERE categorie_personne IS NOT NULL AND categorie_personne <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_resultat_humain(label)
SELECT DISTINCT resultat_humain FROM tmp_resultats_humain_brut
WHERE resultat_humain IS NOT NULL AND resultat_humain <> ''
ON CONFLICT (label) DO NOTHING;

-- ---------------------------------------------------------------
-- Alimenter la table métier (mapping label -> id)
-- ---------------------------------------------------------------
INSERT INTO public.resultats_humain (
  operation_id,
  categorie_personne_id,
  resultat_humain_id,
  nombre,
  dont_nombre_blesse
)
SELECT
  r.operation_id::bigint,
  dcp.categorie_personne_id,
  drh.resultat_humain_id,
  r.nombre::smallint,
  r.dont_nombre_blesse::smallint
FROM tmp_resultats_humain_brut r
JOIN public.operations o ON o.operation_id = r.operation_id::bigint
JOIN public.dim_categorie_personne dcp ON dcp.label = r.categorie_personne
JOIN public.dim_resultat_humain drh ON drh.label = r.resultat_humain;

-- ============================================================
-- D) Création de la table TEMP  OPERATIONS_STATS 
-- CSV (début): operation_id, date, annee, mois, jour, mois_texte, semaine, annee_semaine,
--             jour_semaine, est_weekend, est_jour_ferie, est_vacances_scolaires, phase_journee,
--             ... maree_port, maree_categorie, maree_coefficient, prefecture_maritime + indicateurs
-- ============================================================

CREATE TEMP TABLE tmp_operations_stats_brut (
  operation_id text,

  date text,
  annee text,
  mois text,
  jour text,
  mois_texte text,
  semaine text,
  annee_semaine text,
  jour_semaine text,
  est_weekend text,
  est_jour_ferie text,
  est_vacances_scolaires text,
  phase_journee text,

  concerne_plongee text,
  distance_cote_metres text,
  distance_cote_milles_nautiques text,
  est_dans_stm text,
  nom_stm text,
  est_dans_dst text,
  nom_dst text,

  maree_port text,
  maree_coefficient text,
  maree_categorie text,
  prefecture_maritime text,

  -- indicateurs (tous en text pour COPY)

  nombre_personnes_blessees text,
  nombre_personnes_assistees text,
  nombre_personnes_decedees text,
  nombre_personnes_decedees_accidentellement text,
  nombre_personnes_decedees_naturellement text,
  nombre_personnes_disparues text,
  nombre_personnes_impliquees_dans_fausse_alerte text,
  nombre_personnes_retrouvees text,
  nombre_personnes_secourues text,
  nombre_personnes_tirees_daffaire_seule text,
  nombre_personnes_tous_deces text,
  nombre_personnes_tous_deces_ou_disparues text,
  nombre_personnes_impliquees text,

  nombre_personnes_blessees_sans_clandestins text,
  nombre_personnes_assistees_sans_clandestins text,
  nombre_personnes_decedees_sans_clandestins text,
  nombre_personnes_decedees_accidentellement_sans_clandestins text,
  nombre_personnes_decedees_naturellement_sans_clandestins text,
  nombre_personnes_disparues_sans_clandestins text,
  nombre_personnes_impliquees_dans_fausse_alerte_sans_clandestins text,
  nombre_personnes_retrouvees_sans_clandestins text,
  nombre_personnes_secourues_sans_clandestins text,
  nombre_personnes_tirees_daffaire_seule_sans_clandestins text,
  nombre_personnes_tous_deces_sans_clandestins text,
  nombre_personnes_tous_deces_ou_disparues_sans_clandestins text,
  nombre_personnes_impliquees_sans_clandestins text,

  nombre_flotteurs_commerce_impliques text,
  nombre_flotteurs_peche_impliques text,
  nombre_flotteurs_plaisance_impliques text,
  nombre_flotteurs_loisirs_nautiques_impliques text,
  nombre_aeronefs_impliques text,
  nombre_flotteurs_autre_impliques text,
  nombre_flotteurs_annexe_impliques text,
  nombre_flotteurs_autre_loisir_nautique_impliques text,
  nombre_flotteurs_canoe_kayak_aviron_impliques text,
  nombre_flotteurs_engin_de_plage_impliques text,
  nombre_flotteurs_kitesurf_impliques text,
  nombre_flotteurs_plaisance_voile_legere_impliques text,
  nombre_flotteurs_plaisance_a_moteur_moins_8m_impliques text,
  nombre_flotteurs_plaisance_a_moteur_plus_8m_impliques text,
  nombre_flotteurs_plaisance_a_voile_impliques text,
  nombre_flotteurs_planche_a_voile_impliques text,
  nombre_flotteurs_ski_nautique_impliques text,
  nombre_flotteurs_surf_impliques text,
  nombre_flotteurs_vehicule_nautique_a_moteur_impliques text,

  sans_flotteur_implique text
);


-- Import des données brutes dans la table temporaire `tmp_operations_stats_brut`

COPY tmp_operations_stats_brut FROM '/data/operations_stats.csv' WITH (FORMAT csv, HEADER true);

-- 1) dim_temps

INSERT INTO public.dim_temps (
  date, annee, mois, jour, mois_texte, semaine, annee_semaine, jour_semaine,
  est_weekend, est_jour_ferie, est_vacances_scolaires, phase_journee
)
SELECT DISTINCT
  s.date::date,
  s.annee::smallint,
  s.mois::smallint,
  s.jour::smallint,
  s.mois_texte::mois_francais,
  s.semaine::smallint,
  s.annee_semaine,
  s.jour_semaine::jours_semaine_francais,
  s.est_weekend::boolean,
  s.est_jour_ferie::boolean,
  NULLIF(s.est_vacances_scolaires,'')::boolean,
  NULLIF(s.phase_journee,'')::phase_journee
FROM tmp_operations_stats_brut s
ON CONFLICT (date, phase_journee) DO NOTHING;

-- 2) dims marée / préf

INSERT INTO public.dim_maree_port(label)
SELECT DISTINCT maree_port FROM tmp_operations_stats_brut
WHERE maree_port IS NOT NULL AND maree_port <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_maree_categorie(label)
SELECT DISTINCT maree_categorie FROM tmp_operations_stats_brut
WHERE maree_categorie IS NOT NULL AND maree_categorie <> ''
ON CONFLICT (label) DO NOTHING;

INSERT INTO public.dim_prefecture_maritime(label)
SELECT DISTINCT prefecture_maritime FROM tmp_operations_stats_brut
WHERE prefecture_maritime IS NOT NULL AND prefecture_maritime <> ''
ON CONFLICT (label) DO NOTHING;

-- ---------------------------------------------------------------
-- Alimenter la table métier (mapping label -> id)
-- ---------------------------------------------------------------
INSERT INTO public.operations_stats (
  operation_id, temps_id,
  concerne_plongee, distance_cote_metres, distance_cote_milles_nautiques,
  est_dans_stm, nom_stm, est_dans_dst, nom_dst,
  maree_port_id, maree_coefficient, maree_categorie_id, prefecture_maritime_id,

  nombre_personnes_blessees, nombre_personnes_assistees, nombre_personnes_decedees,
  nombre_personnes_decedees_accidentellement, nombre_personnes_decedees_naturellement,
  nombre_personnes_disparues, nombre_personnes_impliquees_dans_fausse_alerte,
  nombre_personnes_retrouvees, nombre_personnes_secourues,      
  nombre_personnes_tirees_daffaire_seule,
  nombre_personnes_tous_deces, nombre_personnes_tous_deces_ou_disparues,  
  nombre_personnes_impliquees,

  nombre_personnes_blessees_sans_clandestins, 
  nombre_personnes_assistees_sans_clandestins,
  nombre_personnes_decedees_sans_clandestins, 
  nombre_personnes_decedees_accidentellement_sans_clandestins,
  nombre_personnes_decedees_naturellement_sans_clandestins, 
  nombre_personnes_disparues_sans_clandestins,
  nombre_personnes_impliquees_dans_fausse_alerte_sans_clandestins, 
  nombre_personnes_retrouvees_sans_clandestins,
  nombre_personnes_secourues_sans_clandestins, 
  nombre_personnes_tirees_daffaire_seule_sans_clandestins,
  nombre_personnes_tous_deces_sans_clandestins,  
  nombre_personnes_tous_deces_ou_disparues_sans_clandestins,
  nombre_personnes_impliquees_sans_clandestins,

  nombre_flotteurs_commerce_impliques, nombre_flotteurs_peche_impliques,
  nombre_flotteurs_plaisance_impliques, nombre_flotteurs_loisirs_nautiques_impliques,
  nombre_aeronefs_impliques, nombre_flotteurs_autre_impliques, 
  nombre_flotteurs_annexe_impliques,
  nombre_flotteurs_autre_loisir_nautique_impliques, 
  nombre_flotteurs_canoe_kayak_aviron_impliques,
  nombre_flotteurs_engin_de_plage_impliques, nombre_flotteurs_kitesurf_impliques,
  nombre_flotteurs_plaisance_voile_legere_impliques, 
  nombre_flotteurs_plaisance_a_moteur_moins_8m_impliques,
  nombre_flotteurs_plaisance_a_moteur_plus_8m_impliques, 
  nombre_flotteurs_plaisance_a_voile_impliques,
  nombre_flotteurs_planche_a_voile_impliques, nombre_flotteurs_ski_nautique_impliques,
  nombre_flotteurs_surf_impliques, 
  nombre_flotteurs_vehicule_nautique_a_moteur_impliques,

  sans_flotteur_implique
)
SELECT
  s.operation_id::bigint,
  dt.temps_id,

  s.concerne_plongee::boolean,
  NULLIF(s.distance_cote_metres,'')::int,
  NULLIF(s.distance_cote_milles_nautiques,'')::numeric(6,2),

  s.est_dans_stm::boolean,
  NULLIF(s.nom_stm,''),
  s.est_dans_dst::boolean,
  NULLIF(s.nom_dst,''),

  dmp.maree_port_id,
  NULLIF(s.maree_coefficient,'')::smallint,
  dmc.maree_categorie_id,
  dpm.prefecture_maritime_id,

  s.nombre_personnes_blessees::smallint,
  s.nombre_personnes_assistees::smallint,
  s.nombre_personnes_decedees::smallint,
  s.nombre_personnes_decedees_accidentellement::smallint,
  s.nombre_personnes_decedees_naturellement::smallint,
  s.nombre_personnes_disparues::smallint,
  s.nombre_personnes_impliquees_dans_fausse_alerte::smallint,
  s.nombre_personnes_retrouvees::smallint,
  s.nombre_personnes_secourues::smallint,
  s.nombre_personnes_tirees_daffaire_seule::smallint,
  s.nombre_personnes_tous_deces::smallint,
  s.nombre_personnes_tous_deces_ou_disparues::smallint,
  s.nombre_personnes_impliquees::smallint,

  s.nombre_personnes_blessees_sans_clandestins::smallint,
  s.nombre_personnes_assistees_sans_clandestins::smallint,
  s.nombre_personnes_decedees_sans_clandestins::smallint,
  s.nombre_personnes_decedees_accidentellement_sans_clandestins::smallint,
  s.nombre_personnes_decedees_naturellement_sans_clandestins::smallint,
  s.nombre_personnes_disparues_sans_clandestins::smallint,
  s.nombre_personnes_impliquees_dans_fausse_alerte_sans_clandestins::smallint,
  s.nombre_personnes_retrouvees_sans_clandestins::smallint,
  s.nombre_personnes_secourues_sans_clandestins::smallint,
  s.nombre_personnes_tirees_daffaire_seule_sans_clandestins::smallint,
  s.nombre_personnes_tous_deces_sans_clandestins::smallint,
  s.nombre_personnes_tous_deces_ou_disparues_sans_clandestins::smallint,
  s.nombre_personnes_impliquees_sans_clandestins::smallint,

  s.nombre_flotteurs_commerce_impliques::smallint,
  s.nombre_flotteurs_peche_impliques::smallint,
  s.nombre_flotteurs_plaisance_impliques::smallint,
  s.nombre_flotteurs_loisirs_nautiques_impliques::smallint,
  s.nombre_aeronefs_impliques::smallint,
  s.nombre_flotteurs_autre_impliques::smallint,
  s.nombre_flotteurs_annexe_impliques::smallint,
  s.nombre_flotteurs_autre_loisir_nautique_impliques::smallint,
  s.nombre_flotteurs_canoe_kayak_aviron_impliques::smallint,
  s.nombre_flotteurs_engin_de_plage_impliques::smallint,
  s.nombre_flotteurs_kitesurf_impliques::smallint,
  s.nombre_flotteurs_plaisance_voile_legere_impliques::smallint,
  s.nombre_flotteurs_plaisance_a_moteur_moins_8m_impliques::smallint,
  s.nombre_flotteurs_plaisance_a_moteur_plus_8m_impliques::smallint,
  s.nombre_flotteurs_plaisance_a_voile_impliques::smallint,
  s.nombre_flotteurs_planche_a_voile_impliques::smallint,
  s.nombre_flotteurs_ski_nautique_impliques::smallint,
  s.nombre_flotteurs_surf_impliques::smallint,
  s.nombre_flotteurs_vehicule_nautique_a_moteur_impliques::smallint,

  s.sans_flotteur_implique::boolean
FROM tmp_operations_stats_brut s
JOIN public.operations o ON o.operation_id = s.operation_id::bigint
JOIN public.dim_temps dt
  ON dt.date = s.date::date
 AND ( (dt.phase_journee IS NULL AND NULLIF(s.phase_journee,'') IS NULL)
    OR (dt.phase_journee = NULLIF(s.phase_journee,'')::phase_journee) )
LEFT JOIN public.dim_maree_port dmp ON dmp.label = s.maree_port
LEFT JOIN public.dim_maree_categorie dmc ON dmc.label = s.maree_categorie
LEFT JOIN public.dim_prefecture_maritime dpm ON dpm.label = s.prefecture_maritime;
