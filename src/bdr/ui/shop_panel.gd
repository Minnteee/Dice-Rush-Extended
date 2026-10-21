extends Control
## Dice Rush Extended - the new SHOP screen (sell dice, unlock dice, cosmetic designs).

const UI := preload("res://bdr/ui/ui_kit.gd")
const I18N := preload("res://bdr/core/i18n.gd")
const PANEL_RECT := Rect2(150, 60, 1620, 960)

var game: Node
var main: Node
var tab := "sell"
var frame: Panel
var title_label: Label
var money_label: Label
var tab_buttons: Dictionary = {}
var pages: Dictionary = {}
var _refresh_timer := 0.0

# sell
var sell_list: GridContainer
var sell_entries: Dictionary = {}
var sell_selected := ""
var sell_icon: TextureRect
var sell_name: Label
var sell_owned: Label
var sell_each: Label
var sell_amount: LineEdit
var sell_total: Label
var sell_button: Button
var sell_status: Label
var sell_signature := ""

# unlock
var unlock_box: VBoxContainer
var unlock_cards: Dictionary = {}

# designs
var design_cards: Dictionary = {}


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	name = "BDRShopPanel"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	var dim := ColorRect.new()
	dim.color = Color(0.01, 0.01, 0.03, 0.82)
	dim.position = Vector2(-400, -300)
	dim.size = Vector2(2720, 1680)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)
	frame = UI.panel(self, PANEL_RECT)
	title_label = UI.label(frame, I18N.t("ui.shop"), Rect2(36, 16, 520, 72), 40, HORIZONTAL_ALIGNMENT_LEFT, Color("ffd166"), true)
	money_label = UI.label(frame, "", Rect2(560, 22, 820, 60), 26, HORIZONTAL_ALIGNMENT_RIGHT, Color.WHITE)
	UI.button(frame, "X", Rect2(1520, 18, 74, 64), close, 22)
	var tabs := [["sell", "ui.tab_sell"], ["unlock", "ui.tab_unlock"], ["designs", "ui.tab_designs"]]
	for index in range(tabs.size()):
		var id: String = tabs[index][0]
		tab_buttons[id] = UI.button(frame, I18N.t(tabs[index][1]), Rect2(36 + index * 330, 96, 316, 62), show_tab.bind(id), 16)
	for id in ["sell", "unlock", "designs"]:
		var page := Control.new()
		page.position = Vector2(30, 172)
		page.size = Vector2(1560, 760)
		page.mouse_filter = Control.MOUSE_FILTER_PASS
		frame.add_child(page)
		pages[id] = page
	_build_sell_page(pages.sell)
	_build_unlock_page(pages.unlock)
	_build_designs_page(pages.designs)
	show_tab("sell")


func open() -> void:
	visible = true
	sell_signature = ""
	refresh(true)
	show_tab(tab)


func close() -> void:
	if not visible:
		return
	visible = false
	game.on_shop_closed()


func is_open() -> bool:
	return visible


func show_tab(id: String) -> void:
	tab = id
	for key in pages:
		(pages[key] as Control).visible = key == id
	for key in tab_buttons:
		var button: Button = tab_buttons[key]
		button.add_theme_stylebox_override("normal", UI.style(Color("ffd166") if key == id else Color("10294a"), Color("fff0aa") if key == id else Color("a86f12")))
		button.add_theme_color_override("font_color", Color("07101f") if key == id else Color.WHITE)
	refresh(true)


func _process(delta: float) -> void:
	if not visible:
		return
	_refresh_timer -= delta
	if _refresh_timer <= 0.0:
		_refresh_timer = 0.25
		refresh(false)


func _unhandled_input(event: InputEvent) -> void:
	if visible and event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()


func refresh(full: bool) -> void:
	if not visible:
		return
	money_label.text = main._bdr_money_text(main.money)
	UI.fit(money_label)
	match tab:
		"sell":
			_refresh_sell(full)
		"unlock":
			_refresh_unlock()
		"designs":
			_refresh_designs()


