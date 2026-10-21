const BDR_PAGE_COLUMNS: = 6


const BDR_PAGE_ROWS: = 2


## Set by main: the Dice Rush Extended tarot extension (offer sizes, odds and texts).
var bdr_hooks = null


var bdr_amount: int = 10


var _bdr_page: = 0


var _bdr_amount_buttons: Array[Button] = []


var _bdr_offer_box: Panel


var _bdr_offer_title: Label


var _bdr_points_label: Label


var _bdr_odds_label: RichTextLabel


var _bdr_page_box: Control


var _bdr_prev_button: Button


var _bdr_next_button: Button


var _bdr_page_label: Label


func _bdr_label(text_value: String, rect: Rect2, font_size: int, alignment: HorizontalAlignment, parent: Node, z_value: int) -> Label:
	var label: = Label.new()
	label.clip_text = true
	label.position = rect.position
	label.size = rect.size
	label.horizontal_alignment = alignment
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.z_index = z_value
	label.add_theme_font_override("font", _pixel_font)
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", Color.WHITE)
	label.add_theme_color_override("font_outline_color", Color.BLACK)
	label.add_theme_constant_override("outline_size", 4)
	parent.add_child(label)
	label.text = text_value
	return label


func _bdr_text(method: String, args: Array = [], fallback: String = "") -> String:
	if bdr_hooks == null or not bdr_hooks.has_method(method):
		return fallback
	return str(bdr_hooks.callv(method, args))


func _bdr_amounts() -> Array:
	if bdr_hooks == null:
		return [10]
	return bdr_hooks.amounts()


