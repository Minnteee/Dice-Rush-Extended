extends RefCounted
## Dice Rush Extended - 9 new random events (the golden bone of the original game is the 10th).
## Only one of these events runs at a time; they pause together with the table.

const I18N := preload("res://bdr/core/i18n.gd")
const NumFmt := preload("res://bdr/core/numfmt.gd")
const UIKit := preload("res://bdr/ui/ui_kit.gd")

const IDS := ["meteor_shower", "coin_rain", "tornado", "happy_hour", "rainbow", "black_cat", "treasure_chest", "thief", "lucky_clover"]
const ART := "res://bdr/art/events/"
const FIRST_DELAY := 90.0
const MIN_INTERVAL := 150.0
const MAX_INTERVAL := 300.0
const DURATION := {"meteor_shower": 12.0, "coin_rain": 10.0, "tornado": 10.0, "happy_hour": 30.0, "rainbow": 20.0,
	"black_cat": 12.0, "treasure_chest": 12.0, "thief": 8.0, "lucky_clover": 15.0}
const HAPPY_HOUR_MULTIPLIER := 2.0
const RAINBOW_CHANCE := 0.25
const RAINBOW_MULTIPLIER := 7.0
const METEOR_EVERY := 0.45
const METEOR_RADIUS := 95.0
const COIN_EVERY := 0.18
const COIN_LIFE := 2.6
const COIN_SECONDS := 2.0
const CAT_SECONDS := 60.0
const CHEST_SECONDS := 120.0
const CHEST_CLICKS := 5
const THIEF_SECONDS := 90.0
const THIEF_STEAL_SECONDS := 20.0
const CLOVER_STREAK := 20.0
const MIN_RATE := 25.0

var game: Node
var main: Node
var rng := RandomNumberGenerator.new()
## visuals (positions of coins, chests, visitors ...) - seeded per event so that the coop
## partner sees exactly the same objects
var vrng := RandomNumberGenerator.new()
var _obj_seq := 0
var next_in := FIRST_DELAY
var active := ""
var time_left := 0.0
var _serial := 0
var _spawn_timer := 0.0
var _nodes: Array[Node] = []
var _mover: Control
var _mover_from := Vector2.ZERO
var _mover_to := Vector2.ZERO
var _mover_total := 1.0
var _mover_hit_radius := 0.0
var _mover_roll_mult := 1.0
var _chest_clicks := 0
var _tmp: Array = []
var _hud: Panel
var _hud_icon: TextureRect
var _hud_label: Label


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	rng.randomize()


func reset() -> void:
	_clear_nodes()
	active = ""
	time_left = 0.0
	next_in = FIRST_DELAY


func is_active() -> bool:
	return not active.is_empty()


func frequency_multiplier() -> float:
	var multiplier: float = game.tarot.value("event_freq")
	if main._is_talent_owned("bdr_event_freq_1"):
		multiplier *= 1.25
	if main._is_talent_owned("bdr_event_freq_2"):
		multiplier *= 1.25
	return maxf(0.1, multiplier)


func _next_interval() -> float:
	return rng.randf_range(MIN_INTERVAL, MAX_INTERVAL) / frequency_multiplier()


## Money for "seconds of income" rewards (never less than a small minimum).
func _income_reward(seconds: float) -> float:
	var rate := maxf(MIN_RATE, float(game.income_rate()))
	return rate * seconds * float(game.event_reward_multiplier())


func global_multiplier() -> float:
	return HAPPY_HOUR_MULTIPLIER if active == "happy_hour" else 1.0


## Called for every landing dice (rainbow event).
func on_landing(die: DiceActor) -> void:
	if active != "rainbow" or rng.randf() >= RAINBOW_CHANCE:
		return
	die.pending_mult *= RAINBOW_MULTIPLIER
	game.mech._popup(die, "fx.rainbow", {"n": int(RAINBOW_MULTIPLIER)})


