extends Control
## Dice Shaker - the game scene: a fortune teller's table with a glass ball full of dice.
## Click (or hold) the ball to shake the dice, earn money, level the dice up, buy talent points
## at the gumball machine and spend everything in the talent tree, Lucky Cube, tarot and shop.

const Data := preload("res://shaker/game/data.gd")
const Rules := preload("res://shaker/game/rules.gd")
const Ball := preload("res://shaker/game/ball.gd")
const Save := preload("res://shaker/core/save.gd")
const I18N := preload("res://shaker/core/i18n.gd")
const NumFmt := preload("res://shaker/core/numfmt.gd")
const Tex := preload("res://shaker/core/tex.gd")
const Kit := preload("res://shaker/ui/kit.gd")
const Sound := preload("res://shaker/core/sound.gd")
const TalentScreen := preload("res://shaker/ui/talent_screen.gd")
const LuckyScreen := preload("res://shaker/ui/lucky_screen.gd")
const TarotScreen := preload("res://shaker/ui/tarot_screen.gd")
const ShopScreen := preload("res://shaker/ui/shop_screen.gd")
const BookScreen := preload("res://shaker/ui/book_screen.gd")
const PauseScreen := preload("res://shaker/ui/pause_screen.gd")
const ScreenBase := preload("res://shaker/ui/screen_base.gd")
const GitHubButton := preload("res://bdr/ui/github_button.gd")

const START_MENU := "res://scenes/start_menu.tscn"
const ART := "res://shaker/art/"
const SCALE := 4
const BACKGROUND := "res://assets/art/фон.png"
const ICON_TALENTS := "res://assets/art/hud/talent_tree_icon.png"
const ICON_LUCKY := "res://assets/art/lucky_dice/lucky_cube_placeholder.webp"
const ICON_TAROT := "res://assets/art/dog_shrine/tarot_grimoire_icon.png"
const ICON_BOOK := "res://assets/art/dog_shrine/grimoire_icon.png"
## the gauntlet rack on the right side of the screen (design coordinates)
const RACK := Rect2(1712, 168, 196, 772)

var slot := 1
var state: Dictionary = {}
var stats: Dictionary = {}
var rng := RandomNumberGenerator.new()
var layout: Dictionary = {}

# scene
var stage: Control
var world: Node2D
var cloth_sprite: Sprite2D
var cushion_sprite: Sprite2D
var ball_root: Node2D
var ball: Ball
var ball_front: Sprite2D
var hand_left: Sprite2D
var hand_right: Sprite2D
var hand_frames: Array = []
var hand_base: Array[Vector2] = []
var flames: Array = []
var flame_frames: Array = []
var gum_machine: Sprite2D
var gum_crank: Sprite2D
var crank_frames: Array = []
var ball_center := Vector2(960, 432)
var ball_radius := 224.0

# HUD
var hud: Control
var money_label: Label
var income_label: Label
var tp_label: Label
var tp_value: Label
var gum_price_label: Label
var hint_label: Label
var auto_label: Label
var dice_bar: Control
var dice_slots: Array = []
var tooltip: PanelContainer
var tip_text: RichTextLabel
var popup_layer: Control
var screen: Control
var screen_name := ""

# game flow
var shaking := false
var shake_left := 0.0
var shake_manual := true
var pending_result: Dictionary = {}
var queued_shake := false
var auto_timer := 0.0
var last_shake_time := -100.0
var clock := 0.0
var autosave_timer := 0.0
var market_timer := 0.0
var income_window: Array = []        # [time, money]
var income_per_sec := 0.0
var hud_timer := 0.0
var holding_ball := false
var gum_queue := 0
var gum_busy := false
var hand_frame_timer := 0.0
var flame_timer := 0.0
var hand_phase := 0.0
var conjure := 0.0
var wobble := 0.0
var leaving := false
var manual_shakes := 0
var machine_tip := false
# gauntlet rack (right side) and random events (every 5 minutes)
var rack_icon: TextureRect
var rack_name: Label
var rack_effects: Label
var rack_grid: GridContainer
var rack_signature := ""
var event_panel: Panel
var event_label: Label
var next_event_label: Label


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)
	rng.randomize()
	Data.ensure()
	Kit.setup()
	slot = clampi(int(GameSession.get_meta(&"shaker_active_slot", 1)), 1, Save.SLOT_COUNT)
	var loaded := Save.read(slot)
	state = Rules.sanitize(loaded) if not loaded.is_empty() else Rules.new_state()
	_load_layout()
	_sort_dice()
	stats = _compute_stats()
	_build_background()
	_build_stage()
	_build_hud()
	_refresh_table_design()
	_refresh_dice(true)
	_apply_cursor()
	_refresh_hud(true)
	resized.connect(_layout_stage)
	_layout_stage()
	if not bool(state.get("hint_done", false)):
		hint_label.visible = true
	Save.write(slot, state)


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_EXIT_TREE:
		if not state.is_empty() and not leaving:
			Save.write(slot, state)
	if what == NOTIFICATION_EXIT_TREE:
		_restore_cursor()


# =========================================================================================== layout
func _load_layout() -> void:
	layout = {
		"native": [480, 270], "scale": 4,
		"table": [0, 170, 480, 100], "cloth": [0, 170, 480, 100], "cushion": [156, 170, 168, 52],
		"stand": [178, 154, 124, 36], "ball": [176, 44, 128, 128],
		"ball_inner": {"center": [240, 108], "radius": 56},
		"hand_left": [50, 62, 112, 88], "hand_right": [318, 62, 112, 88],
		"gumball_machine": [14, 70, 72, 140], "gumball_chute": [52, 196], "gumball_slot": [58, 150],
		"candles": [[392, 160], [414, 170]], "flame_offset": [4, -14],
	}
	var path := ART + "scene/layout.json"
	if FileAccess.file_exists(path):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		if parsed is Dictionary:
			for key in parsed:
				layout[key] = parsed[key]


func _rect(key: String) -> Rect2:
	var r: Array = layout.get(key, [0, 0, 0, 0])
	return Rect2(float(r[0]) * SCALE, float(r[1]) * SCALE, float(r[2]) * SCALE, float(r[3]) * SCALE)


func _point(key: String) -> Vector2:
	var p: Array = layout.get(key, [0, 0])
	return Vector2(float(p[0]), float(p[1])) * SCALE


func _sprite(parent: Node, path: String, position_native: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.centered = false
	sprite.texture = Tex.get_tex(path)
	sprite.scale = Vector2(SCALE, SCALE)
	sprite.position = position_native * SCALE
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(sprite)
	return sprite


func _build_background() -> void:
	var back := TextureRect.new()
	back.set_anchors_preset(Control.PRESET_FULL_RECT)
	back.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	back.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	back.texture = CleanTextureLoader.load_texture(BACKGROUND)
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(back)
	var shade := ColorRect.new()
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.05, 0.0, 0.08, 0.35)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)


