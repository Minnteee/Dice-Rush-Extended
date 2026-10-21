extends Node
## Test automation harness for the Dice Rush Extended TEST install only.
## TCP JSON-lines server on 127.0.0.1 (port from --bdr-port=, default 47811).
## Lets the developer drive the game without touching the real mouse/keyboard.

var server := TCPServer.new()
var clients: Array[StreamPeerTCP] = []
var buffers: Dictionary = {}
var port := 47811
var frame_times: Array[float] = []
var max_frame_samples := 600
var last_usec := 0
var log_lines: Array[String] = []
var autostart := ""
var autostart_slot := 1
var autostart_done := false
var window_parked := false


func _init() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--bdr-port="):
			port = int(arg.trim_prefix("--bdr-port="))
		elif arg.begins_with("--bdr-autostart="):
			autostart = arg.trim_prefix("--bdr-autostart=")
		elif arg.begins_with("--bdr-slot="):
			autostart_slot = int(arg.trim_prefix("--bdr-slot="))
	var err := server.listen(port, "127.0.0.1")
	print("BDR_TEST_HARNESS port=%d listen=%d" % [port, err])
	last_usec = Time.get_ticks_usec()


func _process(_delta: float) -> void:
	var now := Time.get_ticks_usec()
	frame_times.append(float(now - last_usec) / 1000.0)
	last_usec = now
	if frame_times.size() > max_frame_samples:
		frame_times.pop_front()
	if not autostart.is_empty() and not autostart_done:
		_try_autostart()
	if (not bench_mode.is_empty() and bench_n > 0) or not bench_set.is_empty():
		_bench_step()
	while server.is_connection_available():
		var peer := server.take_connection()
		peer.set_no_delay(true)
		clients.append(peer)
		buffers[peer.get_instance_id()] = ""
	for peer_value in clients.duplicate():
		var peer: StreamPeerTCP = peer_value
		peer.poll()
		var status: int = peer.get_status()
		if status != StreamPeerTCP.STATUS_CONNECTED:
			if status == StreamPeerTCP.STATUS_NONE or status == StreamPeerTCP.STATUS_ERROR:
				clients.erase(peer)
				buffers.erase(peer.get_instance_id())
			continue
		var available: int = peer.get_available_bytes()
		if available > 0:
			var chunk: String = peer.get_utf8_string(available)
			var buffer: String = buffers.get(peer.get_instance_id(), "") + chunk
			while buffer.find("\n") >= 0:
				var cut := buffer.find("\n")
				var line := buffer.substr(0, cut).strip_edges()
				buffer = buffer.substr(cut + 1)
				if not line.is_empty():
					_handle_line(peer, line)
			buffers[peer.get_instance_id()] = buffer


func _try_autostart() -> void:
	var scene := get_tree().current_scene
	if scene == null:
		return
	if scene.scene_file_path.ends_with("start_menu.tscn"):
		autostart_done = true
		GameSession.set_active_save_slot(autostart_slot, false)
		GameSession.launch_mode = "continue" if autostart == "continue" else "new"
		get_tree().change_scene_to_file("res://scenes/main.tscn")


func _send(peer: StreamPeerTCP, payload: Dictionary) -> void:
	var text := JSON.stringify(payload) + "\n"
	peer.put_data(text.to_utf8_buffer())


func _handle_line(peer: StreamPeerTCP, line: String) -> void:
	var request = JSON.parse_string(line)
	if request is not Dictionary:
		_send(peer, {"ok": false, "error": "bad json"})
		return
	var response := {"id": request.get("id", 0)}
	var result = await _execute(request)
	if result is Dictionary and result.has("__error"):
		response["ok"] = false
		response["error"] = result["__error"]
	else:
		response["ok"] = true
		response["result"] = _jsonable(result)
	if is_instance_valid(peer):
		_send(peer, response)


