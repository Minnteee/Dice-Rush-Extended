# Dice Rush Extended patch for dice_actor.gd
# - no physics body / picking per dice (main.gd picks dice through a spatial grid)
# - no Tween per lightweight roll (main.gd completes them through one scheduler)
# - resting dice are drawn by the batch renderer (sprites hidden while batched)
# - support for the 100 new dice kinds (custom faces, roll speed, per-dice state)

var grid_cell: int = -1
var batch_band: int = -1
var batch_slot: int = -1
var light_due_msec: int = 0
var light_generation: int = 0
var roll_speed: float = 1.0
var pending_mult: float = 1.0
var last_payout: float = 0.0
var last_payout_msec: int = 0
var mstate: Dictionary = {}
var faces: PackedInt32Array = PackedInt32Array()
var player_rolled: bool = false
var bdr_tier: int = 0
var display_size: float = 62.0
var spin3d: bool = false
var special_motion: bool = false
## coop: network id of the dice, and the face / duration of a roll replayed from the host
var net_id: int = 0
var forced_face: int = -1
var forced_duration: float = -1.0
var last_face: int = 0
var last_roll_duration: float = 0.0


func configure(
	kind: String,
	texture_path: String,
	allowed_rect: Rect2,
	random_seed: int = 0,
	tint: Color = Color.WHITE,
	show_gold_aura: bool = true
) -> void :
	process_mode = Node.PROCESS_MODE_PAUSABLE
	set_process(false)
	die_kind = kind
	board_rect = allowed_rect
	_persistent_position = position
	if random_seed != 0:
		rng.seed = random_seed
	else:
		rng.randomize()
	input_pickable = false
	collision_layer = 0
	collision_mask = 0
	monitoring = false
	monitorable = false
	z_index = 12 + int(position.y / 100.0)
	gold_aura_visual_enabled = show_gold_aura
	if kind == "golden" and gold_aura_visual_enabled:
		_build_gold_aura()

	var texture: = CleanTextureLoaderScript.load_texture(texture_path)
	_shadow = Sprite2D.new()
	_shadow.texture = texture
	_shadow.modulate = Color(0.0, 0.0, 0.0, 0.3)
	_shadow.position = Vector2(5, 9)
	_shadow.z_index = -1
	_shadow.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_shadow)

	_sprite = Sprite2D.new()
	_sprite.texture = texture
	_sprite.modulate = tint
	_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_sprite)

	display_size = 66.0 if kind == "50_50" else 62.0
	if texture:
		var texture_size: = texture.get_size()
		var factor: float = display_size / maxf(texture_size.x, texture_size.y)
		_sprite.scale = Vector2.ONE * factor
		_shadow.scale = _sprite.scale
	_rest_sprite_scale = _sprite.scale
	_rest_sprite_position = _sprite.position
	_rest_shadow_position = _shadow.position


func grid_position() -> Vector2:
	return _persistent_position if rolling else position


func set_batched(on: bool) -> void:
	var show_own: = not on
	if is_instance_valid(_sprite):
		if show_own and _diagonal_visual != null and _diagonal_visual.is_active():
			pass
		else:
			_sprite.visible = show_own
	if is_instance_valid(_shadow):
		_shadow.visible = show_own


func is_animated_roll() -> bool:
	return rolling and _active_roll_animated


func is_light_roll() -> bool:
	return rolling and not _active_roll_animated and not _active_roll_context.is_empty()


func finish_light_roll() -> bool:
	if not rolling or _active_roll_animated or _active_roll_context.is_empty():
		return false
	if light_generation != _roll_generation:
		return false
	_finish_active_roll(_roll_generation)
	return true


func set_texture(texture: Texture2D) -> void:
	if texture == null:
		return
	if is_instance_valid(_sprite):
		_sprite.texture = texture
		var texture_size: = texture.get_size()
		var factor: float = display_size / maxf(texture_size.x, texture_size.y)
		_sprite.scale = Vector2.ONE * factor
		_rest_sprite_scale = _sprite.scale
	if is_instance_valid(_shadow):
		_shadow.texture = texture
		_shadow.scale = _rest_sprite_scale


## Cancels a running roll without paying anything (used when dice are sold or offered).
func abort_roll() -> void:
	if not rolling:
		return
	_roll_generation += 1
	var movement_tween: = _active_roll_tween
	_active_roll_tween = null
	if movement_tween and movement_tween.is_valid():
		movement_tween.kill()
	var target: Vector2 = _active_roll_context.get("target", position)
	_active_roll_context = {}
	_active_roll_animated = false
	_next_roll_visual_origin = {}
	_bridge_next_completion = false
	set_process(false)
	position = target
	_persistent_position = position
	_settle_roll_visuals(_rest_sprite_scale, Color.WHITE, Color(0.0, 0.0, 0.0, 0.3), Color.WHITE)
	_set_motion_texture_filter(false)
	rolling = false


