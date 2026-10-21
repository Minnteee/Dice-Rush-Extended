extends RefCounted
## Dice Rush Extended - uniform spatial grid for dice.
## Replaces the physics shape queries and the O(n) scans over all dice
## (clicks, hover rolls, worker targeting, waves, auras, hermit).
## Dice are stored at their *logical* position (the landing target while rolling).

const CELL := 64.0

var origin := Vector2.ZERO
var cols := 1
var rows := 1
var cells: Array = []   # Array[Array] of dice
var count := 0


func setup(area: Rect2) -> void:
	origin = area.position - Vector2(CELL, CELL)
	cols = int(ceil((area.size.x + CELL * 2.0) / CELL)) + 1
	rows = int(ceil((area.size.y + CELL * 2.0) / CELL)) + 1
	cells.clear()
	cells.resize(cols * rows)
	for index in range(cols * rows):
		cells[index] = []
	count = 0


func clear() -> void:
	for index in range(cells.size()):
		(cells[index] as Array).clear()
	count = 0


func cell_index(point: Vector2) -> int:
	var cx := clampi(int((point.x - origin.x) / CELL), 0, cols - 1)
	var cy := clampi(int((point.y - origin.y) / CELL), 0, rows - 1)
	return cy * cols + cx


func insert(die: DiceActor, point: Vector2) -> void:
	if die.grid_cell >= 0:
		move(die, point)
		return
	var index := cell_index(point)
	(cells[index] as Array).append(die)
	die.grid_cell = index
	count += 1


func remove(die: DiceActor) -> void:
	var index: int = die.grid_cell
	if index < 0 or index >= cells.size():
		die.grid_cell = -1
		return
	var bucket: Array = cells[index]
	var at := bucket.find(die)
	if at >= 0:
		var last := bucket.size() - 1
		bucket[at] = bucket[last]
		bucket.resize(last)
		count -= 1
	die.grid_cell = -1


func move(die: DiceActor, point: Vector2) -> void:
	var index := cell_index(point)
	if index == die.grid_cell:
		return
	remove(die)
	(cells[index] as Array).append(die)
	die.grid_cell = index
	count += 1


## Appends every die whose logical position lies within radius of center.
## use_visual: compare against the current node position instead of the logical one.
func query_radius(center: Vector2, radius: float, out: Array, use_visual: bool = false) -> void:
	var r2 := radius * radius
	var min_cx := clampi(int((center.x - radius - origin.x) / CELL), 0, cols - 1)
	var max_cx := clampi(int((center.x + radius - origin.x) / CELL), 0, cols - 1)
	var min_cy := clampi(int((center.y - radius - origin.y) / CELL), 0, rows - 1)
	var max_cy := clampi(int((center.y + radius - origin.y) / CELL), 0, rows - 1)
	for cy in range(min_cy, max_cy + 1):
		var row := cy * cols
		for cx in range(min_cx, max_cx + 1):
			for die: DiceActor in cells[row + cx]:
				var p: Vector2 = die.position if use_visual else die.grid_position()
				if p.distance_squared_to(center) <= r2:
					out.append(die)


## True when any other die is within radius (early exit) - used for the Hermit card.
func any_within(center: Vector2, radius: float, exclude: DiceActor) -> bool:
	var r2 := radius * radius
	var min_cx := clampi(int((center.x - radius - origin.x) / CELL), 0, cols - 1)
	var max_cx := clampi(int((center.x + radius - origin.x) / CELL), 0, cols - 1)
	var min_cy := clampi(int((center.y - radius - origin.y) / CELL), 0, rows - 1)
	var max_cy := clampi(int((center.y + radius - origin.y) / CELL), 0, rows - 1)
	for cy in range(min_cy, max_cy + 1):
		var row := cy * cols
		for cx in range(min_cx, max_cx + 1):
			for die: DiceActor in cells[row + cx]:
				if die == exclude:
					continue
				if die.grid_position().distance_squared_to(center) <= r2:
					return true
	return false