func _jsonable(value: Variant) -> Variant:
	match typeof(value):
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_FLOAT, TYPE_STRING:
			return value
		TYPE_STRING_NAME, TYPE_NODE_PATH:
			return str(value)
		TYPE_VECTOR2, TYPE_VECTOR2I:
			return [value.x, value.y]
		TYPE_ARRAY, TYPE_PACKED_STRING_ARRAY, TYPE_PACKED_INT32_ARRAY, TYPE_PACKED_INT64_ARRAY, TYPE_PACKED_FLOAT32_ARRAY, TYPE_PACKED_FLOAT64_ARRAY, TYPE_PACKED_VECTOR2_ARRAY:
			var out := []
			for item in value:
				out.append(_jsonable(item))
			return out
		TYPE_DICTIONARY:
			var out := {}
			for key in value:
				out[str(key)] = _jsonable(value[key])
			return out
		TYPE_OBJECT:
			if value == null:
				return null
			if value is Node:
				return "<%s %s>" % [value.get_class(), str(value.get_path()) if value.is_inside_tree() else value.name]
			return "<%s>" % value.get_class()
	return str(value)


# ---------- helpers usable from "eval" expressions ----------
func m() -> Node:
	return get_tree().current_scene


func n(path: String) -> Node:
	return get_tree().root.get_node_or_null(path)


func core() -> Node:
	return get_tree().root.get_node_or_null("DiceRushExtended/BDRCore")


func S(singleton_name: String) -> Object:
	return Engine.get_singleton(singleton_name)


func perf() -> Dictionary:
	var vp := get_tree().root.get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(vp, true)
	var main := m()
	return {
		"fps": Engine.get_frames_per_second(),
		"max_fps": Engine.max_fps,
		"process_ms": Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
		"physics_ms": Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS) * 1000.0,
		"draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"objects": Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		"nodes": Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		"render_cpu_ms": RenderingServer.viewport_get_measured_render_time_cpu(vp),
		"render_gpu_ms": RenderingServer.viewport_get_measured_render_time_gpu(vp),
		"setup_ms": RenderingServer.get_frame_setup_time_cpu(),
		"anim": main.get("active_animated_roll_count") if main else 0,
		"rolling": main.get("active_roll_count") if main else 0,
	}


func prof() -> Dictionary:
	var script := load("res://bdr/core/prof.gd")
	var out: Dictionary = script.snapshot_and_reset()
	out["tweens"] = get_tree().get_processed_tweens().size()
	return out


func fps() -> float:
	return Engine.get_frames_per_second()


## Nodes that run _process / _physics_process this frame, grouped by script (or class).
func processing_nodes() -> Dictionary:
	var out := {}
	var stack: Array[Node] = [get_tree().root]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		for child in node.get_children():
			stack.append(child)
		var flags := ""
		if node.is_processing():
			flags += "P"
		if node.is_physics_processing():
			flags += "F"
		if node.is_processing_input() or node.is_processing_unhandled_input():
			flags += "I"
		if flags.is_empty():
			continue
		var script: Script = node.get_script()
		var key := (script.resource_path.get_file() if script else node.get_class()) + ":" + flags
		out[key] = int(out.get(key, 0)) + 1
	out["@tweens"] = get_tree().get_processed_tweens().size()
	return out


## Frame phase profiler: process (process_frame -> pre_draw), render (pre_draw -> post_draw),
## other (post_draw -> next process_frame: input, physics, swap).
var phase_on := false
var phase: Dictionary = {}
var _ph_frame := 0
var _ph_pre := 0
var _ph_post := 0
var _ph_connected := false


class PhaseMarker extends Node:
	var harness: Node
	var which := 0
	func _process(_delta: float) -> void:
		harness._ph_mark(which)


var _ph_first := 0
var _ph_markers_added := false


func _ph_mark(which: int) -> void:
	var now := Time.get_ticks_usec()
	if which == 0:
		if phase_on and _ph_frame > 0:
			phase.pre += now - _ph_frame
		_ph_first = now
	else:
		if phase_on and _ph_first > 0:
			phase.callbacks += now - _ph_first
		_ph_last = now
		_ph_deferred.call_deferred()


var _ph_flush_end := 0


func _ph_deferred() -> void:
	var now := Time.get_ticks_usec()
	if phase_on and _ph_last > 0:
		phase.flush += now - _ph_last
	_ph_flush_end = now


var _ph_last := 0


var _tree_counts := {"added": 0, "removed": 0}
var _tree_hooked := false


func _on_node_added(_node: Node) -> void:
	_tree_counts.added += 1


func _on_node_removed(_node: Node) -> void:
	_tree_counts.removed += 1


## Counts nodes added / removed since the last call.
func tree_churn() -> Dictionary:
	if not _tree_hooked:
		_tree_hooked = true
		get_tree().node_added.connect(_on_node_added)
		get_tree().node_removed.connect(_on_node_removed)
	var out := _tree_counts.duplicate()
	_tree_counts = {"added": 0, "removed": 0}
	return out


