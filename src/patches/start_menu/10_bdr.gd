const BDRI18N: = preload("res://bdr/core/i18n.gd")


const BDRNumFmt: = preload("res://bdr/core/numfmt.gd")


const BDRCoop: = preload("res://bdr/net/coop.gd")


const BDRSettings: = preload("res://bdr/core/settings.gd")


const BDR_MOD_VERSION: = "1.0.0"
const BDR_GITHUB_URL: = "https://github.com/Minnteee"
## GitHub mark (octicon "mark-github"), drawn white.
const BDR_GITHUB_SVG: = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 16 16\"><path fill=\"#ffffff\" d=\"M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z\"/></svg>"


var _bdr_host_pending: = false


var _bdr_join_view: Control


var _bdr_ip_edit: LineEdit


var _bdr_port_edit: LineEdit


var _bdr_join_status: Label


var _bdr_message_view: Control


var _bdr_message_label: Label


func _build_main_view() -> void :
	main_view = _make_full_view()
	main_motion_root = _make_motion_root(main_view)
	main_menu_logo = _make_menu_texture(main_motion_root, MAIN_MENU_LOGO_TEXTURE, Rect2(580, 50, 760, 270), 1)
	main_menu_logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	main_menu_logo.pivot_offset = main_menu_logo.size * 0.5
	main_menu_logo.set_meta("motion_base_position", main_menu_logo.position)

	continue_button = _make_main_menu_button(main_motion_root, GameSession.text("continue"), Rect2(650, 325, 620, 162), _on_continue_pressed, true)
	new_game_button = _make_main_menu_button(main_motion_root, GameSession.text("new_game"), Rect2(650, 503, 620, 162), _on_new_game_pressed)
	settings_button = _make_main_menu_button(main_motion_root, GameSession.text("settings"), Rect2(650, 681, 620, 162), _open_settings)
	quit_button = _make_main_menu_button(main_motion_root, GameSession.text("quit"), Rect2(650, 859, 620, 162), _on_quit_pressed)

	var version: = _make_label(main_motion_root, GameSession.GAME_VERSION + "  ·  Dice Rush Extended " + BDR_MOD_VERSION, Rect2(34, 1014, 640, 36), 9, HORIZONTAL_ALIGNMENT_LEFT)
	version.add_theme_color_override("font_color", Color(WHITE, 0.62))
	# Dice Rush Extended: coop buttons (top right)
	var host_button: = _make_button(main_view, BDRI18N.t("coop.menu_host"), Rect2(1540, 34, 340, 78), _bdr_on_host_pressed, true)
	host_button.tooltip_text = BDRI18N.t("coop.menu_host_tip")
	var join_button: = _make_button(main_view, BDRI18N.t("coop.menu_join"), Rect2(1540, 124, 340, 78), _bdr_open_join)
	join_button.tooltip_text = BDRI18N.t("coop.menu_join_tip")
	_bdr_add_github_button(main_view)
	_bdr_build_join_view()
	_bdr_build_message_view()


