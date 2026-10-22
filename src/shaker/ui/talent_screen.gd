extends "res://shaker/ui/screen_base.gd"
## Talent tree: paid with talent points (from the gumball machine) and money.

const NODE_SIZE := 84.0
const ORIGIN := Vector2(92, 140)
const STEP := Vector2(162, 99)

var tree_layer: Control
var nodes: Dictionary = {}        # id -> {button, icon, state}
var selected := ""
var info_name: Label
var info_text: Label
var info_cost: Label
var learn_button: Button
var tp_label: Label


func _build() -> void:
	var panel := frame(I18N.t("talents.title"))
	tp_label = Kit.label(panel, "", Rect2(30, 70, 700, 34), 15, HORIZONTAL_ALIGNMENT_LEFT, Kit.GOOD)
	tree_layer = Control.new()
	tree_layer.position = Vector2.ZERO
	tree_layer.size = Vector2(1840, 1024)
	tree_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(tree_layer)
	tree_layer.draw.connect(_draw_lines)
	for talent in Data.talents:
		_make_node(talent)
	# info panel
	var info := Kit.panel(panel, Rect2(30, 846, 1780, 160), Kit.PANEL_LIGHT, Kit.GOLD, 3, 16)
	info_name = Kit.label(info, "", Rect2(24, 10, 900, 44), 22, HORIZONTAL_ALIGNMENT_LEFT, Kit.GOLD_LIGHT)
	info_text = Kit.paragraph(info, "", Rect2(24, 54, 1100, 96), 14, HORIZONTAL_ALIGNMENT_LEFT, Kit.TEXT)
	info_cost = Kit.label(info, "", Rect2(1150, 14, 600, 50), 18, HORIZONTAL_ALIGNMENT_RIGHT, Kit.TEXT)
	learn_button = Kit.button(info, I18N.t("talents.learn"), Rect2(1420, 78, 330, 66), _learn, 18, Color("2f6a3c"), Kit.GOLD)
	_select(_first_available())
	refresh()


func _node_center(talent: Dictionary) -> Vector2:
	return ORIGIN + Vector2(float(talent.col) * STEP.x, float(talent.row) * STEP.y) + Vector2(NODE_SIZE, NODE_SIZE) * 0.5


func _make_node(talent: Dictionary) -> void:
	var center := _node_center(talent)
	var button := Button.new()
	button.position = center - Vector2(NODE_SIZE, NODE_SIZE) * 0.5
	button.size = Vector2(NODE_SIZE, NODE_SIZE)
	button.focus_mode = Control.FOCUS_ALL
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.pressed.connect(_on_node_pressed.bind(str(talent.id)))
	button.mouse_entered.connect(_select.bind(str(talent.id)))
	tree_layer.add_child(button)
	var icon_tex := icon_texture(str(talent.icon), 64)
	var inset := 10.0
	var icon := Kit.texture(button, icon_tex, Rect2(inset, inset, NODE_SIZE - inset * 2, NODE_SIZE - inset * 2), true)
	if str(talent.icon).begins_with("die:") or str(talent.icon) == "cube":
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	nodes[str(talent.id)] = {"button": button, "icon": icon, "state": ""}


func _talent_state(talent_id: String) -> String:
	var state: Dictionary = game.state
	if talent_id in state.talents:
		return "owned"
	var block := Rules.talent_block(state, talent_id)
	if not block.is_empty():
		return "locked" if block == "talents.locked" else "blocked"
	var cost := Rules.talent_cost(state, game.stats, talent_id)
	if int(state.tp) >= int(cost[0]) and float(state.money) >= float(cost[1]):
		return "ready"
	return "open"


