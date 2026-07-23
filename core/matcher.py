import difflib
import unicodedata
from database.connection import get_connection

# Dictionnaire de traduction vers la nomenclature CIQUAL exacte
SYNONYMS = {
    "spaghetti": "pâtes sèches",
    "coquillette": "pâtes sèches",
    "macaroni": "pâtes sèches",
    "penne": "pâtes sèches",
    "tagliatelle": "pâtes sèches",
    "nouille": "pâtes sèches",
    "nouilles": "pâtes sèches",
    "farfalle": "pâtes sèches",
    "vermicelle": "pâtes sèches",
    "ravioli": "pâtes sèches",
    "maizena": "amidon de maïs",
    "maïzena": "amidon de maïs",
    "levure chimique": "poudre à lever",
    "cassonade": "sucre roux",
    "lait de soja": "boisson au soja",
    "lait d'amande": "boisson à l'amande",
    "lait d'avoine": "boisson à l'avoine",
    "steak végétal": "substitut de viande",
    "haché végétal": "substitut de viande",
    "saucisse végétale": "substitut de viande",
    "vache qui rit": "fromage fondu",
    "kiri": "fromage fondu",
    "philadelphia": "fromage à tartiner",
    "st moret": "fromage à tartiner",
    "nutella": "pâte à tartiner",
    "gruyère râpé": "gruyère",
    "emmental râpé": "emmental"
}

def strip_accents(s: str) -> str:
    """Supprime les accents pour une comparaison tolérante (ex: Pâtes -> Pates)."""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def normalize_text(text: str) -> str:
    """Nettoyage de base."""
    text = text.lower().strip()
    text = text.replace("œ", "oe")
    return text

def get_singular(word: str) -> str:
    """Transforme un mot au singulier simple."""
    if len(word) > 3 and word.endswith(('s', 'x')):
        return word[:-1]
    return word

def find_best_ingredient_match(parsed_name: str, limit: int = 5) -> dict:
    """
    Recherche en mémoire sur toute la BDD pour ignorer les problèmes d'accents SQL
    et appliquer un scoring sémantique ultra-précis.
    """
    raw_name = normalize_text(parsed_name)
    if not raw_name:
        return {"best_match": None, "alternatives": []}

    # 1. Application des synonymes
    for key, value in SYNONYMS.items():
        if key in raw_name:
            raw_name = raw_name.replace(key, value)

    words = raw_name.split()
    singular_words = [get_singular(w) for w in words]
    mapped_name = " ".join(singular_words)

    # 2. Récupération globale pour filtrage 100% Python (très rapide sur ~3000 lignes)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ingredients")
    all_ingredients = [dict(row) for row in cursor.fetchall()]
    conn.close()

    norm_mapped = strip_accents(mapped_name)
    mapped_words_list = norm_mapped.split()
    norm_raw = strip_accents(raw_name)

    def compute_score(candidate: dict) -> float:
        cand_name = normalize_text(candidate["name"])
        norm_cand = strip_accents(cand_name)
        cand_words = norm_cand.replace(',', ' ').split()
        
        # A. Comptage des mots correspondants exacts
        words_in = sum(1 for w in mapped_words_list if len(w) > 2 and any(w in cw for cw in cand_words))
        
        # B. Similarité textuelle globale
        ratio = difflib.SequenceMatcher(None, norm_mapped, norm_cand).ratio()
        
        # Exclusion très rapide des résultats non pertinents
        if words_in == 0 and ratio < 0.4:
            return -100.0
            
        score = ratio + (words_in * 0.5)

        # C. Bonus si le produit commence par le terme recherché
        if norm_cand.startswith(norm_mapped) or norm_cand.startswith(norm_raw):
            score += 1.0

        first_word_cand = cand_words[0] if cand_words else ""
        if mapped_words_list and first_word_cand.startswith(mapped_words_list[0]):
            score += 0.5

        # D. Pénalités de contexte (Différencier la Pasta de la Pâte à tarte)
        if "pate seche" in norm_mapped or "pates seches" in norm_mapped or "nouille" in norm_mapped:
            if any(dough in norm_cand for dough in ["brisee", "sablee", "pizza", "feuilletee"]):
                score -= 2.0

        # E. Pénalités de contexte (Différencier les produits végétaux/laitiers de la viande)
        if "pate" in norm_mapped or "lait" in norm_mapped or "soja" in norm_mapped:
            animal_keywords = ["viande", "boeuf", "poulet", "porc", "poisson", "saumon", "thon", "sanglier", "sprat", "escargot", "sabre", "lardon"]
            if any(kw in norm_cand for kw in animal_keywords):
                score -= 2.0

        # F. Malus de longueur pour privilégier les noms génériques courts et propres
        score -= len(cand_name) * 0.001

        return score

    scored_candidates = []
    for cand in all_ingredients:
        s = compute_score(cand)
        if s > 0:
            scored_candidates.append((s, cand))

    # Tri décroissant selon le score final calculé
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    unique_candidates = []
    seen_ids = set()
    for score, c in scored_candidates:
        if c["id"] not in seen_ids:
            seen_ids.add(c["id"])
            unique_candidates.append(c)
            if len(unique_candidates) == limit:
                break

    return {
        "best_match": unique_candidates[0] if unique_candidates else None,
        "alternatives": unique_candidates
    }