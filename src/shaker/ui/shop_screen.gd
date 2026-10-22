extends "res://shaker/ui/screen_base.gd"
## Shop: gauntlets (mouse cursors with real bonuses), table designs (looks only) and the black market.

const TABS := ["gauntlets", "tables", "black"]
const CARD := Vector2(438, 178)

var tab := "gauntlets"
var tab_buttons: Dictionary = {}
var content: Control
var grid: GridContainer
var cards: Array = []              # [{kind, id, button, price, status}]
var signature := ""
var intro_label: Label


func _build() -> void:
	var panel := frame(I18N.t("shop.title"))
	tab = str(game.state.get("shop_tab", "gauntlets"))
	if tab not in TABS:
		tab = "gauntlets"
	for i in TABS.size():
		var key := str(TABS[i])
		var button := Kit.button(panel, I18N.t("shop." + key), Rect2(330 + i * 400, 96, 380, 64), _set_tab.bind(key), 18,
				Color("3a1222") if key == "black" else Kit.BUTTON, Kit.GOLD)
		tab_buttons[key] = button
	intro_label = Kit.paragraph(panel, "", Rect2(60, 166, 1720, 40), 13, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)
	var scroll := Kit.scroll(panel, Rect2(24, 212, 1792, 792))
	content = scroll
	_fill()


func _set_tab(key: String) -> void:
	tab = key
	game.state["shop_tab"] = key
	_fill()


func _fill() -> void:
	for key in tab_buttons:
		var button: Button = tab_buttons[key]
		var active: bool = key == tab
		var base := Color("3a1222") if key == "black" else Kit.BUTTON
		button.add_theme_stylebox_override("normal", Kit.style(base.lightened(0.15) if active else base, Kit.GOLD_LIGHT if active else Kit.GOLD.darkened(0.3), 5 if active else 3, 12))
	if grid:
		grid.free()
	cards.clear()
	signature = ""
	grid = GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	content.add_child(grid)
	match tab:
		"gauntlets":
			Kit.set_text(intro_label, I18N.f("shop.owned_bonus", {"v": int(Data.b("gauntlet_owned_pct", 2))}))
			for g in Data.gauntlets:
				_add_gauntlet(g)
		"tables":
			Kit.set_text(intro_label, I18N.t("shop.cosmetic"))
			for t in Data.tables:
				_add_table(t)
		"black":
			if float(game.stats.black_market) <= 0.0:
				Kit.set_text(intro_label, I18N.t("shop.black_locked"))
			else:
				Kit.set_text(intro_label, I18N.t("shop.black_intro"))
				for card in Data.black:
					_add_black(card)
	refresh()


func _card_shell(art: Texture2D, art_size: Vector2, title: String, title_color: Color, body: String, dark: bool = false) -> Dictionary:
	var shell := Panel.new()
	shell.custom_minimum_size = CARD
	shell.add_theme_stylebox_override("panel", Kit.style(Color("160812") if dark else Color("1d1030"), Color("7a2a2a") if dark else Color("5a3a7e"), 3, 14))
	grid.add_child(shell)
	var art_rect := Kit.texture(shell, art, Rect2(Vector2(12, (CARD.y - art_size.y) * 0.5), art_size), true)
	var text_x := 24.0 + art_size.x
	var name_label := Kit.label(shell, title, Rect2(text_x, 8, CARD.x - text_x - 10, 32), 15, HORIZONTAL_ALIGNMENT_LEFT, title_color)
	var body_label := Kit.paragraph(shell, body, Rect2(text_x, 40, CARD.x - text_x - 10, 78), 11, HORIZONTAL_ALIGNMENT_LEFT, Kit.TEXT)
	var status := Kit.label(shell, "", Rect2(text_x, 122, 110, 44), 12, HORIZONTAL_ALIGNMENT_LEFT, Kit.MUTED)
	var button := Kit.button(shell, "", Rect2(CARD.x - 196, 120, 184, 48), Callable(), 13)
	return {"shell": shell, "art": art_rect, "name": name_label, "body": body_label, "status": status, "button": button}


func _add_gauntlet(g: Dictionary) -> void:
	var index := int(g.index)
	var widgets := _card_shell(Tex.get_tex(ART + "gauntlets/gauntlet_%d.png" % index), Vector2(128, 128),
			I18N.upper(I18N.t("gauntlet.%d.name" % index)), Kit.GOLD_LIGHT, effects_text(g.effects))
	(widgets.button as Button).pressed.connect(_gauntlet_pressed.bind(index))
	widgets["kind"] = "gauntlet"
	widgets["id"] = index
	cards.append(widgets)