func _bdr_build_join_view() -> void :
	_bdr_join_view = _make_full_view()
	_bdr_join_view.z_index = 40
	_make_viewport_dim(_bdr_join_view, Color(0.005, 0.008, 0.02, 0.72))
	var panel: = _make_panel(_bdr_join_view, Rect2(460, 210, 1000, 640))
	var heading: = _make_label(panel, BDRI18N.t("coop.join_title"), Rect2(40, 26, 920, 70), 34, HORIZONTAL_ALIGNMENT_CENTER, display_font)
	heading.add_theme_color_override("font_color", GOLD)
	_make_label(panel, BDRI18N.t("coop.join_ip"), Rect2(60, 120, 560, 44), 15, HORIZONTAL_ALIGNMENT_LEFT)
	_make_label(panel, BDRI18N.t("coop.join_port"), Rect2(700, 120, 240, 44), 15, HORIZONTAL_ALIGNMENT_LEFT)
	_bdr_ip_edit = _bdr_line_edit(panel, Rect2(60, 168, 600, 70))
	_bdr_ip_edit.placeholder_text = "25.12.34.56"
	_bdr_ip_edit.text_submitted.connect(func(_text: String) -> void: _bdr_connect())
	_bdr_port_edit = _bdr_line_edit(panel, Rect2(700, 168, 240, 70))
	var settings: Dictionary = BDRSettings.load_settings()
	_bdr_ip_edit.text = str(settings.get("coop_last_ip", ""))
	_bdr_port_edit.text = str(settings.get("coop_port", BDRCoop.DEFAULT_PORT))
	var info: = Label.new()
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.clip_text = true
	info.position = Vector2(60, 256)
	info.size = Vector2(880, 170)
	info.add_theme_font_override("font", pixel_font)
	info.add_theme_font_size_override("font_size", 12)
	info.add_theme_color_override("font_color", Color(CYAN, 0.95))
	info.add_theme_constant_override("line_spacing", 6)
	panel.add_child(info)
	info.text = BDRI18N.t("coop.join_info")
	_bdr_join_status = _make_label(panel, "", Rect2(60, 430, 880, 50), 14, HORIZONTAL_ALIGNMENT_CENTER)
	_bdr_join_status.add_theme_color_override("font_color", PINK)
	_make_button(panel, BDRI18N.t("coop.connect"), Rect2(60, 500, 420, 92), _bdr_connect, true)
	_make_button(panel, GameSession.text("back"), Rect2(520, 500, 420, 92), _bdr_close_join)
	_bdr_join_view.visible = false


func _bdr_line_edit(parent: Control, rect: Rect2) -> LineEdit:
	var edit: = LineEdit.new()
	edit.position = rect.position
	edit.size = rect.size
	edit.add_theme_font_override("font", pixel_font)
	edit.add_theme_font_size_override("font_size", 20)
	edit.add_theme_color_override("font_color", WHITE)
	edit.add_theme_color_override("font_placeholder_color", Color(MUTED, 0.6))
	edit.add_theme_stylebox_override("normal", _button_style(Color("07101f"), Color("2b3c68")))
	edit.add_theme_stylebox_override("focus", _button_style(Color("0b1530"), GOLD))
	parent.add_child(edit)
	return edit


func _bdr_build_message_view() -> void :
	_bdr_message_view = _make_full_view()
	_bdr_message_view.z_index = 45
	_make_viewport_dim(_bdr_message_view, Color(0.005, 0.008, 0.02, 0.72))
	var panel: = _make_panel(_bdr_message_view, Rect2(560, 350, 800, 360))
	_bdr_message_label = Label.new()
	_bdr_message_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_bdr_message_label.clip_text = true
	_bdr_message_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_bdr_message_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_bdr_message_label.position = Vector2(40, 40)
	_bdr_message_label.size = Vector2(720, 180)
	_bdr_message_label.add_theme_font_override("font", pixel_font)
	_bdr_message_label.add_theme_font_size_override("font_size", 16)
	_bdr_message_label.add_theme_color_override("font_color", WHITE)
	panel.add_child(_bdr_message_label)
	_make_button(panel, "OK", Rect2(250, 246, 300, 80), func() -> void: _bdr_message_view.visible = false, true)
	_bdr_message_view.visible = false


func _bdr_show_message(text: String) -> void :
	_bdr_message_label.text = text
	_bdr_message_view.visible = true


