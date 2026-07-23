import os

def export_recipe_to_txt(recipe_title: str, servings: int, ingredients_text_list: list, instructions: str, nutrition_summary: str) -> str:
    """
    Exporte une recette formatée dans un fichier texte local.
    """
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    
    safe_title = "".join([c for c in recipe_title if c.isalpha() or c.isdigit() or c == ' ']).strip()
    filename = f"{safe_title.replace(' ', '_')}_{servings}pers.txt"
    filepath = os.path.join(export_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"RECETTE : {recipe_title.upper()}\n")
        f.write(f"Portions : {servings} personnes\n")
        f.write("-" * 40 + "\n\n")
        
        f.write("INGRÉDIENTS :\n")
        for ing in ingredients_text_list:
            f.write(f"{ing}\n")
        f.write("\n" + "-" * 40 + "\n\n")
        
        f.write("INSTRUCTIONS :\n")
        f.write(f"{instructions if instructions else 'Aucune instruction.'}\n")
        f.write("\n" + "-" * 40 + "\n\n")
        
        f.write("VALEURS NUTRITIONNELLES :\n")
        f.write(f"{nutrition_summary}\n")
        
    return filepath

if __name__ == "__main__":
    # Exemple d'export
    path = export_recipe_to_txt(
        "Pâte à crêpes", 
        4, 
        ["- 250.0 g Farine", "- 3.0 Oeufs"], 
        "Mélanger le tout.", 
        "Total (4 pers.) : 1200 kcal"
    )
    print(f"Fichier exporté vers : {path}")