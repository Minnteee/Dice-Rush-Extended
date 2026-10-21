# Dice Rush Extended - main.gd patch: shop cards (hold to buy), world references, tooltips.

var bdr_felt: TextureRect
var _hold_kind: = ""
var _hold_callback: Callable
var _hold_button: Button
var _hold_elapsed: = 0.0
var _hold_next: = 0.0
var _hold_ticks: = 0
var _hold_bought: = 0


func _build_world() -> void :
	world_viewport_backdrop = _add_texture(ART + "фон.png", Rect2(0, 0, 1920, 1080), -30)
	world_viewport_backdrop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_add_texture(ART + "фон.png", Rect2(-1942, -37, 1937, 1121), -21)
	_add_texture(ART + "фон.png", Rect2(-5, -37, 1937, 1121), -20)
	_add_texture(ART + "фон.png", Rect2(1932, -37, 1937, 1121), -21)
	var fog_a: = _add_texture(ART + "фон дымка.png", Rect2(-14, -38, 1872, 1100), -15)
	var fog_b: = _add_texture(ART + "фон дымка.png", Rect2(1634, -34, 1748, 1136), -15)
	fog_parts.assign([fog_a, fog_b])
	bdr_felt = _add_texture(ART + "сукно.png", Rect2(46, 141, 1006, 873), 0)


func _make_shop_card(parent: Control, kind: String, title: String, rect: Rect2, icon_path: String, tint: Color, callback: Callable) -> void :
	_bdr_buy_callbacks[kind] = callback
	var card_root: = Control.new()
	card_root.position = rect.position
	card_root.size = rect.size
	card_root.mouse_filter = Control.MOUSE_FILTER_PASS
	parent.add_child(card_root)
	if parent == shop_list:
		shop_card_containers[kind] = card_root
	var card_visual: = Control.new()
	card_visual.size = rect.size
	card_visual.pivot_offset = card_visual.size * 0.5
	card_visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card_root.add_child(card_visual)
	shop_card_visuals[kind] = card_visual
	_add_texture(ART + "подложка под товар.png", Rect2(Vector2.ZERO, rect.size), 22, card_visual)
	var picture_background: = ColorRect.new()
	picture_background.position = Vector2(15, 18)
	picture_background.size = Vector2(194, 176)
	picture_background.color = Color("09253b")
	picture_background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	picture_background.z_index = 21
	card_visual.add_child(picture_background)
	var icon_rect: = Rect2(Vector2(47, 62), Vector2(129, 98))
	if kind == "cat":
		icon_rect = Rect2(Vector2(47, 82), Vector2(129, 90))
	if kind == "npc":
		icon_rect = Rect2(Vector2(47, 54), Vector2(131, 120))
	if kind == "npc":
		npc_shop_preview = NPCActorScript.new() as NPCActor
		card_visual.add_child(npc_shop_preview)
		npc_shop_preview.position = Vector2(112, 122)
		npc_shop_preview.scale = Vector2(1.65, 1.65)
		npc_shop_preview.configure(0, GameSession.npc_skin)
		npc_shop_preview.z_index = 24
		npc_shop_preview.set_process(false)
	else:
		var icon: = _add_texture(icon_path, icon_rect, 24, card_visual)
		icon.modulate = tint
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	var title_size: = 25
	var title_label: = _make_label(title, Rect2(Vector2(12, 20), Vector2(199, 48)), title_size, HORIZONTAL_ALIGNMENT_CENTER, 25, card_visual)
	_fit_shop_title(title_label)
	owned_labels[kind] = _make_label("0/10", Rect2(Vector2(15, 207), Vector2(193, 40)), 17, HORIZONTAL_ALIGNMENT_CENTER, 27, card_visual)
	price_labels[kind] = _make_price_label(Rect2(Vector2(15, 250), Vector2(193, 57)), 27, card_visual)
	var buy_button: = _make_invisible_button(
		Rect2(Vector2(15, 246), Vector2(193, 78)),
		_on_shop_buy_pressed.bind(kind, callback),
		35,
		"",
		card_root
	)
	buy_button.name = "Buy_%s" % kind
	buy_button.focus_mode = Control.FOCUS_ALL
	buy_button.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
	buy_button.button_down.connect(_on_shop_buy_button_down.bind(kind, callback, buy_button))
	buy_button.button_up.connect(_on_shop_buy_button_up)
	shop_buttons[kind] = buy_button
	buy_button.mouse_entered.connect(_show_product_tooltip.bind(kind))
	buy_button.mouse_exited.connect(_hide_hover_tooltip)
	buy_button.focus_entered.connect(_on_shop_button_focused.bind(kind))
	buy_button.focus_exited.connect(_hide_hover_tooltip)
	_wire_ui_feedback(card_root, card_visual, 1.018, 0.965, false)
	_wire_ui_feedback(buy_button, card_visual, 1.018, 0.965)
	if kind == "npc":
		_make_npc_skin_edit_button(card_root, Rect2(Vector2.ZERO, rect.size), card_visual)


func _on_shop_buy_pressed(kind: String, single_purchase: Callable) -> void :
	if bdr.is_coop_client():
		bdr.coop_request("buy", [kind, 10 if Input.is_key_pressed(KEY_SHIFT) else 1])
		return
	_buy_shop_product(kind, single_purchase, Input.is_key_pressed(KEY_SHIFT))


# ---------------------------------------------------------------- hold to buy (accelerating)
func _on_shop_buy_button_down(kind: String, callback: Callable, button: Button) -> void:
	_hold_kind = kind
	_hold_callback = callback
	_hold_button = button
	_hold_elapsed = 0.0
	_hold_next = 0.42
	_hold_ticks = 0
	_hold_bought = 0