# ================================================================ SELL
func _build_sell_page(page: Control) -> void:
	var left := UI.panel(page, Rect2(0, 0, 900, 760), Color("07162fef"), Color("785217"), 3, 14)
	UI.label(left, I18N.t("ui.sell_choose"), Rect2(20, 10, 860, 50), 16, HORIZONTAL_ALIGNMENT_LEFT, Color("75ead8"))
	var scroll := UI.scroll(left, Rect2(14, 64, 872, 682))
	sell_list = GridContainer.new()
	sell_list.columns = 2
	sell_list.add_theme_constant_override("h_separation", 10)
	sell_list.add_theme_constant_override("v_separation", 10)
	scroll.add_child(sell_list)
	var right := UI.panel(page, Rect2(920, 0, 640, 760), Color("07162fef"), Color("785217"), 3, 14)
	sell_icon = UI.texture(right, "", Rect2(220, 24, 200, 200))
	sell_name = UI.label(right, I18N.t("ui.sell_none"), Rect2(20, 236, 600, 56), 22, HORIZONTAL_ALIGNMENT_CENTER, Color("ffd166"))
	sell_owned = UI.label(right, "", Rect2(20, 296, 600, 40), 16, HORIZONTAL_ALIGNMENT_CENTER)
	sell_each = UI.label(right, "", Rect2(20, 338, 600, 40), 15, HORIZONTAL_ALIGNMENT_CENTER, Color("bfe8ff"))
	UI.label(right, I18N.t("ui.amount"), Rect2(20, 392, 600, 36), 14, HORIZONTAL_ALIGNMENT_CENTER, Color("8aa0bd"))
	UI.button(right, "-10", Rect2(24, 436, 92, 64), _change_amount.bind(-10), 14)
	UI.button(right, "-1", Rect2(122, 436, 80, 64), _change_amount.bind(-1), 14)
	sell_amount = LineEdit.new()
	sell_amount.position = Vector2(210, 436)
	sell_amount.size = Vector2(220, 64)
	sell_amount.text = "1"
	sell_amount.alignment = HORIZONTAL_ALIGNMENT_CENTER
	sell_amount.max_length = 9
	sell_amount.add_theme_font_override("font", UI.pixel_font)
	sell_amount.add_theme_font_size_override("font_size", 22)
	sell_amount.add_theme_stylebox_override("normal", UI.style(Color("050d1c"), Color("ffd166")))
	sell_amount.add_theme_stylebox_override("focus", UI.style(Color("050d1c"), Color("fff0aa")))
	sell_amount.text_changed.connect(_on_amount_text_changed)
	right.add_child(sell_amount)
	UI.button(right, "+1", Rect2(438, 436, 80, 64), _change_amount.bind(1), 14)
	UI.button(right, "+10", Rect2(524, 436, 92, 64), _change_amount.bind(10), 14)
	UI.button(right, I18N.t("ui.max"), Rect2(210, 508, 220, 52), _set_amount_max, 14)
	sell_total = UI.label(right, "", Rect2(20, 570, 600, 46), 17, HORIZONTAL_ALIGNMENT_CENTER, Color("8dff86"))
	sell_button = UI.button(right, I18N.t("ui.sell"), Rect2(60, 622, 520, 80), _on_sell_pressed, 20, Color("6e1f1f"), Color("ffb070"))
	sell_status = UI.label(right, "", Rect2(20, 706, 600, 44), 13, HORIZONTAL_ALIGNMENT_CENTER, Color("ffd166"))


func _sellable_kinds() -> Array:
	var result: Array = []
	for kind in game.VANILLA_DICE_KINDS:
		if main._owned_die_count(kind) > (1 if kind == "50_50" else 0):
			result.append(kind)
	for kind in game.shop_custom_kinds():
		if game.count(kind) > 0:
			result.append(kind)
	return result


