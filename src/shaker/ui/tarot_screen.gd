extends "res://shaker/ui/screen_base.gd"
## Tarot: pay money to draw cards, pick one. The same card again raises its rank
## (1 copy common, 2 rare, 3 epic, 4 legendary).

var cells: Dictionary = {}            # card id -> {texture, label}
var draw_button: Button
var offer_layer: Control
var offer_signature := ""
var info_label: Label
var cells_signature := ""


static func rank_name(copies: int) -> String:
	var ranks: Array = Data.raw.get("tarot_ranks", ["common", "rare", "epic", "legendary"])
	return str(ranks[clampi(copies, 1, 4) - 1])


static func card_effect_text(card_id: String, copies: int) -> String:
	var card: Dictionary = Data.tarot_by_id.get(card_id, {})
	var lines: Array[String] = []
	for effect in card.get("effects", []):
		lines.append(stat_line(str(effect[0]), float((effect[1] as Array)[clampi(copies, 1, 4) - 1])))
	return "\n".join(lines)


func _build() -> void:
	var panel := frame(I18N.t("tarot.title"))
	draw_button = Kit.button(panel, I18N.t("tarot.draw"), Rect2(620, 96, 600, 80), _draw_cards, 22, Color("4a2a70"), Kit.GOLD_LIGHT)
	info_label = Kit.paragraph(panel, I18N.t("tarot.hint"), Rect2(420, 180, 1000, 34), 13, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)
	offer_layer = Control.new()
	offer_layer.position = Vector2(0, 96)
	offer_layer.size = Vector2(1840, 470)
	offer_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(offer_layer)
	var bottom := Kit.panel(panel, Rect2(24, 572, 1792, 432), Kit.PANEL_LIGHT, Kit.GOLD, 3, 16)
	Kit.label(bottom, I18N.t("tarot.your_cards"), Rect2(16, 4, 1760, 36), 18, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT)
	var columns := 15
	var cell_w := 112.0
	var x0 := (1792.0 - cell_w * columns) * 0.5
	for i in Data.tarot.size():
		var card: Dictionary = Data.tarot[i]
		var cell := Control.new()
		cell.position = Vector2(x0 + (i % columns) * cell_w, 42 + (i / columns) * 192)
		cell.size = Vector2(cell_w, 188)
		cell.mouse_filter = Control.MOUSE_FILTER_STOP
		cell.mouse_entered.connect(_cell_tip.bind(str(card.id)))
		cell.mouse_exited.connect(hide_tip)
		bottom.add_child(cell)
		var texture := Kit.texture(cell, Tex.get_tex(ART + "tarot/%s.png" % card.id), Rect2(5, 2, 102, 158), true)
		var label := Kit.label(cell, "", Rect2(0, 160, cell_w, 26), 12, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)
		cells[str(card.id)] = {"texture": texture, "label": label}
	refresh()


func refresh() -> void:
	super.refresh()
	var state: Dictionary = game.state
	var tarot_state: Dictionary = state.tarot
	var sig := str(tarot_state)
	if sig != cells_signature:
		cells_signature = sig
		for card_id in cells:
			var copies := int(tarot_state.get(card_id, 0))
			var widgets: Dictionary = cells[card_id]
			(widgets.texture as TextureRect).modulate = Color(1, 1, 1, 1) if copies > 0 else Color(0.32, 0.26, 0.4, 0.85)
			Kit.set_text(widgets.label, I18N.f("tarot.copies", {"n": copies}))
			(widgets.label as Label).add_theme_color_override("font_color", Data.rarity_color(rank_name(copies)) if copies > 0 else Kit.MUTED)
	var offer: Array = state.get("tarot_offer", [])
	var complete := true
	for card in Data.tarot:
		if int(tarot_state.get(str(card.id), 0)) < 4:
			complete = false
			break
	if complete:
		Kit.set_button_text(draw_button, I18N.t("tarot.complete"))
		draw_button.disabled = true
	elif not offer.is_empty():
		Kit.set_button_text(draw_button, I18N.t("tarot.choose"))
		draw_button.disabled = true
	else:
		var price: float = Rules.tarot_price(state, game.stats)
		Kit.set_button_text(draw_button, "%s  ·  %s" % [I18N.t("tarot.draw"), I18N.money(price)])
		draw_button.disabled = float(state.money) < price
	var offer_sig := str(offer)
	if offer_sig != offer_signature:
		offer_signature = offer_sig
		_build_offer(offer)


