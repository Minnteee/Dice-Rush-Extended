# Dice Rush Extended - main.gd patch: cheaper shop label updates on crowded tables.
# With 100+ shop cards the vanilla code rebuilt the whole gamepad focus graph (O(n^2), ~18 ms)
# on every label update (every 66 ms), and re-applied every price colour (which re-shapes the
# text). Both now only happen when something actually changed.

var _bdr_focus_signature: String = ""


func _refresh_shop_focus_navigation() -> void :
	var focusable_kinds: = _focusable_shop_kinds()
	var hud_buttons: Array[Button] = []
	for candidate in [talent_hud_button, lucky_hud_button, dog_shrine_hud_button]:
		if is_instance_valid(candidate):
			hud_buttons.append(candidate as Button)
	var signature_parts: PackedStringArray = PackedStringArray()
	for kind in shop_visible_kinds:
		signature_parts.append(kind)
	signature_parts.append("#")
	for kind in focusable_kinds:
		var focus_button: = shop_buttons.get(kind) as Button
		signature_parts.append("%s:%d" % [kind, focus_button.get_instance_id() if is_instance_valid(focus_button) else 0])
	signature_parts.append("#")
	for hud_button in hud_buttons:
		signature_parts.append(str(hud_button.get_instance_id()))
	var signature: = "|".join(signature_parts)
	if signature == _bdr_focus_signature:
		return
	_bdr_focus_signature = signature
	for button_value in shop_buttons.values():
		var button: = button_value as Button
		if not is_instance_valid(button):
			continue
		button.focus_neighbor_left = NodePath("")
		button.focus_neighbor_right = NodePath("")
		button.focus_neighbor_top = NodePath("")
		button.focus_neighbor_bottom = NodePath("")
		button.focus_next = NodePath("")
		button.focus_previous = NodePath("")
	for index in range(focusable_kinds.size()):
		var kind: = focusable_kinds[index]
		var button: = shop_buttons.get(kind) as Button
		if not is_instance_valid(button):
			continue
		for direction in ["left", "right", "top", "bottom"]:
			_set_focus_neighbor(button, direction, button)
			var target_kind: = _shop_focus_neighbor_kind(kind, direction, focusable_kinds)
			if not target_kind.is_empty():
				_set_focus_neighbor(button, direction, shop_buttons.get(target_kind) as Control)
		if focusable_kinds.size() > 1:
			button.focus_next = button.get_path_to(shop_buttons.get(focusable_kinds[(index + 1) % focusable_kinds.size()]) as Node)
			button.focus_previous = button.get_path_to(shop_buttons.get(focusable_kinds[wrapi(index - 1, 0, focusable_kinds.size())]) as Node)
	for index in range(hud_buttons.size()):
		var hud_button: = hud_buttons[index]
		hud_button.focus_neighbor_left = NodePath("")
		hud_button.focus_neighbor_right = NodePath("")
		hud_button.focus_neighbor_top = NodePath("")
		hud_button.focus_neighbor_bottom = NodePath("")
		if index > 0:
			_set_focus_neighbor(hud_button, "top", hud_buttons[index - 1])
		if index + 1 < hud_buttons.size():
			_set_focus_neighbor(hud_button, "bottom", hud_buttons[index + 1])
	var right_column: Array[String] = []
	for kind in focusable_kinds:
		if shop_visible_kinds.find(kind) % 2 == 1:
			right_column.append(kind)
	for index in range(mini(hud_buttons.size(), right_column.size())):
		var shop_button: = shop_buttons.get(right_column[index]) as Control
		_set_focus_neighbor(shop_button, "right", hud_buttons[index])
		_set_focus_neighbor(hud_buttons[index], "left", shop_button)


func _bdr_set_label_color(label: Label, color: Color) -> void:
	if label.get_meta("bdr_font_color", Color(-1, -1, -1, -1)) == color:
		return
	label.set_meta("bdr_font_color", color)
	label.add_theme_color_override("font_color", color)


func _bdr_set_label_text(label: Label, text_value: String) -> void:
	if label.text == text_value:
		return
	label.text = text_value
	UITextFitterScript.fit(label)


func _update_product_label(kind: String, count: int, maximum: int, next_price: float, table_full: bool = false) -> void :
	var owned: = owned_labels.get(kind) as Label
	var price: = price_labels.get(kind) as Label
	if owned:
		_bdr_set_label_text(owned, "%d/%d" % [count, maximum] if maximum > 0 else str(count))
	if price:
		if maximum > 0 and count >= maximum:
			_bdr_set_label_text(price, GameSession.text("max"))
			_bdr_set_label_color(price, PRICE_AFFORDABLE_COLOR)
		elif table_full and kind != "npc":
			_bdr_set_label_text(price, GameSession.text("max"))
			_bdr_set_label_color(price, PRICE_AFFORDABLE_COLOR)
		elif next_price < 0.0:
			_bdr_set_label_text(price, GameSession.text("tbd"))
			_bdr_set_label_color(price, PRICE_AFFORDABLE_COLOR)
		else:
			_bdr_set_label_text(price, _bdr_money_text(next_price))
			_bdr_set_label_color(price, PRICE_UNAFFORDABLE_COLOR if money < next_price else PRICE_AFFORDABLE_COLOR)
