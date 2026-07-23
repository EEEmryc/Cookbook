from database.connection import get_connection

def init_db():
    
    #Crée l'ensemble des tables nécessaires dans mon_livre.db si elles n'existent pas.
    
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1 : ingredients (Catalogue CIQUAL et nutriments pour 100g)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code_ciqual INTEGER UNIQUE,
        name TEXT NOT NULL,
        energy_kcal REAL DEFAULT 0,
        proteins REAL DEFAULT 0,
        carbs REAL DEFAULT 0,
        fat REAL DEFAULT 0,
        density REAL DEFAULT 1.0,
        unit_weight REAL
    );
    """)

    # Table 2 : recipes (Métadonnées globales de la recette)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        instructions TEXT NOT NULL,
        servings INTEGER DEFAULT 1,
        prep_time INTEGER,
        cook_time INTEGER,
        difficulty TEXT
    );
    """)

    # Table 3 : recipe_ingredients (Table d'association Recette <-> Ingrédient)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipe_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        ingredient_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
    );
    """)

    # Table 4 : user_mappings (Correspondances texte saisie <-> ingrédient CIQUAL)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_term TEXT UNIQUE NOT NULL,
        ingredient_id INTEGER NOT NULL,
        FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
    );
    """)

    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès.")

if __name__ == "__main__":
    init_db()    