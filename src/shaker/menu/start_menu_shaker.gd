extends "res://scripts/start_menu.gd"
## Dice Rush Extended - Dice Shaker: the game's start menu (with the other changes of the mod) plus a
## DICE SHAKER button under NEW GAME. The save card screen is shared: in Dice Shaker mode it shows,
## starts and deletes the Dice Shaker save cards (user://shaker_slot_N.json) instead.

const ShakerSave := preload("res://shaker/core/save.gd")
const ShakerI18N := preload("res://shaker/core/i18n.gd")
const ShakerNumFmt := preload("res://shaker/core/numfmt.gd")
const SHAKER_SCENE := "res://shaker/scenes/shaker.tscn"
## five buttons instead of four: same look, a bit smaller (620x162 -> 540x141)
const SHAKER_BUTTON_SIZE := Vector2(540, 141)
const SHAKER_BUTTON_Y := [318.0, 466.0, 614.0, 762.0, 910.0]
const SHAKER_CARD_TINT := Color("dcc2ff")
const SHAKER_SLOT_META := &"shaker_active_slot"

var shaker_button: Button
var shaker_mode := false
var _shaker_heading: Label
var _shaker_subtitle: Label
var _shaker_normal_heading := ""
var _shaker_normal_subtitle := ""
var _shaker_message_view: Control
var _shaker_message_label: Label


func _build_main_view() -> void:
	super._build_main_view()
	shaker_button = _make_main_menu_button(main_motion_root, ShakerI18N.t("menu.button"), Rect2(Vector2(690, SHAKER_BUTTON_Y[2]), SHAKER_BUTTON_SIZE), _on_shaker_pressed)
	# order for the entrance animation and the controller: continue, new game, dice shaker, settings, quit
	main_menu_buttons.erase(shaker_button)
	main_menu_buttons.insert(main_menu_buttons.find(new_game_button) + 1, shaker_button)
	_shaker_build_message_view()


func _layout_main_menu(has_save: bool) -> void:
	super._layout_main_menu(has_save)
	if not is_instance_valid(shaker_button):
		return
	var order := [continue_button, new_game_button, shaker_button, settings_button, quit_button]
	for index in order.size():
		var button := order[index] as Button
		if is_instance_valid(button):
			_layout_main_button(button, Rect2(Vector2(960.0 - SHAKER_BUTTON_SIZE.x * 0.5, float(SHAKER_BUTTON_Y[index])), SHAKER_BUTTON_SIZE))


func _build_save_slots_view() -> void:
	super._build_save_slots_view()
	_shaker_normal_heading = GameSession.text("save_slots")
	_shaker_normal_subtitle = GameSession.text("choose_save_slot")
	for child in save_slots_motion_root.get_children():
		if child is Label:
			if _shaker_heading == null and (child as Label).text == _shaker_normal_heading:
				_shaker_heading = child
			elif _shaker_subtitle == null and (child as Label).text == _shaker_normal_subtitle:
				_shaker_subtitle = child


func _on_shaker_pressed() -> void:
	if "_bdr_host_pending" in self:
		set("_bdr_host_pending", false)
	shaker_mode = true
	_shaker_apply_texts()
	_open_save_slots(false)


func _show_main() -> void:
	if shaker_mode:
		shaker_mode = false
		_shaker_apply_texts()
	super._show_main()


func _shaker_apply_texts() -> void:
	if _shaker_heading:
		_shaker_heading.text = ShakerI18N.t("slots.title") if shaker_mode else _shaker_normal_heading
	if _shaker_subtitle:
		_shaker_subtitle.text = ShakerI18N.t("slots.subtitle") if shaker_mode else _shaker_normal_subtitle


func _preferred_save_slot(prefer_empty: bool) -> int:
	if shaker_mode:
		for slot_index in range(1, ShakerSave.SLOT_COUNT + 1):
			if ShakerSave.occupied(slot_index):
				return ShakerSave.most_recent()
		return 1
	return super._preferred_save_slot(prefer_empty)


func _refresh_save_slots() -> void:
	if not shaker_mode:
		super._refresh_save_slots()
		return
	for widget in save_slot_widgets:
		var slot_index := int(widget.slot)
		var summary := ShakerSave.summary(slot_index)
		var occupied := bool(summary.occupied)
		var valid := bool(summary.valid)
		(widget.money_value as Label).visible = valid
		(widget.time_value as Label).visible = valid
		(widget.money_value as Label).text = GameSession.currency_text(ShakerNumFmt.compact(float(summary.money)))
		(widget.time_value as Label).text = _format_save_slot_time(int(summary.play_time))
		(widget.card_button as Button).tooltip_text = GameSession.text("corrupt_save") if occupied and not valid else (GameSession.text("play_save") if occupied else GameSession.text("new_save"))
		(widget.play_button as Button).tooltip_text = GameSession.text("play_save")
		(widget.play_button as Button).visible = occupied
		(widget.delete_button as Button).visible = occupied
		(widget.texture as TextureRect).modulate = Color("ffb2bd") if occupied and not valid else SHAKER_CARD_TINT
		UITextFitterScript.fit(widget.money_value as Label)
		UITextFitterScript.fit(widget.time_value as Label)
	_wire_save_slot_focus()


