-- ============================================================================
-- Script d'initialisation de la base de données YKAS (Secours en Mer) - DuckDB
-- ============================================================================

-- Suppression des tables existantes (si elles existent)
DROP TABLE IF EXISTS resultat_humain;
DROP TABLE IF EXISTS flotteur;
DROP TABLE IF EXISTS operation_stats;
DROP TABLE IF EXISTS operations;

-- ============================================================================
-- TABLE : operations (Table principale)
-- ============================================================================
CREATE TABLE operations (
    operation_id INTEGER PRIMARY KEY,
    type_operation VARCHAR,
    pourquoi_alerte VARCHAR,
    moyen_alerte VARCHAR,
    qui_alerte VARCHAR,
    categorie_qui_alerte VARCHAR,
    cross VARCHAR,
    departement VARCHAR,
    est_metropolitain BOOLEAN,
    evenement VARCHAR,
    categorie_evenement VARCHAR,
    autorite VARCHAR,
    seconde_autorite VARCHAR,
    zone_responsabilite VARCHAR,
    latitude DOUBLE,
    longitude DOUBLE,
    vent_direction DOUBLE,
    vent_direction_categorie VARCHAR,
    vent_force DOUBLE,
    mer_force DOUBLE,
    date_heure_reception_alerte TIMESTAMP,
    date_heure_fin_operation TIMESTAMP,
    numero_sitrep DOUBLE,
    cross_sitrep VARCHAR,
    fuseau_horaire VARCHAR,
    systeme_source VARCHAR
);

-- ============================================================================
-- TABLE : flotteur (Flotteurs impliqués dans les opérations)
-- ============================================================================
CREATE TABLE flotteur (
    id INTEGER PRIMARY KEY,
    operation_id INTEGER,
    numero_ordre DOUBLE,
    pavillon VARCHAR,
    resultat_flotteur VARCHAR,
    type_flotteur VARCHAR,
    categorie_flotteur VARCHAR,
    numero_immatriculation VARCHAR
);

-- ============================================================================
-- TABLE : resultat_humain (Résultats humains par opération)
-- ============================================================================
CREATE TABLE resultat_humain (
    id INTEGER PRIMARY KEY,
    operation_id INTEGER,
    categorie_personne VARCHAR,
    resultat_humain VARCHAR,
    nombre INTEGER,
    dont_nombre_blesse INTEGER
);