func _refresh_sell(full: bool) -> void:
	var kinds := _sellable_kinds()
	var signature := ",".join(kinds)
	if full or signature != sell_signature:
		sell_signature = signature
		for child in sell_list.get_children():
			child.queue_free()
		sell_entries.clear()
		for kind in kinds:
			var entry := Button.new()
			entry.custom_minimum_size = Vector2(426, 96)
			entry.focus_mode = Control.FOCUS_ALL
			entry.add_theme_stylebox_override("normal", UI.style(Color("0d2142"), Color("3a4f7a"), 2, 10))
			entry.add_theme_stylebox_override("hover", UI.style(Color("153262"), Color("ffd166"), 2, 10))
			entry.add_theme_stylebox_override("pressed", UI.style(Color("0a1a33"), Color("ffe59a"), 2, 10))
			entry.add_theme_stylebox_override("focus", UI.style(Color("153262"), Color("ffd166"), 2, 10))
			entry.pressed.connect(_select_sell.bind(kind))
			sell_list.add_child(entry)
			UI.texture(entry, main._lucky_kind_icon_path(kind), Rect2(10, 8, 80, 80))
			var name_label := UI.label(entry, main._product_name(kind), Rect2(98, 6, 320, 40), 13, HORIZONTAL_ALIGNMENT_LEFT, Color("ffd166"))
			var count_label := UI.label(entry, "", Rect2(98, 48, 320, 40), 12, HORIZONTAL_ALIGNMENT_LEFT)
			sell_entries[kind] = {"button": entry, "name": name_label, "count": count_label}
		if not sell_selected.is_empty() and sell_selected not in kinds:
			sell_selected = ""
		if sell_selected.is_empty() and not kinds.is_empty():
			sell_selected = kinds[0]
	for kind in sell_entries:
		var data: Dictionary = sell_entries[kind]
		(data.count as Label).text = I18N.f("ui.owned_value", {"n": main._owned_die_count(kind), "v": main._bdr_money_text(game.sell_value(kind, 1))})
		UI.fit(data.count)
		(data.button as Button).add_theme_stylebox_override("normal", UI.style(Color("1d3a6e") if kind == sell_selected else Color("0d2142"), Color("ffd166") if kind == sell_selected else Color("3a4f7a"), 2, 10))
	_refresh_sell_detail()


func _select_sell(kind: String) -> void:
	sell_selected = kind
	sell_amount.text = "1"
	sell_status.text = ""
	_refresh_sell(false)


func _amount() -> int:
	var text := sell_amount.text.strip_edges()
	if not text.is_valid_int():
		return 0
	return clampi(int(text), 0, game.max_sellable(sell_selected) if not sell_selected.is_empty() else 0)


func _on_amount_text_changed(new_text: String) -> void:
	var digits := ""
	for character in new_text:
		if character >= "0" and character <= "9":
			digits += character
	if digits != new_text:
		var caret := sell_amount.caret_column
		sell_amount.text = digits
		sell_amount.caret_column = mini(caret, digits.length())
	_refresh_sell_detail()


func _change_amount(delta: int) -> void:
	if sell_selected.is_empty():
		return
	sell_amount.text = str(clampi(_amount() + delta, 0, game.max_sellable(sell_selected)))
	_refresh_sell_detail()


func _set_amount_max() -> void:
	if sell_selected.is_empty():
		return
	sell_amount.text = str(game.max_sellable(sell_selected))
	_refresh_sell_detail()


func _refresh_sell_detail() -> void:
	if sell_selected.is_empty():
		sell_icon.texture = null
		sell_name.text = I18N.t("ui.sell_none")
		sell_owned.text = ""
		sell_each.text = ""
		sell_total.text = ""
		sell_button.disabled = true
		return
	sell_icon.texture = CleanTextureLoader.load_texture(main._lucky_kind_icon_path(sell_selected))
	sell_name.text = main._product_name(sell_selected)
	sell_owned.text = I18N.f("ui.owned", {"n": main._owned_die_count(sell_selected)})
	sell_each.text = I18N.f("ui.sell_each", {"v": main._bdr_money_text(game.sell_value(sell_selected, 1))})
	var amount := _amount()
	sell_total.text = I18N.f("ui.sell_total", {"v": main._bdr_money_text(game.sell_value(sell_selected, amount))})
	sell_button.text = I18N.f("ui.sell_button", {"n": amount})
	sell_button.disabled = amount <= 0
	for label in [sell_name, sell_owned, sell_each, sell_total]:
		UI.fit(label)
	UI.fit(sell_button)


func _on_sell_pressed() -> void:
	if sell_selected.is_empty():
		return
	var amount := _amount()
	if amount <= 0:
		return
	var result: Dictionary = game.shop_sell(sell_selected, amount)
	if bool(result.get("ok", false)):
		sell_status.text = I18N.f("ui.sold", {"n": int(result.sold), "name": main._product_name(sell_selected), "v": main._bdr_money_text(float(result.refund))})
		sell_status.add_theme_color_override("font_color", Color("8dff86"))
		sell_amount.text = "1"
	else:
		sell_status.text = I18N.t(str(result.get("error", "ui.sell_failed")))
		sell_status.add_theme_color_override("font_color", Color("ff7a7a"))
	UI.fit(sell_status)
	sell_signature = ""
	refresh(false)


