extends Node2D
## Dice Rush Extended - cheap world effects (rings, lightning lines, cones, trails, slashes).
## Everything is drawn by this single node in _draw(), so effects cost almost nothing.

const MAX_EFFECTS := 96

var effects: Array[Dictionary] = []


func _init() -> void:
	name = "BDRWorldFX"
	z_index = 60
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _add(effect: Dictionary) -> void:
	if not GameSession.visual_effects_enabled:
		return
	if effects.size() >= MAX_EFFECTS:
		effects.pop_front()
	effect["t"] = 0.0
	effects.append(effect)
	set_process(true)
	queue_redraw()


func ring(center: Vector2, radius: float, color: Color, duration: float = 0.55) -> void:
	_add({"type": "ring", "c": center, "r": radius, "color": color, "d": duration})


func lines(from: Vector2, targets: Array, color: Color, duration: float = 0.35) -> void:
	var points: Array = []
	for target in targets:
		if is_instance_valid(target):
			points.append(target.position)
	if points.is_empty():
		return
	_add({"type": "lines", "from": from, "to": points, "color": color, "d": duration, "seed": randi()})


func cone(center: Vector2, direction: Vector2, radius: float, color: Color, duration: float = 0.5) -> void:
	_add({"type": "cone", "c": center, "dir": direction, "r": radius, "color": color, "d": duration})


func trail(from: Vector2, to: Vector2, duration: float = 0.6) -> void:
	_add({"type": "trail", "a": from, "b": to, "d": duration})


func slash(y: float, left: float, right: float, duration: float = 0.35) -> void:
	_add({"type": "slash", "y": y, "l": left, "r": right, "d": duration})


func _process(delta: float) -> void:
	if effects.is_empty():
		set_process(false)
		queue_redraw()
		return
	for index in range(effects.size() - 1, -1, -1):
		var effect: Dictionary = effects[index]
		effect.t = float(effect.t) + delta
		if float(effect.t) >= float(effect.d):
			effects.remove_at(index)
	queue_redraw()


func _draw() -> void:
	for effect in effects:
		var progress := clampf(float(effect.t) / float(effect.d), 0.0, 1.0)
		var fade := 1.0 - progress
		match str(effect.type):
			"ring":
				var color: Color = effect.color
				color.a = 0.85 * fade
				draw_arc(effect.c, float(effect.r) * (0.15 + 0.85 * sqrt(progress)), 0.0, TAU, 48, color, 4.0)
			"lines":
				var color: Color = effect.color
				color.a = fade
				var rng := RandomNumberGenerator.new()
				rng.seed = int(effect.seed)
				for target in effect.to:
					var a: Vector2 = effect.from
					var b: Vector2 = target
					var previous := a
					for step in range(1, 7):
						var point := a.lerp(b, float(step) / 6.0)
						if step < 6:
							point += Vector2(rng.randf_range(-14, 14), rng.randf_range(-14, 14))
						draw_line(previous, point, color, 3.0)
						previous = point
			"cone":
				var color: Color = effect.color
				color.a = 0.35 * fade
				var direction: Vector2 = effect.dir
				var center: Vector2 = effect.c
				var radius := float(effect.r) * (0.3 + 0.7 * progress)
				var points := PackedVector2Array([center])
				for step in range(9):
					points.append(center + direction.rotated(lerpf(-0.62, 0.62, float(step) / 8.0)) * radius)
				draw_colored_polygon(points, color)
			"trail":
				var a: Vector2 = effect.a
				var b: Vector2 = effect.b
				var colors := [Color("ff4a4a"), Color("ffa41f"), Color("ffe25a"), Color("4aff7a"), Color("4a9aff"), Color("b45aff")]
				var normal := (b - a).normalized().orthogonal()
				for index in range(colors.size()):
					var color: Color = colors[index]
					color.a = 0.6 * fade
					var offset := normal * (float(index) - 2.5) * 4.0
					draw_line(a + offset, b + offset, color, 4.0)
			"slash":
				var color := Color(1.0, 1.0, 1.0, fade)
				draw_line(Vector2(float(effect.l), float(effect.y)), Vector2(float(effect.r), float(effect.y)), color, 3.0 + 6.0 * fade)
