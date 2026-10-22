extends Node2D
## The dice inside the glass ball: a small 2D physics simulation plus the drawing of the dice.
## Coordinates are screen pixels (1920x1080 design space), `center` is the middle of the glass.

const LEVEL_RING_TIME := 0.9

var center := Vector2(960, 432)
var radius := 224.0                 # inner radius of the glass
var floor_y := 100000.0             # the dice rest on this line (bottom of the glass above the stand)
var die_size := 128.0
var bodies: Array = []              # one Dictionary per die (see _make_body)
var shake_left := 0.0               # active shaking (kicks)
var settle_left := 0.0              # falling and landing
var kick_timer := 0.0
var strength := 1.0
var resting := true
var fast := false                   # turbo event: the dice fall and land faster
var font: Font
var rng := RandomNumberGenerator.new()
var hovered := -1


func _ready() -> void:
	rng.randomize()
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR


func _make_body(texture: Texture2D, index: int, count: int) -> Dictionary:
	# start in a small heap on the floor of the glass
	var spread := minf(radius * 0.7, die_size * 0.55 * count)
	var x := lerpf(-spread, spread, 0.5 if count <= 1 else float(index) / float(count - 1))
	var y := radius - die_size * 0.5 - float(index % 3) * die_size * 0.3
	return {
		"pos": center + Vector2(x * 0.6, y * 0.85), "vel": Vector2.ZERO, "angle": 0.0, "spin": 0.0,
		"rest_angle": 0.0, "tex": texture, "face": 0, "show_face": false, "group": 1, "ring": 0.0,
	}


## Replaces the dice (keeps the old positions where possible).
func set_dice(textures: Array, size: float) -> void:
	var old := bodies
	bodies = []
	die_size = size
	for i in textures.size():
		var body := _make_body(textures[i], i, textures.size())
		if i < old.size():
			body.pos = old[i].pos
			body.face = old[i].face
			body.show_face = old[i].show_face and old[i].tex == textures[i]
			body.group = old[i].group
		bodies.append(body)
	_resolve_overlaps(12)
	queue_redraw()


func shake(duration: float, power: float = 1.0) -> void:
	strength = power
	shake_left = duration * (0.3 if fast else 0.42)
	settle_left = 1.6     # safety limit: the dice land long before
	kick_timer = 0.0
	resting = false
	for body in bodies:
		body.show_face = false
		body.rest_angle = deg_to_rad(rng.randf_range(-7.0, 7.0))
		body.spin += rng.randf_range(-14.0, 14.0)


## Shows the faces once the dice landed. groups[i] = size of the group the die belongs to.
func show_faces(faces: Array, groups: Array) -> void:
	for i in bodies.size():
		if i < faces.size():
			bodies[i].face = int(faces[i])
			bodies[i].group = int(groups[i]) if i < groups.size() else 1
			bodies[i].show_face = true
	queue_redraw()


func level_up(index: int) -> void:
	if index >= 0 and index < bodies.size():
		bodies[index].ring = LEVEL_RING_TIME


func die_at(point: Vector2) -> int:
	var best := -1
	for i in bodies.size():
		if bodies[i].pos.distance_to(point) <= die_size * 0.5:
			if best < 0 or bodies[i].pos.y > bodies[best].pos.y:
				best = i
	return best


func die_position(index: int) -> Vector2:
	if index < 0 or index >= bodies.size():
		return center
	return bodies[index].pos


func _process(delta: float) -> void:
	var animating := false
	for body in bodies:
		if body.ring > 0.0:
			body.ring = maxf(0.0, body.ring - delta)
			animating = true
	if not resting:
		var steps := 3
		var dt := minf(delta, 0.05) / steps
		for _i in steps:
			_step(dt)
		if shake_left <= 0.0 and (settle_left <= 0.0 or _all_settled()):
			_finish_landing()
		animating = true
	if animating:
		queue_redraw()