func _add_table(t: Dictionary) -> void:
	var table_id := int(t.id)
	var widgets := _card_shell(Tex.get_tex(ART + "scene/table_%d_thumb.png" % table_id), Vector2(192, 128),
			I18N.upper(I18N.t("table.%d.name" % table_id)), Kit.GOLD_LIGHT, I18N.t("shop.cosmetic"))
	(widgets.button as Button).pressed.connect(_table_pressed.bind(table_id))
	widgets["kind"] = "table"
	widgets["id"] = table_id
	cards.append(widgets)


func _add_black(card: Dictionary) -> void:
	var card_id := str(card.id)
	var body := I18N.t("shop.per_copy") + "\n" + effects_text(_black_effects(card))
	var widgets := _card_shell(Tex.get_tex(ART + "black/%s.png" % card_id), Vector2(102, 158),
			I18N.upper(I18N.t("black.%s.name" % card_id)), Color("ff8a7a"), body, true)
	(widgets.button as Button).pressed.connect(_black_pressed.bind(card_id))
	widgets["kind"] = "black"
	widgets["id"] = card_id
	cards.append(widgets)


## "copies+1" (loaded dice) is shown as the value of the next copy.
func _black_effects(card: Dictionary) -> Array:
	var copies := int((game.state.black as Dictionary).get(str(card.id), 0))
	var result: Array = []
	for effect in card.effects:
		var value = effect[1]
		if value is String:
			value = float(mini(copies + 1, int(card.cap)) + 1)
		result.append([effect[0], value])
	return result


func refresh() -> void:
	super.refresh()
	var state: Dictionary = game.state
	var sig := "%s|%s|%s|%s|%s|%d" % [state.gauntlets, state.gauntlet, state.tables, state.table, state.black, int(float(state.money) > 0.0)]
	for widgets in cards:
		var button: Button = widgets.button
		var status: Label = widgets.status
		match str(widgets.kind):
			"gauntlet":
				var index := int(widgets.id)
				var owned: bool = index in state.gauntlets
				if int(state.gauntlet) == index:
					Kit.set_button_text(button, I18N.t("shop.equipped"))
					button.disabled = true
				elif owned:
					Kit.set_button_text(button, I18N.t("shop.equip"))
					button.disabled = false
				else:
					var price: float = Rules.gauntlet_price(game.stats, index)
					Kit.set_button_text(button, I18N.money(price))
					button.disabled = float(state.money) < price
				Kit.set_text(status, "")
			"table":
				var table_id := int(widgets.id)
				var owned_table: bool = table_id in state.tables
				if int(state.table) == table_id:
					Kit.set_button_text(button, I18N.t("shop.equipped"))
					button.disabled = true
				elif owned_table:
					Kit.set_button_text(button, I18N.t("shop.equip"))
					button.disabled = false
				else:
					var table_price: float = Rules.table_price(game.stats, table_id)
					Kit.set_button_text(button, I18N.money(table_price))
					button.disabled = float(state.money) < table_price
			"black":
				var card_id := str(widgets.id)
				var card: Dictionary = Data.black_by_id[card_id]
				var copies := int((state.black as Dictionary).get(card_id, 0))
				Kit.set_text(status, I18N.f("shop.copies", {"n": copies, "max": int(card.cap)}))
				if copies >= int(card.cap):
					Kit.set_button_text(button, I18N.t("shop.maxed"))
					button.disabled = true
				else:
					var black_price: float = Rules.black_price(state, game.stats, card_id)
					Kit.set_button_text(button, I18N.money(black_price))
					button.disabled = float(state.money) < black_price
	if sig != signature:
		signature = sig
		for widgets in cards:
			if str(widgets.kind) == "black":
				var card: Dictionary = Data.black_by_id[str(widgets.id)]
				Kit.set_text(widgets.body, I18N.t("shop.per_copy") + "\n" + effects_text(_black_effects(card)))


func _gauntlet_pressed(index: int) -> void:
	if index in game.state.gauntlets:
		game.call("equip_gauntlet", index)
	else:
		game.call("buy_gauntlet", index)
	refresh()


func _table_pressed(table_id: int) -> void:
	if table_id in game.state.tables:
		game.call("equip_table", table_id)
	else:
		game.call("buy_table", table_id)
	refresh()


func _black_pressed(card_id: String) -> void:
	game.call("buy_black", card_id)
	refresh()
