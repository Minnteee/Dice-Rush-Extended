extends RefCounted
## Dice Shaker UI helpers: dark purple velvet panels with gold borders, pixel font.

const META_MAX := &"shaker_max_font"
const MIN_FONT := 7

const PANEL := Color("170b26f0")
const PANEL_LIGHT := Color("2a1640f2")
const GOLD := Color("d9a441")
const GOLD_LIGHT := Color("ffd77a")
const INK := Color("1a0d26")
const TEXT := Color("f6ecff")
const MUTED := Color("b9a6cf")
const GOOD := Color("7dffb0")
const BAD := Color("ff7a8a")
const BUTTON := Color("3a1d5c")
const BUTTON_HOT := Color("5a2d8a")

static var pixel_font: Font
static var display_font: Font


static func setup() -> void:
	pixel_font = GameSession.ui_font()
	display_font = GameSession.display_font()


static func style(fill: Color, border: Color, border_width: int = 3, radius: int = 12) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = border
	box.set_border_width_all(border_width)
	box.set_corner_radius_all(radius)
	box.content_margin_left = 10
	box.content_margin_right = 10
	box.content_margin_top = 4
	box.content_margin_bottom = 4
	return box


static func panel(parent: Node, rect: Rect2, fill: Color = PANEL, border: Color = GOLD, border_width: int = 4, radius: int = 18) -> Panel:
	var node := Panel.new()
	node.position = rect.position
	node.size = rect.size
	node.add_theme_stylebox_override("panel", style(fill, border, border_width, radius))
	parent.add_child(node)
	return node


static func label(parent: Node, text: String, rect: Rect2, font_size: int = 16, align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT, color: Color = TEXT, display: bool = false) -> Label:
	var node := Label.new()
	node.clip_text = true
	node.position = rect.position
	node.size = rect.size
	node.set_meta(META_MAX, font_size)
	node.horizontal_alignment = align
	node.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	node.add_theme_font_override("font", display_font if display and display_font else pixel_font)
	node.add_theme_font_size_override("font_size", font_size)
	node.add_theme_color_override("font_color", color)
	node.add_theme_color_override("font_outline_color", Color("0b0512"))
	node.add_theme_constant_override("outline_size", 6 if font_size >= 20 else 4)
	parent.add_child(node)
	node.text = text
	fit(node)
	return node


static func paragraph(parent: Node, text: String, rect: Rect2, font_size: int = 12, align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT, color: Color = TEXT) -> Label:
	var node := label(parent, "", rect, font_size, align, color)
	node.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	node.add_theme_constant_override("line_spacing", 3)
	node.text = text
	fit(node)
	return node


static func set_text(node: Label, text: String) -> void:
	if node == null or node.text == text:
		return
	node.text = text
	fit(node)


static func button(parent: Node, text: String, rect: Rect2, callback: Callable, font_size: int = 15, fill: Color = BUTTON, border: Color = GOLD) -> Button:
	var node := Button.new()
	node.clip_text = true
	node.position = rect.position
	node.size = rect.size
	node.set_meta(META_MAX, font_size)
	node.focus_mode = Control.FOCUS_ALL
	node.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	node.add_theme_font_override("font", pixel_font)
	node.add_theme_font_size_override("font_size", font_size)
	node.add_theme_color_override("font_color", TEXT)
	node.add_theme_color_override("font_hover_color", GOLD_LIGHT)
	node.add_theme_color_override("font_pressed_color", GOLD_LIGHT)
	node.add_theme_color_override("font_focus_color", TEXT)
	node.add_theme_color_override("font_disabled_color", Color("7d6f8c"))
	node.add_theme_color_override("font_outline_color", Color("0b0512"))
	node.add_theme_constant_override("outline_size", 4)
	node.add_theme_stylebox_override("normal", style(fill, border))
	node.add_theme_stylebox_override("hover", style(fill.lightened(0.18), GOLD_LIGHT))
	node.add_theme_stylebox_override("pressed", style(fill.darkened(0.25), GOLD_LIGHT))
	node.add_theme_stylebox_override("focus", style(Color.TRANSPARENT, GOLD_LIGHT))
	node.add_theme_stylebox_override("disabled", style(Color("221830"), Color("4a3d5a")))
	if callback.is_valid():
		node.pressed.connect(callback)
	node.mouse_entered.connect(func() -> void: GameSession.play_sfx("ui_hover"))
	node.button_down.connect(func() -> void: GameSession.play_sfx("ui_select"))
	parent.add_child(node)
	node.text = text
	fit(node)
	return node