# ================================================================ UNLOCK
func _build_unlock_page(page: Control) -> void:
	var holder := UI.panel(page, Rect2(0, 0, 1560, 760), Color("07162fef"), Color("785217"), 3, 14)
	var scroll := UI.scroll(holder, Rect2(14, 12, 1532, 736))
	unlock_box = VBoxContainer.new()
	unlock_box.custom_minimum_size = Vector2(1500, 0)
	unlock_box.add_theme_constant_override("separation", 10)
	scroll.add_child(unlock_box)
	for tier in range(1, 11):
		var header := Control.new()
		header.custom_minimum_size = Vector2(1500, 52)
		unlock_box.add_child(header)
		UI.label(header, I18N.f("ui.tier", {"n": tier}), Rect2(8, 4, 1480, 44), 20, HORIZONTAL_ALIGNMENT_LEFT, Color("ffd166"), true)
		var grid := GridContainer.new()
		grid.columns = 5
		grid.add_theme_constant_override("h_separation", 10)
		grid.add_theme_constant_override("v_separation", 10)
		unlock_box.add_child(grid)
		for entry in game.catalog.by_tier(tier):
			_build_unlock_card(grid, str(entry.id))


func _build_unlock_card(parent: Node, kind: String) -> void:
	var card := Panel.new()
	card.custom_minimum_size = Vector2(292, 214)
	card.add_theme_stylebox_override("panel", UI.style(Color("0d2142"), Color("3a4f7a"), 2, 12))
	parent.add_child(card)
	var icon := UI.texture(card, game.icon_path(kind), Rect2(96, 8, 100, 92))
	var name_label := UI.label(card, "", Rect2(8, 102, 276, 34), 13, HORIZONTAL_ALIGNMENT_CENTER, Color("ffd166"))
	var info := UI.label(card, "", Rect2(8, 136, 276, 30), 10, HORIZONTAL_ALIGNMENT_CENTER, Color("bfe8ff"))
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var button := UI.button(card, "", Rect2(16, 168, 260, 38), _on_unlock_pressed.bind(kind), 11)
	card.mouse_entered.connect(game.show_dice_tooltip.bind(kind))
	card.mouse_exited.connect(game.hide_tooltip)
	unlock_cards[kind] = {"card": card, "icon": icon, "name": name_label, "info": info, "button": button}


func _refresh_unlock() -> void:
	var per_tier: Array[int] = game.shop.tier_counts()
	for kind in unlock_cards:
		var data: Dictionary = unlock_cards[kind]
		var def: Dictionary = game.catalog.get_def(kind)
		var unlocked: bool = game.is_unlocked(kind)
		var revealed: bool = game.is_revealed(kind)
		var icon: TextureRect = data.icon
		icon.modulate = Color.WHITE if (unlocked or revealed) else Color(0.05, 0.05, 0.08, 0.9)
		(data.name as Label).text = game.display_name(kind) if (unlocked or revealed) else "???"
		var info: Label = data.info
		var button: Button = data.button
		var card: Panel = data.card
		if unlocked:
			info.text = I18N.f("ui.owned", {"n": game.count(kind)})
			button.text = I18N.t("ui.unlocked")
			button.disabled = true
			card.add_theme_stylebox_override("panel", UI.style(Color("12341f"), Color("4fd27a"), 2, 12))
		else:
			card.add_theme_stylebox_override("panel", UI.style(Color("0d2142"), Color("3a4f7a"), 2, 12))
			match str(def.unlock):
				"shop":
					if revealed and not game.shop.tier_requirement_met(kind, per_tier):
						var need: int = game.shop.tier_requirement(kind)
						var below := int(def.tier) - 1
						info.text = I18N.f("ui.need_tier", {"n": need, "t": below, "have": mini(per_tier[below], need)})
						button.text = I18N.f("ui.unlock_for", {"v": main._bdr_money_text(float(def.unlock_price))})
						button.disabled = true
					elif revealed:
						info.text = I18N.t("ui.unlock_shop")
						button.text = I18N.f("ui.unlock_for", {"v": main._bdr_money_text(float(def.unlock_price))})
						button.disabled = main.money < float(def.unlock_price)
					else:
						info.text = I18N.f("ui.reveal_at", {"v": main._bdr_money_text(game.reveal_threshold(kind))})
						button.text = "???"
						button.disabled = true
				"talent":
					info.text = I18N.t("ui.via_talent")
					button.text = I18N.t("ui.locked")
					button.disabled = true
				"lucky":
					info.text = I18N.f("ui.via_lucky_gate", {"n": game.lucky.gate_of(kind)}) if game.lucky.gate_of(kind) > 0 else I18N.t("ui.via_lucky")
					button.text = I18N.t("ui.locked")
					button.disabled = true
				"tarot":
					info.text = I18N.f("ui.via_tarot", {"card": game.tarot_unlock_card_name(kind)})
					button.text = I18N.t("ui.locked")
					button.disabled = true
		UI.fit(data.name)
		UI.fit(info)
		UI.fit(button)


