var _bdr_rows_built: = false


var _bdr_achievement_ids: Array[String] = []


func _bdr_game() -> Object:
	var parent: = get_parent()
	if parent == null:
		return null
	var game = parent.get("bdr")
	if game == null or game.get("achievements") == null:
		return null
	return game


## Adds the Dice Rush Extended achievements below the original ones (built once, when opened).
func _bdr_build_rows() -> void :
	if _bdr_rows_built or not achievement_list:
		return
	var game = _bdr_game()
	if game == null:
		return
	_bdr_rows_built = true
	var header: = Panel.new()
	header.custom_minimum_size = Vector2(1392, 76)
	var header_style: = StyleBoxFlat.new()
	header_style.bg_color = Color("0d1a33")
	header_style.border_color = Color("d49316")
	header_style.set_border_width_all(3)
	header_style.corner_radius_top_left = 8
	header_style.corner_radius_top_right = 8
	header_style.corner_radius_bottom_left = 8
	header_style.corner_radius_bottom_right = 8
	header.add_theme_stylebox_override("panel", header_style)
	achievement_list.add_child(header)
	var header_label: = _make_label(header, "DICE RUSH EXTENDED", Rect2(24, 8, 900, 60), 26, HORIZONTAL_ALIGNMENT_LEFT, display_font)
	_sharpen_achievement_label(header_label, 3)
	header_label.add_theme_color_override("font_color", Color("ffd166"))
	for entry in game.achievements.entries():
		var achievement_id: = str(entry.id)
		_build_achievement_row(entry)
		_bdr_achievement_ids.append(achievement_id)
		var row_data: Dictionary = achievement_rows.get(achievement_id, {})
		if not row_data.is_empty():
			(row_data.icon as TextureRect).texture = CleanTextureLoader.load_texture(game.achievements.icon(achievement_id))


func _open_achievements() -> void :
	if not game_active:
		return
	_bdr_build_rows()
	if achievement_toast_tween and achievement_toast_tween.is_valid():
		achievement_toast_tween.kill()
	achievement_toast.visible = false
	_refresh_achievements()
	achievement_menu.visible = true
	game_menu_button.visible = false
	achievement_button.visible = false
	_animate_overlay_in(achievement_menu)
	if is_instance_valid(achievement_close_button):
		_focus_achievement_menu.call_deferred()


func _refresh_achievements() -> void :
	if not achievement_summary_label:
		return
	var definitions: = AchievementService.catalog()
	var game = _bdr_game()
	var unlocked_total: int = AchievementService.unlocked_count()
	var total: int = definitions.size()
	if game != null:
		unlocked_total += int(game.achievements.unlocked_count())
		total += int(game.achievements.total())
	achievement_summary_label.text = GameSession.text("achievements_summary") % [unlocked_total, total]
	UITextFitterScript.fit(achievement_summary_label)
	for entry in definitions:
		var achievement_id: = str(entry.id)
		var row_data: Dictionary = achievement_rows.get(achievement_id, {})
		if row_data.is_empty():
			continue
		var is_open: = AchievementService.is_unlocked(achievement_id)
		var is_hidden: = bool(entry.get("hidden", false)) and not is_open
		var current: = mini(AchievementService.progress(achievement_id), AchievementService.target(achievement_id))
		var target_value: = AchievementService.target(achievement_id)
		(row_data.panel as Panel).add_theme_stylebox_override("panel", _achievement_row_style(is_open))
		(row_data.icon as TextureRect).modulate = Color.WHITE if is_open else Color(0.28, 0.3, 0.36, 0.62)
		var title_label: = row_data.title as Label
		var description_label: = row_data.description as Label
		title_label.text = "???" if is_hidden else AchievementService.localized_name(achievement_id)
		description_label.text = GameSession.text("achievement_locked") if is_hidden else AchievementService.localized_description(achievement_id)
		UITextFitterScript.fit(title_label)
		UITextFitterScript.fit(description_label)
		var progress_label: = row_data.progress as Label
		progress_label.text = GameSession.text("achievement_open") if is_open else ("???" if is_hidden else "%s / %s" % [_compact_achievement_value(current), _compact_achievement_value(target_value)])
		UITextFitterScript.fit(progress_label)
		progress_label.add_theme_color_override("font_color", Color("7aff72") if is_open else Color("d9deea"))
		var bar: = row_data.bar as ProgressBar
		bar.max_value = float(maxi(1, target_value))
		bar.value = 0.0 if is_hidden else float(current)
	if game == null:
		return
	for achievement_id in _bdr_achievement_ids:
		var row_data: Dictionary = achievement_rows.get(achievement_id, {})
		if row_data.is_empty():
			continue
		var entry: Dictionary = game.achievements.entry(achievement_id)
		var is_open: bool = game.achievements.is_unlocked(achievement_id)
		var is_hidden: = bool(entry.get("hidden", false)) and not is_open
		(row_data.panel as Panel).add_theme_stylebox_override("panel", _achievement_row_style(is_open))
		(row_data.icon as TextureRect).modulate = Color.WHITE if is_open else Color(0.28, 0.3, 0.36, 0.62)
		var title_label: = row_data.title as Label
		var description_label: = row_data.description as Label
		title_label.text = "???" if is_hidden else str(game.achievements.title(achievement_id))
		description_label.text = GameSession.text("achievement_locked") if is_hidden else str(game.achievements.description(achievement_id))
		UITextFitterScript.fit(title_label)
		UITextFitterScript.fit(description_label)
		var progress_label: = row_data.progress as Label
		progress_label.text = GameSession.text("achievement_open") if is_open else ("???" if is_hidden else str(game.achievements.progress_text(achievement_id)))
		UITextFitterScript.fit(progress_label)
		progress_label.add_theme_color_override("font_color", Color("7aff72") if is_open else Color("d9deea"))
		var bar: = row_data.bar as ProgressBar
		bar.max_value = 1000.0
		bar.value = 0.0 if is_hidden else (1000.0 if is_open else 1000.0 * float(game.achievements.progress_ratio(achievement_id)))


