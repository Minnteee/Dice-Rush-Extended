extends RefCounted
## Dice Rush Extended - GitHub logo button (main menu and in game, bottom right).
## A click opens the author's GitHub page.

const URL := "https://github.com/Minnteee"
## GitHub mark (octicon "mark-github"), drawn white.
const SVG := "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 16 16\"><path fill=\"#ffffff\" d=\"M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z\"/></svg>"
const IDLE_ALPHA := 0.72


static func texture() -> Texture2D:
	var image := Image.new()
	if image.load_svg_from_string(SVG, 8.0) != OK or image.is_empty():
		return null
	return ImageTexture.create_from_image(image)


## Adds the logo button to `parent` (Control or Node2D) at `rect`.
static func make(parent: Node, rect: Rect2, z_value: int = 0) -> TextureButton:
	var button := TextureButton.new()
	button.name = "BDRGitHub"
	button.position = rect.position
	button.size = rect.size
	button.z_index = z_value
	button.ignore_texture_size = true
	button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	button.texture_normal = texture()
	button.tooltip_text = "github.com/Minnteee"
	button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	button.focus_mode = Control.FOCUS_NONE
	button.modulate = Color(1.0, 1.0, 1.0, IDLE_ALPHA)
	button.mouse_entered.connect(func() -> void: button.modulate = Color.WHITE)
	button.mouse_exited.connect(func() -> void: button.modulate = Color(1.0, 1.0, 1.0, IDLE_ALPHA))
	button.pressed.connect(func() -> void:
		GameSession.play_sfx("ui_select")
		OS.shell_open(URL)
	)
	parent.add_child(button)
	if button.texture_normal == null:
		# no SVG support: show the word instead
		var fallback := Label.new()
		fallback.text = "GitHub"
		fallback.size = rect.size
		fallback.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		fallback.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		fallback.mouse_filter = Control.MOUSE_FILTER_IGNORE
		button.add_child(fallback)
	return button