func start_roll(
	chain_id: int = 0,
	dynamic_value: int = 0,
	forced_target: Vector2 = Vector2(-1.0, -1.0),
	animate_motion: bool = true,
	table_population: int = 0,
	responsive_lightweight: bool = false,
	interactive_motion: bool = false
) -> void :
	if rolling:
		return
	_trailer_dragging = false
	rolling = true
	reserved_by = 0
	if animate_motion:
		_set_motion_texture_filter(true)

	var face_count: = faces.size() if not faces.is_empty() else 6
	var face: = rng.randi_range(0, face_count - 1)
	if forced_face >= 0:
		face = clampi(forced_face, 0, face_count - 1)
		forced_face = -1
	last_face = face
	var result: = _money_result(1, FIRST_DIE_REWARD) if trailer_force_one_dollar else _result_for_face(face, dynamic_value)
	var reward: int = result.reward
	var text: String = result.text
	var result_value: int = result.value

	var continued_motion: Dictionary = {}
	if not _next_roll_visual_origin.is_empty():
		var visual_origin: = _next_roll_visual_origin
		continued_motion = visual_origin.get("motion", {})
		_next_roll_visual_origin = {}
		_bridge_next_completion = false
		position = visual_origin.get("position", position)
		rotation = float(visual_origin.get("rotation", rotation))
		_roll_spin_angle = float(visual_origin.get("spin_angle", _roll_spin_angle))
		if is_instance_valid(_sprite):
			_sprite.position = visual_origin.get("sprite_position", _sprite.position)
			_sprite.scale = visual_origin.get("sprite_scale", _sprite.scale)
			_sprite.rotation = float(visual_origin.get("sprite_rotation", _sprite.rotation))
		if is_instance_valid(_shadow):
			_shadow.position = visual_origin.get("shadow_position", _shadow.position)
			_shadow.rotation = float(visual_origin.get("shadow_rotation", _shadow.rotation))
		if _diagonal_visual != null:
			_diagonal_visual.set_angle(_roll_spin_angle)
	var start: = position
	var target: = forced_target
	if trailer_force_one_dollar:
		target = start
	var safe_board_rect: = board_rect.grow( - TARGET_MARGIN)
	if target.x < 0.0 or target.y < 0.0:
		target = Vector2(
			rng.randf_range(safe_board_rect.position.x, safe_board_rect.end.x),
			rng.randf_range(safe_board_rect.position.y, safe_board_rect.end.y)
		)
	else:
		target.x = clampf(target.x, safe_board_rect.position.x, safe_board_rect.end.x)
		target.y = clampf(target.y, safe_board_rect.position.y, safe_board_rect.end.y)
	if not animate_motion:
		target = start
	_persistent_position = target

	rotation = 0.0
	var start_sprite_scale: = _sprite.scale
	var start_sprite_position: = _sprite.position
	var base_scale: = _rest_sprite_scale
	var base_sprite_modulate: = _sprite.modulate
	var base_shadow_modulate: = _shadow.modulate
	var base_face_modulate: = _face_label.modulate if is_instance_valid(_face_label) else Color.WHITE

	var dense_spread: = clampf(float(maxi(0, table_population - 1000)) / 5500.0, 0.0, 1.0)
	var lightweight_max_duration: = lerpf(1.15, 2.4, dense_spread)
	var responsive_max_duration: = lerpf(0.15, 0.28, dense_spread)
	var roll_duration: = rng.randf_range(0.42, 0.58) if animate_motion and interactive_motion\
	else rng.randf_range(0.68, 0.92) if animate_motion\
	else rng.randf_range(0.08, responsive_max_duration) if responsive_lightweight\
	else rng.randf_range(0.48, lightweight_max_duration)
	roll_duration /= maxf(0.05, roll_speed)
	if forced_duration > 0.0:
		roll_duration = forced_duration
		forced_duration = -1.0
	last_roll_duration = roll_duration
	_roll_generation += 1
	var generation: = _roll_generation
	_active_roll_context = {
		"target": target,
		"base_scale": base_scale,
		"start_sprite_scale": start_sprite_scale,
		"start_sprite_position": start_sprite_position,
		"base_sprite_modulate": base_sprite_modulate,
		"base_shadow_modulate": base_shadow_modulate,
		"base_face_modulate": base_face_modulate,
		"animate_motion": animate_motion,
		"reward": reward,
		"text": text,
		"result_value": result_value,
		"chain_id": chain_id,
	}
	_active_roll_tween = null
	_active_roll_animated = animate_motion
	if animate_motion:
		_roll_elapsed = 0.0
		_roll_duration = roll_duration
		_roll_start_position = start
		_roll_target_position = target
		_roll_start_sprite_scale = start_sprite_scale
		_roll_start_sprite_position = start_sprite_position
		_roll_base_scale = base_scale
		_begin_roll_spin()
		if not continued_motion.is_empty()\
		and target.is_equal_approx(continued_motion.get("target", Vector2.INF))\
		and float(continued_motion.get("duration", 0.0)) > 0.0:
			_roll_elapsed = float(continued_motion["elapsed"])
			_roll_duration = float(continued_motion["duration"])
			_roll_start_position = continued_motion["start"]
			_roll_start_sprite_scale = continued_motion["sprite_scale"]
			_roll_start_sprite_position = continued_motion["sprite_position"]
			_roll_base_scale = continued_motion["base_scale"]
			_roll_start_sprite_rotation = float(continued_motion["spin_start"])
			_roll_target_sprite_rotation = float(continued_motion["spin_target"])
		set_process(true)
	else:
		_settle_roll_visuals(base_scale, base_sprite_modulate, base_shadow_modulate, base_face_modulate)
		_set_motion_texture_filter(false)
		light_generation = generation
		light_due_msec = Time.get_ticks_msec() + int(roll_duration * 1000.0)


