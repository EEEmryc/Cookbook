import flet as ft
import os
import shutil
from core.parser import parse_ingredient
from core.matcher import find_best_ingredient_match
from core.calculator import calculate_ingredient_nutrition
from core.scaler import scale_recipe_ingredients
from core.exporter import export_recipe_to_txt
from core.recipe_manager import (
    save_recipe,
    search_recipes,
    get_recipe_with_ingredients,
    delete_recipe,
    add_custom_ingredient
)

def main(page: ft.Page):
    page.title = "Mon livre de recettes"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121214"
    page.padding = 20
    page.window_width = 1200
    page.window_height = 850
    page.window_maximized = True

    COLOR_CARD_BG = "#1E1E22"
    COLOR_BORDER = "#3F3F46"
    COLOR_TEXT_MUTED = "#A1A1AA"
    COLOR_BUTTON_BG = "#27272A"

    os.makedirs("assets/images", exist_ok=True)
    
    editing_recipe_id = None
    current_image_path = None
    selected_ingredients_state = []

    # --- EN-TÊTE GLOBAL ---
    header_logo_placeholder = ft.Container(
        content=ft.Icon(ft.icons.MENU_BOOK, size=32, color=ft.colors.WHITE70),
        padding=5,
        border=ft.border.all(1, COLOR_BORDER),
        border_radius=8,
    )

    header = ft.Container(
        content=ft.Row(
            controls=[
                header_logo_placeholder,
                ft.Text("Mon livre de recettes", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=15
        ),
        padding=ft.padding.only(bottom=10),
        alignment=ft.alignment.center
    )

    # --- FENÊTRES MODALES ET DIALOGUES ---
    
    # 1. Ajout d'ingrédient personnalisé
    custom_ing_name = ft.TextField(label="Nom de l'ingrédient")
    custom_ing_kcal = ft.TextField(label="Kcal / 100g", value="0", keyboard_type=ft.KeyboardType.NUMBER)
    custom_ing_p = ft.TextField(label="Protéines (g)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
    custom_ing_c = ft.TextField(label="Glucides (g)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
    custom_ing_f = ft.TextField(label="Lipides (g)", value="0", keyboard_type=ft.KeyboardType.NUMBER)
    custom_ing_status = ft.Text("", size=12)

    def save_custom_ingredient(e):
        try:
            name = custom_ing_name.value.strip()
            if not name:
                raise ValueError("Le nom est obligatoire.")
            kcal = float(custom_ing_kcal.value)
            p = float(custom_ing_p.value)
            c = float(custom_ing_c.value)
            f = float(custom_ing_f.value)
            
            res = add_custom_ingredient(name, kcal, p, c, f)
            if res != -1:
                custom_ing_dialog.open = False
                status_text.value = f"Ingrédient '{name}' ajouté à la base."
                status_text.color = ft.colors.GREEN_400
                page.update()
            else:
                custom_ing_status.value = "Erreur base de données."
                custom_ing_status.color = ft.colors.RED_400
                page.update()
        except ValueError as ex:
            custom_ing_status.value = f"Erreur : {ex}"
            custom_ing_status.color = ft.colors.RED_400
            page.update()

    custom_ing_dialog = ft.AlertDialog(
        title=ft.Text("Nouvel ingrédient personnalisé", size=18),
        content=ft.Column([
            custom_ing_name, custom_ing_kcal, custom_ing_p, custom_ing_c, custom_ing_f, custom_ing_status
        ], tight=True, spacing=10),
        actions=[
            ft.TextButton("Ajouter", on_click=save_custom_ingredient),
            ft.TextButton("Annuler", on_click=lambda e: setattr(custom_ing_dialog, 'open', False) or page.update())
        ]
    )
    page.dialog = custom_ing_dialog

    # 2. Fenêtre de consultation (Détails, Image, Export)
    def open_recipe_details(recipe_id: int):
        recipe = get_recipe_with_ingredients(recipe_id)
        if not recipe:
            return

        original_servings = recipe["servings"]
        current_servings_text = ft.Text(str(original_servings), size=16, weight=ft.FontWeight.BOLD)

        ingredients_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=150)
        nutrition_summary_text = ft.Text("", size=13, color=COLOR_TEXT_MUTED)
        export_status = ft.Text("", size=12, color=ft.colors.GREEN_400)
        
        current_ingredients_text_list = []

        def update_scaled_details():
            try:
                target_servings = int(current_servings_text.value)
            except ValueError:
                target_servings = original_servings

            scaled_ings = scale_recipe_ingredients(recipe["ingredients"], original_servings, target_servings)
            ingredients_list_col.controls.clear()
            current_ingredients_text_list.clear()

            tot_kcal, tot_p, tot_c, tot_f = 0.0, 0.0, 0.0, 0.0

            for ing in scaled_ings:
                ing_id = ing.get("ingredient_id") or ing.get("ciqual_code")
                qty = ing.get("quantity", 0.0)
                unit = ing.get("unit", "")
                ing_name = ing.get("ingredient_name") or f"Ingrédient #{ing_id}"

                if ing_id:
                    nutr = calculate_ingredient_nutrition(ing_id, qty, unit)
                    tot_kcal += nutr["energy_kcal"]
                    tot_p += nutr["proteins"]
                    tot_c += nutr["carbs"]
                    tot_f += nutr["fat"]
                    nutr_str = f"({nutr['energy_kcal']} kcal | P: {nutr['proteins']}g)"
                else:
                    nutr_str = ""

                line_text = f"- {qty} {unit} {ing_name} {nutr_str}".strip()
                ingredients_list_col.controls.append(ft.Text(line_text, size=13, color=ft.colors.WHITE))
                current_ingredients_text_list.append(line_text)

            nutrition_summary_text.value = (
                f"Total ({target_servings} pers.) : {round(tot_kcal, 1)} kcal | "
                f"P: {round(tot_p, 1)}g | G: {round(tot_c, 1)}g | L: {round(tot_f, 1)}g"
            )
            page.update()

        def dec_servings(e):
            val = max(1, int(current_servings_text.value) - 1)
            current_servings_text.value = str(val)
            update_scaled_details()

        def inc_servings(e):
            val = int(current_servings_text.value) + 1
            current_servings_text.value = str(val)
            update_scaled_details()
            
        def trigger_export(e):
            path = export_recipe_to_txt(
                recipe["title"], 
                int(current_servings_text.value), 
                current_ingredients_text_list, 
                recipe["instructions"], 
                nutrition_summary_text.value
            )
            export_status.value = f"Exporté : {path}"
            page.update()

        img_display = ft.Container()
        if recipe.get("image_path") and os.path.exists(recipe["image_path"]):
            img_display = ft.Image(src=recipe["image_path"], height=150, fit=ft.ImageFit.COVER, border_radius=8)

        details_dialog = ft.AlertDialog(
            title=ft.Text(recipe["title"], size=20, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=550,
                content=ft.Column([
                    img_display,
                    ft.Row([
                        ft.Text("Ajuster portions :", size=13, color=COLOR_TEXT_MUTED),
                        ft.IconButton(icon=ft.icons.REMOVE, on_click=dec_servings, icon_size=16),
                        current_servings_text,
                        ft.IconButton(icon=ft.icons.ADD, on_click=inc_servings, icon_size=16),
                        ft.ElevatedButton("Exporter (TXT)", on_click=trigger_export, icon=ft.icons.DOWNLOAD)
                    ], alignment=ft.MainAxisAlignment.START),
                    export_status,
                    ft.Divider(color=COLOR_BORDER),
                    ft.Text("Ingrédients :", weight=ft.FontWeight.BOLD, size=14),
                    ingredients_list_col,
                    nutrition_summary_text,
                    ft.Divider(color=COLOR_BORDER),
                    ft.Text("Instructions :", weight=ft.FontWeight.BOLD, size=14),
                    ft.Text(recipe["instructions"] or "Aucune instruction.", size=13, color=COLOR_TEXT_MUTED)
                ], spacing=10, tight=True)
            ),
            actions=[
                ft.TextButton("Fermer", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update())
            ]
        )

        page.dialog = details_dialog
        details_dialog.open = True
        update_scaled_details()

    # --- ÉDITEUR : GESTION DES IMAGES ---
    editor_image_display = ft.Image(src=None, height=100, fit=ft.ImageFit.CONTAIN, visible=False)

    def on_image_picked(e: ft.FilePickerResultEvent):
        nonlocal current_image_path
        if e.files:
            file_path = e.files[0].path
            filename = os.path.basename(file_path)
            dest_path = os.path.join("assets", "images", filename)
            shutil.copy(file_path, dest_path)
            
            current_image_path = os.path.abspath(dest_path)
            editor_image_display.src = current_image_path
            editor_image_display.visible = True
            page.update()

    image_picker = ft.FilePicker(on_result=on_image_picked)
    page.overlay.append(image_picker)

    # --- VUE ACCUEIL ---
    recipes_list_container = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=12, expand=True)
    search_field = ft.TextField(
        hint_text="Rechercher par titre ou par ingrédient...",
        prefix_icon=ft.icons.SEARCH,
        width=600,
        border_color=COLOR_BORDER,
        focused_border_color=ft.colors.WHITE54,
        content_padding=12,
        on_change=lambda e: refresh_home_recipes(search_field.value)
    )

    def load_recipe_for_edit(recipe_id: int):
        nonlocal editing_recipe_id, current_image_path
        recipe = get_recipe_with_ingredients(recipe_id)
        if not recipe: return
        
        editing_recipe_id = recipe["id"]
        title_field.value = recipe["title"]
        servings_value.value = str(recipe["servings"])
        instructions_field.value = recipe["instructions"]
        
        raw_ings = []
        for ing in recipe["ingredients"]:
            qty = ing.get("quantity", "")
            unit = ing.get("unit", "")
            name = ing.get("ingredient_name", "")
            raw_ings.append(f"{qty} {unit} {name}".strip())
        ingredients_field.value = "\n".join(raw_ings)
        
        current_image_path = recipe.get("image_path")
        if current_image_path and os.path.exists(current_image_path):
            editor_image_display.src = current_image_path
            editor_image_display.visible = True
        else:
            editor_image_display.visible = False
            
        status_text.value = f"Mode édition : {recipe['title']}"
        status_text.color = ft.colors.ORANGE_400
        
        tabs.selected_index = 1
        page.update()
        analyze_action(None)

    def delete_action_from_home(recipe_id: int):
        delete_recipe(recipe_id)
        refresh_home_recipes(search_field.value)

    def refresh_home_recipes(filter_text: str = ""):
        recipes_list_container.controls.clear()
        recipes = search_recipes(filter_text)

        if not recipes:
            recipes_list_container.controls.append(
                ft.Container(content=ft.Text("Aucune recette trouvée.", color=COLOR_TEXT_MUTED), padding=30)
            )
        else:
            for r in recipes:
                rec_id = r["id"]
                full_recipe = get_recipe_with_ingredients(rec_id)
                
                if full_recipe and full_recipe.get("ingredients"):
                    ing_str = " - ".join([f"{ing.get('quantity', '')} {ing.get('unit', '')} {ing.get('ingredient_name', '')}".strip() for ing in full_recipe["ingredients"]])
                else:
                    ing_str = "Aucun ingrédient."

                card = ft.Card(
                    color=COLOR_CARD_BG,
                    content=ft.Container(
                        on_click=lambda e, rid=rec_id: open_recipe_details(rid),
                        padding=16,
                        height=95,
                        content=ft.Row([
                            ft.Column([
                                ft.Text(r["title"], weight=ft.FontWeight.BOLD, size=18, color=ft.colors.WHITE),
                                ft.Text(ing_str, size=13, color=COLOR_TEXT_MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                            ], expand=True),
                            ft.Row([
                                ft.IconButton(icon=ft.icons.EDIT, on_click=lambda e, rid=rec_id: load_recipe_for_edit(rid)),
                                ft.IconButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=lambda e, rid=rec_id: delete_action_from_home(rid))
                            ])
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                )
                recipes_list_container.controls.append(card)
        page.update()

    home_view_content = ft.Container(
        content=ft.Column([search_field, ft.Container(content=recipes_list_container, width=700, expand=True)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, expand=True),
        alignment=ft.alignment.top_center, expand=True, padding=10
    )

    # --- VUE NOUVELLE RECETTE / ÉDITION ---
    servings_value = ft.Text("4", size=16, weight=ft.FontWeight.BOLD)
    
    title_field = ft.TextField(border_color=COLOR_BORDER, focused_border_color=ft.colors.WHITE54)
    
    ingredients_field = ft.TextField(
        multiline=True, 
        min_lines=6, 
        max_lines=6, 
        border_color=COLOR_BORDER,
        focused_border_color=ft.colors.WHITE54
    )
    
    instructions_field = ft.TextField(
        multiline=True, 
        min_lines=8, 
        max_lines=8, 
        border_color=COLOR_BORDER,
        focused_border_color=ft.colors.WHITE54
    )
    
    status_text = ft.Text(value="", size=13)

    cards_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)
    total_nutrition_badge = ft.Text(value="Total : 0 kcal", size=14, weight=ft.FontWeight.W_500, color=ft.colors.WHITE)

    def recalculate_totals():
        total_kcal, total_p, total_c, total_f = 0.0, 0.0, 0.0, 0.0
        for item in selected_ingredients_state:
            ing_id = item["selected_id"]
            if ing_id:
                nutr = calculate_ingredient_nutrition(ing_id, item["qty"], item["unit"])
                total_kcal += nutr["energy_kcal"]
                total_p += nutr["proteins"]
                total_c += nutr["carbs"]
                total_f += nutr["fat"]
                item["card_nutr_text"].value = f"Valeurs : {nutr['energy_kcal']} kcal | Protéines : {nutr['proteins']} g | Glucides : {nutr['carbs']} g | Lipides : {nutr['fat']} g"
        total_nutrition_badge.value = f"Total : {round(total_kcal, 1)} kcal | Protéines : {round(total_p, 1)} g | Glucides : {round(total_c, 1)} g | Lipides : {round(total_f, 1)} g"
        page.update()

    def analyze_action(e):
        selected_ingredients_state.clear()
        cards_container.controls.clear()
        lines = [l.strip() for l in ingredients_field.value.split("\n") if l.strip()]

        for idx, line in enumerate(lines):
            parsed = parse_ingredient(line)
            matched = find_best_ingredient_match(parsed["name"])
            alternatives = matched.get("alternatives", [])
            best = matched.get("best_match")

            options = [ft.dropdown.Option(key=str(alt["id"]), text=alt["name"]) for alt in alternatives]
            selected_id = best["id"] if best else None
            nutr_text = ft.Text(value="", size=12, color=COLOR_TEXT_MUTED)

            state_item = {"parsed": parsed, "selected_id": selected_id, "qty": parsed["quantity"], "unit": parsed["unit"], "card_nutr_text": nutr_text}
            selected_ingredients_state.append(state_item)

            dropdown = ft.Dropdown(
                label="Correspondance BDD", options=options, value=str(selected_id) if selected_id else None,
                on_change=lambda ev, index=idx: (selected_ingredients_state.__setitem__(index, {**selected_ingredients_state[index], "selected_id": int(ev.control.value)}) or recalculate_totals()),
                border_color=COLOR_BORDER, expand=True
            )

            card = ft.Card(
                color=COLOR_CARD_BG,
                content=ft.Container(
                    padding=12,
                    content=ft.Column([
                        ft.Text(f"Saisie : {line}", weight=ft.FontWeight.W_600, size=13, color=ft.colors.WHITE),
                        ft.Row([dropdown]),
                        ft.Text(f"Quantité extraite : {parsed['quantity']} {parsed['unit']}", size=12, color=COLOR_TEXT_MUTED),
                        nutr_text
                    ])
                )
            )
            cards_container.controls.append(card)
        recalculate_totals()

    def save_action(e):
        nonlocal editing_recipe_id, current_image_path
        if not title_field.value.strip():
            status_text.value = "Erreur : Titre obligatoire."
            status_text.color = ft.colors.RED_400
            page.update()
            return

        if not selected_ingredients_state:
            analyze_action(None)

        payload = [{"ingredient_id": item["selected_id"], "quantity": item["qty"], "unit": item["unit"]} for item in selected_ingredients_state if item["selected_id"]]
        if not payload:
            status_text.value = "Erreur : Aucun ingrédient valide."
            status_text.color = ft.colors.RED_400
            page.update()
            return

        recipe_id = save_recipe(title_field.value, int(servings_value.value), payload, instructions_field.value, current_image_path, editing_recipe_id)

        if recipe_id != -1:
            status_text.value = "Recette enregistrée avec succès."
            status_text.color = ft.colors.GREEN_400
            editing_recipe_id = None 
            refresh_home_recipes()
        else:
            status_text.value = "Erreur base de données."
            status_text.color = ft.colors.RED_400
        page.update()

    def reset_editor(e):
        nonlocal editing_recipe_id, current_image_path
        editing_recipe_id = None
        current_image_path = None
        title_field.value = ""
        ingredients_field.value = ""
        instructions_field.value = ""
        servings_value.value = "4"
        editor_image_display.visible = False
        cards_container.controls.clear()
        status_text.value = "Formulaire réinitialisé."
        status_text.color = COLOR_TEXT_MUTED
        page.update()

    left_column = ft.Column([
        ft.Row([
            ft.Text("Créer/Éditer une recette", size=18, weight=ft.FontWeight.W_600, color=ft.colors.WHITE),
            ft.IconButton(icon=ft.icons.RESTART_ALT, tooltip="Réinitialiser", on_click=reset_editor)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        
        ft.Text("Titre de la recette", size=13, color=COLOR_TEXT_MUTED),
        title_field,
        
        ft.Row([
            ft.Text("Portions :", size=13, color=COLOR_TEXT_MUTED),
            ft.IconButton(icon=ft.icons.REMOVE, on_click=lambda e: setattr(servings_value, 'value', str(max(1, int(servings_value.value)-1))) or page.update(), icon_size=18),
            servings_value,
            ft.IconButton(icon=ft.icons.ADD, on_click=lambda e: setattr(servings_value, 'value', str(int(servings_value.value)+1)) or page.update(), icon_size=18),
        ], alignment=ft.MainAxisAlignment.START),
        
        ft.Row([
            ft.ElevatedButton("Ajouter une image", icon=ft.icons.IMAGE, on_click=lambda _: image_picker.pick_files(allow_multiple=False)),
            editor_image_display
        ]),
        
        ft.Text("Ingrédients (un par ligne)", size=13, color=COLOR_TEXT_MUTED),
        ingredients_field,
        
        ft.Text("Instructions de préparation", size=13, color=COLOR_TEXT_MUTED),
        instructions_field,
        
        ft.Container(expand=True),
        
        ft.Row([
            ft.OutlinedButton("Analyser", on_click=analyze_action, icon=ft.icons.ANALYTICS),
            ft.ElevatedButton("Sauvegarder", on_click=save_action, icon=ft.icons.SAVE, bgcolor=COLOR_BUTTON_BG, color=ft.colors.WHITE),
        ]),
        status_text
    ], expand=1, spacing=10)

    right_column = ft.Column([
        ft.Row([
            ft.Text("Validation BDD", size=18, weight=ft.FontWeight.W_600, color=ft.colors.WHITE),
            ft.ElevatedButton("Créer ingrédient", icon=ft.icons.ADD, on_click=lambda e: setattr(custom_ing_dialog, 'open', True) or page.update())
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        total_nutrition_badge,
        ft.Divider(color=COLOR_BORDER),
        cards_container
    ], expand=1, spacing=12)

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(text="Accueil / Livre de recettes", icon=ft.icons.BOOKMARK_BORDER, content=home_view_content),
            ft.Tab(text="Éditeur de recette", icon=ft.icons.EDIT_DOCUMENT, content=ft.Container(content=ft.Row([left_column, ft.VerticalDivider(width=1, color=COLOR_BORDER), right_column], expand=True, spacing=20), padding=10, expand=True))
        ],
        expand=True
    )

    page.add(header, ft.Container(content=tabs, expand=True))
    refresh_home_recipes()

if __name__ == "__main__":
    ft.app(target=main)