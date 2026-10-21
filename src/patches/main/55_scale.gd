# Dice Rush Extended - main.gd patch: crowded tables. From 200 dice on, all dice get smaller
# (and fly shorter distances, effects and auras shrink with them), so the table looks bigger and
# far fewer dice are touched by every effect.

func _random_roll_target(from_position: Vector2) -> Vector2:
	var safe: = BOARD_RECT.grow( - DICE_BOARD_MARGIN)
	var scale_value: float = bdr.dice_scale()
	var minimum_distance: = MIN_RANDOM_ROLL_TRAVEL * scale_value
	var minimum_distance_squared: = minimum_distance * minimum_distance
	for _attempt in range(RANDOM_ROLL_TARGET_ATTEMPTS):
		var candidate: = Vector2(
			rng.randf_range(safe.position.x, safe.end.x),
			rng.randf_range(safe.position.y, safe.end.y)
		)
		if scale_value < 0.999:
			candidate = from_position.lerp(candidate, scale_value)
		if not _die_position_is_on_playable_felt(candidate):
			continue
		var distance_squared: = candidate.distance_squared_to(from_position)
		if distance_squared >= minimum_distance_squared:
			return candidate
	var center: = safe.get_center()
	return center + Vector2(
		safe.size.x * (0.25 if from_position.x <= center.x else -0.25),
		safe.size.y * (0.25 if from_position.y <= center.y else -0.25)
	)


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