func phases_start() -> void:
	phase = {"frames": 0, "process": 0, "render": 0, "other": 0, "pre": 0, "callbacks": 0, "post": 0, "flush": 0, "tail": 0}
	if not _ph_markers_added:
		_ph_markers_added = true
		for which in [0, 1]:
			var marker := PhaseMarker.new()
			marker.harness = self
			marker.which = which
			marker.process_mode = Node.PROCESS_MODE_ALWAYS
			marker.process_priority = -1000000 if which == 0 else 1000000
			add_child(marker)
	_ph_frame = 0
	_ph_pre = 0
	_ph_post = 0
	phase_on = true
	if not _ph_connected:
		_ph_connected = true
		get_tree().process_frame.connect(_ph_on_process_frame)
		RenderingServer.frame_pre_draw.connect(_ph_on_pre_draw)
		RenderingServer.frame_post_draw.connect(_ph_on_post_draw)


func phases_stop() -> Dictionary:
	phase_on = false
	var frames := maxi(1, int(phase.frames))
	var out := {"frames": frames}
	for key in ["process", "render", "other", "pre", "callbacks", "post", "flush", "tail"]:
		out[key + "_ms"] = float(phase[key]) / 1000.0 / frames
	return out


func _ph_on_process_frame() -> void:
	var now := Time.get_ticks_usec()
	if phase_on and _ph_post > 0:
		phase.other += now - _ph_post
		phase.frames += 1
	_ph_frame = now


func _ph_on_pre_draw() -> void:
	var now := Time.get_ticks_usec()
	if phase_on and _ph_frame > 0:
		phase.process += now - _ph_frame
	if phase_on and _ph_last > 0:
		phase.post += now - _ph_last
	if phase_on and _ph_flush_end > 0:
		phase.tail += now - _ph_flush_end
	_ph_pre = now


func _ph_on_post_draw() -> void:
	var now := Time.get_ticks_usec()
	if phase_on and _ph_pre > 0:
		phase.render += now - _ph_pre
	_ph_post = now


## Micro benchmark: every frame `n` random resting dice go through one step of the roll cycle.
var bench_mode := ""
var bench_n := 0


var bench_mech := ""


func bench(mode: String, count_value: int, mech_name: String = "") -> void:
	bench_mode = mode
	bench_n = count_value
	bench_mech = mech_name


## Shows the tarot card choice with the given cards (tests the card visuals).
func show_cards(cards: Array) -> bool:
	var typed: Array[Dictionary] = []
	for card in cards:
		typed.append(card)
	m().dog_shrine_controller._show_blessing_choices(typed, true)
	return true


## Formats numbers with the mod's number format (for tests).
func fmt(values: Array) -> Array:
	var script: Script = load("res://bdr/core/numfmt.gd")
	var out: Array = []
	for value in values:
		out.append(script.compact(value))
	return out


## Dice whose node position lies outside the board rect (debugging stray dice).
func stray_dice(limit: int = 30) -> Array:
	var out: Array = []
	var main := m()
	var rect: Rect2 = main.BOARD_RECT
	for die in main.dice:
		if not is_instance_valid(die):
			continue
		if rect.has_point(die.position) and die.visible:
			continue
		out.append({"kind": die.die_kind, "pos": die.position, "grid": die.grid_position(), "rolling": die.rolling,
			"special": die.special_motion, "visible": die.visible, "batched": die.batch_band, "lift": die.get("_visual_lift") if "_visual_lift" in die else null,
			"sprite_pos": die._sprite.position if is_instance_valid(die._sprite) else null, "sprite_visible": die._sprite.visible if is_instance_valid(die._sprite) else null})
		if out.size() >= limit:
			break
	return out


## Dice count per custom mechanic on the table.
func mech_census() -> Dictionary:
	var out := {}
	var main := m()
	for die in main.dice:
		if not is_instance_valid(die):
			continue
		var def = main.bdr.def_for(die.die_kind)
		var key := "vanilla:" + str(die.die_kind) if def == null else str(def.mech)
		out[key] = int(out.get(key, 0)) + 1
	return out


var bench_set: Array = []