## Runs after the start menu is built: coop messages, Steam join requests, "+bdr_connect ip:port".
func _bdr_after_ready() -> void :
	BDRCoop.clear_launch()
	var message: = BDRCoop.take_message()
	if not message.is_empty():
		_bdr_show_message(message)
	if Engine.has_singleton("Steam"):
		var steam: = Engine.get_singleton("Steam")
		if bool(steam.call("isSteamRunning")):
			if steam.has_signal("join_requested") and not steam.is_connected("join_requested", _bdr_on_steam_join_requested):
				steam.connect("join_requested", _bdr_on_steam_join_requested)
			if steam.has_signal("lobby_joined") and not steam.is_connected("lobby_joined", _bdr_on_steam_lobby_joined):
				steam.connect("lobby_joined", _bdr_on_steam_lobby_joined)
			if steam.has_signal("join_game_requested") and not steam.is_connected("join_game_requested", _bdr_on_steam_join_game):
				steam.connect("join_game_requested", _bdr_on_steam_join_game)
	var args: = OS.get_cmdline_args()
	for index in range(args.size()):
		if str(args[index]) == "+bdr_connect" and index + 1 < args.size():
			_bdr_connect_to_text(str(args[index + 1]))
			return


func _bdr_on_steam_join_requested(lobby_id: int, _friend_id: int) -> void :
	Engine.get_singleton("Steam").call("joinLobby", lobby_id)


func _bdr_on_steam_lobby_joined(lobby_id: int, _permissions: int, _locked: bool, _response: int) -> void :
	var steam: = Engine.get_singleton("Steam")
	var ips: = str(steam.call("getLobbyData", lobby_id, "bdr_ip")).split(",", false)
	var port: = int(str(steam.call("getLobbyData", lobby_id, "bdr_port")))
	if ips.is_empty():
		return
	_bdr_start_client(ips[0], port if port > 0 else BDRCoop.DEFAULT_PORT)


func _bdr_on_steam_join_game(_friend_id: int, connect_string: String) -> void :
	var parts: = connect_string.split(" ", false)
	if parts.size() >= 2 and parts[0] == "+bdr_connect":
		_bdr_connect_to_text(parts[1])


func _bdr_connect_to_text(address_text: String) -> void :
	var parts: = address_text.split(":", false)
	if parts.is_empty():
		return
	_bdr_start_client(parts[0], int(parts[1]) if parts.size() > 1 else BDRCoop.DEFAULT_PORT)


func _bdr_on_host_pressed() -> void :
	if save_slot_transition_active:
		return
	_bdr_host_pending = true
	if GameSession.has_any_game_save():
		BDRCoop.set_launch({"mode": "host", "port": _bdr_port()})
		_on_continue_pressed()
	else:
		_open_save_slots(true)


func _bdr_port() -> int:
	var settings: Dictionary = BDRSettings.load_settings()
	return int(settings.get("coop_port", BDRCoop.DEFAULT_PORT))


func _bdr_open_join() -> void :
	_bdr_join_status.text = ""
	_bdr_join_view.visible = true
	_bdr_ip_edit.grab_focus()
	GameSession.play_sfx("ui_select")


func _bdr_close_join() -> void :
	_bdr_join_view.visible = false
	GameSession.play_sfx("ui_select")


func _bdr_connect() -> void :
	var address: = _bdr_ip_edit.text.strip_edges()
	var port: = int(_bdr_port_edit.text.strip_edges()) if _bdr_port_edit.text.strip_edges().is_valid_int() else BDRCoop.DEFAULT_PORT
	if address.is_empty():
		_bdr_join_status.text = BDRI18N.t("coop.join_need_ip")
		GameSession.play_sfx("denied")
		return
	var settings: Dictionary = BDRSettings.load_settings()
	settings["coop_last_ip"] = address
	settings["coop_port"] = port
	BDRSettings.save_settings(settings)
	_bdr_start_client(address, port)


func _bdr_start_client(address: String, port: int) -> void :
	BDRCoop.set_launch({"mode": "client", "address": address, "port": port})
	GameSession.launch_mode = ""
	_open_game_scene()


