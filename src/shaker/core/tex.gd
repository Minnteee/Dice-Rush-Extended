extends RefCounted
## Dice Shaker texture loader.
## - res://shaker/... and res://bdr/... are raw PNG files inside the mod packs (not imported)
## - everything else is an imported texture of the original game
## Dice pictures can be requested at a fixed size: they are cropped to their visible part,
## centred on a square and scaled once (pixel art by an integer factor stays crisp).

static var _cache: Dictionary = {}


static func load_image(path: String) -> Image:
	if path.is_empty():
		return null
	var image: Image = null
	if path.begins_with("res://shaker/") or path.begins_with("res://bdr/") or path.begins_with("user://"):
		if FileAccess.file_exists(path):
			image = Image.load_from_file(path)
	else:
		var texture: Texture2D = CleanTextureLoader.load_texture(path)
		if texture:
			image = texture.get_image()
	if image == null or image.is_empty():
		return null
	if image.is_compressed():
		image.decompress()
	if image.get_format() != Image.FORMAT_RGBA8:
		image.convert(Image.FORMAT_RGBA8)
	return image


## The texture as it is (cached).
static func get_tex(path: String) -> Texture2D:
	if _cache.has(path):
		return _cache[path]
	var image := load_image(path)
	var texture: Texture2D = ImageTexture.create_from_image(image) if image else null
	_cache[path] = texture
	return texture


## A square texture of `size` pixels: visible part only, centred, scaled.
static func square(path: String, size: int) -> Texture2D:
	var key := "%s@sq%d" % [path, size]
	if _cache.has(key):
		return _cache[key]
	var image := load_image(path)
	var texture: Texture2D = null
	if image:
		var used := image.get_used_rect()
		if used.size.x > 0 and used.size.y > 0:
			image = image.get_region(used)
		var side := maxi(image.get_width(), image.get_height())
		var canvas := Image.create_empty(side, side, false, Image.FORMAT_RGBA8)
		canvas.blit_rect(image, Rect2i(Vector2i.ZERO, image.get_size()), Vector2i((side - image.get_width()) / 2, (side - image.get_height()) / 2))
		var interpolation := Image.INTERPOLATE_LANCZOS
		if side >= size and side % size == 0:
			interpolation = Image.INTERPOLATE_NEAREST   # pixel art: exact factor, keep it crisp
		elif side < size and size % side == 0:
			interpolation = Image.INTERPOLATE_NEAREST
		canvas.resize(size, size, interpolation)
		texture = ImageTexture.create_from_image(canvas)
	_cache[key] = texture
	return texture


## Scaled by an integer factor with nearest filtering (scene pixel art: native x4).
static func scaled(path: String, factor: int) -> Texture2D:
	var key := "%s@x%d" % [path, factor]
	if _cache.has(key):
		return _cache[key]
	var image := load_image(path)
	var texture: Texture2D = null
	if image:
		image.resize(image.get_width() * factor, image.get_height() * factor, Image.INTERPOLATE_NEAREST)
		texture = ImageTexture.create_from_image(image)
	_cache[key] = texture
	return texture


static func clear() -> void:
	_cache.clear()