func _step(dt: float) -> void:
	var r := die_size * 0.42
	var gravity := 2600.0 if shake_left > 0.0 else (5200.0 if fast else 3400.0)
	if shake_left > 0.0:
		shake_left -= dt
		kick_timer -= dt
		if kick_timer <= 0.0:
			kick_timer = 0.075
			for body in bodies:
				var kick := Vector2(rng.randf_range(-950.0, 950.0), rng.randf_range(-1500.0, -500.0)) * strength
				# dice high up in the glass get a smaller kick so they do not stick to the top
				var height := clampf((center.y - body.pos.y) / radius, -1.0, 1.0)
				kick.y *= clampf(0.85 - height * 0.6, 0.25, 1.4)
				body.vel += kick
				body.spin += rng.randf_range(-10.0, 10.0)
	else:
		settle_left -= dt
	var drag := 0.45 if shake_left > 0.0 else (2.6 if fast else 1.6)
	for body in bodies:
		body.vel.y += gravity * dt
		body.vel *= exp(-drag * dt)
		body.pos += body.vel * dt
		if shake_left > 0.0:
			body.angle += body.spin * dt
			body.spin *= exp(-1.2 * dt)
		else:
			body.spin *= exp(-6.0 * dt)
			body.angle = lerp_angle(body.angle + body.spin * dt, body.rest_angle, clampf(9.0 * dt, 0.0, 1.0))
		# floor of the glass
		var half := die_size * 0.5
		if body.pos.y + half > floor_y:
			body.pos.y = floor_y - half
			if body.vel.y > 0.0:
				body.vel.y *= -0.35
				body.vel.x *= 0.82
		# glass wall
		var offset: Vector2 = body.pos - center
		var limit := radius - r
		var dist := offset.length()
		if dist > limit and dist > 0.001:
			var normal := offset / dist
			body.pos = center + normal * limit
			var vn: float = body.vel.dot(normal)
			if vn > 0.0:
				# bounce off the glass; the glass is smooth, so the dice keep sliding along it
				var bounce := 0.55 if shake_left > 0.0 else 0.25
				body.vel -= normal * vn * (1.0 + bounce)
				body.vel *= 0.985
	_resolve_overlaps(2)


func _resolve_overlaps(passes: int) -> void:
	var r := die_size * 0.42
	var min_dist := r * 2.0
	for _p in passes:
		for i in bodies.size():
			for j in range(i + 1, bodies.size()):
				var a: Dictionary = bodies[i]
				var b: Dictionary = bodies[j]
				var delta: Vector2 = b.pos - a.pos
				var dist := delta.length()
				if dist >= min_dist:
					continue
				var normal := Vector2(0, -1) if dist < 0.001 else delta / dist
				var push := (min_dist - dist) * 0.5
				a.pos -= normal * push
				b.pos += normal * push
				var relative: float = (b.vel - a.vel).dot(normal)
				if relative < 0.0:
					var impulse := -relative * 0.68
					a.vel -= normal * impulse
					b.vel += normal * impulse
		# keep everything inside the glass after pushing
		for body in bodies:
			var offset: Vector2 = body.pos - center
			var limit := radius - r
			if offset.length() > limit:
				body.pos = center + offset.normalized() * limit
			if body.pos.y + die_size * 0.5 > floor_y:
				body.pos.y = floor_y - die_size * 0.5


## Every die lies still on the floor or on another die.
func _all_settled() -> bool:
	if settle_left > 1.25:
		return false
	for body in bodies:
		if (body.vel as Vector2).length() > 22.0:
			return false
	return true


func _finish_landing() -> void:
	resting = true
	for body in bodies:
		body.vel = Vector2.ZERO
		body.spin = 0.0
		body.angle = body.rest_angle
	_resolve_overlaps(8)
	queue_redraw()


func _draw() -> void:
	var order: Array = range(bodies.size())
	order.sort_custom(func(a: int, b: int) -> bool: return bodies[a].pos.y < bodies[b].pos.y)
	var half := die_size * 0.5
	for i in order:
		var body: Dictionary = bodies[i]
		# soft shadow on the glass floor
		draw_set_transform(body.pos, body.angle, Vector2.ONE)
		if body.tex:
			draw_texture_rect(body.tex, Rect2(-half, -half, die_size, die_size), false, Color(1, 1, 1, 1) if i != hovered else Color(1.15, 1.1, 1.0, 1))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		if body.ring > 0.0:
			var t: float = 1.0 - body.ring / LEVEL_RING_TIME
			draw_arc(body.pos, half * (0.75 + t * 0.5), 0.0, TAU, 40, Color(1.0, 0.82, 0.3, (1.0 - t) * 0.8), 4.0, true)
	if not resting:
		return
	for i in order:
		var body: Dictionary = bodies[i]
		if not body.show_face or font == null:
			continue
		var badge_r := maxf(11.0, die_size * 0.13)
		var at: Vector2 = body.pos + Vector2(half * 0.62, -half * 0.62)
		var gold: bool = int(body.group) >= 2
		draw_circle(at, badge_r + 2.0, Color("1a0d26"))
		draw_circle(at, badge_r, Color("ffcf4a") if gold else Color("f4ecff"))
		var text := str(body.face)
		var font_size := int(badge_r * (0.95 if text.length() < 2 else 0.75))
		var size := font.get_string_size(text, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size)
		draw_string(font, at + Vector2(-size.x * 0.5, size.y * 0.32), text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Color("2a1640"))
