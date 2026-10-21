# Dice Rush Extended: load raw PNG/WebP files that ship inside the mod pack (res://bdr/...).

static func load_texture(path: String) -> Texture2D:
	if _texture_cache.has(path):
		return _texture_cache[path] as Texture2D
	var texture: Texture2D = null
	if path.begins_with("res://bdr/") or path.begins_with("user://"):
		if not FileAccess.file_exists(path):
			_texture_cache[path] = null
			return null
		var image: = Image.load_from_file(path)
		if image and not image.is_empty():
			texture = ImageTexture.create_from_image(image)
		_texture_cache[path] = texture
		return texture
	texture = load(path) as Texture2D
	if not texture:
		return null
	if path == CRYPTO_TEXTURE_PATH:
		var source_image: = texture.get_image()
		if source_image and not source_image.is_empty():
			source_image.set_pixelv(CRYPTO_STRAY_PIXEL, Color(0, 0, 0, 0))
			var cropped_image: = source_image.get_region(CRYPTO_VISIBLE_REGION)
			texture = ImageTexture.create_from_image(cropped_image)
		else:
			var cropped_texture: = AtlasTexture.new()
			cropped_texture.atlas = texture
			cropped_texture.region = Rect2(CRYPTO_VISIBLE_REGION)
			cropped_texture.filter_clip = true
			texture = cropped_texture
	elif path == TALENT_TREE_ICON_PATH:
		var source_image: = texture.get_image()
		if source_image and not source_image.is_empty():
			for pixel in TALENT_TREE_STRAY_PIXELS:
				source_image.set_pixelv(pixel, Color(0, 0, 0, 0))
			texture = ImageTexture.create_from_image(source_image)
	_texture_cache[path] = texture
	return texture
