import pandera.pandas as pa
from pandera.typing import Series
from datetime import datetime

# --- 1. Schéma Opérations ---
class OperationsSchema(pa.DataFrameModel):
    operation_id: Series[int] = pa.Field(unique=True, description="ID unique de l'opération")
    type_operation: Series[str] = pa.Field(nullable=True, isin=["SAR", "MAS", "DIV"], description="Type d'opération")
    pourquoi_alerte: Series[str] = pa.Field(nullable=True)
    moyen_alerte: Series[str] = pa.Field(nullable=True) 
    latitude: Series[float] = pa.Field(nullable=True, ge=-90, le=90)
    longitude: Series[float] = pa.Field(nullable=True, ge=-180, le=180)
    date_heure_reception_alerte: Series[datetime] = pa.Field(nullable=True)
    date_heure_fin_operation: Series[datetime] = pa.Field(nullable=True)

    class Config:
        coerce = True
        strict = False

# --- 2. Schéma Flotteurs (CORRIGÉ) ---
class FlotteursSchema(pa.DataFrameModel):
    operation_id: Series[int]
    # On passe en float + nullable car certaines lignes n'ont pas de numéro
    numero_ordre: Series[float] = pa.Field(nullable=True)
    # Regex modifiée pour accepter les accents (Latin-1 Supplement block \u00C0-\u00FF)
    type_flotteur: Series[str] = pa.Field(nullable=True, str_matches=r"^[a-zA-Z0-9\s\u00C0-\u00FF\-\']+$")
    
    class Config:
        coerce = True

# --- 3. Schéma Résultats Humains ---
class ResultatsHumainSchema(pa.DataFrameModel):
    operation_id: Series[int]
    categorie_personne: Series[str] = pa.Field(nullable=True)
    resultat_humain: Series[str] = pa.Field(nullable=True)
    nombre: Series[int] = pa.Field(ge=0)
    dont_nombre_blesse: Series[int] = pa.Field(ge=0)

    class Config:
        coerce = True
        
# --- 4. Schéma Opérations Stats (CORRIGÉ) ---
class OperationsStatsSchema(pa.DataFrameModel):
    operation_id: Series[int] = pa.Field(unique=True)
    date: Series[datetime] = pa.Field(nullable=True)
    
    annee: Series[int] = pa.Field(ge=1900, le=2100)
    mois: Series[int] = pa.Field(ge=1, le=12)
    jour: Series[int] = pa.Field(ge=1, le=31)
    
    mois_texte: Series[str] = pa.Field(nullable=True)
    jour_semaine: Series[str] = pa.Field(nullable=True)
    phase_journee: Series[str] = pa.Field(nullable=True)
    
    est_weekend: Series[bool] = pa.Field(nullable=True)
    est_jour_ferie: Series[bool] = pa.Field(nullable=True)
    concerne_plongee: Series[bool] = pa.Field(nullable=True)
    
    # Données géographiques/physiques
    distance_cote_milles_nautiques: Series[float] = pa.Field(nullable=True, ge=0)
    # On passe maree_coefficient en float pour accepter les NaNs (vides)
    maree_coefficient: Series[float] = pa.Field(nullable=True, ge=0, le=200)
    
    # Statistiques
    nombre_personnes_blessees: Series[int] = pa.Field(ge=0)
    nombre_personnes_assistees: Series[int] = pa.Field(ge=0)
    nombre_personnes_decedees: Series[int] = pa.Field(ge=0)
    nombre_personnes_disparues: Series[int] = pa.Field(ge=0)
    nombre_personnes_secourues: Series[int] = pa.Field(ge=0)
    nombre_personnes_impliquees: Series[int] = pa.Field(ge=0)
    
    nombre_flotteurs_plaisance_impliques: Series[int] = pa.Field(ge=0)
    nombre_flotteurs_commerce_impliques: Series[int] = pa.Field(ge=0)
    nombre_flotteurs_peche_impliques: Series[int] = pa.Field(ge=0)

    class Config:
        coerce = True 
        strict = False