func refresh() -> void:
	super.refresh()
	var state: Dictionary = game.state
	Kit.set_text(tp_label, I18N.t("hud.tp") + ": " + NumFmt.compact(int(state.tp)))
	var changed := false
	for talent_id in nodes:
		var entry: Dictionary = nodes[talent_id]
		var now := _talent_state(talent_id)
		if now == entry.state:
			continue
		entry.state = now
		changed = true
		var button: Button = entry.button
		var fill := Color("221432")
		var border := Color("4a3a5e")
		var alpha := 1.0
		match now:
			"owned":
				fill = Color("4a2c12")
				border = Kit.GOLD_LIGHT
			"ready":
				fill = Color("173a24")
				border = Kit.GOOD
			"open":
				fill = Color("2a1840")
				border = Color("a58ad1")
			"blocked":
				fill = Color("221432")
				border = Color("6a5a7e")
				alpha = 0.75
			_:
				alpha = 0.42
		for style_name in ["normal", "hover", "pressed", "focus"]:
			var box := Kit.style(fill.lightened(0.12) if style_name == "hover" else fill, border if style_name != "hover" else border.lightened(0.25), 4, 14)
			if style_name == "focus":
				box = Kit.style(Color.TRANSPARENT, Kit.GOLD_LIGHT, 3, 14)
			button.add_theme_stylebox_override(style_name, box)
		(entry.icon as TextureRect).modulate = Color(1, 1, 1, alpha)
	if changed:
		tree_layer.queue_redraw()
	_update_info()


func _draw_lines() -> void:
	var owned: Array = game.state.talents
	for talent in Data.talents:
		for parent_id in talent.parents:
			var parent: Dictionary = Data.talents_by_id.get(str(parent_id), {})
			if parent.is_empty():
				continue
			var both := str(talent.id) in owned and str(parent_id) in owned
			var reachable := str(parent_id) in owned
			var color := Kit.GOLD if both else (Color("a58ad1") if reachable else Color("3d2d50"))
			tree_layer.draw_line(_node_center(parent), _node_center(talent), Color(0, 0, 0, 0.6), 9.0)
			tree_layer.draw_line(_node_center(parent), _node_center(talent), color, 5.0)


func _first_available() -> String:
	for talent in Data.talents:
		var now := _talent_state(str(talent.id))
		if now == "ready" or now == "open":
			return str(talent.id)
	return "shaker"


func _select(talent_id: String) -> void:
	selected = talent_id
	_update_info()


func _on_node_pressed(talent_id: String) -> void:
	if selected == talent_id and _talent_state(talent_id) == "ready":
		_learn()
		return
	_select(talent_id)


func _update_info() -> void:
	if selected.is_empty() or not Data.talents_by_id.has(selected):
		return
	var talent: Dictionary = Data.talents_by_id[selected]
	var state: Dictionary = game.state
	Kit.set_text(info_name, I18N.upper(I18N.t("talent.%s.name" % selected)))
	var lines: Array[String] = []
	for effect in talent.effects:
		lines.append(stat_line(str(effect[0]), float(effect[1])))
	if Rules.is_slot_talent(talent):
		lines.append(I18N.t("talents.new_die"))
		lines.append(I18N.f("talents.dice_now", {"v": (state.dice as Array).size()}))
	if selected == "shaker":
		lines = [I18N.f("talents.points", {"v": int(state.tp)})]
	var now := _talent_state(selected)
	match now:
		"locked":
			lines.append(I18N.t("talents.locked"))
		"blocked":
			lines.append(I18N.t(Rules.talent_block(state, selected)))
	Kit.set_text(info_text, "\n".join(lines))
	if now == "owned" or selected == "shaker":
		Kit.set_text(info_cost, I18N.t("talents.learned"))
		info_cost.add_theme_color_override("font_color", Kit.GOLD_LIGHT)
		learn_button.visible = false
		return
	var cost := Rules.talent_cost(state, game.stats, selected)
	var parts: Array[String] = []
	if int(cost[0]) > 0:
		parts.append("%s: %s" % [I18N.t("hud.tp"), NumFmt.compact(int(cost[0]))])
	if float(cost[1]) > 0.0:
		parts.append(I18N.money(float(cost[1])))
	Kit.set_text(info_cost, " + ".join(parts))
	var affordable := int(state.tp) >= int(cost[0]) and float(state.money) >= float(cost[1])
	info_cost.add_theme_color_override("font_color", Kit.GOOD if affordable else Kit.BAD)
	learn_button.visible = now != "locked" and now != "blocked"
	learn_button.disabled = now != "ready"


func _learn() -> void:
	if selected.is_empty():
		return
	var error: String = game.call("learn_talent", selected)
	if not error.is_empty():
		game.call("toast", I18N.t(error), Kit.BAD)
		return
	for entry in nodes.values():
		entry.state = ""
	refresh()