func _on_save_slot_play_pressed(slot_index: int) -> void :
	if save_slot_transition_active or save_delete_confirm_view.visible:
		return
	var summary: = GameSession.game_save_summary(slot_index)
	if _bdr_host_pending:
		BDRCoop.set_launch({"mode": "host", "port": _bdr_port()})
	GameSession.set_active_save_slot(slot_index)
	if not bool(summary.occupied):
		GameSession.launch_mode = "new"
		get_tree().paused = false
		get_tree().change_scene_to_file(STORY_SCENE)
		return
	if not bool(summary.valid):
		BDRCoop.clear_launch()
		_open_save_error()
		return
	GameSession.launch_mode = "continue"
	_open_game_scene()


func _refresh_save_slots() -> void :
	for widget in save_slot_widgets:
		var slot_index: = int(widget.slot)
		var summary: = GameSession.game_save_summary(slot_index)
		var status: = str(summary.status)
		var occupied: = bool(summary.occupied)
		var valid: = bool(summary.valid)
		(widget.money_value as Label).visible = valid
		(widget.time_value as Label).visible = valid
		(widget.money_value as Label).text = GameSession.currency_text(_bdr_slot_money_text(slot_index, int(summary.money)))
		(widget.time_value as Label).text = _format_save_slot_time(int(summary.play_time_seconds))
		(widget.card_button as Button).tooltip_text = GameSession.text("corrupt_save") if occupied and not valid else (GameSession.text("play_save") if occupied else GameSession.text("new_save"))
		var play_button: = widget.play_button as Button
		var delete_button: = widget.delete_button as Button
		play_button.tooltip_text = GameSession.text("play_save")
		play_button.visible = occupied
		delete_button.visible = occupied
		(widget.texture as TextureRect).modulate = Color("ffb2bd") if status == "corrupt" else Color.WHITE
		UITextFitterScript.fit(widget.money_value as Label)
		UITextFitterScript.fit(widget.time_value as Label)
	_wire_save_slot_focus()


## Dice Rush Extended saves big amounts as "1.234e30" - the original summary only reads integers.
func _bdr_slot_money_text(slot_index: int, fallback: int) -> String:
	var inspected: Dictionary = GameSession.inspect_game_save(slot_index)
	var data: Dictionary = inspected.get("data", {})
	var raw: = str(data.get("money", str(fallback)))
	if raw.contains("e") or raw.contains("E") or raw.contains("."):
		return BDRNumFmt.compact(raw.to_float())
	return _format_save_slot_number(fallback)


## Dice Rush Extended: same short number style everywhere (1.1K, 2.5M ... never "e").
func _format_save_slot_number(value: int) -> String:
	return BDRNumFmt.compact(value)


## Dice Rush Extended: GitHub logo at the bottom right of the main menu, opens the author's page.
func _bdr_add_github_button(parent: Control) -> void :
	var button: = TextureButton.new()
	button.name = "BDRGitHub"
	button.position = Vector2(1812, 972)
	button.size = Vector2(76, 76)
	button.ignore_texture_size = true
	button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	button.texture_normal = _bdr_github_texture()
	button.tooltip_text = "github.com/Minnteee"
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.focus_mode = Control.FOCUS_NONE
	button.modulate = Color(1.0, 1.0, 1.0, 0.72)
	button.mouse_entered.connect(func() -> void: button.modulate = Color.WHITE)
	button.mouse_exited.connect(func() -> void: button.modulate = Color(1.0, 1.0, 1.0, 0.72))
	button.pressed.connect(_bdr_open_github)
	parent.add_child(button)
	if button.texture_normal == null:
		# no SVG support: show the word instead
		var fallback: = _make_label(button, "GitHub", Rect2(Vector2(-40, 0), Vector2(156, 76)), 14, HORIZONTAL_ALIGNMENT_CENTER)
		fallback.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _bdr_github_texture() -> Texture2D:
	var image: = Image.new()
	if image.load_svg_from_string(BDR_GITHUB_SVG, 8.0) != OK or image.is_empty():
		return null
	return ImageTexture.create_from_image(image)


func _bdr_open_github() -> void :
	GameSession.play_sfx("ui_select")
	OS.shell_open(BDR_GITHUB_URL)