func _build_stage() -> void:
	stage = Control.new()
	stage.size = Vector2(1920, 1080)
	stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(stage)
	world = Node2D.new()
	stage.add_child(world)
	var order: Array = layout.get("draw_order", ["hand_left", "hand_right", "table", "cloth", "gumball_machine", "gumball_crank",
			"candles", "flames", "cushion", "ball_back", "dice", "ball_front", "stand"])
	for part in order:
		_build_part(str(part))
	popup_layer = Control.new()
	popup_layer.size = Vector2(1920, 1080)
	popup_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stage.add_child(popup_layer)


func _native(key: String) -> Vector2:
	var r: Array = layout.get(key, [0, 0])
	return Vector2(float(r[0]), float(r[1]))


func _build_part(part: String) -> void:
	match part:
		"hand_left":
			hand_frames.append([Tex.get_tex(ART + "scene/hand_left.png"), Tex.get_tex(ART + "scene/hand_left_b.png")])
			hand_left = _sprite(world, ART + "scene/hand_left.png", _native("hand_left"))
			hand_base.append(hand_left.position)
		"hand_right":
			hand_frames.append([Tex.get_tex(ART + "scene/hand_right.png"), Tex.get_tex(ART + "scene/hand_right_b.png")])
			hand_right = _sprite(world, ART + "scene/hand_right.png", _native("hand_right"))
			hand_base.append(hand_right.position)
		"table":
			_sprite(world, ART + "scene/table.png", _native("table"))
		"cloth":
			cloth_sprite = _sprite(world, ART + "scene/cloth_0.png", _native("cloth"))
		"cushion":
			cushion_sprite = _sprite(world, ART + "scene/cushion_0.png", _native("cushion"))
		"gumball_machine":
			gum_machine = _sprite(world, ART + "scene/gumball_machine.png", _native("gumball_machine"))
		"gumball_crank":
			for i in range(4):
				crank_frames.append(Tex.get_tex(ART + "scene/gumball_crank_%d.png" % i))
			gum_crank = _sprite(world, ART + "scene/gumball_crank_0.png", _native("gumball_machine"))
		"candles":
			var sprites: Array = layout.get("candle_sprites", [])
			var candles: Array = layout.get("candles", [])
			for i in candles.size():
				var sprite_name := str(sprites[i]) if i < sprites.size() else "candle"
				_sprite(world, ART + "scene/%s.png" % sprite_name, Vector2(float(candles[i][0]), float(candles[i][1])))
		"flames":
			for i in range(3):
				flame_frames.append(Tex.get_tex(ART + "scene/flame_%d.png" % i))
			var offset: Array = layout.get("flame_offset", [4, -14])
			for candle in layout.get("candles", []):
				var at := Vector2(float(candle[0]) + float(offset[0]), float(candle[1]) + float(offset[1]))
				flames.append(_sprite(world, ART + "scene/flame_0.png", at))
		"ball_back":
			_build_ball()
		"stand":
			_sprite(world, ART + "scene/stand.png", _native("stand"))


## The glass ball (back layer, dice, front layer) wobbles around the point where it sits on the stand.
func _build_ball() -> void:
	var ball_rect := _rect("ball")
	var inner: Dictionary = layout.get("ball_inner", {})
	var inner_center: Array = inner.get("center", [240, 108])
	ball_center = Vector2(float(inner_center[0]), float(inner_center[1])) * SCALE
	ball_radius = float(inner.get("radius", 56)) * SCALE
	ball_root = Node2D.new()
	world.add_child(ball_root)
	var pivot := Vector2(ball_center.x, ball_rect.end.y - 6.0 * SCALE)
	ball_root.position = pivot
	var ball_layer := Node2D.new()
	ball_layer.position = -pivot
	ball_root.add_child(ball_layer)
	_sprite(ball_layer, ART + "scene/ball_back.png", ball_rect.position / SCALE)
	ball = Ball.new()
	ball.center = ball_center
	ball.radius = ball_radius
	var dice_floor: Dictionary = layout.get("dice_floor", {})
	if dice_floor.has("center"):
		ball.floor_y = (float(dice_floor.center[1]) + float(dice_floor.get("ry", 8))) * SCALE
	ball.font = Kit.pixel_font
	ball_layer.add_child(ball)
	ball_front = _sprite(ball_layer, ART + "scene/ball_front.png", ball_rect.position / SCALE)


func _layout_stage() -> void:
	var view := get_viewport_rect().size
	var origin := Vector2(maxf(0.0, (view.x - 1920.0) * 0.5), maxf(0.0, (view.y - 1080.0) * 0.5))
	if stage:
		stage.position = origin
	if hud:
		hud.position = origin


# ============================================================================================== HUD
func _build_hud() -> void:
	hud = Control.new()
	hud.size = Vector2(1920, 1080)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(hud)
	# money
	money_label = Kit.label(hud, "0$", Rect2(560, 18, 800, 84), 52, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT, true)
	income_label = Kit.label(hud, "", Rect2(660, 100, 600, 34), 15, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)
	# menu button
	var menu_button := Kit.button(hud, I18N.t("hud.menu"), Rect2(28, 24, 170, 64), _open_pause, 16)
	menu_button.focus_mode = Control.FOCUS_NONE
	# screen buttons (top right)
	var buttons := [
		["hud.talents", ICON_TALENTS, "talents"], ["hud.lucky", ICON_LUCKY, "lucky"], ["hud.tarot", ART + "tarot/back.png", "tarot"],
		["hud.shop", ART + "gauntlets/gauntlet_6.png", "shop"], ["hud.book", ICON_BOOK, "book"],
	]
	for i in buttons.size():
		var entry: Array = buttons[i]
		_hud_icon_button(Rect2(1148 + i * 154, 16, 146, 132), str(entry[1]), I18N.t(str(entry[0])), _open_screen.bind(str(entry[2])))
	# talent points and the gumball machine price
	var machine := _rect("gumball_machine")
	tp_label = Kit.label(hud, I18N.t("hud.tp"), Rect2(machine.position.x - 40, machine.position.y - 96, machine.size.x + 80, 30), 13, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)
	tp_value = Kit.label(hud, "0", Rect2(machine.position.x - 40, machine.position.y - 68, machine.size.x + 80, 56), 34, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOOD, true)
	var price_panel := Kit.panel(hud, Rect2(machine.position.x - 10, machine.end.y + 4, machine.size.x + 20, 46), Color("2a0f1ce8"), Kit.GOLD, 3, 12)
	price_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	gum_price_label = Kit.label(price_panel, "", Rect2(6, 2, machine.size.x + 8, 42), 17, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT)
	# hints
	hint_label = Kit.label(hud, I18N.t("hud.hint"), Rect2(460, 150, 1000, 40), 17, HORIZONTAL_ALIGNMENT_CENTER, Kit.TEXT)
	hint_label.visible = false
	auto_label = Kit.label(hud, "", Rect2(660, 132, 600, 26), 11, HORIZONTAL_ALIGNMENT_CENTER, Kit.MUTED)
	# dice bar at the bottom
	dice_bar = Control.new()
	dice_bar.position = Vector2(0, 952)
	dice_bar.size = Vector2(1920, 120)
	dice_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(dice_bar)
	_build_rack()
	_build_event_panel()
	GitHubButton.make(hud, Rect2(1812, 972, 76, 76))
	# tooltip
	tooltip = PanelContainer.new()
	tooltip.add_theme_stylebox_override("panel", Kit.style(Color("12081ef5"), Kit.GOLD, 3, 12))
	tooltip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tooltip.z_index = 50
	tip_text = RichTextLabel.new()
	tip_text.bbcode_enabled = true
	tip_text.fit_content = true
	tip_text.scroll_active = false
	tip_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tip_text.custom_minimum_size = Vector2(420, 0)
	tip_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tip_text.add_theme_font_override("normal_font", Kit.pixel_font)
	tip_text.add_theme_font_override("bold_font", Kit.pixel_font)
	tip_text.add_theme_font_size_override("normal_font_size", 13)
	tip_text.add_theme_font_size_override("bold_font_size", 15)
	tip_text.add_theme_constant_override("line_separation", 5)
	tooltip.add_child(tip_text)
	tooltip.visible = false
	add_child(tooltip)