func _on_shop_buy_button_up() -> void:
	_finish_hold_buy()


func _finish_hold_buy() -> void:
	if _hold_kind.is_empty():
		return
	_hold_kind = ""
	_hold_button = null
	if _hold_bought > 0:
		bdr.report_hold_purchase(_hold_bought)
		_report_achievement_snapshot()
		_update_all_labels()
	_hold_bought = 0


func _update_hold_buy(delta: float) -> void:
	if _hold_kind.is_empty():
		return
	if not is_instance_valid(_hold_button) or not _hold_button.is_visible_in_tree() or not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_finish_hold_buy()
		return
	_hold_elapsed += delta
	if _hold_elapsed < _hold_next:
		return
	_hold_ticks += 1
	var interval: = maxf(0.025, 0.2 * pow(0.84, float(_hold_ticks)))
	_hold_next = _hold_elapsed + interval
	var per_tick: = 1
	if _hold_elapsed >= 6.0:
		per_tick = 50
	elif _hold_elapsed >= 5.0:
		per_tick = 25
	elif _hold_elapsed >= 4.0:
		per_tick = 10
	elif _hold_elapsed >= 3.0:
		per_tick = 5
	elif _hold_elapsed >= 2.0:
		per_tick = 2
	if bdr.is_coop_client():
		bdr.coop_request("buy", [_hold_kind, per_tick])
		return
	_suppress_label_updates = true
	var bought: = 0
	for _index in range(per_tick):
		var got: = _buy_shop_product(_hold_kind, _hold_callback, false)
		if got <= 0:
			break
		bought += got
	_suppress_label_updates = false
	_hold_bought += bought
	if bought > 0:
		_update_all_labels()
		var card: = shop_card_visuals.get(_hold_kind) as Control
		if card and _can_show_reward_popup(true) and per_tick > 1:
			_show_reward(card.get_global_rect().get_center() - get_viewport().get_canvas_transform().origin, "+%d" % bought, true)
	else:
		_finish_hold_buy()


func _product_tooltip_text(kind: String) -> String:
	if bdr.is_custom_die(kind):
		return bdr.tooltip_text(kind)
	if bdr.is_staff(kind):
		return bdr.staff_tooltip_text(kind)
	if kind == "cat":
		var purchase_text: = _cat_text("purchase_used") if cat_purchased else _cat_text("price_info") % _bdr_money_text(_format_number(CAT_PRICE))
		var unlock_text: = "" if DiceRushEdition.is_demo() else _cat_text("rare_unlock")
		var cat_quantity: = str(cat_count)
		return "[color=#ffd166]%s[/color]\n\n%s\n\n%s\n%s\n%s" % [_cat_text("name"), _cat_text("description"), unlock_text, purchase_text, _cat_text("owned_count") % cat_quantity]
	var count: = _product_count(kind)
	var maximum: = _worker_limit() if kind == "npc" else (_accountant_limit() if kind == "accountant" else -1)
	var price: float = _next_price(kind, _price_progress_count(kind, count))
	var faces_key: = "tooltip_%s_faces" % kind
	var effect_key: = "tooltip_%s_effect" % kind
	if kind == "50_50":
		faces_key = "tooltip_50_faces"
		effect_key = "tooltip_50_effect"
	elif kind == "npc":
		faces_key = "tooltip_worker_faces"
		effect_key = "tooltip_worker_effect"
	var faces_text: = GameSession.text(faces_key)
	var effect: = GameSession.text(effect_key)
	if kind in SPECIAL_DICE_KINDS:
		faces_text = _lucky_text("%s_faces" % kind)
		effect = _lucky_text("%s_effect" % kind)
		if kind == "crypto":
			faces_text = faces_text % _format_number(crypto_market_value)
			effect = effect % _format_number(_crypto_minimum_value())
		elif kind == "diamond":
			faces_text = faces_text % _format_number(_diamond_payout_value())
		elif kind == "pi":
			faces_text = faces_text % _format_number(_pi_payout_value())
	if kind == "npc_die":
		var pay_per_worker: = _npc_die_pay_per_worker()
		effect = effect % [_format_number(pay_per_worker), _format_number(npc_count * pay_per_worker)]
	elif kind == "accountant":
		faces_text = "—"
		effect = _lucky_text("accountant_efficiency_effect") % _accountant_percent_per_accountant()
	var limited_product: = maximum > 0 and maximum < MAX_INT64
	var price_text: = GameSession.text("max") if limited_product and count >= maximum else (GameSession.text("tbd") if price < 0.0 else _bdr_money_text(price))
	var quantity_text: = "%d / %d" % [count, maximum] if limited_product else str(count)
	return "[color=#ffd166][font_size=18]%s[/font_size][/color]\n\n[color=#3ee6d0]%s[/color]\n%s\n\n[color=#3ee6d0]%s[/color]\n%s\n\n[color=#8aa0bd]%s:[/color] %s\n[color=#8aa0bd]%s:[/color] [color=#3ee6d0]%s[/color]" % [
		_product_name(kind),
		GameSession.text("faces"), faces_text,
		GameSession.text("effect"), effect,
		GameSession.text("quantity"), quantity_text,
		GameSession.text("next_price"), price_text,
	]


func _visual_overlay_blocks_wave() -> bool:
	if quadrillion_story_active:
		return true
	if upgrade_overlay and upgrade_overlay.visible:
		return true
	if dog_shrine_controller and dog_shrine_controller.visible:
		return true
	if bdr and bdr.overlay_open():
		return true
	if not menu_controller:
		return false
	for overlay in [menu_controller.main_menu, menu_controller.pause_menu, menu_controller.settings_menu, menu_controller.credits_menu, menu_controller.achievement_menu]:
		if overlay and overlay.visible:
			return true
	return false
