from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Operation(Base):
    __tablename__ = 'operations'

    operation_id = Column(Integer, primary_key=True, autoincrement=False)
    type_operation = Column(String(50))
    pourquoi_alerte = Column(String(255))
    moyen_alerte = Column(String(255))
    qui_alerte = Column(String(255))
    categorie_qui_alerte = Column(String(255))
    cross = Column(String(50))
    departement = Column(String(50))
    est_metropolitain = Column(Boolean)
    evenement = Column(String(255))
    categorie_evenement = Column(String(255))
    autorite = Column(String(100))
    seconde_autorite = Column(String(100))
    zone_responsabilite = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    vent_direction = Column(Float)
    vent_direction_categorie = Column(String(50))
    vent_force = Column(Float)
    mer_force = Column(Float)
    date_heure_reception_alerte = Column(DateTime(timezone=True))
    date_heure_fin_operation = Column(DateTime(timezone=True))
    numero_sitrep = Column(Integer)
    cross_sitrep = Column(String(100))
    fuseau_horaire = Column(String(50))
    systeme_source = Column(String(50))

class Flotteur(Base):
    __tablename__ = 'flotteurs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(Integer, ForeignKey('operations.operation_id'), nullable=False)
    numero_ordre = Column(Float)
    pavillon = Column(String(100))
    resultat_flotteur = Column(String(255))
    type_flotteur = Column(String(100))
    categorie_flotteur = Column(String(100))
    numero_immatriculation = Column(String(100))

class ResultatHumain(Base):
    __tablename__ = 'resultats_humain'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(Integer, ForeignKey('operations.operation_id'), nullable=False)
    categorie_personne = Column(String(100))
    resultat_humain = Column(String(255))
    nombre = Column(Integer)
    dont_nombre_blesse = Column(Integer)

class OperationStats(Base):
    __tablename__ = 'operations_stats'
    
    # Clé primaire et étrangère
    operation_id = Column(Integer, ForeignKey('operations.operation_id'), primary_key=True)
    
    # Temps
    date = Column(DateTime(timezone=True))
    annee = Column(Integer)
    mois = Column(Integer)
    jour = Column(Integer)
    mois_texte = Column(String(20))
    semaine = Column(Integer)
    annee_semaine = Column(String(20))
    jour_semaine = Column(String(20))
    est_weekend = Column(Boolean)
    est_jour_ferie = Column(Boolean)
    est_vacances_scolaires = Column(Boolean)
    phase_journee = Column(String(50))
    
    # Context
    concerne_plongee = Column(Boolean)
    implique_wingfoil = Column(Boolean)
    avec_clandestins = Column(Boolean)
    distance_cote_metres = Column(Float)
    distance_cote_milles_nautiques = Column(Float)
    est_dans_stm = Column(Boolean)
    nom_stm = Column(String(100))
    est_dans_dst = Column(Boolean)
    nom_dst = Column(String(100))
    prefecture_maritime = Column(String(100))
    maree_port = Column(String(100))
    maree_coefficient = Column(Float)
    maree_categorie = Column(String(50))
    
    # Bilans Humains (Total)
    nombre_personnes_blessees = Column(Integer)
    nombre_personnes_assistees = Column(Integer)
    nombre_personnes_decedees = Column(Integer)
    nombre_personnes_decedees_accidentellement = Column(Integer)
    nombre_personnes_decedees_naturellement = Column(Integer)
    nombre_personnes_disparues = Column(Integer)
    nombre_personnes_impliquees_dans_fausse_alerte = Column(Integer)
    nombre_personnes_retrouvees = Column(Integer)
    nombre_personnes_secourues = Column(Integer)
    nombre_personnes_tirees_daffaire_seule = Column(Integer)
    nombre_personnes_tous_deces = Column(Integer)
    nombre_personnes_tous_deces_ou_disparues = Column(Integer)
    nombre_personnes_impliquees = Column(Integer)

    # Bilans Humains (Sans Clandestins)
    nombre_personnes_blessees_sans_clandestins = Column(Integer)
    nombre_personnes_assistees_sans_clandestins = Column(Integer)
    nombre_personnes_decedees_sans_clandestins = Column(Integer)
    nombre_personnes_decedees_accidentellement_sans_clandestins = Column(Integer)
    nombre_personnes_decedees_naturellement_sans_clandestins = Column(Integer)
    nombre_personnes_disparues_sans_clandestins = Column(Integer)
    nombre_personnes_impliquees_dans_fausse_alerte_sans_clandestins = Column(Integer)
    nombre_personnes_retrouvees_sans_clandestins = Column(Integer)
    nombre_personnes_secourues_sans_clandestins = Column(Integer)
    nombre_personnes_tirees_daffaire_seule_sans_clandestins = Column(Integer)
    nombre_personnes_tous_deces_sans_clandestins = Column(Integer)
    nombre_personnes_tous_deces_ou_disparues_sans_clandestins = Column(Integer)
    nombre_personnes_impliquees_sans_clandestins = Column(Integer)

    # Flotteurs
    nombre_flotteurs_commerce_impliques = Column(Integer)
    nombre_flotteurs_peche_impliques = Column(Integer)
    nombre_flotteurs_plaisance_impliques = Column(Integer)
    nombre_flotteurs_loisirs_nautiques_impliques = Column(Integer)
    nombre_aeronefs_impliques = Column(Integer)
    nombre_flotteurs_autre_impliques = Column(Integer)
    nombre_flotteurs_annexe_impliques = Column(Integer)
    nombre_flotteurs_autre_loisir_nautique_impliques = Column(Integer)
    nombre_flotteurs_canoe_kayak_aviron_impliques = Column(Integer)
    nombre_flotteurs_engin_de_plage_impliques = Column(Integer)
    nombre_flotteurs_kitesurf_impliques = Column(Integer)
    nombre_flotteurs_plaisance_voile_legere_impliques = Column(Integer)
    nombre_flotteurs_plaisance_a_moteur_impliques = Column(Integer)
    nombre_flotteurs_plaisance_a_moteur_moins_8m_impliques = Column(Integer)
    nombre_flotteurs_plaisance_a_moteur_plus_8m_impliques = Column(Integer)
    nombre_flotteurs_plaisance_a_voile_impliques = Column(Integer)
    nombre_flotteurs_planche_a_voile_impliques = Column(Integer)
    nombre_flotteurs_ski_nautique_impliques = Column(Integer)
    nombre_flotteurs_surf_impliques = Column(Integer)
    nombre_flotteurs_vehicule_nautique_a_moteur_impliques = Column(Integer)
    
    # Flag final
    sans_flotteur_implique = Column(Boolean)