func _hud_icon_button(rect: Rect2, icon_path: String, text: String, callback: Callable) -> Button:
	var button := Kit.button(hud, "", rect, callback, 12, Color("1d0d30e0"), Kit.GOLD)
	button.focus_mode = Control.FOCUS_NONE
	var icon_tex: Texture2D = Tex.square(icon_path, 128) if not icon_path.begins_with(ART) else Tex.get_tex(icon_path)
	var icon := Kit.texture(button, icon_tex, Rect2((rect.size.x - 74.0) * 0.5, 8, 74, 80), not icon_path.ends_with(".webp"))
	icon.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR if not icon_path.begins_with(ART) else CanvasItem.TEXTURE_FILTER_NEAREST
	Kit.label(button, text, Rect2(4, 92, rect.size.x - 8, 34), 11, HORIZONTAL_ALIGNMENT_CENTER, Kit.TEXT)
	return button


func _refresh_hud(force: bool = false) -> void:
	Kit.set_text(money_label, I18N.money(float(state.money)))
	Kit.set_text(income_label, I18N.f("hud.per_sec", {"v": NumFmt.compact(income_per_sec)}) if income_per_sec > 0.0 else "")
	Kit.set_text(tp_value, NumFmt.compact(int(state.tp)))
	Kit.set_text(gum_price_label, I18N.money(Rules.gumball_price(state, stats)))
	var auto := Rules.auto_interval(stats)
	Kit.set_text(auto_label, I18N.f("hud.auto", {"v": snappedf(auto, 0.1)}) if auto > 0.0 else "")
	_refresh_dice_bar(force)
	_refresh_rack()
	_refresh_event_panel()


func _refresh_dice_bar(rebuild: bool) -> void:
	var dice: Array = state.dice
	if rebuild or dice_slots.size() != dice.size():
		for child in dice_bar.get_children():
			child.queue_free()
		dice_slots.clear()
		var width := 136.0
		var total := width * dice.size()
		var x0 := (1920.0 - total) * 0.5
		for i in dice.size():
			var card := Panel.new()
			card.position = Vector2(x0 + i * width + 4, 0)
			card.size = Vector2(width - 8, 116)
			card.add_theme_stylebox_override("panel", Kit.style(Color("1a0b2ad8"), Kit.GOLD, 2, 12))
			card.mouse_filter = Control.MOUSE_FILTER_PASS
			card.mouse_entered.connect(_show_die_tooltip.bind(i))
			card.mouse_exited.connect(_hide_tooltip)
			dice_bar.add_child(card)
			var icon := Kit.texture(card, null, Rect2((width - 8) * 0.5 - 29, 2, 58, 58), false)
			var level := Kit.label(card, "", Rect2(2, 58, width - 12, 34), 13, HORIZONTAL_ALIGNMENT_CENTER, Kit.TEXT)
			var xp := Kit.bar(card, Rect2(12, 94, width - 32, 13), Color("8f5bd6"))
			dice_slots.append({"card": card, "icon": icon, "level": level, "xp": xp, "id": ""})
	for i in dice.size():
		var die: Dictionary = dice[i]
		var widgets: Dictionary = dice_slots[i]
		var def := Data.die(str(die.id))
		if widgets.id != str(die.id):
			widgets.id = str(die.id)
			(widgets.icon as TextureRect).texture = Tex.square(str(def.art), 64)
			(widgets.card as Panel).add_theme_stylebox_override("panel", Kit.style(Color("1a0b2ad8"), Data.rarity_color(str(def.rarity)), 3, 12))
		var max_level := int(Data.b("max_level", 100))
		var level := int(die.level)
		Kit.set_text(widgets.level, I18N.t("die.max") if level >= max_level else I18N.f("die.level", {"v": level}))
		(widgets.xp as ProgressBar).value = 1.0 if level >= max_level else clampf(float(die.xp) / Rules.xp_need(level, stats), 0.0, 1.0)


# ======================================================================================= dice & ball
func die_texture(die_id: String, size: int) -> Texture2D:
	return Tex.square(str(Data.die(die_id).get("art", "")), size)


func die_name(die_id: String) -> String:
	return I18N.die_name(Data.die(die_id))


func die_size_now() -> int:
	var count := (state.dice as Array).size()
	return int(roundf(ball_radius * (0.47 if count <= Rules.big_dice_max() else 0.33)))


## Dice are kept sorted by rarity (legendary first), then by level. Locks move with the dice.
func _sort_dice() -> void:
	var dice: Array = state.dice
	var keyed: Array = []
	for i in dice.size():
		var def := Data.die(str(dice[i].id))
		keyed.append([Data.rarity_index(str(def.rarity)), int(dice[i].level), -i, dice[i]])
	keyed.sort_custom(func(a: Array, b: Array) -> bool:
		if a[0] != b[0]:
			return a[0] > b[0]
		if a[1] != b[1]:
			return a[1] > b[1]
		return a[2] > b[2])
	var sorted: Array = []
	for entry in keyed:
		sorted.append(entry[3])
	state["dice"] = sorted


func _refresh_dice(_initial: bool = false) -> void:
	var size := die_size_now()
	var textures: Array = []
	for die in state.dice:
		textures.append(die_texture(str(die.id), size))
	ball.set_dice(textures, float(size))


func effect_text(def: Dictionary) -> String:
	var params: Dictionary = (def.get("p", {}) as Dictionary).duplicate()
	if params.has("rarity"):
		params["rarity"] = I18N.t("rarity." + str(params.rarity))
	return I18N.f("fx." + str(def.get("fx", "none")), params)