## Dice whose logical position is within radius of the segment a-b (capsule).
func query_segment(a: Vector2, b: Vector2, radius: float, out: Array) -> void:
	var segment := b - a
	var length_squared := segment.length_squared()
	if length_squared <= 0.0001:
		query_radius(b, radius, out)
		return
	var r2 := radius * radius
	var lo := Vector2(minf(a.x, b.x), minf(a.y, b.y)) - Vector2(radius, radius)
	var hi := Vector2(maxf(a.x, b.x), maxf(a.y, b.y)) + Vector2(radius, radius)
	var min_cx := clampi(int((lo.x - origin.x) / CELL), 0, cols - 1)
	var max_cx := clampi(int((hi.x - origin.x) / CELL), 0, cols - 1)
	var min_cy := clampi(int((lo.y - origin.y) / CELL), 0, rows - 1)
	var max_cy := clampi(int((hi.y - origin.y) / CELL), 0, rows - 1)
	for cy in range(min_cy, max_cy + 1):
		var row := cy * cols
		for cx in range(min_cx, max_cx + 1):
			for die: DiceActor in cells[row + cx]:
				var p: Vector2 = die.grid_position()
				var t := clampf((p - a).dot(segment) / length_squared, 0.0, 1.0)
				if p.distance_squared_to(a + segment * t) <= r2:
					out.append(die)


## Up to `limit` dice within radius, searched ring by ring from the center (roughly the nearest
## ones first). Stops as soon as enough dice were found, so it stays cheap on a crowded table.
func query_nearest(center: Vector2, radius: float, limit: int, out: Array, filter: Callable = Callable()) -> void:
	if limit <= 0 or count <= 0:
		return
	var r2 := radius * radius
	var ccx := clampi(int((center.x - origin.x) / CELL), 0, cols - 1)
	var ccy := clampi(int((center.y - origin.y) / CELL), 0, rows - 1)
	var max_ring := mini(int(ceil(radius / CELL)) + 1, maxi(cols, rows))
	var start := out.size()
	for ring in range(0, max_ring + 1):
		for cy in range(ccy - ring, ccy + ring + 1):
			if cy < 0 or cy >= rows:
				continue
			var on_edge_y := cy == ccy - ring or cy == ccy + ring
			var step := 1 if on_edge_y else maxi(1, ring * 2)
			var cx := ccx - ring
			while cx <= ccx + ring:
				if cx >= 0 and cx < cols:
					for die: DiceActor in cells[cy * cols + cx]:
						if die.grid_position().distance_squared_to(center) <= r2 and (not filter.is_valid() or filter.call(die)):
							out.append(die)
				cx += step
		if out.size() - start >= limit:
			break
	if out.size() - start > limit:
		out.resize(start + limit)


## Nearest die accepted by filter, searching outward ring by ring.
func nearest(center: Vector2, filter: Callable, max_radius: float = 4096.0) -> DiceActor:
	var ccx := clampi(int((center.x - origin.x) / CELL), 0, cols - 1)
	var ccy := clampi(int((center.y - origin.y) / CELL), 0, rows - 1)
	var best: DiceActor = null
	var best_d := INF
	var max_ring := int(ceil(max_radius / CELL)) + 1
	var max_needed := maxi(cols, rows)
	for ring in range(0, mini(max_ring, max_needed) + 1):
		# once we have a candidate, stop when the ring is farther than the best distance
		if best != null:
			var ring_distance := (float(ring) - 1.0) * CELL
			if ring_distance * ring_distance > best_d:
				break
		for cy in range(ccy - ring, ccy + ring + 1):
			if cy < 0 or cy >= rows:
				continue
			var on_edge_y := cy == ccy - ring or cy == ccy + ring
			var step := 1 if on_edge_y else ring * 2
			if step == 0:
				step = 1
			var cx := ccx - ring
			while cx <= ccx + ring:
				if cx >= 0 and cx < cols:
					for die: DiceActor in cells[cy * cols + cx]:
						var d := die.grid_position().distance_squared_to(center)
						if d < best_d and filter.call(die):
							best_d = d
							best = die
				cx += step
	return best


## Random sample of up to n dice from anywhere (uniform over cells, then dice).
func random_dice(n: int, rng: RandomNumberGenerator, out: Array, filter: Callable = Callable()) -> void:
	if count <= 0:
		return
	var tries := n * 6 + 12
	while out.size() < n and tries > 0:
		tries -= 1
		var bucket: Array = cells[rng.randi_range(0, cells.size() - 1)]
		if bucket.is_empty():
			continue
		var die = bucket[rng.randi_range(0, bucket.size() - 1)]
		if die in out:
			continue
		if filter.is_valid() and not filter.call(die):
			continue
		out.append(die)