func _bench_persistent(main: Node) -> bool:
	if bench_mode != "mv_visible" and bench_mode != "mv_visible_static" and bench_mode != "mv_zrot":
		if not bench_set.is_empty():
			for die in bench_set:
				if is_instance_valid(die):
					die.special_motion = false
					main._bdr_rest_die(die)
			bench_set.clear()
		return false
	if bench_set.is_empty():
		for die in main.dice:
			if is_instance_valid(die) and not die.rolling and not die.special_motion and die.die_kind != "cat":
				die.special_motion = true
				if bench_mode != "mv_zrot":
					main._bdr_unrest_die(die)
				bench_set.append(die)
				if bench_set.size() >= bench_n:
					break
	var t := Time.get_ticks_msec() / 1000.0
	for die in bench_set:
		if not is_instance_valid(die):
			continue
		match bench_mode:
			"mv_visible":
				die.position += Vector2(sin(t * 3.0), cos(t * 3.0)) * 0.5
			"mv_zrot":
				die.position += Vector2(sin(t * 3.0), cos(t * 3.0)) * 0.5
				die.z_index = 12 + int(die.position.y / 100.0)
				die.rotation = sin(t)
	return true


func _bench_step() -> void:
	var main := m()
	if main == null or not ("dice" in main):
		return
	if _bench_persistent(main):
		return
	var dice: Array = main.dice
	if dice.is_empty():
		return
	var done := 0
	var tries := 0
	while done < bench_n and tries < bench_n * 4:
		tries += 1
		var die = dice[randi() % dice.size()]
		if not is_instance_valid(die) or die.rolling or die.die_kind == "cat" or die.special_motion:
			continue
		if not bench_mech.is_empty():
			var mech_def = main.bdr.def_for(die.die_kind)
			if mech_def == null or str(mech_def.mech) != bench_mech:
				continue
		match bench_mode:
			"cycle":
				main._start_die_roll(die, 0, Vector2(-1, -1), false, false, false, true)
				die.finish_light_roll()
			"start":
				main._start_die_roll(die, 0, Vector2(-1, -1), false, false, false, true)
			"actor":
				die.start_roll(0, 0, Vector2(-1, -1), false, main.dice.size(), false, false)
				die.light_generation = -1
				die.abort_roll()
			"settle":
				die._settle_roll_visuals(die._rest_sprite_scale, Color.WHITE, Color(0, 0, 0, 0.3), Color.WHITE)
			"batch":
				main._batch.add(die)
			"pos":
				die.position = die.position
			"mv_hidden":
				die.position += Vector2(0.01, 0.0) if randi() % 2 == 0 else Vector2(-0.01, 0.0)
			"zindex":
				die.z_index = die.z_index + 0
			"payout":
				main._add_money(1.0)
			"filter":
				die._set_motion_texture_filter(false)
			"filter2":
				die._set_motion_texture_filter(true)
				die._set_motion_texture_filter(false)
			"rot":
				die.rotation = 0.0
			"result":
				die._result_for_face(randi() % 6, 0)
			"abort":
				die.rolling = true
				die._active_roll_context = {"target": die.position}
				die.abort_roll()
			"land":
				main._on_die_roll_completed(die, 1, "", randi() % 6 + 1, 0)
			"eco":
				main._eco_kind(die.die_kind)
			"after":
				var def = main.bdr.def_for(die.die_kind)
				if def != null:
					main.bdr.after_landing(die, 1.0, randi() % 6 + 1, def)
			"posperc":
				main.bdr.positional_percent(die)
			"rest":
				main._bdr_rest_die(die)
			"consume":
				main._consume_queued_player_reroll(die)
			"safe":
				main._finish_pending_safe_action()
				main._finish_pending_autosave()
			"gold":
				main._gold_income_multiplier(die)
			"hermit":
				main._hermit_income_multiplier(die)
			"ach":
				main._achievement_income_percent()
			"baseinc":
				var def2 = main.bdr.def_for(die.die_kind)
				if def2 != null:
					main.bdr.base_reward(die, randi() % 6 + 1, def2)
			"onroll":
				main.bdr.on_roll_started(die, die.position, false, false)
			"target":
				main._random_roll_target(die.position)
			"startfinish":
				die.start_roll(0, 0, Vector2(-1, -1), false, main.dice.size(), false, false)
				die.light_generation = die._roll_generation
				var was_connected: bool = die.roll_completed.is_connected(main._on_die_roll_completed)
				if was_connected:
					die.roll_completed.disconnect(main._on_die_roll_completed)
				die.finish_light_roll()
				if was_connected:
					die.roll_completed.connect(main._on_die_roll_completed)
			"popup":
				main._show_reward(die.position, "+1", true)
		done += 1