func faces_text(def: Dictionary) -> String:
	var faces: Array = def.get("faces", [])
	if faces == [1, 2, 3, 4, 5, 6]:
		return ""
	var unique: Array = []
	for face in faces:
		if not unique.has(face):
			unique.append(face)
	if str(def.fx) != "pi":
		unique.sort()
	var parts: Array[String] = []
	for face in unique.slice(0, 12):
		parts.append(str(face))
	return I18N.f("die.faces", {"v": " ".join(parts) + ("…" if unique.size() > 12 else "")})


## Tooltip text (bbcode) for a die in the ball (index) or any die id.
func die_info(die_id: String, die: Dictionary = {}) -> String:
	var def := Data.die(die_id)
	var color := Data.rarity_color(str(def.rarity)).to_html(false)
	var lines: Array[String] = []
	lines.append("[b][color=#%s]%s[/color][/b]" % [color, I18N.upper(die_name(die_id))])
	lines.append("[color=#%s]%s[/color]" % [color, I18N.t("rarity." + str(def.rarity))])
	if not die.is_empty():
		var level := int(die.level)
		if level >= int(Data.b("max_level", 100)):
			lines.append(I18N.t("die.max"))
		else:
			lines.append("%s   %s" % [I18N.f("die.level", {"v": level}), I18N.f("die.xp", {"a": floorf(float(die.xp)), "b": Rules.xp_need(level, stats)})])
		lines.append("[color=#ffd77a]%s[/color]" % I18N.f("die.level_bonus", {"v": Rules.level_mult(level)}))
	lines.append(I18N.f("die.pay", {"v": float(def.pay) * Rules.rarity_mult(stats, str(def.rarity))}))
	var faces := faces_text(def)
	if not faces.is_empty():
		lines.append(faces)
	lines.append("[color=#c8b6ff]%s[/color]" % effect_text(def))
	return "\n".join(lines)


func _show_die_tooltip(index: int) -> void:
	if index < 0 or index >= (state.dice as Array).size():
		return
	var die: Dictionary = state.dice[index]
	show_tooltip(die_info(str(die.id), die))


func show_tooltip(text: String) -> void:
	tip_text.text = text
	tooltip.visible = true
	tooltip.reset_size()
	_place_tooltip()


func _hide_tooltip() -> void:
	tooltip.visible = false


func hide_tooltip() -> void:
	tooltip.visible = false


func _place_tooltip() -> void:
	if not tooltip.visible:
		return
	var mouse := get_local_mouse_position()
	var view := get_viewport_rect().size
	var size := tooltip.size
	var pos := mouse + Vector2(22, 18)
	if pos.x + size.x > view.x - 8:
		pos.x = mouse.x - size.x - 18
	if pos.y + size.y > view.y - 8:
		pos.y = view.y - size.y - 8
	tooltip.position = pos


# ============================================================================================ input
func _stage_mouse() -> Vector2:
	return stage.get_local_mouse_position()


func _on_ball(point: Vector2) -> bool:
	return point.distance_to(ball_center) <= ball_radius * 1.12


func _on_machine(point: Vector2) -> bool:
	return _rect("gumball_machine").grow(-4).has_point(point)


func _mouse_on_ball() -> bool:
	return _on_ball(_stage_mouse())


func _mouse_on_machine() -> bool:
	return _on_machine(_stage_mouse())


func _gui_input(event: InputEvent) -> void:
	if screen != null:
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		var point: Vector2 = event.position - stage.position
		if event.pressed:
			if _on_ball(point):
				holding_ball = true
				request_shake(true)
				accept_event()
			elif _on_machine(point):
				buy_gumball()
				accept_event()
		else:
			holding_ball = false
	elif event is InputEventMouseMotion and holding_ball:
		if not _on_ball(event.position - stage.position):
			holding_ball = false


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") or (event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE):
		if screen != null:
			close_screen()
		else:
			_open_pause()
		get_viewport().set_input_as_handled()
	elif screen == null and event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_SPACE:
		request_shake(true)
		get_viewport().set_input_as_handled()


# ============================================================================================ loop
func _process(delta: float) -> void:
	if state.is_empty() or leaving:
		return
	clock += delta
	state["play_time"] = float(state.get("play_time", 0.0)) + delta
	_update_events(delta)
	_animate_scene(delta)
	# shaking
	if shaking:
		shake_left -= delta
		if shake_left <= 0.0:
			_finish_shake()
	# the auto-shake counts from the start of the last shake: "every 6 s" really means every 6 s
	auto_timer += delta
	if not shaking:
		if queued_shake or (holding_ball and screen == null):
			queued_shake = false
			_start_shake(true)
		else:
			var auto := Rules.auto_interval(stats)
			if auto > 0.0 and auto_timer >= auto:
				_start_shake(false)
	# streak breaks after a pause
	if clock - last_shake_time > float(Data.b("streak_window", 3.0)) + Rules.shake_time(stats):
		state["streak"] = 0
	# crypto / stonks dice change their value
	market_timer -= delta
	if market_timer <= 0.0:
		market_timer = float(Data.b("market_period", 30.0))
		for die in state.dice:
			var def := Data.die(str(die.id))
			if str(def.fx) == "market":
				die["market"] = rng.randf_range(float(def.p.min), float(def.p.max))
	# income per second (last 30 s)
	while not income_window.is_empty() and float(income_window[0][0]) < clock - 30.0:
		income_window.pop_front()
	var window_sum := 0.0
	for entry in income_window:
		window_sum += float(entry[1])
	income_per_sec = window_sum / clampf(clock, 1.0, 30.0)
	hud_timer -= delta
	if hud_timer <= 0.0:
		hud_timer = 0.1
		_refresh_hud(false)
		if screen != null and screen.has_method("refresh"):
			screen.call("refresh")
	autosave_timer += delta
	if autosave_timer >= float(Data.b("autosave_seconds", 30.0)):
		autosave_timer = 0.0
		Save.write(slot, state)
	# hover over the dice in the ball
	if screen == null:
		var hovered: int = ball.die_at(_ball_local_mouse())
		if hovered != ball.hovered:
			ball.hovered = hovered
			ball.queue_redraw()
			if hovered >= 0:
				_show_die_tooltip(hovered)
			elif not _mouse_over_dice_bar():
				_hide_tooltip()
		var on_machine := _mouse_on_machine()
		if on_machine:
			machine_tip = true
			show_tooltip(_machine_info())
		elif machine_tip:
			machine_tip = false
			_hide_tooltip()
	_place_tooltip()
	var hand_cursor := _mouse_on_ball() or _mouse_on_machine()
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if hand_cursor and screen == null else Control.CURSOR_ARROW


func _ball_local_mouse() -> Vector2:
	var layer := ball_root.get_child(0) as Node2D
	return layer.get_local_mouse_position()


func _mouse_over_dice_bar() -> bool:
	for widgets in dice_slots:
		var card := widgets.card as Control
		if card.get_global_rect().has_point(get_global_mouse_position()):
			return true
	return false


