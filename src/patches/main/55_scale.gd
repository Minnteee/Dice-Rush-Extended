# Dice Rush Extended - main.gd patch: crowded tables. From 200 dice on, all dice get smaller
# (and fly shorter distances, effects and auras shrink with them), so the table looks bigger and
# far fewer dice are touched by every effect.

## Version 1.1: 500 more dice fit on the table.
const MAX_PURCHASABLE_DICE_ACTORS: = 7000


func _random_roll_target(from_position: Vector2) -> Vector2:
	var safe: = BOARD_RECT.grow( - DICE_BOARD_MARGIN)
	var scale_value: float = bdr.dice_scale()
	if scale_value >= 0.999:
		# normal table: the original behaviour (anywhere on the felt)
		var minimum_distance_squared: = MIN_RANDOM_ROLL_TRAVEL * MIN_RANDOM_ROLL_TRAVEL
		for _attempt in range(RANDOM_ROLL_TARGET_ATTEMPTS):
			var candidate: = Vector2(
				rng.randf_range(safe.position.x, safe.end.x),
				rng.randf_range(safe.position.y, safe.end.y)
			)
			if not _die_position_is_on_playable_felt(candidate):
				continue
			if candidate.distance_squared_to(from_position) >= minimum_distance_squared:
				return candidate
		return _bdr_random_felt_point()
	# Crowded table (smaller dice): shorter flights. The dice makes a random step of limited length
	# that bounces off the edges - that keeps the dice evenly spread over the whole table
	# (version 1.0 pulled every target towards the dice itself, so the dice gathered in the middle).
	var max_step: float = maxf(safe.size.x, safe.size.y) * 0.75 * scale_value
	var min_step: float = MIN_RANDOM_ROLL_TRAVEL * scale_value
	var min_travel_squared: = min_step * min_step * 0.25
	for _attempt in range(RANDOM_ROLL_TARGET_ATTEMPTS):
		# uniform point in the ring min_step..max_step around the dice (a symmetric step)
		var step_length: float = sqrt(rng.randf_range(min_step * min_step, max_step * max_step))
		var candidate: Vector2 = from_position + Vector2.RIGHT.rotated(rng.randf_range(0.0, TAU)) * step_length
		candidate = _bdr_reflect_into(candidate, safe)
		if _die_position_is_on_playable_felt(candidate) and candidate.distance_squared_to(from_position) >= min_travel_squared:
			return candidate
	return _bdr_random_felt_point()


## Mirrors a point back into the area (bouncing off the edges, also several times).
func _bdr_reflect_into(point: Vector2, area: Rect2) -> Vector2:
	var result: = point
	for axis in range(2):
		var low: float = area.position[axis]
		var span: float = area.size[axis]
		if span <= 0.0:
			continue
		var value: float = fposmod(result[axis] - low, 2.0 * span)
		if value > span:
			value = 2.0 * span - value
		result[axis] = low + value
	return result


## A random point anywhere on the playable felt.
func _bdr_random_felt_point() -> Vector2:
	var safe: = BOARD_RECT.grow( - DICE_BOARD_MARGIN)
	for _attempt in range(64):
		var candidate: = Vector2(rng.randf_range(safe.position.x, safe.end.x), rng.randf_range(safe.position.y, safe.end.y))
		if _die_position_is_on_playable_felt(candidate):
			return candidate
	return safe.get_center()


func _hover_roll_radius() -> float:
	var radius: = HOVER_ROLL_UPGRADED_RADIUS if bool(upgrades.get("hover_roll_radius", false)) else HOVER_ROLL_BASE_RADIUS
	return radius * bdr.dice_scale()


func _prehistoric_wave_radius() -> float:
	var radius: = 340.0 if bool(upgrades.get("prehistoric_radius", false)) else 220.0
	return radius * bdr.dice_scale()


func _gold_aura_radius() -> float:
	var radius: = int(DiceActor.GOLD_AURA_RADIUS)
	for tier in range(1, 3):
		if bool(upgrades.get("gold_aura_radius_%d" % tier, false)):
			radius = _gold_aura_radius_for_tier(tier)
	return float(radius) * bdr.dice_scale()