static func set_button_text(node: Button, text: String) -> void:
	if node == null or node.text == text:
		return
	node.text = text
	fit(node)


static func texture(parent: Node, tex: Texture2D, rect: Rect2, nearest: bool = true) -> TextureRect:
	var node := TextureRect.new()
	node.position = rect.position
	node.size = rect.size
	node.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	node.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	node.texture = tex
	node.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST if nearest else CanvasItem.TEXTURE_FILTER_LINEAR
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(node)
	return node


static func bar(parent: Node, rect: Rect2, fill_color: Color = GOLD) -> ProgressBar:
	var node := ProgressBar.new()
	node.position = rect.position
	node.size = rect.size
	node.min_value = 0.0
	node.max_value = 1.0
	node.step = 0.0
	node.show_percentage = false
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	node.add_theme_stylebox_override("background", style(Color("120819"), Color("4a2d66"), 2, 6))
	node.add_theme_stylebox_override("fill", style(fill_color, fill_color.lightened(0.3), 1, 6))
	parent.add_child(node)
	return node


static func scroll(parent: Node, rect: Rect2) -> ScrollContainer:
	var node := ScrollContainer.new()
	node.position = rect.position
	node.size = rect.size
	node.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	node.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	parent.add_child(node)
	return node


## Full screen dark overlay that eats clicks (returns the layer to put a panel on).
static func overlay(parent: Node, alpha: float = 0.72) -> Control:
	var layer := Control.new()
	layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.mouse_filter = Control.MOUSE_FILTER_STOP
	parent.add_child(layer)
	var dim := ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.03, 0.0, 0.06, alpha)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(dim)
	return layer


## Lowers the font size until the text fits into the control (labels may wrap).
static func fit(control: Control) -> void:
	if not is_instance_valid(control):
		return
	var text := ""
	var wraps := false
	var reserve := Vector2(10, 4)
	if control is Label:
		var label_node := control as Label
		text = label_node.text
		wraps = label_node.autowrap_mode != TextServer.AUTOWRAP_OFF or text.contains("\n")
	elif control is Button:
		text = (control as Button).text
		var box := control.get_theme_stylebox("normal")
		reserve = Vector2(16, 8) + (box.get_minimum_size() if box else Vector2.ZERO)
	else:
		return
	var maximum := int(control.get_meta(META_MAX, control.get_theme_font_size("font_size")))
	var font := control.get_theme_font("font")
	if text.is_empty() or font == null or control.size.x <= 2.0:
		control.add_theme_font_size_override("font_size", maximum)
		return
	var outline := float(maxi(0, control.get_theme_constant("outline_size")) * 2)
	var width := maxf(1.0, control.size.x - reserve.x - outline)
	var height := maxf(1.0, control.size.y - reserve.y - outline)
	var chosen := MIN_FONT
	for font_size in range(maximum, MIN_FONT - 1, -1):
		var measured := font.get_multiline_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, width if wraps else -1.0, font_size)
		if wraps:
			var lines := maxi(1, ceili(measured.y / maxf(1.0, font.get_height(font_size))))
			measured.y += float(maxi(0, control.get_theme_constant("line_spacing")) * (lines - 1))
		if measured.x <= width + 0.5 and measured.y <= height + 0.5:
			chosen = font_size
			break
	control.add_theme_font_size_override("font_size", chosen)