func _animate_scene(delta: float) -> void:
	# hands slowly come closer to the ball and move back (never touching it)
	conjure = maxf(0.0, conjure - delta)
	var speed := 1.0 + conjure * 0.8
	hand_phase += delta * speed * TAU / 3.8
	var reach := (1.0 - cos(hand_phase)) * 0.5
	var amplitude := 7.0 * SCALE
	if hand_left and hand_base.size() == 2:
		hand_left.position = hand_base[0] + Vector2(-amplitude * (1.0 - reach), sin(hand_phase * 0.5) * 2.0 * SCALE)
		hand_right.position = hand_base[1] + Vector2(amplitude * (1.0 - reach), sin(hand_phase * 0.5 + 1.3) * 2.0 * SCALE)
	hand_frame_timer -= delta
	if hand_frame_timer <= 0.0:
		hand_frame_timer = rng.randf_range(0.45, 0.9) / speed
		var frame := rng.randi_range(0, 1)
		hand_left.texture = hand_frames[0][frame]
		hand_right.texture = hand_frames[1][rng.randi_range(0, 1)]
	flame_timer -= delta
	if flame_timer <= 0.0:
		flame_timer = rng.randf_range(0.12, 0.22)
		for flame in flames:
			(flame as Sprite2D).texture = flame_frames[rng.randi_range(0, flame_frames.size() - 1)]
	# the ball wobbles on its stand while shaking
	wobble = maxf(0.0, wobble - delta * 2.4)
	ball_root.rotation = sin(clock * 38.0) * deg_to_rad(2.2) * wobble
	ball_front.modulate = Color(1, 1, 1, 1) if not (_mouse_on_ball() and screen == null) else Color(1.12, 1.08, 1.2, 1)


# =========================================================================================== shake
func request_shake(manual: bool) -> void:
	if shaking:
		queued_shake = manual
		return
	_start_shake(manual)


func _start_shake(manual: bool) -> void:
	if (state.dice as Array).is_empty():
		return
	shaking = true
	shake_manual = manual
	auto_timer = 0.0
	var duration := Rules.shake_time(stats)
	shake_left = duration
	if clock - last_shake_time <= float(Data.b("streak_window", 3.0)) + duration:
		state["streak"] = int(state.get("streak", 0)) + 1
	else:
		state["streak"] = 0
	var rolled := Rules.roll_faces(state, rng)
	pending_result = {"faces": rolled.faces, "meteor": rolled.meteor}
	ball.fast = Rules.turbo(stats)
	ball.shake(duration, 1.0 if manual else 0.8)
	wobble = 1.0
	conjure = 1.2
	Sound.play("rattle", 0.85 if manual else 0.6)
	if hint_label.visible and manual:
		hint_label.visible = false
		state["hint_done"] = true
	if manual:
		manual_shakes += 1
		if manual_shakes == 12 and not bool(state.get("hold_hint_done", false)):
			state["hold_hint_done"] = true
			toast(I18N.t("hud.hint_hold"), Kit.TEXT)


func _finish_shake() -> void:
	shaking = false
	last_shake_time = clock
	var result := Rules.resolve(state, stats, pending_result.faces, rng, shake_manual)
	var total := float(result.total)
	if bool(pending_result.get("meteor", false)):
		(result.events as Array).push_front("meteor")
	add_money(total)
	income_window.append([clock, total])
	ball.show_faces(result.faces, result.groups)
	var leveled := Rules.give_xp(state, stats)
	_show_shake_popups(result)
	for index in leveled:
		ball.level_up(index)
	if leveled.size() <= 2:
		for index in leveled:
			_popup(I18N.f("die.level_up", {"v": int(state.dice[index].level)}), _stage_from_ball(ball.die_position(index)) + Vector2(0, -70), Kit.GOLD_LIGHT, 18)
	else:
		_popup(I18N.f("die.levels_up", {"n": leveled.size()}), ball_center + Vector2(0, ball_radius * 0.15), Kit.GOLD_LIGHT, 20)
	if not leveled.is_empty():
		Sound.play("level", 0.6)
	Sound.play("land", 0.5)


func _stage_from_ball(point: Vector2) -> Vector2:
	var layer := ball_root.get_child(0) as Node2D
	return world.to_local(layer.to_global(point))


func _show_shake_popups(result: Dictionary) -> void:
	var total := float(result.total)
	var top := ball_center + Vector2(0, -ball_radius + 70)
	_popup("+" + I18N.money(total), top, Kit.GOLD_LIGHT, 30 if total >= income_per_sec * 2.0 else 24)
	var names: Array[String] = []
	var best := int(result.get("best_group", 1))
	if best >= 2:
		names.append(I18N.t("combo.group%d" % mini(best, 6)))
	for event in result.events:
		names.append(I18N.t("combo." + str(event)))
	if not names.is_empty():
		_popup(" · ".join(names), top + Vector2(0, -46), Color("f0b8ff"), 18)


func _popup(text: String, at: Vector2, color: Color, font_size: int) -> void:
	var node := Kit.label(popup_layer, text, Rect2(at.x - 400, at.y - 24, 800, 48), font_size, HORIZONTAL_ALIGNMENT_CENTER, color)
	var tween := node.create_tween().set_parallel(true)
	tween.tween_property(node, "position:y", node.position.y - 46.0, 1.2).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.tween_property(node, "modulate:a", 0.0, 1.2).set_delay(0.35)
	tween.chain().tween_callback(node.queue_free)


func toast(text: String, color: Color = Kit.TEXT) -> void:
	_popup(text, Vector2(960, 230), color, 20)


# =========================================================================================== money
func add_money(amount: float) -> void:
	if amount <= 0.0 or is_nan(amount):
		return
	var cap := float(Data.b("money_cap", 1.0e300))
	state["money"] = minf(cap, float(state.money) + amount)
	state["total_earned"] = minf(cap, float(state.get("total_earned", 0.0)) + amount)


func can_pay(amount: float) -> bool:
	return float(state.money) >= amount - 0.0001


func spend(amount: float) -> bool:
	if not can_pay(amount):
		toast(I18N.t("common.not_enough"), Kit.BAD)
		Sound.play("denied", 0.6)
		return false
	state["money"] = maxf(0.0, float(state.money) - amount)
	return true


func refresh_stats() -> void:
	stats = _compute_stats()
	_refresh_hud(true)


## The bonuses of talents, cards and gauntlets plus the running random event.
func _compute_stats() -> Dictionary:
	var result := Rules.compute_stats(state)
	match str(state.get("event", "")):
		"shop_sale":
			result["event_shop"] = 0.5
		"talent_sale":
			result["event_talent"] = 0.5
		"lucky_sale":
			result["event_lucky"] = 0.5
		"tarot_sale":
			result["event_tarot"] = 0.5
		"money_rush":
			result["event_money"] = 5.0
		"turbo":
			result["event_turbo"] = 1.0
	return result