func _on_save_slot_play_pressed(slot_index: int) -> void:
	if not shaker_mode:
		for widget in save_slot_widgets:
			(widget.texture as TextureRect).modulate = Color.WHITE
		super._on_save_slot_play_pressed(slot_index)
		return
	if save_slot_transition_active or save_delete_confirm_view.visible:
		return
	var summary := ShakerSave.summary(slot_index)
	if bool(summary.occupied) and not bool(summary.valid):
		_shaker_show_message(GameSession.text("corrupt_save"))
		return
	# the scene of the game mode reads the chosen save card from here
	GameSession.set_meta(SHAKER_SLOT_META, slot_index)
	get_tree().paused = false
	get_tree().change_scene_to_file(SHAKER_SCENE)


func _open_save_delete_confirmation(slot_index: int) -> void:
	if not shaker_mode:
		super._open_save_delete_confirmation(slot_index)
		return
	if save_slot_transition_active or not ShakerSave.occupied(slot_index):
		return
	pending_delete_slot = clampi(slot_index, 1, ShakerSave.SLOT_COUNT)
	save_delete_warning_label.text = GameSession.text("delete_save_confirm") % pending_delete_slot
	UITextFitterScript.fit(save_delete_warning_label)
	_set_save_slot_interaction_enabled(false)
	save_delete_confirm_view.visible = true
	get_viewport().gui_release_focus()
	_animate_view_in(save_delete_confirm_view)
	save_delete_no_button.grab_focus.call_deferred()


## Same as the game's version, but deletes the Dice Shaker save card in Dice Shaker mode.
func _confirm_delete_save_slot() -> void:
	if not shaker_mode:
		super._confirm_delete_save_slot()
		return
	if pending_delete_slot < 1 or save_slot_transition_active:
		return
	var slot_index := pending_delete_slot
	pending_delete_slot = 0
	save_delete_confirm_view.visible = false
	var widget := _save_slot_widget(slot_index)
	if widget.is_empty():
		return
	var card_root := widget.root as Control
	save_slot_transition_active = true
	_set_save_slot_interaction_enabled(false)
	get_viewport().gui_release_focus()
	if _ui_motion_enabled():
		save_delete_tween = create_tween().set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
		save_delete_tween.tween_property(card_root, "rotation", deg_to_rad(-2.0), 0.05).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		save_delete_tween.tween_property(card_root, "rotation", deg_to_rad(2.0), 0.07).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)
		save_delete_tween.tween_property(card_root, "rotation", 0.0, 0.05).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		save_delete_tween.set_parallel(true)
		save_delete_tween.tween_property(card_root, "scale", Vector2(0.84, 0.9), 0.18).set_delay(0.17).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
		save_delete_tween.tween_property(card_root, "modulate:a", 0.0, 0.15).set_delay(0.19).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		await save_delete_tween.finished
	ShakerSave.delete(slot_index)
	_refresh_save_slots()
	card_root.rotation = 0.0
	card_root.scale = Vector2(0.86, 0.86)
	card_root.modulate.a = 0.0
	if _ui_motion_enabled():
		save_delete_tween = create_tween().set_pause_mode(Tween.TWEEN_PAUSE_PROCESS).set_parallel(true)
		save_delete_tween.tween_property(card_root, "scale", Vector2.ONE, 0.24).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		save_delete_tween.tween_property(card_root, "modulate:a", 1.0, 0.16).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		await save_delete_tween.finished
	_reset_save_slot_motion()
	save_delete_tween = null
	save_slot_transition_active = false
	_set_save_slot_interaction_enabled(true)
	_wire_save_slot_focus()
	(widget.card_button as Button).grab_focus()


func _shaker_build_message_view() -> void:
	_shaker_message_view = _make_full_view()
	_shaker_message_view.z_index = 60
	_make_viewport_dim(_shaker_message_view, Color(0.005, 0.008, 0.02, 0.72))
	var panel := _make_panel(_shaker_message_view, Rect2(560, 350, 800, 360))
	_shaker_message_label = Label.new()
	_shaker_message_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_shaker_message_label.clip_text = true
	_shaker_message_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_shaker_message_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_shaker_message_label.position = Vector2(40, 40)
	_shaker_message_label.size = Vector2(720, 180)
	_shaker_message_label.add_theme_font_override("font", pixel_font)
	_shaker_message_label.add_theme_font_size_override("font_size", 16)
	_shaker_message_label.add_theme_color_override("font_color", Color.WHITE)
	panel.add_child(_shaker_message_label)
	_make_button(panel, "OK", Rect2(250, 246, 300, 80), func() -> void: _shaker_message_view.visible = false, true)
	_shaker_message_view.visible = false


func _shaker_show_message(text: String) -> void:
	if _shaker_message_label == null:
		return
	_shaker_message_label.text = text
	_shaker_message_view.visible = true
