from database.connection import get_connection

def ensure_schema_updates():
    """Vérifie et met à jour dynamiquement la structure de la base de données si nécessaire."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ajout de la colonne image_path si manquante
    cursor.execute("PRAGMA table_info(recipes);")
    columns = [row[1] for row in cursor.fetchall()]
    if "image_path" not in columns:
        cursor.execute("ALTER TABLE recipes ADD COLUMN image_path TEXT")
        
    conn.commit()
    conn.close()

def save_recipe(title: str, servings: int, ingredients_data: list, instructions: str = "", image_path: str = None, recipe_id: int = None) -> int:
    """Sauvegarde une nouvelle recette ou met à jour une recette existante."""
    ensure_schema_updates()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if recipe_id:
            # Mode Édition : Mise à jour de la recette
            cursor.execute(
                "UPDATE recipes SET title = ?, servings = ?, instructions = ?, image_path = ? WHERE id = ?", 
                (title.strip(), servings, instructions.strip(), image_path, recipe_id)
            )
            # Suppression des anciens ingrédients
            cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
            current_recipe_id = recipe_id
        else:
            # Mode Création : Nouvelle recette
            cursor.execute(
                "INSERT INTO recipes (title, servings, instructions, image_path) VALUES (?, ?, ?, ?)", 
                (title.strip(), servings, instructions.strip(), image_path)
            )
            current_recipe_id = cursor.lastrowid
        
        # Insertion des ingrédients
        for item in ingredients_data:
            ing_id = item.get("ingredient_id") or item.get("id") or item.get("ciqual_code")
            cursor.execute(
                """
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit)
                VALUES (?, ?, ?, ?)
                """,
                (current_recipe_id, ing_id, item.get("quantity", 1.0), item.get("unit", ""))
            )
            
        conn.commit()
        return current_recipe_id
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de la sauvegarde : {e}")
        return -1
    finally:
        conn.close()

def get_all_recipes() -> list:
    """Récupère la liste de toutes les recettes sauvegardées."""
    ensure_schema_updates()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM recipes ORDER BY id DESC")
    recipes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return recipes

def search_recipes(search_query: str = "") -> list:
    """Recherche des recettes par titre OU par nom d'ingrédient."""
    ensure_schema_updates()
    conn = get_connection()
    cursor = conn.cursor()
    
    if not search_query.strip():
        cursor.execute("SELECT * FROM recipes ORDER BY id DESC")
        recipes = [dict(row) for row in cursor.fetchall()]
    else:
        pattern = f"%{search_query.strip().lower()}%"
        cursor.execute("""
            SELECT DISTINCT r.* 
            FROM recipes r
            LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            LEFT JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE LOWER(r.title) LIKE ? 
               OR LOWER(i.name) LIKE ?
            ORDER BY r.id DESC
        """, (pattern, pattern))
        recipes = [dict(row) for row in cursor.fetchall()]
        
    conn.close()
    return recipes

def get_recipe_with_ingredients(recipe_id: int) -> dict:
    """Récupère une recette complète avec ses ingrédients associés."""
    ensure_schema_updates()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    recipe = cursor.fetchone()
    
    if not recipe:
        conn.close()
        return None
        
    recipe_dict = dict(recipe)
    
    cursor.execute("""
        SELECT ri.*, i.name as ingredient_name, i.energy_kcal, i.proteins, i.carbs, i.fat
        FROM recipe_ingredients ri
        LEFT JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
    """, (recipe_id,))
    
    recipe_dict["ingredients"] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return recipe_dict

def delete_recipe(recipe_id: int) -> bool:
    """Supprime une recette et ses ingrédients associés."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de la suppression : {e}")
        return False
    finally:
        conn.close()

def add_custom_ingredient(name: str, kcal: float, proteins: float, carbs: float, fat: float) -> int:
    """Ajoute un ingrédient personnalisé dans la base de données."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO ingredients (name, energy_kcal, proteins, carbs, fat) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (name.strip(), kcal, proteins, carbs, fat)
        )
        ing_id = cursor.lastrowid
        conn.commit()
        return ing_id
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de l'ajout de l'ingrédient : {e}")
        return -1
    finally:
        conn.close()