func _on_unlock_pressed(kind: String) -> void:
	game.shop_unlock(kind)
	refresh(false)


# ================================================================ DESIGNS
func _build_designs_page(page: Control) -> void:
	var holder := UI.panel(page, Rect2(0, 0, 1560, 760), Color("07162fef"), Color("785217"), 3, 14)
	var scroll := UI.scroll(holder, Rect2(14, 12, 1532, 736))
	var box := VBoxContainer.new()
	box.custom_minimum_size = Vector2(1500, 0)
	box.add_theme_constant_override("separation", 12)
	scroll.add_child(box)
	for design_type in ["cursor", "board"]:
		var header := Control.new()
		header.custom_minimum_size = Vector2(1500, 74)
		box.add_child(header)
		UI.label(header, I18N.t("ui.cursor_designs" if design_type == "cursor" else "ui.board_designs"), Rect2(8, 0, 1000, 44), 20, HORIZONTAL_ALIGNMENT_LEFT, Color("ffd166"), true)
		UI.label(header, I18N.t("ui.design_note"), Rect2(8, 42, 1480, 30), 12, HORIZONTAL_ALIGNMENT_LEFT, Color("8aa0bd"))
		var grid := GridContainer.new()
		grid.columns = 6
		grid.add_theme_constant_override("h_separation", 10)
		grid.add_theme_constant_override("v_separation", 10)
		box.add_child(grid)
		for index in range(0, 11):
			_build_design_card(grid, design_type, index)


func _build_design_card(parent: Node, design_type: String, index: int) -> void:
	var card := Panel.new()
	card.custom_minimum_size = Vector2(240, 250)
	card.add_theme_stylebox_override("panel", UI.style(Color("0d2142"), Color("3a4f7a"), 2, 12))
	parent.add_child(card)
	var preview := UI.texture(card, game.design_preview_path(design_type, index), Rect2(20, 10, 200, 140), design_type == "cursor")
	var name_label := UI.label(card, game.design_name(design_type, index), Rect2(8, 152, 224, 36), 12, HORIZONTAL_ALIGNMENT_CENTER, Color("ffd166"))
	var button := UI.button(card, "", Rect2(14, 194, 212, 46), _on_design_pressed.bind(design_type, index), 11)
	design_cards["%s_%d" % [design_type, index]] = {"card": card, "preview": preview, "name": name_label, "button": button, "type": design_type, "index": index}


func _refresh_designs() -> void:
	for key in design_cards:
		var data: Dictionary = design_cards[key]
		var design_type: String = data.type
		var index: int = data.index
		var owned: bool = game.design_owned(design_type, index)
		var equipped: bool = game.design_equipped(design_type) == index
		var button: Button = data.button
		if equipped:
			button.text = I18N.t("ui.equipped")
			button.disabled = true
		elif owned:
			button.text = I18N.t("ui.equip")
			button.disabled = false
		else:
			var price: float = game.design_price(design_type, index)
			button.text = I18N.f("ui.buy_for", {"v": main._bdr_money_text(price)})
			button.disabled = main.money < price
		(data.card as Panel).add_theme_stylebox_override("panel", UI.style(Color("1d3a6e") if equipped else Color("0d2142"), Color("ffd166") if equipped else Color("3a4f7a"), 2, 12))
		UI.fit(button)


func _on_design_pressed(design_type: String, index: int) -> void:
	if game.design_owned(design_type, index):
		game.design_equip(design_type, index)
	else:
		game.design_buy(design_type, index)
	refresh(false)