func redirect_roll_visual(target: Vector2, promote_lightweight: bool = false) -> bool:
	if not rolling or _active_roll_context.is_empty():
		return false
	_bridge_next_completion = true
	if not _active_roll_animated and not promote_lightweight:
		return true
	if not _active_roll_animated:
		var completion_tween: = _active_roll_tween
		_active_roll_tween = null
		if completion_tween and completion_tween.is_valid():
			completion_tween.kill()
		light_generation = -1
		_active_roll_animated = true
		_active_roll_context["animate_motion"] = true
		_set_motion_texture_filter(true)
	var safe_board_rect: = board_rect.grow( - TARGET_MARGIN)
	var clamped_target: = Vector2(
		clampf(target.x, safe_board_rect.position.x, safe_board_rect.end.x),
		clampf(target.y, safe_board_rect.position.y, safe_board_rect.end.y)
	)
	rotation = 0.0
	_roll_elapsed = 0.0
	_roll_duration = clampf(position.distance_to(clamped_target) / 900.0, 0.65, 0.85) / maxf(0.05, roll_speed)
	_roll_start_position = position
	_roll_target_position = clamped_target
	_roll_start_sprite_scale = _sprite.scale if is_instance_valid(_sprite) else _rest_sprite_scale
	_roll_start_sprite_position = _sprite.position if is_instance_valid(_sprite) else _rest_sprite_position
	_roll_base_scale = _rest_sprite_scale
	_begin_roll_spin()
	set_process(true)
	return true


func _set_pointer_pick_enabled(_enabled: bool, _update_collision_layer: bool = true) -> void :
	# Dice Rush Extended: dice are picked through the spatial grid in main.gd.
	pass


func _result_for_face(face: int, dynamic_value: int = 0) -> Dictionary:
	if not faces.is_empty():
		var value: = int(faces[clampi(face, 0, faces.size() - 1)])
		return {"value": value, "reward": 0, "text": ""}
	match die_kind:
		"50_50":
			return _money_result(1, FIRST_DIE_REWARD) if face < 3 else {"value": 0, "reward": 0, "text": ""}
		"d4":
			return _money_result(1, 1) if face < 5 else _money_result(4, 4)
		"3x4":
			var values: = [3, 3, 3, 4, 4, 12]
			var value: int = values[face]
			return _money_result(value, value)
		"d2":
			var values: = [2, 4, 8, 16, 32, 64]
			var value: int = values[face]
			return _money_result(value, value)
		"777":
			return _money_result(7, 7) if face < 3 else {"value": 0, "reward": 0, "text": ""}
		"prehistoric":
			return _money_result(123, 123)
		"golden":
			return _money_result(1, 1)
		"npc_die":
			var value: = maxi(dynamic_value, 0)
			return _money_result(value, value)
		"crypto":
			var value: = maxi(dynamic_value, 0)
			return _money_result(value, value)
		"diamond":
			return _money_result(1000000, 1000000)
		"pi":
			return _money_result(31415926, 31415926)
	return {"value": 0, "reward": 0, "text": ""}

# The trailer drag handler made Godot dispatch every mouse event to every single dice
# (thousands of script calls per mouse move). It is only used by the developer trailer mode.
#@delete _input


## Rocket flight: lifts the sprite (and shrinks the shadow) without moving the logical position.
func set_visual_lift(lift: float, _progress: float) -> void:
	if is_instance_valid(_sprite):
		_sprite.visible = true
		_sprite.position = _rest_sprite_position + Vector2(0.0, - lift)
		_sprite.rotation = lift * 0.01
	if is_instance_valid(_shadow):
		_shadow.visible = true
		_shadow.scale = _rest_sprite_scale * lerpf(1.0, 0.25, minf(1.0, lift / 500.0))
	if lift <= 0.0 and is_instance_valid(_sprite):
		_sprite.position = _rest_sprite_position
		_sprite.rotation = 0.0
		if is_instance_valid(_shadow):
			_shadow.scale = _rest_sprite_scale