# ---------------------------------------------------------------- scheduling
func process(delta: float) -> void:
	var client: bool = game.is_coop_client()
	if active.is_empty():
		if client:
			_update_hud()
			return
		next_in -= delta
		if next_in <= 0.0:
			if main._visual_overlay_blocks_wave() or main.golden_bone_offer_time_left > 0.0:
				next_in = 5.0
			else:
				start(IDS[rng.randi_range(0, IDS.size() - 1)])
		_update_hud()
		return
	time_left -= delta
	match active:
		"meteor_shower":
			_spawn_timer -= delta
			if _spawn_timer <= 0.0:
				_spawn_timer = METEOR_EVERY
				_spawn_meteor()
		"coin_rain":
			_spawn_timer -= delta
			if _spawn_timer <= 0.0:
				_spawn_timer = COIN_EVERY
				_spawn_coin()
		"tornado", "black_cat", "thief":
			_update_mover()
	if time_left <= (-3.0 if client else 0.0):
		finish()
	_update_hud()


func start(event_id: String) -> void:
	if game.is_coop_client():
		return
	if not active.is_empty():
		finish()
	var duration := float(DURATION.get(event_id, 10.0)) * float(game.tarot.value("event_duration"))
	var seed := rng.randi()
	_begin(event_id, _serial + 1, seed, duration)
	game.coop.on_event_message(["start", event_id, _serial, seed, duration])
	game.stat("events_seen", 1)
	game.stat("event_" + event_id, 1)
	game.toast(I18N.t("event.%s.banner" % event_id))
	var streak: float = game.tarot.value("event_streak")
	if streak > 0.0:
		game.lucky.add_boost(streak)


## Starts the visuals of an event (host and coop partner).
func _begin(event_id: String, serial: int, seed: int, duration: float) -> void:
	_clear_nodes()
	active = event_id
	_serial = serial
	time_left = duration
	vrng.seed = seed
	_obj_seq = 0
	_spawn_timer = 0.0
	_chest_clicks = 0
	GameSession.play_sfx("rare")
	match event_id:
		"tornado":
			_start_mover(ART + "tornado_sprite.png", Vector2(110, 138), false, 70.0, 3.0)
		"black_cat":
			_start_mover(ART + "cat_walk.png", Vector2(120, 80), true, 46.0, 1.0)
		"thief":
			_start_mover(ART + "thief_run.png", Vector2(104, 104), true, 0.0, 1.0)
		"treasure_chest":
			_spawn_chest()
		"lucky_clover":
			for _index in range(4):
				_spawn_clover()
	game.invalidate_global_multiplier()


func finish() -> void:
	if active.is_empty():
		return
	if not game.is_coop_client():
		if active == "thief" and is_instance_valid(_mover) and not _mover.has_meta("caught"):
			_thief_escaped()
		game.coop.on_event_message(["finish", _serial])
	_clear_nodes()
	active = ""
	time_left = 0.0
	next_in = _next_interval()
	game.invalidate_global_multiplier()


func _clear_nodes() -> void:
	for node in _nodes:
		if is_instance_valid(node):
			node.queue_free()
	_nodes.clear()
	_mover = null


func _safe_rect() -> Rect2:
	return game.board_safe_rect()


func _random_point() -> Vector2:
	var rect := _safe_rect()
	return Vector2(vrng.randf_range(rect.position.x, rect.end.x), vrng.randf_range(rect.position.y, rect.end.y))


func _texture_button(path: String, size: Vector2, at: Vector2, z: int = 47) -> TextureButton:
	var button := TextureButton.new()
	button.texture_normal = CleanTextureLoader.load_texture(path)
	button.ignore_texture_size = true
	button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	button.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	button.size = size
	button.pivot_offset = size * 0.5
	button.position = at - size * 0.5
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.z_index = z
	button.set_meta("obj", _obj_seq)
	_obj_seq += 1
	main.add_child(button)
	_nodes.append(button)
	return button


