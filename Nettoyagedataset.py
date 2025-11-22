#!/usr/bin/env python3
"""
Script de consolidation des données d'accidents de la route 2024
Fusionne les 4 fichiers CSV (caractéristiques, lieux, usagers, véhicules) 
en un dataset unique pour analyse et visualisation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def load_and_clean_data():
    """
    Charge et nettoie les 4 fichiers CSV d'accidents
    """
    print("📊 Chargement des données...")
    
    # Chargement des fichiers
    caract = pd.read_csv('caract-2024.csv', sep=';', decimal=',', low_memory=False)
    lieux = pd.read_csv('lieux-2024.csv', sep=';', decimal=',', low_memory=False)
    usagers = pd.read_csv('usagers-2024.csv', sep=';', decimal=',', low_memory=False)
    vehicules = pd.read_csv('vehicules-2024.csv', sep=';', decimal=',', low_memory=False)
    
    print(f"✓ Caractéristiques: {len(caract)} accidents")
    print(f"✓ Lieux: {len(lieux)} enregistrements")
    print(f"✓ Usagers: {len(usagers)} personnes impliquées")
    print(f"✓ Véhicules: {len(vehicules)} véhicules")
    
    return caract, lieux, usagers, vehicules

def clean_numeric_columns(df):
    """
    Nettoie les colonnes numériques en remplaçant les valeurs invalides
    """
    for col in df.columns:
        if df[col].dtype == 'object':
            # Essayer de convertir en numérique si possible
            try:
                df[col] = df[col].str.replace(',', '.').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
    return df

def create_datetime_column(caract):
    """
    Crée une colonne datetime à partir des colonnes jour, mois, an, hrmn
    """
    # Créer la date complète
    caract['date'] = pd.to_datetime(
        caract['an'].astype(str) + '-' + 
        caract['mois'].astype(str).str.zfill(2) + '-' + 
        caract['jour'].astype(str).str.zfill(2),
        errors='coerce'
    )
    
    # Convertir hrmn en string et nettoyer
    caract['hrmn'] = caract['hrmn'].astype(str).str.strip()
    caract['hrmn'] = caract['hrmn'].replace(['na', 'nan', 'NaN', '', 'None'], np.nan)
    
    # Extraire l'heure et minute avec gestion des valeurs manquantes
    caract['heure'] = caract['hrmn'].fillna('').astype(str).str[:2]
    caract['heure'] = caract['heure'].replace('', np.nan)
    caract['heure'] = pd.to_numeric(caract['heure'], errors='coerce')
    
    caract['minute'] = caract['hrmn'].fillna('').astype(str).str[3:5]
    caract['minute'] = caract['minute'].replace('', np.nan)
    caract['minute'] = pd.to_numeric(caract['minute'], errors='coerce')
    
    # Ajouter des colonnes temporelles utiles
    caract['jour_semaine'] = caract['date'].dt.dayofweek
    caract['nom_jour'] = caract['date'].dt.day_name()
    caract['mois_nom'] = caract['date'].dt.month_name()
    caract['trimestre'] = caract['date'].dt.quarter
    caract['est_weekend'] = (caract['jour_semaine'] >= 5).astype(int)
    
    # Périodes de la journée (avec gestion des valeurs manquantes)
    caract['periode_journee'] = pd.cut(
        caract['heure'],
        bins=[0, 6, 9, 12, 14, 18, 21, 24],
        labels=['Nuit', 'Matin_tôt', 'Matin', 'Midi', 'Après-midi', 'Soirée', 'Nuit_tardive'],
        include_lowest=True
    )
    
    return caract

def decode_values(df, column_mapping):
    """
    Décode les valeurs codées en descriptions lisibles
    """
    for col, mapping in column_mapping.items():
        if col in df.columns:
            df[f'{col}_desc'] = df[col].map(mapping).fillna('Non spécifié')
    return df

def consolidate_accident_level(caract, lieux):
    """
    Consolide les données au niveau accident
    """
    print("\n🔄 Consolidation niveau accident...")
    
    # Fusion caractéristiques et lieux
    accidents = caract.merge(lieux, on='Num_Acc', how='left')
    
    # Mappings des valeurs codées
    lum_mapping = {
        1: 'Plein jour',
        2: 'Crépuscule ou aube',
        3: 'Nuit sans éclairage public',
        4: 'Nuit avec éclairage public non allumé',
        5: 'Nuit avec éclairage public allumé'
    }
    
    atm_mapping = {
        1: 'Normale',
        2: 'Pluie légère',
        3: 'Pluie forte',
        4: 'Neige - grêle',
        5: 'Brouillard - fumée',
        6: 'Vent fort - tempête',
        7: 'Temps éblouissant',
        8: 'Temps couvert',
        9: 'Autre'
    }
    
    col_mapping = {
        1: 'Deux véhicules - frontale',
        2: 'Deux véhicules - par l\'arrière',
        3: 'Deux véhicules - par le côté',
        4: 'Trois véhicules et plus - en chaîne',
        5: 'Trois véhicules et plus - collisions multiples',
        6: 'Autre collision',
        7: 'Sans collision'
    }
    
    surf_mapping = {
        1: 'Normale',
        2: 'Mouillée',
        3: 'Flaques',
        4: 'Inondée',
        5: 'Enneigée',
        6: 'Boue',
        7: 'Verglacée',
        8: 'Corps gras',
        9: 'Autre'
    }
    
    catr_mapping = {
        1: 'Autoroute',
        2: 'Route nationale',
        3: 'Route départementale',
        4: 'Voie communale',
        5: 'Hors réseau public',
        6: 'Parc de stationnement',
        7: 'Routes de métropole urbaine',
        9: 'Autre'
    }
    
    agg_mapping = {
        1: 'Hors agglomération',
        2: 'En agglomération'
    }
    
    # Appliquer les décodages
    accidents = decode_values(accidents, {
        'lum': lum_mapping,
        'atm': atm_mapping,
        'col': col_mapping,
        'surf': surf_mapping,
        'catr': catr_mapping,
        'agg': agg_mapping
    })
    
    return accidents

def aggregate_usagers_vehicules(usagers, vehicules):
    """
    Agrège les données usagers et véhicules au niveau accident
    """
    print("🔄 Agrégation usagers et véhicules...")
    
    # Mappings pour usagers
    grav_mapping = {
        1: 'Indemne',
        2: 'Tué',
        3: 'Blessé hospitalisé',
        4: 'Blessé léger'
    }
    
    catu_mapping = {
        1: 'Conducteur',
        2: 'Passager',
        3: 'Piéton',
        4: 'Piéton en roller ou trottinette'
    }
    
    sexe_mapping = {
        1: 'Homme',
        2: 'Femme'
    }
    
    # Décodage usagers
    usagers = decode_values(usagers, {
        'grav': grav_mapping,
        'catu': catu_mapping,
        'sexe': sexe_mapping
    })
    
    # Calculer l'âge avec gestion des erreurs
    usagers['an_nais'] = pd.to_numeric(usagers['an_nais'], errors='coerce')
    usagers['age'] = 2024 - usagers['an_nais']
    usagers['tranche_age'] = pd.cut(
        usagers['age'],
        bins=[0, 18, 25, 35, 45, 55, 65, 75, 150],
        labels=['0-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75+']
    )
    
    # Mappings pour véhicules
    catv_mapping = {
        1: 'Bicyclette',
        2: 'Cyclomoteur <50cm3',
        3: 'Voiturette',
        7: 'VL seul',
        10: 'VU seul 1,5T <= PTAC <= 3,5T',
        13: 'PL seul 3,5T <PTCA <= 7,5T',
        14: 'PL seul > 7,5T',
        15: 'PL > 3,5T + remorque',
        16: 'Tracteur routier seul',
        17: 'Tracteur routier + semi-remorque',
        20: 'Engin spécial',
        21: 'Tracteur agricole',
        30: 'Scooter < 50 cm3',
        31: 'Motocyclette > 50 cm3 et <= 125 cm3',
        32: 'Scooter > 50 cm3 et <= 125 cm3',
        33: 'Motocyclette > 125 cm3',
        34: 'Scooter > 125 cm3',
        35: 'Quad léger <= 50 cm3',
        36: 'Quad lourd > 50 cm3',
        37: 'Autobus',
        38: 'Autocar',
        39: 'Train',
        40: 'Tramway',
        50: 'EDP à moteur',
        60: 'EDP sans moteur',
        80: 'VAE',
        99: 'Autre'
    }
    
    vehicules = decode_values(vehicules, {'catv': catv_mapping})
    
    # =========================
    # AGRÉGATION USAGERS
    # =========================
    
    # Agrégation principale des usagers
    agg_usagers = usagers.groupby('Num_Acc').agg({
        'id_usager': 'count',  # Nombre total d'usagers
        'grav': lambda x: (x == 2).sum(),  # Nombre de tués
        'age': ['mean', 'min', 'max'],  # Stats âge
        'sexe': lambda x: (x == 1).sum() / len(x) if len(x) > 0 else 0,  # % hommes
        'catu': lambda x: (x == 3).sum()  # Nombre de piétons
    }).round(2)
    
    agg_usagers.columns = [
        'nb_usagers', 'nb_tues', 
        'age_moyen', 'age_min', 'age_max',
        'pct_hommes', 'nb_pietons'
    ]
    
    # Calculer blessés graves et légers
    blesses = usagers.groupby('Num_Acc')['grav'].apply(
        lambda x: pd.Series({
            'nb_blesses_hospitalises': (x == 3).sum(),
            'nb_blesses_legers': (x == 4).sum(),
            'nb_indemnes': (x == 1).sum()
        })
    ).unstack(fill_value=0)
    
    # Combiner les agrégations usagers et réinitialiser l'index
    agg_usagers = pd.concat([agg_usagers, blesses], axis=1)
    agg_usagers = agg_usagers.reset_index()
    
    # =========================
    # AGRÉGATION VÉHICULES
    # =========================
    
    # Créer un DataFrame vide si pas de véhicules
    if len(vehicules) == 0:
        agg_vehicules = pd.DataFrame({'Num_Acc': usagers['Num_Acc'].unique()})
        agg_vehicules['nb_vehicules'] = 0
        agg_vehicules['catv_principal'] = 0
        agg_vehicules['implique_2roues'] = 0
        agg_vehicules['implique_pl'] = 0
        agg_vehicules['implique_tc'] = 0
        agg_vehicules['implique_edp'] = 0
    else:
        # Nombre de véhicules par accident
        nb_vehicules = vehicules.groupby('Num_Acc').size().reset_index(name='nb_vehicules')
        
        # Catégorie principale de véhicule
        catv_principal = vehicules.groupby('Num_Acc')['catv'].apply(
            lambda x: x.value_counts().index[0] if len(x) > 0 else 0
        ).reset_index(name='catv_principal')
        
        # Types de véhicules impliqués
        veh_types = vehicules.groupby('Num_Acc')['catv'].apply(
            lambda x: pd.Series({
                'implique_2roues': ((x >= 1) & (x <= 3) | (x >= 30) & (x <= 36) | (x == 80)).any(),
                'implique_pl': ((x >= 13) & (x <= 17)).any(),
                'implique_tc': ((x == 37) | (x == 38)).any(),
                'implique_edp': ((x == 50) | (x == 60)).any()
            })
        ).astype(int).reset_index()
        
        # Fusion de toutes les agrégations véhicules
        agg_vehicules = nb_vehicules
        agg_vehicules = agg_vehicules.merge(catv_principal, on='Num_Acc', how='left')
        agg_vehicules = agg_vehicules.merge(veh_types, on='Num_Acc', how='left')
    
    return agg_usagers, agg_vehicules

def create_severity_indicators(df):
    """
    Crée des indicateurs de gravité
    """
    # Score de gravité (0-100)
    df['score_gravite'] = (
        df['nb_tues'].fillna(0) * 100 +
        df['nb_blesses_hospitalises'].fillna(0) * 30 +
        df['nb_blesses_legers'].fillna(0) * 10
    )
    
    # Catégorie de gravité
    df['categorie_gravite'] = pd.cut(
        df['score_gravite'],
        bins=[0, 10, 50, 200, float('inf')],
        labels=['Matériel uniquement', 'Léger', 'Grave', 'Très grave']
    )
    
    # Accident mortel
    df['accident_mortel'] = (df['nb_tues'] > 0).astype(int)
    
    return df

def main():
    """
    Fonction principale de consolidation
    """
    print("=" * 60)
    print("🚗 CONSOLIDATION DES DONNÉES ACCIDENTS ROUTIERS 2024")
    print("=" * 60)
    
    try:
        # Chargement
        caract, lieux, usagers, vehicules = load_and_clean_data()
        
        # Nettoyage des colonnes numériques
        print("\n🧹 Nettoyage des données...")
        caract = clean_numeric_columns(caract)
        lieux = clean_numeric_columns(lieux)
        usagers = clean_numeric_columns(usagers)
        vehicules = clean_numeric_columns(vehicules)
        
        # Création des colonnes temporelles
        print("📅 Création des colonnes temporelles...")
        caract = create_datetime_column(caract)
        
        # Consolidation niveau accident
        accidents = consolidate_accident_level(caract, lieux)
        
        # Agrégation usagers et véhicules
        agg_usagers, agg_vehicules = aggregate_usagers_vehicules(usagers, vehicules)
        
        # Fusion finale
        print("\n🔗 Fusion finale des données...")
        
        # Debug: afficher les colonnes disponibles
        print(f"  - Colonnes accidents: {accidents.columns[:5].tolist()}...")
        print(f"  - Colonnes agg_usagers: {agg_usagers.columns.tolist()}")
        print(f"  - Colonnes agg_vehicules: {agg_vehicules.columns.tolist()}")
        
        # Fusion avec gestion d'erreur
        accidents_final = accidents.merge(agg_usagers, on='Num_Acc', how='left')
        print(f"  ✓ Fusion usagers réussie: {len(accidents_final)} lignes")
        
        accidents_final = accidents_final.merge(agg_vehicules, on='Num_Acc', how='left')
        print(f"  ✓ Fusion véhicules réussie: {len(accidents_final)} lignes")
        
        # Ajout indicateurs de gravité
        print("📊 Calcul des indicateurs de gravité...")
        accidents_final = create_severity_indicators(accidents_final)
        
        # Nettoyage final
        print("🧹 Nettoyage final...")
        # Remplacer les NaN par 0 pour les colonnes numériques
        cols_numeriques = ['nb_usagers', 'nb_tues', 'nb_blesses_hospitalises', 
                          'nb_blesses_legers', 'nb_indemnes', 'nb_pietons',
                          'nb_vehicules', 'implique_2roues', 'implique_pl', 
                          'implique_tc', 'implique_edp', 'score_gravite', 
                          'accident_mortel']
        
        for col in cols_numeriques:
            if col in accidents_final.columns:
                accidents_final[col] = accidents_final[col].fillna(0)
        
        # Sélection et organisation des colonnes clés
        colonnes_finales = [
            # Identifiants et localisation
            'Num_Acc', 'date', 'heure', 'minute', 'lat', 'long', 'dep', 'com',
            
            # Temporel
            'jour_semaine', 'nom_jour', 'mois_nom', 'trimestre', 'est_weekend', 'periode_journee',
            
            # Conditions
            'lum_desc', 'atm_desc', 'surf_desc', 'col_desc',
            
            # Infrastructure
            'catr_desc', 'agg_desc', 'vma', 'nbv',
            
            # Bilan humain
            'nb_usagers', 'nb_tues', 'nb_blesses_hospitalises', 'nb_blesses_legers', 'nb_indemnes',
            'nb_pietons', 'age_moyen', 'pct_hommes',
            
            # Véhicules
            'nb_vehicules', 'implique_2roues', 'implique_pl', 'implique_tc', 'implique_edp',
            
            # Gravité
            'score_gravite', 'categorie_gravite', 'accident_mortel'
        ]
        
        # Garder seulement les colonnes disponibles
        colonnes_disponibles = [col for col in colonnes_finales if col in accidents_final.columns]
        accidents_final = accidents_final[colonnes_disponibles]
        
        # Sauvegarde
        output_file = 'accidents_routiers_2024_consolide.csv'
        print(f"\n💾 Sauvegarde du fichier consolidé: {output_file}")
        accidents_final.to_csv(output_file, index=False, encoding='utf-8')
        
        # Statistiques finales
        print("\n📈 STATISTIQUES DU DATASET CONSOLIDÉ:")
        print("=" * 60)
        print(f"✓ Nombre total d'accidents: {len(accidents_final):,}")
        print(f"✓ Nombre de colonnes: {len(accidents_final.columns)}")
        
        # Gérer les dates invalides
        dates_valides = accidents_final['date'].dropna()
        if len(dates_valides) > 0:
            print(f"✓ Période: {dates_valides.min()} à {dates_valides.max()}")
        
        print(f"✓ Nombre de départements: {accidents_final['dep'].nunique()}")
        print(f"\n🔴 Bilan humain global:")
        print(f"  - Tués: {accidents_final['nb_tues'].sum():.0f}")
        print(f"  - Blessés hospitalisés: {accidents_final['nb_blesses_hospitalises'].sum():.0f}")
        print(f"  - Blessés légers: {accidents_final['nb_blesses_legers'].sum():.0f}")
        print(f"  - Total victimes: {(accidents_final['nb_tues'] + accidents_final['nb_blesses_hospitalises'] + accidents_final['nb_blesses_legers']).sum():.0f}")
        print(f"\n✨ Consolidation terminée avec succès!")
        print("=" * 60)
        
        # Création d'un échantillon pour tests
        sample_file = 'accidents_sample.csv'
        sample_size = min(1000, len(accidents_final))
        if sample_size > 0:
            sample = accidents_final.sample(sample_size)
            sample.to_csv(sample_file, index=False, encoding='utf-8')
            print(f"\n📄 Échantillon de test créé: {sample_file} ({len(sample)} lignes)")
        
        return accidents_final
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la consolidation: {str(e)}")
        print(f"Type d'erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    df = main()
    if df is not None:
        print("\n✅ Script terminé avec succès!")
    else:
        print("\n⚠️ Le script s'est terminé avec des erreurs.")