func _bdr_build_offer_panel() -> void :
	_bdr_offer_box = Panel.new()
	_bdr_offer_box.name = "BDROfferSize"
	_bdr_offer_box.position = Vector2(14, 8)
	_bdr_offer_box.size = Vector2(452, 218)
	_bdr_offer_box.mouse_filter = Control.MOUSE_FILTER_PASS
	_bdr_offer_box.z_index = 2
	var box_style: = _panel_style(Color("050811df"), Color("323b4a"), 2, 16)
	box_style.shadow_color = Color("000000a8")
	box_style.shadow_size = 10
	box_style.shadow_offset = Vector2(0, 5)
	_bdr_offer_box.add_theme_stylebox_override("panel", box_style)
	_carousel_panel.add_child(_bdr_offer_box)
	_bdr_offer_title = _bdr_label("", Rect2(12, 6, 428, 30), 14, HORIZONTAL_ALIGNMENT_CENTER, _bdr_offer_box, 2)
	_bdr_offer_title.add_theme_color_override("font_color", Color("ffd06a"))
	_bdr_amount_buttons.clear()
	var amounts: = _bdr_amounts()
	var step: = 428.0 / float(maxi(1, amounts.size()))
	for index in range(amounts.size()):
		var amount: = int(amounts[index])
		var button: = Button.new()
		button.text = str(amount)
		button.position = Vector2(12.0 + float(index) * step, 40)
		button.size = Vector2(step - 8.0, 44)
		button.clip_text = true
		button.focus_mode = Control.FOCUS_ALL
		button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		button.toggle_mode = true
		button.add_theme_font_override("font", _pixel_font)
		button.add_theme_font_size_override("font_size", 16)
		button.add_theme_color_override("font_color", Color.WHITE)
		button.add_theme_color_override("font_pressed_color", Color("1a1405"))
		button.add_theme_color_override("font_hover_pressed_color", Color("1a1405"))
		button.add_theme_color_override("font_outline_color", Color.BLACK)
		button.add_theme_constant_override("outline_size", 3)
		button.add_theme_stylebox_override("normal", _panel_style(Color("0b101bdd"), Color("737b8b"), 2, 10))
		button.add_theme_stylebox_override("hover", _panel_style(Color("192337f2"), Color("e6bc54"), 3, 10))
		button.add_theme_stylebox_override("pressed", _panel_style(Color("ffd06a"), Color("fff0a0"), 3, 10))
		button.add_theme_stylebox_override("hover_pressed", _panel_style(Color("ffe08a"), Color("fff6c8"), 3, 10))
		button.add_theme_stylebox_override("focus", _panel_style(Color("00000000"), Color("fff0a0"), 3, 10))
		button.pressed.connect(_bdr_set_amount.bind(amount))
		_bdr_offer_box.add_child(button)
		_bdr_amount_buttons.append(button)
	_bdr_points_label = _bdr_label("", Rect2(12, 90, 428, 28), 13, HORIZONTAL_ALIGNMENT_CENTER, _bdr_offer_box, 2)
	_bdr_points_label.add_theme_color_override("font_color", Color("e8edf5"))
	_bdr_odds_label = RichTextLabel.new()
	_bdr_odds_label.bbcode_enabled = true
	_bdr_odds_label.fit_content = false
	_bdr_odds_label.scroll_active = false
	_bdr_odds_label.position = Vector2(10, 122)
	_bdr_odds_label.size = Vector2(432, 90)
	_bdr_odds_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bdr_odds_label.add_theme_font_override("normal_font", _readable_font)
	_bdr_odds_label.add_theme_font_size_override("normal_font_size", 18)
	_bdr_odds_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_bdr_odds_label.add_theme_constant_override("outline_size", 3)
	_bdr_odds_label.z_index = 2
	_bdr_offer_box.add_child(_bdr_odds_label)

	_bdr_page_box = Control.new()
	_bdr_page_box.name = "BDRPages"
	_bdr_page_box.position = Vector2(1326, 8)
	_bdr_page_box.size = Vector2(240, 218)
	_bdr_page_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bdr_page_box.z_index = 6
	_carousel_panel.add_child(_bdr_page_box)
	_bdr_prev_button = _button("<", Rect2(0, 74, 64, 64), _bdr_page_box, 2)
	_bdr_prev_button.pressed.connect(_bdr_change_page.bind(-1))
	_bdr_page_label = _bdr_label("", Rect2(68, 74, 104, 64), 18, HORIZONTAL_ALIGNMENT_CENTER, _bdr_page_box, 2)
	_bdr_next_button = _button(">", Rect2(176, 74, 64, 64), _bdr_page_box, 2)
	_bdr_next_button.pressed.connect(_bdr_change_page.bind(1))
	_bdr_page_box.visible = false
	_bdr_set_amount(int(_bdr_amounts()[0]), false)


func _bdr_set_amount(amount: int, with_sound: = true) -> void :
	bdr_amount = amount
	var amounts: = _bdr_amounts()
	for index in range(_bdr_amount_buttons.size()):
		_bdr_amount_buttons[index].set_pressed_no_signal(int(amounts[index]) == amount)
	if with_sound:
		GameSession.play_sfx("ui_select")
	if _built and is_instance_valid(_donate_button):
		_refresh_donate_state()
		if not _locked_kind.is_empty():
			var item: = _item_for_kind(_locked_kind)
			if _bdr_item_can_donate(item):
				_show_item_status(item)
			else:
				_status_label.text = _unavailable_donation_message(_locked_kind)
				_status_label.modulate = Color("ffc36d")
				UITextFitterScript.fit(_status_label)
	_bdr_refresh_offer_panel()


func _bdr_required_count(kind: String) -> int:
	return bdr_amount + (1 if kind == "50_50" else 0)


func _bdr_item_can_donate(item: Dictionary) -> bool:
	if item.is_empty() or not bool(item.get("can_donate", false)):
		return false
	return int(item.get("count", 0)) >= _bdr_required_count(str(item.get("kind", "")))