func _texture(path: String, size: Vector2, at: Vector2, z: int = 47) -> TextureRect:
	var rect := TextureRect.new()
	rect.texture = CleanTextureLoader.load_texture(path)
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rect.size = size
	rect.pivot_offset = size * 0.5
	rect.position = at - size * 0.5
	rect.z_index = z
	main.add_child(rect)
	_nodes.append(rect)
	return rect


func _roll_around(center: Vector2, radius: float, multiplier: float, max_count: int, mark: String) -> int:
	if game.is_coop_client():
		return 0
	_tmp.clear()
	main._grid.query_radius(center, radius, _tmp)
	var rolled := 0
	for die in _tmp:
		if rolled >= max_count:
			break
		if not is_instance_valid(die) or die.rolling or die.reserved_by != 0:
			continue
		if not mark.is_empty():
			if int(die.get_meta(mark, -1)) == _serial:
				continue
			die.set_meta(mark, _serial)
		if multiplier > 1.0:
			die.pending_mult *= multiplier
		main._start_die_roll(die, 0, Vector2(-1.0, -1.0), false, true)
		rolled += 1
	return rolled


# ---------------------------------------------------------------- meteor shower
func _spawn_meteor() -> void:
	var target := _random_point()
	var start := target + Vector2(-260.0, -360.0)
	var meteor := _texture(ART + "meteor.png", Vector2(72, 72), start, 52)
	meteor.rotation = deg_to_rad(35.0)
	var tween := meteor.create_tween()
	tween.tween_property(meteor, "position", target - meteor.size * 0.5, 0.5).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tween.tween_callback(_meteor_impact.bind(meteor, target, _serial))


func _meteor_impact(meteor: TextureRect, target: Vector2, serial: int) -> void:
	if is_instance_valid(meteor):
		_nodes.erase(meteor)
		meteor.queue_free()
	if serial != _serial or active != "meteor_shower" or game.is_coop_client():
		return
	game.fx_ring(target, METEOR_RADIUS * float(game.effect_radius_mult()), Color("ff7a1f"))
	var rolled := _roll_around(target, METEOR_RADIUS * float(game.effect_radius_mult()), 2.0, int(12 * float(game.effect_count_mult())), "")
	game.stat("event_meteor_hits", 1)
	if rolled > 0:
		main._play_payout_sound()


# ---------------------------------------------------------------- coin rain
func _spawn_coin() -> void:
	var alive := 0
	for node in _nodes:
		if is_instance_valid(node):
			alive += 1
	if alive > 40:
		return
	var rect := _safe_rect()
	var x := vrng.randf_range(rect.position.x, rect.end.x)
	var landing := Vector2(x, vrng.randf_range(rect.position.y + 60.0, rect.end.y))
	var coin := _texture_button(ART + "coin.png", Vector2(56, 56), Vector2(x, rect.position.y - 40.0), 48)
	coin.pressed.connect(_collect_coin.bind(coin))
	var tween := coin.create_tween()
	tween.tween_property(coin, "position", landing - coin.size * 0.5, 0.9).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	tween.tween_interval(COIN_LIFE - 0.9)
	tween.tween_property(coin, "modulate:a", 0.0, 0.25)
	tween.tween_callback(_remove_node.bind(coin))


func _collect_coin(coin: TextureButton, from_partner: bool = false) -> void:
	if not is_instance_valid(coin) or coin.disabled:
		return
	if _forward_click(coin):
		return
	coin.disabled = true
	_send_clicked(coin)
	var amount := _income_reward(COIN_SECONDS)
	game.pay_bonus(amount, coin.position + coin.size * 0.5)
	main._play_payout_sound()
	game.stat("event_coins", 1)
	_remove_node(coin)


func _remove_node(node: Node) -> void:
	if is_instance_valid(node):
		_nodes.erase(node)
		node.queue_free()


