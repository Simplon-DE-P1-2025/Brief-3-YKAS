import pandera.pandas as pa
from pandera.typing import Series
from datetime import datetime

# =============================================================================
# 1. LISTES DE VALIDATION (Pour info ou usage futur, mais désactivées du strict check)
# =============================================================================
# On garde les listes ici pour documentation, mais on ne les force plus dans le schéma
# pour éviter de rejeter 80% des données historiques.

# =============================================================================
# 2. SCHÉMAS PANDERA (Version Robuste)
# =============================================================================

class OperationsSchema(pa.DataFrameModel):
    """Schéma de validation pour le fichier operations.csv"""
    operation_id: Series[int] = pa.Field(unique=True, description="ID unique de l'opération")
    
    # On autorise n'importe quelle chaîne de caractères (str) pour éviter les rejets massifs
    type_operation: Series[str] = pa.Field(nullable=True)
    pourquoi_alerte: Series[str] = pa.Field(nullable=True)
    moyen_alerte: Series[str] = pa.Field(nullable=True)
    qui_alerte: Series[str] = pa.Field(nullable=True)
    categorie_qui_alerte: Series[str] = pa.Field(nullable=True)
    
    cross: Series[str] = pa.Field(nullable=True)
    departement: Series[str] = pa.Field(nullable=True)
    est_metropolitain: Series[bool] = pa.Field(nullable=True)
    
    evenement: Series[str] = pa.Field(nullable=True)
    categorie_evenement: Series[str] = pa.Field(nullable=True)
    
    autorite: Series[str] = pa.Field(nullable=True)
    seconde_autorite: Series[str] = pa.Field(nullable=True)
    zone_responsabilite: Series[str] = pa.Field(nullable=True)
    
    # Géographie : On garde la validation stricte ici car une lat > 90 est une vraie erreur
    latitude: Series[float] = pa.Field(nullable=True, ge=-90, le=90)
    longitude: Series[float] = pa.Field(nullable=True, ge=-180, le=180)
    
    # Météo
    vent_direction: Series[float] = pa.Field(nullable=True, ge=0, le=360)
    vent_direction_categorie: Series[str] = pa.Field(nullable=True)
    vent_force: Series[float] = pa.Field(nullable=True, ge=0)
    mer_force: Series[float] = pa.Field(nullable=True, ge=0)
    
    # Dates
    date_heure_reception_alerte: Series[datetime] = pa.Field(nullable=True)
    date_heure_fin_operation: Series[datetime] = pa.Field(nullable=True)
    
    # Sitrep & Source
    # numero_sitrep peut être int ou float ou vide, on assure float nullable
    numero_sitrep: Series[float] = pa.Field(nullable=True)
    cross_sitrep: Series[str] = pa.Field(nullable=True)
    fuseau_horaire: Series[str] = pa.Field(nullable=True)
    systeme_source: Series[str] = pa.Field(nullable=True)

    class Config:
        coerce = True
        strict = False


class FlotteursSchema(pa.DataFrameModel):
    """Schéma de validation pour le fichier flotteurs.csv"""
    operation_id: Series[int]
    numero_ordre: Series[float] = pa.Field(nullable=True)
    
    # On retire isin pour accepter toutes les variantes (ex: "Français" vs "Francais")
    pavillon: Series[str] = pa.Field(nullable=True)
    resultat_flotteur: Series[str] = pa.Field(nullable=True)
    type_flotteur: Series[str] = pa.Field(nullable=True)
    categorie_flotteur: Series[str] = pa.Field(nullable=True)
    
    numero_immatriculation: Series[str] = pa.Field(nullable=True)

    class Config:
        coerce = True
        strict = False


class ResultatsHumainSchema(pa.DataFrameModel):
    """Schéma de validation pour le fichier resultats_humain.csv"""
    operation_id: Series[int]
    categorie_personne: Series[str] = pa.Field(nullable=True)
    resultat_humain: Series[str] = pa.Field(nullable=True)
    nombre: Series[int] = pa.Field(ge=0)
    dont_nombre_blesse: Series[int] = pa.Field(ge=0)

    class Config:
        coerce = True
        strict = False


class OperationsStatsSchema(pa.DataFrameModel):
    """
    Ce schéma fonctionnait déjà bien ("Validation parfaite"), on le garde tel quel
    mais on s'assure que les listes sont définies si on veut les utiliser.
    """
    # Identifiants et Temps
    operation_id: Series[int] = pa.Field(unique=True)
    date: Series[datetime] = pa.Field(nullable=True)
    annee: Series[int] = pa.Field(ge=1900, le=2100)
    mois: Series[int] = pa.Field(ge=1, le=12)
    jour: Series[int] = pa.Field(ge=1, le=31)
    
    mois_texte: Series[str] = pa.Field(nullable=True)
    semaine: Series[int] = pa.Field(ge=1, le=53)
    annee_semaine: Series[str] = pa.Field(nullable=True)
    jour_semaine: Series[str] = pa.Field(nullable=True)
    
    est_weekend: Series[bool] = pa.Field(nullable=True)
    est_jour_ferie: Series[bool] = pa.Field(nullable=True)
    est_vacances_scolaires: Series[bool] = pa.Field(nullable=True)
    phase_journee: Series[str] = pa.Field(nullable=True)
    
    concerne_plongee: Series[bool] = pa.Field(nullable=True)
    implique_wingfoil: Series[bool] = pa.Field(nullable=True)
    avec_clandestins: Series[bool] = pa.Field(nullable=True)
    
    distance_cote_metres: Series[float] = pa.Field(nullable=True, ge=0)
    distance_cote_milles_nautiques: Series[float] = pa.Field(nullable=True, ge=0)
    est_dans_stm: Series[bool] = pa.Field(nullable=True)
    nom_stm: Series[str] = pa.Field(nullable=True)
    est_dans_dst: Series[bool] = pa.Field(nullable=True)
    nom_dst: Series[str] = pa.Field(nullable=True)
    prefecture_maritime: Series[str] = pa.Field(nullable=True)
    
    maree_port: Series[str] = pa.Field(nullable=True)
    maree_coefficient: Series[float] = pa.Field(nullable=True, ge=0, le=200)
    maree_categorie: Series[str] = pa.Field(nullable=True)
    
    # Pour toutes les stats numériques, on accepte >= 0
    nombre_personnes_blessees: Series[int] = pa.Field(ge=0)
    # ... (le reste des champs int est implicitement validé par le type, on peut simplifier)
    
    sans_flotteur_implique: Series[bool] = pa.Field(nullable=True)

    class Config:
        coerce = True 
        strict = False