## Turns _process on/off for every node whose script file name matches (experiments).
func set_processing(script_file: String, on: bool) -> int:
	var changed := 0
	var stack: Array[Node] = [get_tree().root]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		for child in node.get_children():
			stack.append(child)
		var script: Script = node.get_script()
		if script and script.resource_path.get_file() == script_file:
			node.set_process(on)
			changed += 1
	return changed


## Average time of one call of a main.gd method (usec).
func time_main(method: String, n: int = 10, args: Array = []) -> float:
	var main := m()
	var started := Time.get_ticks_usec()
	for _i in range(n):
		main.callv(method, args)
	return float(Time.get_ticks_usec() - started) / float(n)


## Experiment: turn the transform notifications of all dice on/off.
func set_dice_notify(on: bool) -> int:
	var changed := 0
	for die in m().dice:
		if is_instance_valid(die):
			die.set_notify_transform(on)
			changed += 1
	return changed


## Experiment: take all dice areas out of the physics space (or put them back).
func set_dice_physics(on: bool) -> int:
	var changed := 0
	var space: RID = (m() as Node2D).get_world_2d().space
	for die in m().dice:
		if is_instance_valid(die):
			PhysicsServer2D.area_set_space(die.get_rid(), space if on else RID())
			changed += 1
	return changed


## Canvas items that receive transform notifications (flush_transform_notifications cost).
func notify_census() -> Dictionary:
	var out := {}
	var stack: Array[Node] = [get_tree().root]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		for child in node.get_children():
			stack.append(child)
		if node is CanvasItem or node is Node3D:
			var flags := ""
			if node.is_transform_notification_enabled():
				flags += "G"
			if node.is_local_transform_notification_enabled():
				flags += "L"
			if flags.is_empty():
				continue
			var script: Script = node.get_script()
			var key := (script.resource_path.get_file() if script else node.get_class()) + ":" + flags + " parent=" + (node.get_parent().get_class() if node.get_parent() else "-")
			out[key] = int(out.get(key, 0)) + 1
	return out


## All nodes grouped by script (or class) - where do the node counts come from?
func census() -> Dictionary:
	var out := {}
	var stack: Array[Node] = [get_tree().root]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		for child in node.get_children():
			stack.append(child)
		var script: Script = node.get_script()
		var key := script.resource_path.get_file() if script else node.get_class()
		out[key] = int(out.get(key, 0)) + 1
	return out


func frame_stats() -> Dictionary:
	if frame_times.is_empty():
		return {}
	var sorted := frame_times.duplicate()
	sorted.sort()
	var total := 0.0
	for t in sorted:
		total += t
	return {
		"samples": sorted.size(),
		"avg_ms": total / sorted.size(),
		"p50_ms": sorted[int(sorted.size() * 0.5)],
		"p95_ms": sorted[int(sorted.size() * 0.95)],
		"max_ms": sorted[-1],
		"fps": Engine.get_frames_per_second(),
	}


func reset_frames() -> void:
	frame_times.clear()
	last_usec = Time.get_ticks_usec()


