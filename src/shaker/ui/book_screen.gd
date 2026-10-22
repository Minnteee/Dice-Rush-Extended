extends "res://shaker/ui/screen_base.gd"
## Dice book: all 100 dice sorted by rarity. Dice you have not rolled yet stay dark.

const COLUMNS := 8
const CELL := Vector2(212, 196)

var found_label: Label


func _build() -> void:
	var panel := frame(I18N.t("book.title"))
	var found: Array = game.state.discovered
	found_label = Kit.label(panel, "", Rect2(60, 96, 1720, 40), 18, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOOD)
	Kit.set_text(found_label, I18N.f("book.found", {"n": found.size(), "total": Data.dice.size(), "pct": found.size() * int(Data.b("collection_pct", 2))}))
	Kit.label(panel, I18N.t("book.hint"), Rect2(60, 134, 1720, 30), 12, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)
	var scroll := Kit.scroll(panel, Rect2(24, 172, 1792, 832))
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 10)
	scroll.add_child(list)
	for rarity in Data.rarities:
		var header := Label.new()
		header.custom_minimum_size = Vector2(1760, 44)
		header.text = I18N.upper(I18N.t("rarity." + str(rarity)))
		header.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		header.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		header.add_theme_font_override("font", Kit.pixel_font)
		header.add_theme_font_size_override("font_size", 20)
		header.add_theme_color_override("font_color", Data.rarity_color(str(rarity)))
		header.add_theme_color_override("font_outline_color", Color("0b0512"))
		header.add_theme_constant_override("outline_size", 5)
		list.add_child(header)
		var grid := GridContainer.new()
		grid.columns = COLUMNS
		grid.add_theme_constant_override("h_separation", 8)
		grid.add_theme_constant_override("v_separation", 8)
		list.add_child(grid)
		for def in Data.dice_by_rarity.get(rarity, []):
			_add_cell(grid, def, str(def.id) in found)


func _add_cell(grid: GridContainer, def: Dictionary, known: bool) -> void:
	var cell := Panel.new()
	cell.custom_minimum_size = CELL
	var color := Data.rarity_color(str(def.rarity))
	cell.add_theme_stylebox_override("panel", Kit.style(Color("1d1030") if known else Color("120a1c"), color if known else color.darkened(0.6), 3, 14))
	cell.mouse_filter = Control.MOUSE_FILTER_STOP
	grid.add_child(cell)
	var icon := Kit.texture(cell, Tex.square(str(def.art), 128), Rect2((CELL.x - 128) * 0.5, 10, 128, 128), false)
	if not known:
		icon.modulate = Color(0.08, 0.04, 0.14, 0.92)
	var title: String = I18N.upper(game.call("die_name", str(def.id))) if known else I18N.t("book.unknown")
	Kit.paragraph(cell, title, Rect2(8, 140, CELL.x - 16, 50), 12, HORIZONTAL_ALIGNMENT_CENTER, color if known else Kit.MUTED)
	if known:
		cell.mouse_entered.connect(func() -> void: tooltip(game.call("die_info", str(def.id), {})))
		cell.mouse_exited.connect(hide_tip)