func save_now() -> void:
	Save.write(slot, state)


# ======================================================================================== gumballs
func _machine_info() -> String:
	var lines: Array[String] = []
	lines.append("[b][color=#ffd77a]%s[/color][/b]" % I18N.t("gum.title"))
	lines.append(I18N.t("gum.tooltip"))
	lines.append("[color=#b9a6cf]%s[/color]" % I18N.t("gum.odds"))
	lines.append("[color=#7dffb0]%s: %s[/color]" % [I18N.t("hud.tp"), NumFmt.compact(int(state.tp))])
	lines.append("[color=#ffd77a]%s[/color]" % I18N.money(Rules.gumball_price(state, stats)))
	return "\n".join(lines)



func buy_gumball() -> void:
	if gum_busy:
		if gum_queue < 10:
			gum_queue += 1
		return
	var price := Rules.gumball_price(state, stats)
	if not spend(price):
		return
	state["gumballs"] = int(state.gumballs) + 1
	_run_gumball()


func _run_gumball() -> void:
	gum_busy = true
	Sound.play("coin", 0.7)
	# coin flies from the money display into the slot
	var coin := Sprite2D.new()
	coin.texture = Tex.get_tex(ART + "scene/coin.png")
	coin.scale = Vector2(SCALE, SCALE)
	coin.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	coin.position = Vector2(960, 70)
	world.add_child(coin)
	var slot_point := _point("gumball_slot")
	var tween := create_tween()
	tween.tween_property(coin, "position", slot_point, 0.38).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.tween_property(coin, "scale", Vector2(SCALE * 0.4, SCALE), 0.06)
	tween.tween_callback(coin.queue_free)
	# the crank turns twice
	for turn in range(8):
		tween.tween_callback(func() -> void:
			gum_crank.texture = crank_frames[(turn + 1) % 4]
			if turn % 2 == 0:
				Sound.play("crank", 0.5))
		tween.tween_interval(0.065)
	tween.tween_callback(_drop_gumball)


func _drop_gumball() -> void:
	var balls := 1
	if float(stats.double_ball) > 0.0 and rng.randf() * 100.0 < float(stats.double_ball):
		balls = 2
	var total_tp := 0
	for i in balls:
		var drawn := Rules.roll_gumball(stats, rng)
		total_tp += int(drawn.tp)
		_animate_gumball(int(drawn.ball), int(drawn.tp), i * 0.25)
	state["tp"] = int(state.tp) + total_tp
	state["tp_total"] = int(state.get("tp_total", 0)) + total_tp
	await get_tree().create_timer(0.55 + (balls - 1) * 0.25).timeout
	gum_busy = false
	_refresh_hud(false)
	if gum_queue > 0:
		gum_queue -= 1
		buy_gumball()


func _animate_gumball(ball_index: int, points: int, delay: float) -> void:
	var gum := Sprite2D.new()
	gum.texture = Tex.get_tex(ART + "scene/gumball_ball_%d.png" % ball_index)
	gum.scale = Vector2(SCALE, SCALE)
	gum.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	gum.centered = true
	var chute := _point("gumball_chute")
	gum.position = chute
	gum.modulate.a = 0.0
	world.add_child(gum)
	var machine := _rect("gumball_machine")
	var floor_y := machine.end.y - 3.0 * SCALE
	var tween := create_tween()
	tween.tween_interval(delay)
	tween.tween_property(gum, "modulate:a", 1.0, 0.05)
	tween.tween_callback(func() -> void: Sound.play("pop", 0.6))
	tween.tween_property(gum, "position", Vector2(chute.x + 14.0 * SCALE, floor_y), 0.28).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.tween_property(gum, "position", Vector2(chute.x + 22.0 * SCALE, floor_y - 5.0 * SCALE), 0.14).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_property(gum, "position", Vector2(chute.x + 28.0 * SCALE, floor_y), 0.14).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.tween_callback(func() -> void:
		var text := I18N.t("gum.result_one") if points == 1 else I18N.f("gum.result", {"v": points})
		_popup(text, gum.position + Vector2(40, -60), Kit.GOOD, 18))
	tween.tween_property(gum, "modulate:a", 0.0, 0.7).set_delay(0.6)
	tween.tween_callback(gum.queue_free)


# ======================================================================================== actions
## "" on success, otherwise a text key.
func learn_talent(talent_id: String) -> String:
	var block := Rules.talent_block(state, talent_id)
	if not block.is_empty():
		return block
	var cost := Rules.talent_cost(state, stats, talent_id)
	if int(state.tp) < int(cost[0]):
		return "common.not_enough_tp"
	if not can_pay(float(cost[1])):
		return "common.not_enough"
	state["tp"] = int(state.tp) - int(cost[0])
	state["money"] = float(state.money) - float(cost[1])
	(state.talents as Array).append(talent_id)
	var talent: Dictionary = Data.talents_by_id[talent_id]
	if Rules.is_slot_talent(talent):
		var commons: Array = Data.dice_by_rarity.get("common", [])
		var new_id := str(commons[rng.randi_range(0, commons.size() - 1)].id)
		(state.dice as Array).append({"id": new_id, "level": 1, "xp": 0.0, "locked": false})
		_discover(new_id)
		_sort_dice()
		_refresh_dice()
	Sound.play("learn", 0.7)
	refresh_stats()
	save_now()
	return ""


func _discover(die_id: String) -> bool:
	var found: Array = state.discovered
	if die_id in found:
		return false
	found.append(die_id)
	return true


## Rolls all unlocked dice with a Lucky Cube tier. Returns [{index, old, new, first}] or [] if not paid.
func lucky_roll(tier: int) -> Array:
	var indices: Array[int] = []
	for i in (state.dice as Array).size():
		if not bool(state.dice[i].get("locked", false)):
			indices.append(i)
	if indices.is_empty():
		toast(I18N.t("lucky.all_locked"), Kit.BAD)
		return []
	var price := Rules.lucky_price(state, stats, tier, indices.size())
	if not spend(price):
		return []
	var rolled: Array = state.lucky_rolled
	rolled[tier] = int(rolled[tier]) + indices.size()
	var odds := Rules.lucky_odds(stats, tier)
	var results: Array = []
	for i in indices:
		var roll := rng.randf() * 100.0
		var rarity_index := 0
		for r in odds.size():
			roll -= odds[r]
			if roll <= 0.0:
				rarity_index = r
				break
		var pool: Array = Data.dice_by_rarity.get(Data.rarities[rarity_index], [])
		var new_def: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
		var die: Dictionary = state.dice[i]
		var old_id := str(die.id)
		die["id"] = str(new_def.id)
		die["grow"] = 0
		die["pi"] = 0
		die.erase("market")
		var bonus := int(stats.reroll_levels)
		if bonus > 0:
			for _b in bonus:
				if int(die.level) < int(Data.b("max_level", 100)):
					die["level"] = int(die.level) + 1
		results.append({"index": i, "old": old_id, "new": str(new_def.id), "first": _discover(str(new_def.id)), "die": die})
	_sort_dice()
	for result in results:
		result["index"] = (state.dice as Array).find(result.die)
		result.erase("die")
	Sound.play("lucky", 0.7)
	_refresh_dice()
	refresh_stats()
	save_now()
	return results