# ---------------------------------------------------------------- moving visitors
func _start_mover(path: String, size: Vector2, clickable: bool, hit_radius: float, roll_mult: float) -> void:
	var rect := _safe_rect()
	var left_to_right := vrng.randf() < 0.5
	var y_from := vrng.randf_range(rect.position.y + 80.0, rect.end.y - 80.0)
	var y_to := vrng.randf_range(rect.position.y + 80.0, rect.end.y - 80.0)
	_mover_from = Vector2(rect.position.x - 80.0 if left_to_right else rect.end.x + 80.0, y_from)
	_mover_to = Vector2(rect.end.x + 80.0 if left_to_right else rect.position.x - 80.0, y_to)
	_mover_total = time_left
	_mover_hit_radius = hit_radius
	_mover_roll_mult = roll_mult
	if clickable:
		var button := _texture_button(path, size, _mover_from, 49)
		button.flip_h = not left_to_right
		button.pressed.connect(_mover_clicked.bind(button))
		_mover = button
	else:
		var rect_node := _texture(path, size, _mover_from, 49)
		rect_node.flip_h = not left_to_right
		_mover = rect_node


func _update_mover() -> void:
	if not is_instance_valid(_mover) or _mover.has_meta("caught"):
		return
	var progress := clampf(1.0 - time_left / maxf(0.1, _mover_total), 0.0, 1.0)
	var point := _mover_from.lerp(_mover_to, progress)
	if active == "thief":
		point.y += sin(progress * TAU * 3.0) * 70.0
	elif active == "tornado":
		point.y += sin(progress * TAU * 1.5) * 120.0
	else:
		point.y += sin(progress * TAU * 6.0) * 6.0
	_mover.position = point - _mover.size * 0.5
	if active == "tornado":
		_mover.rotation = sin(progress * TAU * 8.0) * 0.08
	if _mover_hit_radius > 0.0:
		var rolled := _roll_around(point, _mover_hit_radius * float(game.effect_radius_mult()), _mover_roll_mult, 6, "bdr_event_touch")
		if rolled > 0 and active == "tornado":
			game.stat("event_tornado_dice", rolled)


func _mover_clicked(button: TextureButton, from_partner: bool = false) -> void:
	if not is_instance_valid(button) or button.has_meta("caught"):
		return
	if _forward_click(button):
		return
	_send_clicked(button)
	button.set_meta("caught", true)
	button.disabled = true
	var at := button.position + button.size * 0.5
	match active:
		"black_cat":
			game.pay_bonus(_income_reward(CAT_SECONDS), at)
			game.popup_at(at, "fx.meow")
			game.stat("event_cats_petted", 1)
		"thief":
			game.pay_bonus(_income_reward(THIEF_SECONDS), at)
			game.popup_at(at, "fx.caught")
			game.stat("event_thieves_caught", 1)
	GameSession.play_sfx("rare")
	var tween := button.create_tween()
	tween.tween_property(button, "scale", Vector2(1.4, 1.4), 0.18)
	tween.tween_property(button, "modulate:a", 0.0, 0.3)
	tween.tween_callback(finish)


func _thief_escaped() -> void:
	var loss := minf(maxf(MIN_RATE, float(game.income_rate())) * THIEF_STEAL_SECONDS, float(main.money) * 0.02)
	if loss <= 0.0:
		return
	main.money = maxf(0.0, float(main.money) - loss)
	main._request_all_labels_update()
	game.stat("event_thief_escaped", 1)
	game.toast(I18N.f("event.thief.escaped", {"v": main._bdr_money_text(loss, false)}))


# ---------------------------------------------------------------- treasure chest
func _spawn_chest() -> void:
	var chest := _texture_button(ART + "chest_closed.png", Vector2(120, 120), _random_point(), 48)
	chest.pressed.connect(_chest_clicked.bind(chest))
	var tween := chest.create_tween().set_loops()
	tween.tween_property(chest, "scale", Vector2(1.06, 1.06), 0.4).set_trans(Tween.TRANS_SINE)
	tween.tween_property(chest, "scale", Vector2(0.96, 0.96), 0.4).set_trans(Tween.TRANS_SINE)
	chest.set_meta("pulse", tween)