func _bdr_refresh_offer_panel() -> void :
	if not is_instance_valid(_bdr_offer_box):
		return
	_bdr_offer_title.text = _bdr_text("offer_size_title", [], "OFFERING SIZE")
	var kind: = _locked_kind
	if kind.is_empty():
		_bdr_points_label.text = _bdr_text("select_text", [], "")
		_bdr_odds_label.text = ""
		return
	_bdr_points_label.text = _bdr_text("points_text", [kind, bdr_amount], "")
	_bdr_odds_label.text = _bdr_text("odds_bbcode", [kind, bdr_amount], "")


func _bdr_page_size() -> int:
	return BDR_PAGE_COLUMNS * BDR_PAGE_ROWS


## More than 10 dice types: 6 columns, 12 per page (otherwise the original 5 x 2 grid).
func _bdr_paged() -> bool:
	return _items.size() > DICE_GRID_COLUMNS * 2


func _bdr_page_count() -> int:
	if not _bdr_paged():
		return 1
	return maxi(1, ceili(float(_items.size()) / float(_bdr_page_size())))


func _bdr_change_page(direction: int) -> void :
	if _busy:
		return
	var pages: = _bdr_page_count()
	if pages <= 1:
		return
	_bdr_page = wrapi(_bdr_page + direction, 0, pages)
	GameSession.play_sfx("ui_select")
	_refresh_inventory(true)


func _bdr_refresh_page_controls() -> void :
	if not is_instance_valid(_bdr_page_box):
		return
	var pages: = _bdr_page_count()
	_bdr_page_box.visible = pages > 1 and not _choice_mode
	_bdr_page_label.text = "%d/%d" % [_bdr_page + 1, pages]


