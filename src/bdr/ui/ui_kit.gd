extends RefCounted
## Small UI helpers in the visual style of Dice Rush (dark blue panels, gold borders, pixel font).

const META_MAX := &"bdr_max_font_size"
const MIN_FONT := 7

static var pixel_font: Font
static var display_font: Font


static func setup(pixel: Font, display: Font) -> void:
	pixel_font = pixel
	display_font = display


static func style(fill: Color, border: Color, border_width: int = 3, radius: int = 12) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = border
	box.set_border_width_all(border_width)
	box.set_corner_radius_all(radius)
	box.content_margin_left = 10
	box.content_margin_right = 10
	return box


static func panel(parent: Node, rect: Rect2, fill: Color = Color("0a1730f2"), border: Color = Color("d49316"), border_width: int = 4, radius: int = 16) -> Panel:
	var node := Panel.new()
	node.position = rect.position
	node.size = rect.size
	node.add_theme_stylebox_override("panel", style(fill, border, border_width, radius))
	parent.add_child(node)
	return node


static func label(parent: Node, text: String, rect: Rect2, font_size: int = 16, align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT, color: Color = Color.WHITE, display: bool = false) -> Label:
	var node := Label.new()
	# clip_text keeps the label at its rect: a long text must never grow the control
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
	node.add_theme_color_override("font_outline_color", Color.BLACK)
	node.add_theme_constant_override("outline_size", 5)
	parent.add_child(node)
	node.text = text
	fit(node)
	return node


## Multi-line text that wraps inside its rect (not shrunk by the text fitter).
static func paragraph(parent: Node, text: String, rect: Rect2, font_size: int = 12, align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT, color: Color = Color.WHITE) -> Label:
	var node := Label.new()
	node.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	node.clip_text = true
	node.position = rect.position
	node.size = rect.size
	node.set_meta(META_MAX, font_size)
	node.horizontal_alignment = align
	node.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	node.add_theme_font_override("font", pixel_font)
	node.add_theme_font_size_override("font_size", font_size)
	node.add_theme_color_override("font_color", color)
	node.add_theme_color_override("font_outline_color", Color.BLACK)
	node.add_theme_constant_override("outline_size", 4)
	node.add_theme_constant_override("line_spacing", 2)
	parent.add_child(node)
	node.text = text
	fit(node)
	return node


static func button(parent: Node, text: String, rect: Rect2, callback: Callable, font_size: int = 15, fill: Color = Color("10294a"), border: Color = Color("a86f12")) -> Button:
	var node := Button.new()
	node.clip_text = true
	node.position = rect.position
	node.size = rect.size
	node.set_meta(META_MAX, font_size)
	node.focus_mode = Control.FOCUS_ALL
	node.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	node.add_theme_font_override("font", pixel_font)
	node.add_theme_font_size_override("font_size", font_size)
	node.add_theme_color_override("font_color", Color.WHITE)
	node.add_theme_color_override("font_hover_color", Color("fff2a8"))
	node.add_theme_color_override("font_disabled_color", Color("8a8f9a"))
	node.add_theme_stylebox_override("normal", style(fill, border))
	node.add_theme_stylebox_override("hover", style(fill.lightened(0.15), Color("ffd166")))
	node.add_theme_stylebox_override("pressed", style(fill.darkened(0.2), Color("ffe59a")))
	node.add_theme_stylebox_override("focus", style(Color.TRANSPARENT, Color("ffd166")))
	node.add_theme_stylebox_override("disabled", style(Color("252532"), Color("555566")))
	if callback.is_valid():
		node.pressed.connect(callback)
	node.mouse_entered.connect(func() -> void: GameSession.play_sfx("ui_hover"))
	node.button_down.connect(func() -> void: GameSession.play_sfx("ui_select"))
	parent.add_child(node)
	node.text = text
	fit(node)
	return node


static func texture(parent: Node, path: String, rect: Rect2, nearest: bool = true) -> TextureRect:
	var node := TextureRect.new()
	node.position = rect.position
	node.size = rect.size
	node.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	node.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	node.texture = CleanTextureLoader.load_texture(path) if not path.is_empty() else null
	node.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST if nearest else CanvasItem.TEXTURE_FILTER_LINEAR
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(node)
	return node


## Lowers the font size until the text fits into the control (labels may wrap).
static func fit(control: Control) -> void:
	if not is_instance_valid(control):
		return
	var text := ""
	var wraps := false
	var reserve := Vector2(14, 6)
	if control is Label:
		var label_node := control as Label
		text = label_node.text
		wraps = label_node.autowrap_mode != TextServer.AUTOWRAP_OFF or text.contains("\n")
	elif control is Button:
		text = (control as Button).text
		var box := control.get_theme_stylebox("normal")
		reserve = Vector2(22, 10) + (box.get_minimum_size() if box else Vector2.ZERO)
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


static func scroll(parent: Node, rect: Rect2) -> ScrollContainer:
	var node := ScrollContainer.new()
	node.position = rect.position
	node.size = rect.size
	node.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	node.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	parent.add_child(node)
	return node