func _chest_clicked(chest: TextureButton, from_partner: bool = false) -> void:
	if not is_instance_valid(chest) or chest.disabled:
		return
	if _forward_click(chest):
		return
	_chest_clicks += 1
	_send_clicked(chest, _chest_clicks >= CHEST_CLICKS)
	GameSession.play_sfx("ui_select")
	var shake := chest.create_tween()
	shake.tween_property(chest, "rotation", 0.18, 0.05)
	shake.tween_property(chest, "rotation", -0.18, 0.08)
	shake.tween_property(chest, "rotation", 0.0, 0.05)
	if _chest_clicks < CHEST_CLICKS:
		game.popup_at(chest.position + chest.size * 0.5, "fx.chest_clicks", {"n": CHEST_CLICKS - _chest_clicks})
		return
	chest.disabled = true
	var pulse = chest.get_meta("pulse") if chest.has_meta("pulse") else null
	if pulse is Tween:
		(pulse as Tween).kill()
	chest.texture_normal = CleanTextureLoader.load_texture(ART + "chest_open.png")
	var at := chest.position + chest.size * 0.5
	game.pay_bonus(_income_reward(CHEST_SECONDS), at)
	game.stat("event_chests", 1)
	if rng.randf() < 0.15 and game.try_bonus("gold"):
		main.golden_coins += 1
		game.popup_at(at + Vector2(0, -40), "fx.lb_gold")
	GameSession.play_sfx("rare")
	time_left = minf(time_left, 1.6)


# ---------------------------------------------------------------- lucky clover
func _spawn_clover() -> void:
	var clover := _texture_button(ART + "clover.png", Vector2(104, 104), _random_point(), 48)
	clover.pressed.connect(_clover_clicked.bind(clover))
	var tween := clover.create_tween().set_loops().set_parallel(false)
	tween.tween_property(clover, "scale", Vector2(1.18, 1.18), 0.45).set_trans(Tween.TRANS_SINE)
	tween.tween_property(clover, "scale", Vector2(0.92, 0.92), 0.45).set_trans(Tween.TRANS_SINE)


func _clover_clicked(clover: TextureButton, from_partner: bool = false) -> void:
	if not is_instance_valid(clover) or clover.disabled:
		return
	if _forward_click(clover):
		return
	clover.disabled = true
	_send_clicked(clover)
	var seconds := CLOVER_STREAK * float(game.event_reward_multiplier())
	game.lucky.add_boost(seconds)
	game.invalidate_global_multiplier()
	game.popup_at(clover.position + clover.size * 0.5, "fx.clover", {"s": int(seconds)})
	game.stat("event_clovers", 1)
	GameSession.play_sfx("rare")
	_remove_node(clover)


# ---------------------------------------------------------------- HUD
func build_hud() -> void:
	_hud = Panel.new()
	_hud.position = Vector2(302, 22)
	_hud.size = Vector2(118, 96)
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.z_index = 41
	_hud.add_theme_stylebox_override("panel", UIKit.style(Color(0.02, 0.04, 0.09, 0.94), Color("5dabf6"), 3, 12))
	main.add_child(_hud)
	_hud_icon = UIKit.texture(_hud, "", Rect2(29, 4, 60, 54))
	_hud_label = UIKit.label(_hud, "", Rect2(3, 57, 112, 34), 11, HORIZONTAL_ALIGNMENT_CENTER)
	_hud.visible = false


