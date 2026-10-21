extends CanvasLayer
## Dice Rush Extended - coop interface in the game: connecting screen, coop button + panel
## (status, Steam invite, leave) and the cursor of the other player (P1 / P2).

const I18N := preload("res://bdr/core/i18n.gd")
const UIKit := preload("res://bdr/ui/ui_kit.gd")
const CoopScript := preload("res://bdr/net/coop.gd")
const ICON := "res://bdr/art/ui/coop_icon.png"
const P1_CURSOR := "res://bdr/art/ui/p1_cursor.png"
const P2_CURSOR := "res://bdr/art/ui/p2_cursor.png"

var game: Node
var main: Node
var _connecting: Control
var _connecting_label: Label
var _button: Button
var _panel: Panel
var _status_label: Label
var _host_button: Button
var _invite_button: Button
var _leave_button: Button
var _cursor: Control


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	layer = 199
	process_mode = Node.PROCESS_MODE_ALWAYS
	_build_button()
	_build_panel()
	_build_cursor()
	game.coop.status_changed.connect(_refresh)
	_refresh()


# ---------------------------------------------------------------- connecting screen (client)
func show_connecting(address: String) -> void:
	if not is_instance_valid(_connecting):
		_connecting = Control.new()
		_connecting.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_connecting.mouse_filter = Control.MOUSE_FILTER_STOP
		_connecting.z_index = 50
		add_child(_connecting)
		var dim := ColorRect.new()
		dim.color = Color(0.01, 0.02, 0.05, 0.92)
		dim.position = Vector2.ZERO
		dim.size = Vector2(1920, 1080)
		dim.mouse_filter = Control.MOUSE_FILTER_STOP
		_connecting.add_child(dim)
		var box := UIKit.panel(_connecting, Rect2(560, 380, 800, 300))
		UIKit.texture(box, ICON, Rect2(30, 30, 110, 110))
		_connecting_label = UIKit.paragraph(box, "", Rect2(160, 30, 610, 130), 18, HORIZONTAL_ALIGNMENT_LEFT, Color.WHITE)
		UIKit.button(box, I18N.t("coop.cancel"), Rect2(250, 190, 300, 74), _cancel_connecting, 16, Color("4a1420"), Color("c94a5a"))
	_connecting_label.text = I18N.f("coop.connecting", {"address": address})
	UIKit.fit(_connecting_label)
	_connecting.visible = true


func hide_connecting() -> void:
	if is_instance_valid(_connecting):
		_connecting.visible = false


func _cancel_connecting() -> void:
	game.coop.stop(false)
	CoopScript.clear_launch()
	get_tree().paused = false
	get_tree().change_scene_to_file(main.START_MENU_SCENE)


# ---------------------------------------------------------------- coop button + panel
func _build_button() -> void:
	_button = Button.new()
	_button.position = Vector2(208, 24)
	_button.size = Vector2(82, 62)
	_button.focus_mode = Control.FOCUS_NONE
	_button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_button.add_theme_stylebox_override("normal", UIKit.style(Color("0d1c38"), Color("d49316"), 3, 10))
	_button.add_theme_stylebox_override("hover", UIKit.style(Color("15294d"), Color("ffd166"), 3, 10))
	_button.add_theme_stylebox_override("pressed", UIKit.style(Color("0a1528"), Color("ffe59a"), 3, 10))
	_button.pressed.connect(_toggle_panel)
	_button.mouse_entered.connect(func() -> void: game.show_text_tooltip(I18N.t("coop.button_tip"), 110.0))
	_button.mouse_exited.connect(game.hide_tooltip)
	add_child(_button)
	UIKit.texture(_button, ICON, Rect2(13, 3, 56, 56))


func _build_panel() -> void:
	_panel = UIKit.panel(self, Rect2(208, 96, 620, 360))
	_panel.visible = false
	UIKit.label(_panel, I18N.t("coop.title"), Rect2(24, 12, 480, 50), 20, HORIZONTAL_ALIGNMENT_LEFT, Color("ffd166"))
	UIKit.button(_panel, "X", Rect2(546, 12, 56, 50), _toggle_panel, 16)
	_status_label = UIKit.paragraph(_panel, "", Rect2(24, 70, 572, 150), 13, HORIZONTAL_ALIGNMENT_LEFT, Color("e8edf5"))
	_host_button = UIKit.button(_panel, I18N.t("coop.host_now"), Rect2(24, 236, 280, 52), _host_now, 13, Color("0b3d24"), Color("3fbf6a"))
	_invite_button = UIKit.button(_panel, I18N.t("coop.invite"), Rect2(316, 236, 280, 52), _invite, 13)
	_leave_button = UIKit.button(_panel, I18N.t("coop.leave"), Rect2(24, 296, 572, 48), _leave, 13, Color("4a1420"), Color("c94a5a"))


func _toggle_panel() -> void:
	_panel.visible = not _panel.visible
	GameSession.play_sfx("ui_select")
	_refresh()


func _refresh() -> void:
	if not is_instance_valid(_status_label):
		return
	var coop = game.coop
	var lines: Array[String] = []
	if coop.is_host():
		lines.append(I18N.f("coop.status_host", {"port": str(coop.host_port)}))
		var addresses: Array[String] = coop.local_addresses()
		lines.append(I18N.f("coop.your_ips", {"ips": ", ".join(addresses) if not addresses.is_empty() else "-"}))
		if coop.is_active():
			lines.append(I18N.f("coop.partner_connected", {"name": coop.partner_name}))
		else:
			lines.append(I18N.t("coop.waiting"))
	elif coop.role == "client":
		lines.append(I18N.f("coop.status_client", {"address": coop.host_address}))
	else:
		lines.append(I18N.t("coop.status_off"))
		lines.append(I18N.t("coop.hint_host"))
	_status_label.text = "\n".join(lines)
	UIKit.fit(_status_label)
	_host_button.visible = coop.role == ""
	_invite_button.visible = coop.is_host()
	_invite_button.disabled = not coop.steam_available()
	_invite_button.tooltip_text = "" if coop.steam_available() else I18N.t("coop.steam_missing")
	_leave_button.visible = coop.role != ""
	_leave_button.text = I18N.t("coop.leave") if coop.role == "client" else I18N.t("coop.stop_host")
	UIKit.fit(_leave_button)