func _refresh_inventory(animate: bool) -> void :
	if not _built:
		return
	if not _locked_kind.is_empty() and _item_index_for_kind(_locked_kind) < 0:
		_locked_kind = ""
	for child in _carousel_track.get_children():
		if child != _selection_frame:
			child.queue_free()
	_slot_buttons.clear()
	_slot_roots.clear()
	var pages: = _bdr_page_count()
	_bdr_page = clampi(_bdr_page, 0, pages - 1)
	var first_index: = 0
	var visible_count: = _items.size()
	if _bdr_paged():
		first_index = _bdr_page * _bdr_page_size()
		visible_count = clampi(_items.size() - first_index, 0, _bdr_page_size())
		_dice_grid_columns = BDR_PAGE_COLUMNS
	else:
		_dice_grid_columns = DICE_GRID_COLUMNS
	_dice_grid_columns = maxi(1, _dice_grid_columns)
	for slot_index in range(visible_count):
		var row: = slot_index / _dice_grid_columns
		var column: = slot_index % _dice_grid_columns
		var row_start: = row * _dice_grid_columns
		var row_count: = mini(_dice_grid_columns, visible_count - row_start)
		var row_width: = 224.0 + float(maxi(0, row_count - 1)) * DICE_SLOT_STEP_X
		var start_x: = (_carousel_track.size.x - row_width) * 0.5
		var item: = _items[first_index + slot_index]
		var slot_position: = Vector2(start_x + float(column) * DICE_SLOT_STEP_X, float(row) * DICE_SLOT_STEP_Y)
		var slot_root: = _build_dice_slot(item, slot_position)
		_slot_roots.append(slot_root)
	_wire_slot_focus()
	if _locked_kind.is_empty():
		_selection_frame.visible = false
	else:
		_move_selection_to_kind(_locked_kind)
	_refresh_donate_state()
	_bdr_refresh_page_controls()
	_bdr_refresh_offer_panel()
	if _items.is_empty():
		_status_label.text = _text("no_dice")
		_status_label.modulate = Color("d4d8e1")
	elif _offerings_left <= 0:
		_status_label.text = ""
		_status_label.modulate = Color("ffd06a")
	elif animate:
		for index in range(_slot_roots.size()):
			var root: = _slot_roots[index]
			var target_y: = root.position.y
			root.modulate.a = 0.0
			root.position.y = target_y + 18.0
			var reveal: = create_tween().set_parallel(true)
			reveal.tween_interval(float(index) * 0.035)
			reveal.tween_property(root, "modulate:a", 1.0, 0.16)
			reveal.tween_property(root, "position:y", target_y, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _build_dice_slot(item: Dictionary, at_position: Vector2) -> Control:
	var root: = Control.new()
	root.position = at_position
	root.size = Vector2(224, 184)
	root.pivot_offset = root.size * 0.5
	root.mouse_filter = Control.MOUSE_FILTER_PASS
	root.set_meta("kind", str(item.get("kind", "")))
	root.set_meta("grid_position", at_position)
	_carousel_track.add_child(root)
	var backing: = Panel.new()
	backing.position = Vector2(14, 7)
	backing.size = Vector2(196, 164)
	backing.mouse_filter = Control.MOUSE_FILTER_IGNORE
	backing.add_theme_stylebox_override("panel", _panel_style(Color("080c14ee"), Color("4b5360"), 2, 11))
	root.add_child(backing)
	var icon: = _texture_rect(str(item.get("icon_path", "")), Rect2(54, 4, 116, 108), root, 2)
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	var owned_label: = _label("×%s" % _compact_count(int(item.get("count", 0))), Rect2(22, 108, 180, 60), 36, HORIZONTAL_ALIGNMENT_CENTER, root, 3)
	owned_label.add_theme_font_override("font", _readable_font)
	owned_label.add_theme_font_size_override("font_size", 36)
	owned_label.add_theme_constant_override("outline_size", 2)
	owned_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	owned_label.modulate = Color("b8ffd1") if _bdr_item_can_donate(item) else Color("b5bac5")
	if item.has("worth"):
		var worth_label: = _bdr_label("★%d" % int(item.get("worth", 1)), Rect2(128, 8, 80, 40), 30, HORIZONTAL_ALIGNMENT_RIGHT, root, 3)
		worth_label.add_theme_font_override("font", _readable_font)
		worth_label.add_theme_color_override("font_color", Color("ffd06a"))
	var button: = Button.new()
	button.position = Vector2.ZERO
	button.size = root.size
	button.flat = true
	button.focus_mode = Control.FOCUS_ALL
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("hover", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("pressed", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	button.set_meta("kind", str(item.get("kind", "")))
	button.mouse_entered.connect(_preview_slot.bind(root, item))
	button.focus_entered.connect(_preview_slot.bind(root, item))
	button.mouse_exited.connect(_leave_slot.bind(root))
	button.focus_exited.connect(_leave_slot.bind(root))
	button.pressed.connect(_lock_kind.bind(str(item.get("kind", ""))))
	root.add_child(button)
	_slot_buttons.append(button)
	UITextFitterScript.register(owned_label, 36, 22, 4.0, 0.0)
	UITextFitterScript.fit(owned_label)
	return root


func _preview_slot(root: Control, item: Dictionary) -> void :
	if _busy:
		return
	GameSession.play_sfx("ui_hover")
	var grow: = _replace_motion_tween(root)
	grow.tween_property(root, "scale", Vector2(1.035, 1.035), 0.12).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	if _locked_kind.is_empty():
		_move_selection_to(root)
	if _bdr_item_can_donate(item):
		_show_item_status(item)
	else:
		_status_label.text = _unavailable_donation_message(str(item.get("kind", "")))
		_status_label.modulate = Color("ffc36d")
	UITextFitterScript.fit(_status_label)


func _leave_slot(root: Control) -> void :
	if not is_instance_valid(root):
		return
	var shrink: = _replace_motion_tween(root)
	shrink.tween_property(root, "scale", Vector2.ONE, 0.14).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	if _locked_kind.is_empty():
		_selection_frame.visible = false
	else:
		_move_selection_to_kind(_locked_kind)
	if _locked_kind.is_empty():
		_status_label.text = ""
	else:
		var locked_item: = _item_for_kind(_locked_kind)
		if _bdr_item_can_donate(locked_item):
			_show_item_status(locked_item)
		else:
			_status_label.text = _unavailable_donation_message(_locked_kind)
			_status_label.modulate = Color("ffc36d")
			UITextFitterScript.fit(_status_label)


func _lock_kind(kind: String) -> void :
	if _busy or kind.is_empty():
		return
	_locked_kind = kind
	GameSession.play_sfx("ui_select")
	_move_selection_to_kind(kind)
	_refresh_donate_state()
	_bdr_refresh_offer_panel()
	var item: = _item_for_kind(kind)
	if not _bdr_item_can_donate(item):
		_status_label.text = _unavailable_donation_message(kind)
		_status_label.modulate = Color("ffc36d")
	else:
		_show_item_status(item)
		_donate_button.grab_focus()
	UITextFitterScript.fit(_status_label)


func _show_item_status(item: Dictionary) -> void :
	if item.is_empty():
		_status_label.text = ""
		return
	var parts: Array[String] = [str(item.get("name", "")), _text("owned") % int(item.get("count", 0))]
	if item.has("worth"):
		parts.append(_bdr_text("worth_text", [str(item.get("kind", ""))], ""))
	_status_label.text = "  ·  ".join(parts)
	_status_label.modulate = Color("e8edf5")
	UITextFitterScript.fit(_status_label)


func _unavailable_donation_message(kind: String) -> String:
	var item: = _item_for_kind(kind)
	if item.is_empty():
		return ""
	return _bdr_text("need_text", [_bdr_required_count(kind)], "")


func _refresh_donate_state() -> void :
	var item: = _item_for_kind(_locked_kind)
	var allowed: = _world_ready and _bdr_item_can_donate(item) and _offerings_left > 0 and not _busy
	_donate_button.visible = not _locked_kind.is_empty()
	_donate_button.disabled = not allowed
	_donate_button.modulate = Color.WHITE if allowed else Color("7b7f88")
	_donate_button.text = "%s  ×%d" % [_text("donate"), bdr_amount]
	UITextFitterScript.fit(_donate_button)


func _donate_locked_kind() -> void :
	if not _world_ready or _busy or _locked_kind.is_empty():
		return
	var item: = _item_for_kind(_locked_kind)
	if not _bdr_item_can_donate(item) or _offerings_left <= 0:
		GameSession.play_sfx("denied")
		_refresh_donate_state()
		return
	_busy = true
	_donate_button.disabled = true
	donation_requested.emit(_locked_kind)


func _bdr_rarity_color(rarity: String) -> Color:
	if bdr_hooks == null:
		return Color("ffc93c")
	return bdr_hooks.rarity_color(rarity)


func _bdr_rarity_name(rarity: String) -> String:
	return _bdr_text("rarity_name", [rarity], rarity.to_upper())


func _show_blessing_choices(cards: Array[Dictionary], immediate: = false) -> void :
	_hide_card_tooltip()
	_hide_grimoire_immediately()
	_choice_mode = true
	_top_strip.visible = false
	_grimoire_button.visible = false
	if is_instance_valid(_help_button):
		_help_button.visible = false
	if is_instance_valid(_bdr_page_box):
		_bdr_page_box.visible = false
	_hint_label.visible = false
	_carousel_panel.visible = false
	_status_label.visible = false
	_card_layer.visible = true
	for child in _card_layer.get_children():
		child.queue_free()
	_card_buttons.clear()
	_card_roots.clear()
	_card_by_id.clear()
	_requested_card_root = null
	_card_dimmer = ColorRect.new()
	_card_dimmer.position = - _viewport_origin
	_card_dimmer.size = _viewport_size
	_card_dimmer.color = Color(0.0, 0.0, 0.0, 0.32)
	_card_dimmer.mouse_filter = Control.MOUSE_FILTER_STOP
	_card_layer.add_child(_card_dimmer)
	var card_header: = Panel.new()
	card_header.position = Vector2(300, 35)
	card_header.size = Vector2(1320, 112)
	card_header.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card_header.add_theme_stylebox_override("panel", _panel_style(Color("080a12f2"), Color("c99837"), 3, 18))
	_card_layer.add_child(card_header)
	var best_index: = -1
	for card in cards:
		best_index = maxi(best_index, ["common", "rare", "epic", "legendary"].find(str(card.get("rarity", "legendary"))))
	var heading_text: = _text("choose_blessing")
	if best_index >= 0 and bdr_hooks != null:
		heading_text = "%s  ·  %s" % [heading_text, _bdr_rarity_name(["common", "rare", "epic", "legendary"][best_index])]
	var heading: = _label(heading_text, Rect2(28, 8, 1264, 96), 32, HORIZONTAL_ALIGNMENT_CENTER, card_header, 2)
	if best_index >= 0:
		heading.add_theme_color_override("font_color", _bdr_rarity_color(["common", "rare", "epic", "legendary"][best_index]).lerp(Color.WHITE, 0.35))
	var visible_card_count: = mini(4, cards.size())
	var hand_width: = float(visible_card_count) * CHOICE_CARD_SIZE.x + float(maxi(0, visible_card_count - 1)) * CHOICE_CARD_GAP
	var hand_start_x: = (1920.0 - hand_width) * 0.5
	for index in range(visible_card_count):
		var card: = cards[index]
		var root: = _build_blessing_card(card, Vector2(hand_start_x + float(index) * (CHOICE_CARD_SIZE.x + CHOICE_CARD_GAP), 202))
		_card_roots.append(root)
		_card_by_id[str(card.get("id", ""))] = root
		root.position.y = 202.0 if immediate else 720.0 + float(index) * 34.0
		root.scale = Vector2.ONE if immediate else Vector2(0.72, 0.72)
		root.rotation = 0.0 if immediate else deg_to_rad(float(index) * 3.5 - float(visible_card_count - 1) * 1.75)
		root.modulate.a = 1.0 if immediate else 0.1
		if not immediate:
			var delay: = float(index) * 0.09
			var rise: = create_tween().set_parallel(true)
			rise.tween_property(root, "position:y", 202.0, 0.52).set_delay(delay).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			rise.tween_property(root, "scale", Vector2.ONE, 0.48).set_delay(delay).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			rise.tween_property(root, "rotation", 0.0, 0.42).set_delay(delay).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
			rise.tween_property(root, "modulate:a", 1.0, 0.2).set_delay(delay)
	_wire_card_focus()
	_ritual_stage = "choice" if immediate else "cards_rising"
	UITextFitterScript.fit(heading)


func _build_blessing_card(card: Dictionary, card_position: Vector2) -> Control:
	var blessing_id: = str(card.get("id", ""))
	var card_data: = card.duplicate(true)
	var rarity: = str(card.get("rarity", DogShrineCards.rarity(blessing_id)))
	var rarity_color: = _bdr_rarity_color(rarity)
	var root: = Control.new()
	root.position = card_position
	root.size = CHOICE_CARD_SIZE
	root.pivot_offset = root.size * 0.5
	root.mouse_filter = Control.MOUSE_FILTER_PASS
	root.set_meta("blessing_id", blessing_id)
	_card_layer.add_child(root)
	var glow: = Panel.new()
	glow.position = Vector2(-7, -7)
	glow.size = CHOICE_CARD_SIZE + Vector2(14, 14)
	glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	glow.z_index = 0
	var glow_style: = _panel_style(Color(0, 0, 0, 0), rarity_color, 5, 14)
	glow_style.shadow_color = Color(rarity_color.r, rarity_color.g, rarity_color.b, 0.55)
	glow_style.shadow_size = 22 if rarity in ["epic", "legendary"] else 12
	glow.add_theme_stylebox_override("panel", glow_style)
	root.add_child(glow)
	var art: = _texture_rect(DogShrineCards.art_path(blessing_id), Rect2(Vector2.ZERO, CHOICE_CARD_SIZE), root, 1)
	art.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	art.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var owned_rank: = int(card.get("count", 0))
	if owned_rank > 0:
		# Dice Rush Extended: offered cards the player already has get a small "OWNED" badge.
		var badge: = Panel.new()
		badge.size = Vector2(CHOICE_CARD_SIZE.x + 40.0, 42)
		badge.position = Vector2((CHOICE_CARD_SIZE.x - badge.size.x) * 0.5, -20)
		badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
		badge.z_index = 3
		var badge_style: = _panel_style(Color("0d2b17f2"), Color("63e58f"), 3, 10)
		badge.add_theme_stylebox_override("panel", badge_style)
		root.add_child(badge)
		var badge_label: = _bdr_label(_bdr_text("owned_text", [owned_rank], "OWNED x%d" % owned_rank), Rect2(Vector2(4, 2), badge.size - Vector2(8, 4)), 19, HORIZONTAL_ALIGNMENT_CENTER, badge, 4)
		badge_label.add_theme_color_override("font_color", Color("9dffbb"))
		UITextFitterScript.register(badge_label, 19, 10, 2.0, 2.0)
	var tag: = _bdr_label(_bdr_rarity_name(rarity), Rect2(0, CHOICE_CARD_SIZE.y + 12, CHOICE_CARD_SIZE.x, 36), 18, HORIZONTAL_ALIGNMENT_CENTER, root, 2)
	tag.add_theme_color_override("font_color", rarity_color)
	var name_tag: = _bdr_label(str(card.get("name", "")), Rect2(-20, CHOICE_CARD_SIZE.y + 46, CHOICE_CARD_SIZE.x + 40, 34), 14, HORIZONTAL_ALIGNMENT_CENTER, root, 2)
	name_tag.add_theme_font_override("font", _readable_font)
	name_tag.add_theme_font_size_override("font_size", 20)
	var button: = Button.new()
	button.position = Vector2.ZERO
	button.size = CHOICE_CARD_SIZE
	button.flat = true
	button.focus_mode = Control.FOCUS_ALL
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("hover", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("pressed", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	button.mouse_entered.connect(_on_card_hover.bind(button, root, card_data, true))
	button.mouse_exited.connect(_on_card_hover.bind(button, root, card_data, false))
	button.focus_entered.connect(_on_card_hover.bind(button, root, card_data, true))
	button.focus_exited.connect(_on_card_hover.bind(button, root, card_data, false))
	button.pressed.connect(_request_blessing.bind(blessing_id, root))
	root.add_child(button)
	_card_buttons.append(button)
	return root


func _build_grimoire_card(card: Dictionary) -> void :
	var card_id: = str(card.get("id", ""))
	var count: = maxi(0, int(card.get("count", 0)))
	var acquired: = count > 0
	var card_data: = card.duplicate(true)
	var root: = Control.new()
	root.custom_minimum_size = GRIMOIRE_SLOT_SIZE
	root.size = GRIMOIRE_SLOT_SIZE
	root.mouse_filter = Control.MOUSE_FILTER_PASS
	root.set_meta("card_id", card_id)
	root.set_meta("acquired", acquired)
	_grimoire_grid.add_child(root)
	_grimoire_card_roots.append(root)
	var visual: = Control.new()
	visual.position = (GRIMOIRE_SLOT_SIZE - GRIMOIRE_CARD_SIZE) * 0.5
	visual.size = GRIMOIRE_CARD_SIZE
	visual.pivot_offset = visual.size * 0.5
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	visual.set_meta("base_y", visual.position.y)
	root.add_child(visual)
	var rarity: = str(card.get("rarity", DogShrineCards.rarity(card_id)))
	var frame: = Panel.new()
	frame.position = Vector2(-5, -5)
	frame.size = GRIMOIRE_CARD_SIZE + Vector2(10, 10)
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.z_index = 0
	var frame_color: = _bdr_rarity_color(rarity) if acquired else Color("2a2e38")
	frame.add_theme_stylebox_override("panel", _panel_style(Color(0, 0, 0, 0), frame_color, 4, 10))
	visual.add_child(frame)
	var art_path: = DogShrineCards.art_path(card_id) if acquired else DogShrineCards.CARD_BACK_PATH
	var art: = _texture_rect(art_path, Rect2(Vector2.ZERO, GRIMOIRE_CARD_SIZE), visual, 1)
	art.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	art.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var button: = Button.new()
	button.position = visual.position
	button.size = GRIMOIRE_CARD_SIZE
	button.flat = true
	button.focus_mode = Control.FOCUS_ALL
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.z_index = 4
	button.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("hover", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("pressed", StyleBoxEmpty.new())
	button.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	button.mouse_entered.connect(_on_grimoire_card_hover.bind(button, root, visual, card_data, true, false))
	button.mouse_exited.connect(_on_grimoire_card_hover.bind(button, root, visual, card_data, false, false))
	button.focus_entered.connect(_on_grimoire_card_hover.bind(button, root, visual, card_data, true, true))
	button.focus_exited.connect(_on_grimoire_card_hover.bind(button, root, visual, card_data, false, true))
	button.pressed.connect(_on_grimoire_card_pressed.bind(button, visual, acquired))
	root.add_child(button)
	_grimoire_card_buttons.append(button)


func _show_card_tooltip(owner: Control, card: Dictionary, prefer_below: bool) -> void :
	if not _card_tooltips_enabled:
		_hide_card_tooltip()
		return
	if not is_instance_valid(owner) or not is_instance_valid(_card_tooltip):
		return
	var card_id: = str(card.get("id", ""))
	var card_name: = str(card.get("name", "")).strip_edges()
	if card_name.is_empty():
		card_name = _text("dog_card_%s_name" % card_id)
	var description: = str(card.get("description", "")).strip_edges()
	if description.is_empty():
		description = _text("dog_card_%s_desc" % card_id)
	var level: = maxi(0, int(card.get("next_rank", card.get("count", 0))))
	var rarity: = str(card.get("rarity", DogShrineCards.rarity(card_id)))
	_card_tooltip_owner = owner
	_card_tooltip_name.text = card_name
	_card_tooltip_name.add_theme_color_override("font_color", _bdr_rarity_color(rarity).lerp(Color.WHITE, 0.2))
	_card_tooltip_level.text = "%s  ·  %s" % [_bdr_rarity_name(rarity), _card_level_text(level, float(card.get("effect_power", 0.0)))]
	_card_tooltip_description.text = description
	UITextFitterScript.fit(_card_tooltip_name)
	UITextFitterScript.fit(_card_tooltip_level)
	UITextFitterScript.fit(_card_tooltip_description)
	_reposition_card_tooltip(owner, prefer_below)
	_card_tooltip.visible = true
	_card_tooltip.modulate.a = 0.0
	_card_tooltip.scale = Vector2(0.97, 0.97)
	var reveal: = _replace_motion_tween(_card_tooltip).set_parallel(true)
	reveal.tween_property(_card_tooltip, "modulate:a", 1.0, 0.1).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	reveal.tween_property(_card_tooltip, "scale", Vector2.ONE, 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


const BDRNumFmt: = preload("res://bdr/core/numfmt.gd")


## Dice Rush Extended: same short number style everywhere (1.1K, 2.5M ... never "e").
func _compact_count(value: int) -> String:
	return BDRNumFmt.compact(maxi(0, value))