func _on_achievement_unlocked(achievement_id: String) -> void :
	if not achievement_notifications_enabled:
		return
	_refresh_achievements()
	var game = _bdr_game()
	if game != null and game.achievements.is_mod_achievement(achievement_id):
		achievement_toast_title.text = str(game.achievements.title(achievement_id))
	else:
		achievement_toast_title.text = AchievementService.localized_name(achievement_id)
	UITextFitterScript.fit(achievement_toast_title)
	achievement_toast.modulate = Color.WHITE
	achievement_toast.visible = true
	if achievement_toast_tween and achievement_toast_tween.is_valid():
		achievement_toast_tween.kill()
	achievement_toast_tween = create_tween()
	achievement_toast_tween.tween_interval(2.6)
	achievement_toast_tween.tween_property(achievement_toast, "modulate:a", 0.0, 0.45)
	achievement_toast_tween.tween_callback( func(): achievement_toast.visible = false)


const BDRSettingsScript: = preload("res://bdr/core/settings.gd")


const BDRI18NScript: = preload("res://bdr/core/i18n.gd")


const BDR_QUALITY_ORDER: = ["low", "medium", "high"]


var _bdr_quality_label: Label


## Dice Rush Extended: quality preset of the mod (how many dice may animate at the same time).
func _bdr_build_quality_row(page: Control) -> void :
	_make_label(page, BDRI18NScript.t("ui.quality"), Rect2(48, 596, 680, 66), 14, HORIZONTAL_ALIGNMENT_LEFT)
	_make_button(page, "<", Rect2(760, 596, 94, 66), _bdr_cycle_quality.bind(-1), 18)
	_bdr_quality_label = _make_label(page, "", Rect2(875, 596, 270, 66), 15, HORIZONTAL_ALIGNMENT_CENTER)
	_bdr_quality_label.add_theme_color_override("font_color", Color("ffd166"))
	_make_button(page, ">", Rect2(1160, 596, 94, 66), _bdr_cycle_quality.bind(1), 18)
	_bdr_refresh_quality()


func _bdr_cycle_quality(direction: int) -> void :
	var current: = str(BDRSettingsScript.load_settings().get("quality", "medium"))
	var index: = wrapi(BDR_QUALITY_ORDER.find(current) + direction, 0, BDR_QUALITY_ORDER.size())
	var settings: Dictionary = BDRSettingsScript.set_value("quality", BDR_QUALITY_ORDER[index])
	var game = get_parent().get("bdr") if get_parent() else null
	if game != null:
		game.settings = settings
	GameSession.play_sfx("ui_select")
	_bdr_refresh_quality()


func _bdr_refresh_quality() -> void :
	if not is_instance_valid(_bdr_quality_label):
		return
	var current: = str(BDRSettingsScript.load_settings().get("quality", "medium"))
	_bdr_quality_label.text = BDRI18NScript.t("ui.quality_" + current)
	UITextFitterScript.fit(_bdr_quality_label)


const BDRNumFmt: = preload("res://bdr/core/numfmt.gd")


## Dice Rush Extended: same short number style everywhere (1.1K, 2.5M ... never "e").
func _compact_achievement_value(value: int) -> String:
	return BDRNumFmt.compact(value)
