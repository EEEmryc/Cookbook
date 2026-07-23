import math

DISCRETE_UNITS = {"", "pièce", "piece", "tranche", "pincée", "pincee", "gousse", "sachet"}
DISCRETE_KEYWORDS = ["oeuf", "œuf", "jaune", "blanc", "gousse", "sachet", "pincée", "tranche"]

def is_discrete_ingredient(unit: str, ingredient_name: str = "") -> bool:
    """Détermine si un ingrédient ne peut pas être divisé en fractions décimales."""
    unit_clean = unit.strip().lower()
    if unit_clean in DISCRETE_UNITS:
        return True
    
    name_clean = ingredient_name.strip().lower()
    for kw in DISCRETE_KEYWORDS:
        if kw in name_clean:
            return True
            
    return False

def scale_quantity(quantity: float, original_servings: int, target_servings: int, unit: str = "", ingredient_name: str = "") -> float:
    """
    Ajuste la quantité d'un ingrédient selon le nombre de portions.
    Exemple : 3 oeufs pour 4 pers. ramenés à 2 pers. donne 2 oeufs (arrondi à l'unité supérieure).
    Exemple : 250g de farine pour 4 pers. ramenés à 6 pers. donne 375.0g.
    """
    if original_servings <= 0 or target_servings <= 0:
        return quantity

    ratio = target_servings / original_servings
    scaled = quantity * ratio

    if is_discrete_ingredient(unit, ingredient_name):
        return float(math.ceil(scaled))
    
    return round(scaled, 2)

def scale_recipe_ingredients(ingredients: list, original_servings: int, target_servings: int) -> list:
    """Redimensionne une liste complète d'ingrédients d'une recette."""
    scaled_list = []
    for ing in ingredients:
        ing_copy = dict(ing)
        qty = ing_copy.get("quantity", 0.0)
        unit = ing_copy.get("unit", "")
        name = ing_copy.get("ingredient_name", "") or ing_copy.get("name", "")
        
        ing_copy["quantity"] = scale_quantity(qty, original_servings, target_servings, unit, name)
        scaled_list.append(ing_copy)
        
    return scaled_list

if __name__ == "__main__":
    # Exemple 1 : Ingrédient continu (Farine)
    print("Farine (4 pers -> 2 pers) :", scale_quantity(250.0, 4, 2, "g", "farine de blé"), "g")
    
    # Exemple 2 : Ingrédient discret (Oeufs)
    print("Oeufs (4 pers -> 2 pers)  :", scale_quantity(3.0, 4, 2, "", "oeufs"))
    print("Oeufs (4 pers -> 3 pers)  :", scale_quantity(3.0, 4, 3, "", "oeufs"))