func _build_offer(offer: Array) -> void:
	for child in offer_layer.get_children():
		child.queue_free()
	draw_button.visible = offer.is_empty()
	info_label.visible = offer.is_empty()
	if offer.is_empty():
		return
	var count := offer.size()
	var gap := 16.0
	var width := minf(330.0, (1800.0 - gap * (count - 1)) / count)
	var x0 := (1840.0 - (width * count + gap * (count - 1))) * 0.5
	var tarot_state: Dictionary = game.state.tarot
	for i in count:
		var card_id := str(offer[i])
		var copies := int(tarot_state.get(card_id, 0))
		var next := copies + 1
		var button := Button.new()
		button.position = Vector2(x0 + i * (width + gap), 0)
		button.size = Vector2(width, 466)
		button.focus_mode = Control.FOCUS_ALL
		button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		var color := Data.rarity_color(rank_name(next))
		button.add_theme_stylebox_override("normal", Kit.style(Color("1d1030"), color.darkened(0.2), 3, 14))
		button.add_theme_stylebox_override("hover", Kit.style(Color("2d1a48"), color, 5, 14))
		button.add_theme_stylebox_override("pressed", Kit.style(Color("150a24"), color, 5, 14))
		button.add_theme_stylebox_override("focus", Kit.style(Color.TRANSPARENT, Kit.GOLD_LIGHT, 3, 14))
		button.pressed.connect(_pick.bind(card_id))
		offer_layer.add_child(button)
		Kit.texture(button, Tex.get_tex(ART + "tarot/%s.png" % card_id), Rect2((width - 153.0) * 0.5, 10, 153, 237), true)
		Kit.label(button, I18N.upper(I18N.t("tarot.%s.name" % card_id)), Rect2(8, 252, width - 16, 36), 16, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT)
		var tag := I18N.t("tarot.new_card") if copies == 0 else I18N.t("tarot.rank_up")
		Kit.label(button, "%s · %s · %s" % [tag, I18N.upper(I18N.t("rank." + rank_name(next))), I18N.f("tarot.copies", {"n": next})], Rect2(8, 290, width - 16, 30), 12, HORIZONTAL_ALIGNMENT_CENTER, color)
		Kit.paragraph(button, card_effect_text(card_id, next), Rect2(12, 326, width - 24, 130), 15, HORIZONTAL_ALIGNMENT_CENTER, Kit.TEXT)
		button.scale = Vector2(0.92, 0.92)
		button.pivot_offset = button.size * 0.5
		button.modulate.a = 0.0
		var tween := button.create_tween().set_parallel(true)
		tween.tween_property(button, "scale", Vector2.ONE, 0.25).set_delay(i * 0.08).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tween.tween_property(button, "modulate:a", 1.0, 0.2).set_delay(i * 0.08)


func _cell_tip(card_id: String) -> void:
	var copies := int((game.state.tarot as Dictionary).get(card_id, 0))
	var lines: Array[String] = []
	lines.append("[b]%s[/b]" % I18N.upper(I18N.t("tarot.%s.name" % card_id)))
	if copies > 0:
		var color := Data.rarity_color(rank_name(copies)).to_html(false)
		lines.append("[color=#%s]%s · %s[/color]" % [color, I18N.t("rank." + rank_name(copies)), I18N.f("tarot.copies", {"n": copies})])
		lines.append(card_effect_text(card_id, copies))
	if copies < 4:
		lines.append("[color=#b9a6cf]%s[/color]" % I18N.f("tarot.next", {"v": I18N.t("rank." + rank_name(copies + 1))}))
		lines.append("[color=#b9a6cf]%s[/color]" % card_effect_text(card_id, copies + 1))
	tooltip("\n".join(lines))


func _draw_cards() -> void:
	game.call("tarot_draw")
	refresh()


func _pick(card_id: String) -> void:
	var copies: int = game.call("tarot_pick", card_id)
	if copies > 0:
		game.call("toast", "%s · %s" % [I18N.upper(I18N.t("tarot.%s.name" % card_id)), I18N.upper(I18N.t("rank." + rank_name(copies)))], Data.rarity_color(rank_name(copies)))
	refresh()