func toggle_lock(index: int) -> void:
	if index >= 0 and index < (state.dice as Array).size():
		state.dice[index]["locked"] = not bool(state.dice[index].get("locked", false))


## Pays for a tarot draw and stores the offered cards (kept until one is picked).
func tarot_draw() -> Array:
	var offer: Array = state.get("tarot_offer", [])
	if not offer.is_empty():
		return offer
	var open: Array = []
	for card in Data.tarot:
		if int((state.tarot as Dictionary).get(str(card.id), 0)) < 4:
			open.append(str(card.id))
	if open.is_empty():
		return []
	if not spend(Rules.tarot_price(state, stats)):
		return []
	state["tarot_draws"] = int(state.tarot_draws) + 1
	open.shuffle()
	offer = open.slice(0, mini(open.size(), Rules.tarot_choices(stats)))
	state["tarot_offer"] = offer
	Sound.play("card", 0.7)
	save_now()
	return offer


func tarot_pick(card_id: String) -> int:
	var offer: Array = state.get("tarot_offer", [])
	if card_id not in offer:
		return 0
	var tarot_state: Dictionary = state.tarot
	tarot_state[card_id] = mini(4, int(tarot_state.get(card_id, 0)) + 1)
	state["tarot_offer"] = []
	Sound.play("learn", 0.7)
	refresh_stats()
	save_now()
	return int(tarot_state[card_id])


func buy_gauntlet(index: int) -> bool:
	if index in state.gauntlets:
		return false
	if not spend(Rules.gauntlet_price(stats, index)):
		return false
	(state.gauntlets as Array).append(index)
	state["gauntlet"] = index
	Sound.play("buy", 0.7)
	_apply_cursor()
	refresh_stats()
	save_now()
	return true


func equip_gauntlet(index: int) -> void:
	if index in state.gauntlets or index == 0:
		state["gauntlet"] = index
		_apply_cursor()
		refresh_stats()
		save_now()


func buy_table(table_id: int) -> bool:
	if table_id in state.tables:
		return false
	if not spend(Rules.table_price(stats, table_id)):
		return false
	(state.tables as Array).append(table_id)
	state["table"] = table_id
	Sound.play("buy", 0.7)
	_refresh_table_design()
	save_now()
	return true


func equip_table(table_id: int) -> void:
	if table_id in state.tables:
		state["table"] = table_id
		_refresh_table_design()
		save_now()


func buy_black(card_id: String) -> bool:
	var card: Dictionary = Data.black_by_id.get(card_id, {})
	var copies := int((state.black as Dictionary).get(card_id, 0))
	if card.is_empty() or copies >= int(card.cap) or float(stats.black_market) <= 0.0:
		return false
	if not spend(Rules.black_price(state, stats, card_id)):
		return false
	(state.black as Dictionary)[card_id] = copies + 1
	Sound.play("buy", 0.7)
	refresh_stats()
	save_now()
	return true


func _refresh_table_design() -> void:
	var design := int(state.get("table", 0))
	cloth_sprite.texture = Tex.get_tex(ART + "scene/cloth_%d.png" % design)
	cushion_sprite.texture = Tex.get_tex(ART + "scene/cushion_%d.png" % design)


# ===================================================================================== gauntlet rack
## Right side of the screen: the bought gauntlets. Click one to equip it (no need to open the shop).
func _build_rack() -> void:
	var panel := Kit.panel(hud, RACK, Color("170b26d8"), Kit.GOLD, 3, 16)
	Kit.label(panel, I18N.t("shop.gauntlets"), Rect2(8, 6, RACK.size.x - 16, 30), 13, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT)
	rack_icon = Kit.texture(panel, null, Rect2((RACK.size.x - 72.0) * 0.5, 38, 72, 72), true)
	rack_name = Kit.paragraph(panel, "", Rect2(8, 112, RACK.size.x - 16, 40), 11, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT)
	rack_effects = Kit.paragraph(panel, "", Rect2(8, 152, RACK.size.x - 16, 100), 10, HORIZONTAL_ALIGNMENT_CENTER, Kit.TEXT)
	var scroll := Kit.scroll(panel, Rect2(6, 258, RACK.size.x - 12, RACK.size.y - 264))
	rack_grid = GridContainer.new()
	rack_grid.columns = 3
	rack_grid.add_theme_constant_override("h_separation", 4)
	rack_grid.add_theme_constant_override("v_separation", 4)
	scroll.add_child(rack_grid)


func _refresh_rack() -> void:
	if rack_grid == null:
		return
	var owned: Array = (state.get("gauntlets", []) as Array).duplicate()
	owned.sort()
	var equipped := int(state.get("gauntlet", 0))
	var signature := "%s|%d|%s" % [str(owned), equipped, I18N.language()]
	if signature == rack_signature:
		return
	rack_signature = signature
	if equipped > 0:
		rack_icon.texture = Tex.get_tex(ART + "gauntlets/gauntlet_%d.png" % equipped)
		Kit.set_text(rack_name, I18N.upper(I18N.t("gauntlet.%d.name" % equipped)))
		Kit.set_text(rack_effects, ScreenBase.effects_text(Data.gauntlet(equipped).get("effects", [])))
	else:
		rack_icon.texture = null
		Kit.set_text(rack_name, "")
		Kit.set_text(rack_effects, I18N.t("gauntlets.none"))
	for child in rack_grid.get_children():
		child.queue_free()
	for value in owned:
		var index := int(value)
		var active := index == equipped
		var button := Button.new()
		button.custom_minimum_size = Vector2(56, 56)
		button.focus_mode = Control.FOCUS_NONE
		button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		button.add_theme_stylebox_override("normal", Kit.style(Color("3a1d5c") if active else Color("1d1030"), Kit.GOLD_LIGHT if active else Color("5a3a7e"), 3 if active else 2, 10))
		button.add_theme_stylebox_override("hover", Kit.style(Color("4a2a70"), Kit.GOLD_LIGHT, 3, 10))
		button.add_theme_stylebox_override("pressed", Kit.style(Color("2a1240"), Kit.GOLD_LIGHT, 3, 10))
		button.pressed.connect(_on_rack_pressed.bind(index))
		button.mouse_entered.connect(_on_rack_hover.bind(index))
		button.mouse_exited.connect(_hide_tooltip)
		rack_grid.add_child(button)
		Kit.texture(button, Tex.get_tex(ART + "gauntlets/gauntlet_%d.png" % index), Rect2(4, 4, 48, 48), false)


