import re

def parse_ingredient(line: str) -> dict:
    """
    Analyse une ligne de texte brute d'ingrédient et extrait la quantité, l'unité et le nom.
    Gère les abréviations (gr, cs, cc, dl), les contenants (boîtes, bottes, tasses),
    les plages de valeurs (2 à 3), les fractions et le nettoyage des parenthèses.
    """
    line = line.strip().lower()
    if not line:
        return {"quantity": 0.0, "unit": "", "name": ""}

    # 1. Nettoyage des précisions entre parenthèses (ex: "(160g)")
    line = re.sub(r"\(.*?\)", "", line).strip()

    has_half = False

    # 2. Détection et suppression des structures "et demi" / "et demie"
    if re.search(r"\bet demies?\b|\bet demis?\b", line):
        has_half = True
        line = re.sub(r"\bet demies?\b|\bet demis?\b", "", line).strip()

    # 3. Traitement des fourchettes de quantités (ex: "2 à 3" -> moyenne 2.5)
    range_match = re.search(r"^(\d+(?:[\.,]\d+)?)\s*(?:à|-)\s*(\d+(?:[\.,]\d+)?)", line)
    if range_match:
        val1 = float(range_match.group(1).replace(",", "."))
        val2 = float(range_match.group(2).replace(",", "."))
        avg_val = (val1 + val2) / 2.0
        line = re.sub(r"^(\d+(?:[\.,]\d+)?)\s*(?:à|-)\s*(\d+(?:[\.,]\d+)?)", str(avg_val), line)

    # 4. Remplacement des fractions textuelles et numériques
    text_fractions = {
        "un quart": "0.25", "1 quart": "0.25",
        "trois quarts": "0.75", "3 quarts": "0.75",
        "1/2": "0.5", "1/4": "0.25", "3/4": "0.75",
        "1/3": "0.33", "2/3": "0.66"
    }
    for frac_text, frac_val in text_fractions.items():
        line = line.replace(frac_text, frac_val)

    # 5. Remplacement des nombres écrits en toutes lettres
    text_numbers = {
        "un": "1", "une": "1", "deux": "2", "trois": "3", 
        "quatre": "4", "cinq": "5", "six": "6", "sept": "7", 
        "huit": "8", "neuf": "9", "dix": "10"
    }
    for word, digit in text_numbers.items():
        line = re.sub(rf"\b{word}\b", digit, line)

    # 6. Remplacement des expressions "demi" isolées en début de chaîne
    line = re.sub(r"^\b(1\s+)?demi\b", "0.5", line)

    # 7. Nettoyage des tirets de début
    line = re.sub(r"^(\d+(?:\.\d+)?)\s*-\s*", r"\1 ", line)

    # 8. Unités ordonnées par longueur décroissante avec limites de mots (\b)
    units_list = [
        r"cuillères?\s*à\s*soupe", r"cuillères?\s*à\s*café",
        r"cuillère?\s*à\s*soupe", r"cuillère?\s*à\s*café",
        r"c\.?\s*à\s*s\.?", r"c\.?\s*à\s*c\.?",
        r"boîtes?", r"boites?", r"bouquets?", r"poignées?",
        r"gousses?", r"tranches?", r"sachets?", r"bottes?",
        r"pincées?", r"verres?", r"brins?", r"pièces?", r"pots?", r"bols?", r"tasses?",
        r"gr\.?", r"cs", r"cc", r"kg", r"ml", r"cl", r"dl", r"g", r"l"
    ]

    units_pattern = r"|".join(units_list)
    pattern = rf"^([\d\.,]+)?\s*({units_pattern})\b\s*(?:d'|de|d’)?\s*(.*)$"

    match = re.match(pattern, line, re.IGNORECASE)

    if match:
        qty_str, unit_str, name_str = match.groups()

        if qty_str:
            try:
                quantity = float(qty_str.replace(",", "."))
            except ValueError:
                quantity = 1.0
        else:
            quantity = 1.0

        if has_half:
            quantity += 0.5

        unit = unit_str.strip().lower() if unit_str else ""

        unit_map = {
            "gr": "g", "gr.": "g",
            "cs": "cuillère à soupe", "c.a.s": "cuillère à soupe", "c.à.s": "cuillère à soupe", "c.à s.": "cuillère à soupe",
            "cc": "cuillère à café", "c.a.c": "cuillère à café", "c.à.c": "cuillère à café", "c.à c.": "cuillère à café",
            "boite": "boîte", "boites": "boîte", "boîtes": "boîte"
        }
        unit = unit_map.get(unit, unit)

        name = name_str.strip() if name_str else line

        return {
            "quantity": round(quantity, 2),
            "unit": unit,
            "name": name
        }

    # Cas sans unité spécifique détectée
    pattern_no_unit = r"^([\d\.,]+)?\s*(?:d'|de|d’)?\s*(.*)$"
    match_no_unit = re.match(pattern_no_unit, line, re.IGNORECASE)
    if match_no_unit:
        qty_str, name_str = match_no_unit.groups()
        if qty_str:
            try:
                quantity = float(qty_str.replace(",", "."))
            except ValueError:
                quantity = 1.0
        else:
            quantity = 1.0
        if has_half:
            quantity += 0.5
        return {"quantity": round(quantity, 2), "unit": "", "name": name_str.strip()}

    return {"quantity": 0.5 if has_half else 1.0, "unit": "", "name": line}


if __name__ == "__main__":
    test_lines = [
        "250gr de farine de blé",
        "2cs d'huile d'olive",
        "1 cc de sel",
        "2 dl de crème fraîche",
        "1 boîte de tomates pelées (160g)",
        "1/2 botte de persil",
        "2 brins de thym",
        "1 poignée de noix",
        "2 à 3 gousses d'ail",
        "un quart de citron",
        "un oignon et demi"
    ]

    print("--- Tests avancés du parser ---")
    for test in test_lines:
        res = parse_ingredient(test)
        print(f"Saisie : '{test}'")
        print(f"  -> Quantité : {res['quantity']}")
        print(f"  -> Unité    : '{res['unit']}'")
        print(f"  -> Produit  : '{res['name']}'")
        print("-" * 35)