func _execute(request: Dictionary) -> Variant:
	var cmd := str(request.get("cmd", ""))
	match cmd:
		"ping":
			return "pong"
		"eval":
			var expression := Expression.new()
			var err := expression.parse(str(request.get("expr", "")))
			if err != OK:
				return {"__error": "parse: " + expression.get_error_text()}
			var value = expression.execute([], self, true)
			if expression.has_execute_failed():
				return {"__error": "exec: " + expression.get_error_text()}
			return value
		"call":
			var target := get_tree().root.get_node_or_null(str(request.get("path", "")))
			if request.get("path", "") == "main":
				target = m()
			if target == null:
				return {"__error": "no node"}
			return target.callv(str(request.get("method", "")), request.get("args", []))
		"screenshot":
			await RenderingServer.frame_post_draw
			var image := get_viewport().get_texture().get_image()
			var path := str(request.get("path", "user://shot.png"))
			if request.has("scale"):
				var s := float(request.scale)
				image.resize(int(image.get_width() * s), int(image.get_height() * s), Image.INTERPOLATE_BILINEAR)
			var err := image.save_png(path)
			return {"saved": path, "err": err, "size": [image.get_width(), image.get_height()]}
		"click":
			var pos := Vector2(float(request.get("x", 0)), float(request.get("y", 0)))
			await _mouse_click(pos, int(request.get("button", MOUSE_BUTTON_LEFT)), float(request.get("hold", 0.05)))
			return true
		"hold":
			var hold_pos := Vector2(float(request.get("x", 0)), float(request.get("y", 0)))
			await _mouse_click(hold_pos, MOUSE_BUTTON_LEFT, float(request.get("seconds", 1.0)))
			return true
		"move":
			var from := Vector2(float(request.get("x1", 0)), float(request.get("y1", 0)))
			var to := Vector2(float(request.get("x2", 0)), float(request.get("y2", 0)))
			var steps := int(request.get("steps", 20))
			var per_frame := int(request.get("per_frame", 1))
			await _mouse_path(from, to, steps, per_frame)
			return true
		"key":
			await _key(int(request.get("keycode", KEY_ESCAPE)), bool(request.get("shift", false)))
			return true
		"wait":
			await get_tree().create_timer(float(request.get("seconds", 1.0)), true, false, true).timeout
			return true
		"frames":
			for _i in range(int(request.get("count", 1))):
				await get_tree().process_frame
			return true
		"scene":
			return get_tree().current_scene.scene_file_path if get_tree().current_scene else ""
		"start_game":
			GameSession.set_active_save_slot(int(request.get("slot", 1)), false)
			GameSession.launch_mode = str(request.get("mode", "continue"))
			get_tree().change_scene_to_file("res://scenes/main.tscn")
			return true
		"window":
			var mode := str(request.get("action", "info"))
			if mode == "park":
				DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
				DisplayServer.window_set_size(Vector2i(int(request.get("w", 1280)), int(request.get("h", 720))))
				DisplayServer.window_set_position(Vector2i(int(request.get("x", -12000)), int(request.get("y", 0))))
			return {"pos": [DisplayServer.window_get_position().x, DisplayServer.window_get_position().y], "size": [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y], "mode": DisplayServer.window_get_mode()}
		"quit":
			get_tree().quit()
			return true
	return {"__error": "unknown cmd " + cmd}


func _viewport_to_window(pos: Vector2) -> Vector2:
	# Game coordinates are in the 1920x1080 canvas; convert to window pixels.
	return get_tree().root.get_final_transform() * pos


func _mouse_click(pos: Vector2, button: int, hold_seconds: float) -> void:
	var window_pos := _viewport_to_window(pos)
	var motion := InputEventMouseMotion.new()
	motion.position = window_pos
	motion.global_position = window_pos
	Input.parse_input_event(motion)
	await get_tree().process_frame
	var press := InputEventMouseButton.new()
	press.button_index = button
	press.pressed = true
	press.position = window_pos
	press.global_position = window_pos
	press.button_mask = MOUSE_BUTTON_MASK_LEFT if button == MOUSE_BUTTON_LEFT else 0
	Input.parse_input_event(press)
	if hold_seconds > 0.0:
		await get_tree().create_timer(hold_seconds, true, false, true).timeout
	else:
		await get_tree().process_frame
	var release := InputEventMouseButton.new()
	release.button_index = button
	release.pressed = false
	release.position = window_pos
	release.global_position = window_pos
	Input.parse_input_event(release)
	await get_tree().process_frame


func _mouse_path(from: Vector2, to: Vector2, steps: int, per_frame: int) -> void:
	var previous := _viewport_to_window(from)
	for index in range(steps + 1):
		var t := float(index) / float(maxi(1, steps))
		var current := _viewport_to_window(from.lerp(to, t))
		var motion := InputEventMouseMotion.new()
		motion.position = current
		motion.global_position = current
		motion.relative = current - previous
		motion.velocity = (current - previous) * 60.0
		Input.parse_input_event(motion)
		previous = current
		if index % maxi(1, per_frame) == 0:
			await get_tree().process_frame


func _key(keycode: int, shift: bool) -> void:
	var down := InputEventKey.new()
	down.keycode = keycode
	down.physical_keycode = keycode
	down.pressed = true
	down.shift_pressed = shift
	Input.parse_input_event(down)
	await get_tree().process_frame
	var up := InputEventKey.new()
	up.keycode = keycode
	up.physical_keycode = keycode
	up.pressed = false
	up.shift_pressed = shift
	Input.parse_input_event(up)
	await get_tree().process_frame
