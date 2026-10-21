extends RefCounted
## Dice Rush Extended - warm-up after loading: step by step (a few milliseconds per frame) all
## effect textures, the glyphs of the popup texts and every effect shape are prepared once in the
## background, so nothing stutters the first time it appears on a crowded table.

const I18N := preload("res://bdr/core/i18n.gd")
const FOLDERS := ["res://bdr/art/events/", "res://bdr/art/staff/", "res://bdr/art/ui/", "res://bdr/art/tarot/", "res://bdr/art/boards/", "res://bdr/art/cursors/"]
const BUDGET_USEC := 2500
const FONT_SIZES := [11, 13, 15, 16, 17, 18]

var game: Node
var main: Node
var _paths: Array[String] = []
var _step := 0
var _done := false
var _labels: Array[Label] = []
var _fx_done := false


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	for folder in FOLDERS:
		for file_name in DirAccess.get_files_at(folder):
			var clean := file_name.trim_suffix(".remap").trim_suffix(".import")
			if clean.ends_with(".png") and not clean.begins_with("contact_sheet"):
				var path: String = folder + clean
				if path not in _paths:
					_paths.append(path)


func is_done() -> bool:
	return _done


## Called every frame until everything is prepared.
func process() -> void:
	if _done or not bool(main.game_started):
		return
	for label in _labels:
		if is_instance_valid(label):
			label.queue_free()
	_labels.clear()
	var started := Time.get_ticks_usec()
	while _step < _paths.size() and Time.get_ticks_usec() - started < BUDGET_USEC:
		CleanTextureLoader.load_texture(_paths[_step])
		_step += 1
	if _step < _paths.size():
		return
	if _step == _paths.size():
		_step += 1
		_warm_glyphs()
		return
	if not _fx_done:
		_fx_done = true
		var faint := Color(1.0, 1.0, 1.0, 0.01)
		var center: Vector2 = game.board_safe_rect().get_center()
		game._ensure_fx()
		game.fx.ring(center, 40.0, faint, 0.05)
		game.fx.lines(center, [], faint, 0.05)
		game.fx.cone(center, Vector2.RIGHT, 40.0, faint, 0.05)
		game.fx.trail(center, center + Vector2(10, 0), 0.05)
		return
	_done = true


## Draws every popup / banner text once, almost invisible, so the font glyphs are rasterized.
func _warm_glyphs() -> void:
	var text := ""
	var table: Dictionary = I18N.table(str(GameSession.language))
	for key in table:
		var name := str(key)
		if name.begins_with("fx.") or name.begins_with("event.") or name.begins_with("lucky.") or name.begins_with("staff."):
			text += str(table[key]) + " "
	text += "0123456789.,+-x%KMBTqQsSoNdabcdefghijk"
	var center: Vector2 = game.board_safe_rect().get_center()
	for size in FONT_SIZES:
		var label := Label.new()
		label.text = text
		label.position = center
		label.size = Vector2(4, 4)
		label.clip_text = true
		label.modulate = Color(1, 1, 1, 0.01)
		label.add_theme_font_override("font", main.pixel_font)
		label.add_theme_font_size_override("font_size", size)
		label.add_theme_constant_override("outline_size", 5)
		label.z_index = -50
		main.add_child(label)
		_labels.append(label)