func _on_rack_pressed(index: int) -> void:
	if index == int(state.get("gauntlet", 0)):
		return
	GameSession.play_sfx("ui_select")
	equip_gauntlet(index)
	_on_rack_hover(index)


func _on_rack_hover(index: int) -> void:
	var lines: Array[String] = []
	lines.append("[b][color=#ffd77a]%s[/color][/b]" % I18N.upper(I18N.t("gauntlet.%d.name" % index)))
	lines.append(ScreenBase.effects_text(Data.gauntlet(index).get("effects", [])))
	if index == int(state.get("gauntlet", 0)):
		lines.append("[color=#7dffb0]%s[/color]" % I18N.t("shop.equipped"))
	else:
		lines.append("[color=#b9a6cf]%s[/color]" % I18N.t("gauntlets.hint"))
	show_tooltip("\n".join(lines))


# ===================================================================================== random events
## Every 5 minutes of play a random event starts: 50 % sales, a money rush or turbo shaking.
func _build_event_panel() -> void:
	event_panel = Kit.panel(hud, Rect2(28, 100, 470, 52), Color("3a1d5ce8"), Kit.GOLD_LIGHT, 3, 14)
	event_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	event_label = Kit.label(event_panel, "", Rect2(10, 4, 450, 44), 17, HORIZONTAL_ALIGNMENT_CENTER, Kit.GOLD_LIGHT)
	event_panel.visible = false
	next_event_label = Kit.label(hud, "", Rect2(28, 100, 470, 30), 11, HORIZONTAL_ALIGNMENT_LEFT, Kit.MUTED)


func _update_events(delta: float) -> void:
	var events: Dictionary = Data.b("events", {})
	if events.is_empty():
		return
	if not str(state.get("event", "")).is_empty():
		state["event_left"] = float(state.get("event_left", 0.0)) - delta
		if float(state.event_left) <= 0.0:
			state["event"] = ""
			state["event_left"] = 0.0
			refresh_stats()
	state["event_timer"] = float(state.get("event_timer", 300.0)) - delta
	if float(state.event_timer) <= 0.0:
		state["event_timer"] = float(Data.b("event_every", 300.0))
		_start_event(events)


func _start_event(events: Dictionary) -> void:
	var choices: Array = []
	for event_id in events:
		if str(event_id) != str(state.get("last_event", "")):
			choices.append(str(event_id))
	var event_id := str(choices[rng.randi_range(0, choices.size() - 1)])
	state["event"] = event_id
	state["event_left"] = float(events[event_id])
	state["last_event"] = event_id
	refresh_stats()
	toast(I18N.f("event.%s.desc" % event_id, {"v": int(events[event_id])}), Kit.GOLD_LIGHT)
	Sound.play("learn", 0.8)


func _refresh_event_panel() -> void:
	if event_panel == null:
		return
	var event_id := str(state.get("event", ""))
	if event_id.is_empty():
		event_panel.visible = false
		next_event_label.visible = true
		var left := maxi(0, int(ceilf(float(state.get("event_timer", 0.0)))))
		Kit.set_text(next_event_label, I18N.f("event.next", {"v": "%d:%02d" % [left / 60, left % 60]}))
		return
	next_event_label.visible = false
	event_panel.visible = true
	var seconds := maxi(0, int(ceilf(float(state.get("event_left", 0.0)))))
	Kit.set_text(event_label, "%s  ·  0:%02d" % [I18N.t("event.%s.name" % event_id), seconds])
	# a slow, calm glow (no flashing)
	event_panel.modulate.a = 0.86 + 0.14 * sin(clock * 3.0)


# ========================================================================================= cursor
const CURSOR_SHAPES := [Input.CURSOR_ARROW, Input.CURSOR_POINTING_HAND, Input.CURSOR_DRAG, Input.CURSOR_CAN_DROP, Input.CURSOR_MOVE]


func _apply_cursor() -> void:
	var index := int(state.get("gauntlet", 0))
	if index <= 0:
		_restore_cursor()
		return
	var info := _gauntlet_info(index)
	var image := Tex.load_image(ART + "gauntlets/gauntlet_%d.png" % index)
	if image == null:
		return
	var target := 68
	var factor := float(target) / float(maxi(image.get_width(), image.get_height()))
	image.resize(maxi(1, int(image.get_width() * factor)), maxi(1, int(image.get_height() * factor)), Image.INTERPOLATE_NEAREST)
	var hotspot: Array = info.get("hotspot", [15, 7])
	var texture := ImageTexture.create_from_image(image)
	for shape in CURSOR_SHAPES:
		Input.set_custom_mouse_cursor(texture, shape, Vector2(float(hotspot[0]), float(hotspot[1])) * factor)


func _gauntlet_info(index: int) -> Dictionary:
	var path := ART + "gauntlets/gauntlets.json"
	if FileAccess.file_exists(path):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		if parsed is Dictionary:
			return parsed.get("gauntlet_%d" % index, {})
	return {}


func _restore_cursor() -> void:
	for shape in CURSOR_SHAPES:
		Input.set_custom_mouse_cursor(null, shape)
	if GameSession.has_method("_apply_custom_cursor"):
		GameSession.call("_apply_custom_cursor")


# ======================================================================================== screens
func _open_screen(name: String) -> void:
	if screen != null:
		close_screen()
	hide_tooltip()
	var script: GDScript = null
	match name:
		"talents":
			script = TalentScreen
		"lucky":
			script = LuckyScreen
		"tarot":
			script = TarotScreen
		"shop":
			script = ShopScreen
		"book":
			script = BookScreen
		"pause":
			script = PauseScreen
	if script == null:
		return
	screen = script.new()
	screen_name = name
	screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(screen)
	move_child(tooltip, -1)
	screen.call("build", self)
	GameSession.play_sfx("ui_select")


func close_screen() -> void:
	if screen != null:
		screen.queue_free()
	screen = null
	screen_name = ""
	hide_tooltip()


func _open_pause() -> void:
	_open_screen("pause")


func exit_to_menu() -> void:
	if leaving:
		return
	Save.write(slot, state)
	leaving = true
	_restore_cursor()
	get_tree().paused = false
	get_tree().change_scene_to_file(START_MENU)


## The design-space origin of the 1920x1080 area (screens use it to centre their panels).
func safe_origin() -> Vector2:
	return stage.position if stage else Vector2.ZERO


## Test helper: average payout of `count` shakes with the current dice (no money, no xp, no side effects).
func debug_average(count: int, manual: bool = true) -> float:
	var copy: Dictionary = state.duplicate(true)
	copy["streak"] = 0
	var test_rng := RandomNumberGenerator.new()
	test_rng.seed = 12345
	var total := 0.0
	for _i in count:
		var rolled := Rules.roll_faces(copy, test_rng)
		var result := Rules.resolve(copy, stats, rolled.faces, test_rng, manual)
		total += float(result.total)
	return total / float(maxi(1, count))
