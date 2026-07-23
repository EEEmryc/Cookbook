from database.connection import get_connection

# Table de conversion étendue vers des grammes/millilitres
UNIT_CONVERSIONS = {
    # Poids et Volumes standards
    "g": 1.0,
    "kg": 1000.0,
    "ml": 1.0,
    "cl": 10.0,
    "dl": 100.0,
    "l": 1000.0,
    
    # Cuillères et pincees
    "cuillère à soupe": 15.0,
    "cuillères à soupe": 15.0,
    "cuillère à café": 5.0,
    "cuillères à café": 5.0,
    "pincée": 0.5,
    "pincées": 0.5,
    
    # Unités usuelles & contenants
    "gousse": 5.0,
    "gousses": 5.0,
    "boîte": 400.0,
    "boîtes": 400.0,
    "botte": 50.0,
    "bottes": 50.0,
    "brin": 2.0,
    "brins": 2.0,
    "poignée": 30.0,
    "poignées": 30.0,
    "tasse": 250.0,
    "tasses": 250.0,
    "verre": 200.0,
    "verres": 200.0,
    "pot": 125.0,
    "pots": 125.0,
    "tranche": 30.0,
    "tranches": 30.0,
    "sachet": 10.0,
    "sachets": 10.0,
    "": 100.0  # Poids par défaut si pièce/unité indéfinie
}

def convert_to_grams(quantity: float, unit: str, density: float = 1.0, unit_weight: float = None) -> float:
    """
    Convertit la quantité et l'unité en un poids net en grammes.
    Prend en compte la densité pour les liquides et le poids unitaire si disponible.
    """
    unit = unit.lower().strip()

    # Si un poids unitaire est renseigné en base (ex: 1 œuf = 60g)
    if unit_weight and unit in ["", "pièce", "pièces"]:
        return quantity * unit_weight

    multiplier = UNIT_CONVERSIONS.get(unit, 1.0)
    weight_g = quantity * multiplier

    # Ajustement selon la densité pour les liquides (ex: huile, lait)
    if unit in ["ml", "cl", "dl", "l"]:
        weight_g *= density

    return weight_g


def calculate_ingredient_nutrition(ingredient_id: int, quantity: float, unit: str) -> dict:
    """
    Calcule l'apport nutritionnel d'un ingrédient en fonction de son ID CIQUAL,
    de la quantité et de l'unité.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ingredients WHERE id = ?", (ingredient_id,))
    ing = cursor.fetchone()
    conn.close()

    if not ing:
        return {
            "weight_g": 0.0,
            "energy_kcal": 0.0,
            "proteins": 0.0,
            "carbs": 0.0,
            "fat": 0.0
        }

    density = ing["density"] if ing["density"] else 1.0
    unit_weight = ing["unit_weight"] if ing["unit_weight"] else None

    # Conversion en grammes
    weight_g = convert_to_grams(quantity, unit, density, unit_weight)

    # Calcul au prorata de la portion CIQUAL (100g)
    factor = weight_g / 100.0

    return {
        "weight_g": round(weight_g, 2),
        "energy_kcal": round(ing["energy_kcal"] * factor, 2),
        "proteins": round(ing["proteins"] * factor, 2),
        "carbs": round(ing["carbs"] * factor, 2),
        "fat": round(ing["fat"] * factor, 2)
    }


if __name__ == "__main__":
    # Test d'exemple sur le premier ingrédient de la BDD
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM ingredients LIMIT 1;")
    first_ing = cursor.fetchone()
    conn.close()

    if first_ing:
        ing_id = first_ing["id"]
        ing_name = first_ing["name"]

        print(f"--- Test de calcul pour : {ing_name} (ID: {ing_id}) ---")
        
        # Test 1 : 250 grammes
        res1 = calculate_ingredient_nutrition(ing_id, 250, "g")
        print(f"250g -> Poids: {res1['weight_g']}g | Énergie: {res1['energy_kcal']} kcal | Protéines: {res1['proteins']}g")

        # Test 2 : 2 cuillères à soupe
        res2 = calculate_ingredient_nutrition(ing_id, 2, "cuillère à soupe")
        print(f"2 cs -> Poids: {res2['weight_g']}g | Énergie: {res2['energy_kcal']} kcal")