## Shows the running event, otherwise a lucky streak or a DJ beat drop.
func _update_hud() -> void:
	if not is_instance_valid(_hud):
		return
	var icon := ""
	var text := ""
	var border := Color("5dabf6")
	if not active.is_empty():
		icon = ART + active + ".png"
		text = _format_time(time_left)
		if active == "happy_hour":
			text = "x2  " + text
		elif active == "rainbow":
			text = "x7?  " + text
	elif game.lucky.boost_left() > 0.0:
		icon = game.lucky.icon("bdr_boost")
		text = "x%s  %s" % [NumFmt.compact(game.lucky.boost_multiplier()), _format_time(game.lucky.boost_left())]
		border = Color("2fa85a")
	elif game.staff.dj_active():
		icon = game.staff.icon_path("staff_dj")
		text = "x2  DJ"
		border = Color("ff4fd8")
	_hud.visible = not icon.is_empty()
	if not _hud.visible:
		return
	if str(_hud.get_meta("icon", "")) != icon:
		_hud.set_meta("icon", icon)
		_hud_icon.texture = CleanTextureLoader.load_texture(icon)
		_hud.add_theme_stylebox_override("panel", UIKit.style(Color(0.02, 0.04, 0.09, 0.94), border, 3, 12))
	if _hud_label.text != text:
		_hud_label.text = text
		UIKit.fit(_hud_label)


static func _format_time(seconds: float) -> String:
	var total := maxi(0, int(ceil(seconds)))
	return "%d:%02d" % [total / 60, total % 60]


# ---------------------------------------------------------------- coop
## Client: a click on an event object is only sent to the host.
func _forward_click(node: Control) -> bool:
	if not game.is_coop_client():
		return false
	game.coop_request("event_click", [_serial, int(node.get_meta("obj", -1))])
	return true


## Host: tells the partner that an object was clicked (by anybody).
func _send_clicked(node: Control, extra: bool = false) -> void:
	if not game.is_coop_client():
		game.coop.on_event_message(["clicked", _serial, int(node.get_meta("obj", -1)), extra])


func _object(index: int) -> TextureButton:
	for node in _nodes:
		if is_instance_valid(node) and node is TextureButton and int(node.get_meta("obj", -1)) == index:
			return node
	return null


## Host: the partner clicked an event object.
func coop_click(serial: int, index: int) -> void:
	if serial != _serial or active.is_empty():
		return
	var node := _object(index)
	if node == null:
		return
	match active:
		"coin_rain":
			_collect_coin(node, true)
		"black_cat", "thief":
			_mover_clicked(node, true)
		"treasure_chest":
			_chest_clicked(node, true)
		"lucky_clover":
			_clover_clicked(node, true)


## Client: event messages of the host.
func coop_message(message: Array) -> void:
	if message.is_empty():
		return
	match str(message[0]):
		"start":
			_begin(str(message[1]), int(message[2]), int(message[3]), float(message[4]))
		"finish":
			if int(message[1]) == _serial:
				_clear_nodes()
				active = ""
				time_left = 0.0
		"clicked":
			if int(message[1]) != _serial:
				return
			var node := _object(int(message[2]))
			if node == null:
				return
			match active:
				"coin_rain", "lucky_clover":
					_remove_node(node)
				"black_cat", "thief":
					node.set_meta("caught", true)
					node.disabled = true
					var tween := node.create_tween()
					tween.tween_property(node, "scale", Vector2(1.4, 1.4), 0.18)
					tween.tween_property(node, "modulate:a", 0.0, 0.3)
				"treasure_chest":
					var shake := node.create_tween()
					shake.tween_property(node, "rotation", 0.18, 0.05)
					shake.tween_property(node, "rotation", -0.18, 0.08)
					shake.tween_property(node, "rotation", 0.0, 0.05)
					if bool(message[3]):
						node.disabled = true
						node.texture_normal = CleanTextureLoader.load_texture(ART + "chest_open.png")
		"staff_pop":
			game.fx_staff(str(message[1]), message[2])
		"storm":
			main._coop_client_storm(message[1])
		"storm_hit":
			main._coop_client_storm_hit(int(message[1]))