func _host_now() -> void:
	game.coop.start_host(CoopScript.DEFAULT_PORT)
	_refresh()


func _invite() -> void:
	if not game.coop.steam_invite():
		game.toast(I18N.t("coop.steam_missing"))


func _leave() -> void:
	if game.coop.role == "client":
		game.coop_leave("main_menu")
		return
	game.coop.stop()
	_refresh()


# ---------------------------------------------------------------- the other player's cursor
func _build_cursor() -> void:
	_cursor = _make_cursor()


## A cursor drawn in the game world (same coordinates as the mouse): design + P1 / P2 tag.
func _make_cursor() -> Control:
	var cursor := Control.new()
	cursor.size = Vector2(80, 70)
	cursor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cursor.z_index = 4000
	cursor.visible = false
	main.add_child.call_deferred(cursor)
	var icon := UIKit.texture(cursor, P2_CURSOR, Rect2(0, 0, 58, 58))
	var tag := UIKit.panel(cursor, Rect2(40, 44, 54, 32), Color(0.02, 0.03, 0.08, 0.85), Color("5dd0ff"), 2, 8)
	tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var label := UIKit.label(tag, "P2", Rect2(0, 0, 54, 32), 15, HORIZONTAL_ALIGNMENT_CENTER, Color("5dd0ff"))
	cursor.set_meta("icon_node", icon)
	cursor.set_meta("label", label)
	cursor.set_meta("tag", tag)
	return cursor


## Shows `cursor` at a world position with a mouse design and the tag of player 1 or 2.
func _show_cursor(cursor: Control, world_position: Vector2, design: int, player_one: bool) -> void:
	var icon: TextureRect = cursor.get_meta("icon_node")
	var wanted := "%s#%d" % ["P1" if player_one else "P2", design]
	if str(cursor.get_meta("icon", "")) != wanted:
		cursor.set_meta("icon", wanted)
		var design_texture: Texture2D = game.shop.cursor_texture(design)
		if design_texture != null:
			# same size as the real mouse cursor (68 px high), click point on the position
			var design_scale := 68.0 / float(maxi(1, design_texture.get_height()))
			icon.texture = design_texture
			icon.size = Vector2(design_texture.get_width(), design_texture.get_height()) * design_scale
			icon.position = Vector2(4, 4) - game.shop.cursor_hotspot(design) * design_scale
		else:
			icon.texture = CleanTextureLoader.load_texture(P1_CURSOR if player_one else P2_CURSOR)
			icon.size = Vector2(58, 58)
			icon.position = Vector2.ZERO
		var label: Label = cursor.get_meta("label")
		label.text = "P1" if player_one else "P2"
		var tint := Color("ffd166") if player_one else Color("5dd0ff")
		label.add_theme_color_override("font_color", tint)
		(cursor.get_meta("tag") as Panel).add_theme_stylebox_override("panel", UIKit.style(Color(0.02, 0.03, 0.08, 0.85), tint, 2, 8))
	cursor.position = world_position - Vector2(4, 4)
	cursor.visible = true


## Screenshots only (test harness): a screenshot of the game does not contain the system mouse,
## so this also draws THIS player's own cursor like the partner's one.
var show_local_cursor := false
var _local_cursor: Control


## The coop button sits right of the achievements (trophy) button. That button lives on the
## table's canvas, which is shifted on wide windows, so its real screen position is used.
func _align_to_trophy() -> void:
	var menu = main.get("menu_controller")
	if menu == null or not is_instance_valid(menu):
		return
	var trophy = menu.get("achievement_button")
	if trophy == null or not is_instance_valid(trophy) or not trophy.is_inside_tree():
		return
	var to_screen: Transform2D = trophy.get_global_transform_with_canvas()
	var top_left: Vector2 = to_screen * Vector2.ZERO
	var bottom_right: Vector2 = to_screen * trophy.size
	_button.position = Vector2(bottom_right.x + 10.0, top_left.y)
	_button.size = Vector2(maxf(40.0, bottom_right.x - top_left.x), maxf(40.0, bottom_right.y - top_left.y))
	_panel.position = Vector2(_button.position.x, bottom_right.y + 10.0)


func _process(_delta: float) -> void:
	var coop = game.coop
	var in_game: bool = bool(main.game_started) and not coop.local_in_menu()
	_button.visible = in_game or _panel.visible
	if _button.visible:
		_align_to_trophy()
	if show_local_cursor and coop.is_active():
		if _local_cursor == null:
			_local_cursor = _make_cursor()
		elif _local_cursor.is_inside_tree():
			_show_cursor(_local_cursor, coop.local_cursor_position(), game.shop.local_cursor_design(), coop.is_host())
	elif _local_cursor != null:
		_local_cursor.visible = false
	if not coop.is_active():
		_cursor.visible = false
		return
	var world_position: Vector2 = coop.partner_cursor if coop.is_host() else coop.host_cursor
	if world_position.x < 0.0:
		_cursor.visible = false
		return
	var host_side: bool = coop.is_host()
	var design: int = coop.partner_cursor_design if host_side else coop.host_cursor_design
	_show_cursor(_cursor, world_position, design, not host_side)