-- ============================================================================
-- TABLE : operation_stats (Statistiques et dimensions enrichies)
-- ============================================================================
CREATE TABLE operation_stats (
    operation_id INTEGER PRIMARY KEY,
    date DATE,
    annee INTEGER,
    mois INTEGER,
    jour INTEGER,
    mois_texte VARCHAR,
    semaine INTEGER,
    annee_semaine VARCHAR,
    jour_semaine VARCHAR,
    est_weekend BOOLEAN,
    est_jour_ferie BOOLEAN,
    est_vacances_scolaires BOOLEAN,
    phase_journee VARCHAR,
    concerne_plongee BOOLEAN,
    implique_wingfoil BOOLEAN,
    avec_clandestins BOOLEAN,
    distance_cote_metres DOUBLE,
    distance_cote_milles_nautiques DOUBLE,
    est_dans_stm BOOLEAN,
    nom_stm VARCHAR,
    est_dans_dst BOOLEAN,
    nom_dst VARCHAR,
    prefecture_maritime VARCHAR,
    maree_port VARCHAR,
    maree_coefficient DOUBLE,
    maree_categorie VARCHAR,
    nombre_personnes_blessees INTEGER,
    nombre_personnes_assistees INTEGER,
    nombre_personnes_decedees INTEGER,
    nombre_personnes_decedees_accidentellement INTEGER,
    nombre_personnes_decedees_naturellement INTEGER,
    nombre_personnes_disparues INTEGER,
    nombre_personnes_impliquees_dans_fausse_alerte INTEGER,
    nombre_personnes_retrouvees INTEGER,
    nombre_personnes_secourues INTEGER,
    nombre_personnes_tirees_daffaire_seule INTEGER,
    nombre_personnes_tous_deces INTEGER,
    nombre_personnes_tous_deces_ou_disparues INTEGER,
    nombre_personnes_impliquees INTEGER,
    nombre_personnes_blessees_sans_clandestins INTEGER,
    nombre_personnes_assistees_sans_clandestins INTEGER,
    nombre_personnes_decedees_sans_clandestins INTEGER,
    nombre_personnes_decedees_accidentellement_sans_clandestins INTEGER,
    nombre_personnes_decedees_naturellement_sans_clandestins INTEGER,
    nombre_personnes_disparues_sans_clandestins INTEGER,
    nombre_personnes_impliquees_dans_fausse_alerte_sans_clandestins INTEGER,
    nombre_personnes_retrouvees_sans_clandestins INTEGER,
    nombre_personnes_secourues_sans_clandestins INTEGER,
    nombre_personnes_tirees_daffaire_seule_sans_clandestins INTEGER,
    nombre_personnes_tous_deces_sans_clandestins INTEGER,
    nombre_personnes_tous_deces_ou_disparues_sans_clandestins INTEGER,
    nombre_personnes_impliquees_sans_clandestins INTEGER,
    nombre_flotteurs_commerce_impliques INTEGER,
    nombre_flotteurs_peche_impliques INTEGER,
    nombre_flotteurs_plaisance_impliques INTEGER,
    nombre_flotteurs_loisirs_nautiques_impliques INTEGER,
    nombre_aeronefs_impliques INTEGER,
    nombre_flotteurs_autre_impliques INTEGER,
    nombre_flotteurs_annexe_impliques INTEGER,
    nombre_flotteurs_autre_loisir_nautique_impliques INTEGER,
    nombre_flotteurs_canoe_kayak_aviron_impliques INTEGER,
    nombre_flotteurs_engin_de_plage_impliques INTEGER,
    nombre_flotteurs_kitesurf_impliques INTEGER,
    nombre_flotteurs_plaisance_voile_legere_impliques INTEGER,
    nombre_flotteurs_plaisance_a_moteur_impliques INTEGER,
    nombre_flotteurs_plaisance_a_moteur_moins_8m_impliques INTEGER,
    nombre_flotteurs_plaisance_a_moteur_plus_8m_impliques INTEGER,
    nombre_flotteurs_plaisance_a_voile_impliques INTEGER,
    nombre_flotteurs_planche_a_voile_impliques INTEGER,
    nombre_flotteurs_ski_nautique_impliques INTEGER,
    nombre_flotteurs_surf_impliques INTEGER,
    nombre_flotteurs_vehicule_nautique_a_moteur_impliques INTEGER,
    sans_flotteur_implique BOOLEAN
);

-- ============================================================================
-- INDEX pour améliorer les performances
-- ============================================================================

-- Index sur les clés étrangères
CREATE INDEX idx_flotteur_operation_id ON flotteur(operation_id);
CREATE INDEX idx_resultat_humain_operation_id ON resultat_humain(operation_id);

-- Index sur les dates et dimensions temporelles
CREATE INDEX idx_operations_date_reception ON operations(date_heure_reception_alerte);
CREATE INDEX idx_operation_stats_date ON operation_stats(date);
CREATE INDEX idx_operation_stats_annee_mois ON operation_stats(annee, mois);

-- Index sur les dimensions géographiques
CREATE INDEX idx_operations_cross ON operations(cross);
CREATE INDEX idx_operations_departement ON operations(departement);
CREATE INDEX idx_operation_stats_prefecture ON operation_stats(prefecture_maritime);

-- Index sur les coordonnées GPS (pour recherches géospatiales)
CREATE INDEX idx_operations_coords ON operations(latitude, longitude);

-- Index sur les catégories importantes
CREATE INDEX idx_operations_type ON operations(type_operation);
CREATE INDEX idx_operations_evenement ON operations(categorie_evenement);