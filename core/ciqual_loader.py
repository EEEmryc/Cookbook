import csv
import re
from pathlib import Path
from database.connection import get_connection

# Chemin absolu vers le fichier CSV de données
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "ciqual.csv"

def clean_float(val: str) -> float:
    """
    Nettoie les chaînes de caractères brutes issues du CSV CIQUAL
    et les convertit en nombres décimaux (float).
    """
    if not val or val.strip() in ["-", "TRACE", "traces", ""]:
        return 0.0
    
    val = val.replace("<", "").strip().replace(",", ".")
    match = re.search(r"[-+]?\d*\.\d+|\d+", val)
    if match:
        return float(match.group())
    return 0.0

def import_ciqual():
    """
    Lit ciqual.csv et insère les aliments dans la table 'ingredients'.
    """
    if not CSV_PATH.exists():
        print(f"Erreur : Le fichier {CSV_PATH} est introuvable.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Nettoyage de la table avant rechargement
    cursor.execute("DELETE FROM ingredients;")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='ingredients';")

    # Détection du séparateur
    with open(CSV_PATH, mode="r", encoding="utf-8-sig", errors="ignore") as file:
        first_line = file.readline()
        delimiter = ";" if ";" in first_line else ","

    count = 0
    with open(CSV_PATH, mode="r", encoding="utf-8-sig", errors="ignore") as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        
        for row in reader:
            code_raw = None
            name_raw = None
            energy = 0.0
            proteins = 0.0
            carbs = 0.0
            fat = 0.0

            for key, val in row.items():
                if not key or not val:
                    continue
                
                k = key.lower().strip()

                # Exclusion explicite des colonnes de catégories/groupes
                if "grp" in k or "groupe" in k or "famille" in k:
                    continue

                # Extraction du code aliment individuel
                if code_raw is None and ("alim_code" in k or "code ciqual" in k or k == "code" or "code aliment" in k):
                    code_raw = val

                # Extraction du nom aliment individuel
                if name_raw is None and ("alim_nom" in k or "nom du produit" in k or "nom_fr" in k or "nom aliment" in k):
                    name_raw = val

                # Extraction des valeurs nutritionnelles
                if "energie" in k or "kcal" in k:
                    energy = clean_float(val)
                elif "protéine" in k or "proteine" in k:
                    proteins = clean_float(val)
                elif "glucide" in k:
                    carbs = clean_float(val)
                elif "lipide" in k:
                    fat = clean_float(val)

            if not code_raw or not name_raw:
                continue

            try:
                code_int = int(clean_float(str(code_raw)))
                
                cursor.execute("""
                INSERT OR REPLACE INTO ingredients (code_ciqual, name, energy_kcal, proteins, carbs, fat)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (code_int, name_raw.strip(), energy, proteins, carbs, fat))
                count += 1
            except ValueError:
                continue

    conn.commit()
    conn.close()
    print(f"Importation terminée : {count} ingrédients insérés dans la base de données.")

if __name__ == "__main__":
    import_ciqual()