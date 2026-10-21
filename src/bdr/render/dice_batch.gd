extends Node2D
## Dice Rush Extended - batched renderer for resting dice.
## All dice that are not visibly moving are drawn by one MultiMesh per depth band
## (plus a shadow copy of the same MultiMesh), instead of two sprites per dice.
## This turns thousands of draw calls into a handful.

const CELL := 128
const SHADOW_OFFSET := Vector2(5, 9)
const SHADOW_COLOR := Color(0.0, 0.0, 0.0, 0.3)
const HIDDEN := Transform2D(Vector2.ZERO, Vector2.ZERO, Vector2(-100000.0, -100000.0))
const SHADER_CODE := """
shader_type canvas_item;
void vertex() {
	UV = INSTANCE_CUSTOM.xy + UV * INSTANCE_CUSTOM.zw;
}
"""

var atlas_texture: ImageTexture
var kind_uv: Dictionary = {}       # kind -> Color(u, v, w, h)
var kind_size: Dictionary = {}     # kind -> display size in px
var bands: Dictionary = {}         # z -> band dictionary
var quad: ArrayMesh
var batch_material: ShaderMaterial
var enabled := true
## crowded tables: all batched dice are drawn smaller (see bdr_game.dice_scale)
var scale_factor := 1.0
var batched_count := 0


func _init() -> void:
	name = "DiceBatchLayer"
	quad = ArrayMesh.new()
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = PackedVector2Array([Vector2(-0.5, -0.5), Vector2(0.5, -0.5), Vector2(0.5, 0.5), Vector2(-0.5, 0.5)])
	arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])
	arrays[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	quad.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var shader := Shader.new()
	shader.code = SHADER_CODE
	batch_material = ShaderMaterial.new()
	batch_material.shader = shader


## textures: Dictionary kind -> Texture2D ; sizes: kind -> display size (px)
func build_atlas(textures: Dictionary, sizes: Dictionary) -> void:
	var kinds: Array = textures.keys()
	var columns := maxi(1, int(ceil(sqrt(float(kinds.size())))))
	var rows := maxi(1, int(ceil(float(kinds.size()) / float(columns))))
	var image := Image.create(columns * CELL, rows * CELL, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	var atlas_size := Vector2(columns * CELL, rows * CELL)
	for index in range(kinds.size()):
		var kind: String = kinds[index]
		var texture: Texture2D = textures[kind]
		if texture == null:
			continue
		var source := texture.get_image()
		if source == null or source.is_empty():
			continue
		if source.is_compressed():
			source.decompress()
		source.convert(Image.FORMAT_RGBA8)
		var w := source.get_width()
		var h := source.get_height()
		var scale := float(CELL) / float(maxi(w, h))
		var nw := maxi(1, int(round(w * scale)))
		var nh := maxi(1, int(round(h * scale)))
		source.resize(nw, nh, Image.INTERPOLATE_LANCZOS if maxi(w, h) > CELL else Image.INTERPOLATE_NEAREST)
		var cx := (index % columns) * CELL
		var cy := (index / columns) * CELL
		image.blit_rect(source, Rect2i(0, 0, nw, nh), Vector2i(cx + (CELL - nw) / 2, cy + (CELL - nh) / 2))
		kind_uv[kind] = Color(float(cx) / atlas_size.x, float(cy) / atlas_size.y, float(CELL) / atlas_size.x, float(CELL) / atlas_size.y)
		kind_size[kind] = float(sizes.get(kind, 62.0))
	atlas_texture = ImageTexture.create_from_image(image)
	for band in bands.values():
		(band.body as MultiMeshInstance2D).texture = atlas_texture
		(band.shadow as MultiMeshInstance2D).texture = atlas_texture


func has_kind(kind: String) -> bool:
	return kind_uv.has(kind)


static func band_for(position_y: float) -> int:
	return 12 + int(position_y / 100.0)


func _band(z: int) -> Dictionary:
	if bands.has(z):
		return bands[z]
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_2D
	mm.use_colors = false
	mm.use_custom_data = true
	mm.mesh = quad
	mm.instance_count = 256
	mm.visible_instance_count = 0
	var shadow := MultiMeshInstance2D.new()
	shadow.multimesh = mm
	shadow.texture = atlas_texture
	shadow.material = batch_material
	shadow.position = SHADOW_OFFSET
	shadow.self_modulate = SHADOW_COLOR
	shadow.z_index = z - 1
	shadow.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(shadow)
	var body := MultiMeshInstance2D.new()
	body.multimesh = mm
	body.texture = atlas_texture
	body.material = batch_material
	body.z_index = z
	body.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(body)
	var band := {"mm": mm, "body": body, "shadow": shadow, "owners": [], "free": [], "high": 0}
	(band.owners as Array).resize(256)
	bands[z] = band
	return band


func _grow(band: Dictionary) -> void:
	var mm: MultiMesh = band.mm
	var old_count := mm.instance_count
	var owners: Array = band.owners
	mm.instance_count = old_count * 2
	owners.resize(old_count * 2)
	for slot in range(int(band.high)):
		var die = owners[slot]
		if die != null and is_instance_valid(die):
			_write(mm, slot, die)
		else:
			mm.set_instance_transform_2d(slot, HIDDEN)
	mm.visible_instance_count = int(band.high)


func _write(mm: MultiMesh, slot: int, die: Node2D) -> void:
	var size: float = kind_size.get(die.die_kind, 62.0) * scale_factor
	mm.set_instance_transform_2d(slot, Transform2D(0.0, Vector2(size, size), 0.0, die.position))
	mm.set_instance_custom_data(slot, kind_uv.get(die.die_kind, Color(0, 0, 0, 0)))


func add(die: Node2D) -> bool:
	if not enabled or not kind_uv.has(die.die_kind):
		return false
	if die.batch_band != -1:
		remove(die)
	var z := band_for(die.position.y)
	var band := _band(z)
	var free: Array = band.free
	var slot := -1
	if not free.is_empty():
		slot = free.pop_back()
	else:
		if int(band.high) >= (band.mm as MultiMesh).instance_count:
			_grow(band)
		slot = int(band.high)
		band.high = slot + 1
		(band.mm as MultiMesh).visible_instance_count = int(band.high)
	(band.owners as Array)[slot] = die
	_write(band.mm, slot, die)
	die.batch_band = z
	die.batch_slot = slot
	batched_count += 1
	return true


func remove(die: Node2D) -> void:
	var z: int = die.batch_band
	if z == -1:
		return
	var band: Dictionary = bands.get(z, {})
	var slot: int = die.batch_slot
	die.batch_band = -1
	die.batch_slot = -1
	if band.is_empty() or slot < 0:
		return
	var owners: Array = band.owners
	if slot < owners.size() and owners[slot] == die:
		owners[slot] = null
		(band.mm as MultiMesh).set_instance_transform_2d(slot, HIDDEN)
		(band.free as Array).append(slot)
		batched_count -= 1


## Redraws every batched dice with a new size factor.
func set_scale_factor(value: float) -> void:
	if is_equal_approx(value, scale_factor):
		return
	scale_factor = value
	for band in bands.values():
		var mm: MultiMesh = band.mm
		var owners: Array = band.owners
		for slot in range(int(band.high)):
			var die = owners[slot]
			if die != null and is_instance_valid(die):
				_write(mm, slot, die)


func clear_all() -> void:
	for band in bands.values():
		var mm: MultiMesh = band.mm
		var owners: Array = band.owners
		for slot in range(int(band.high)):
			var die = owners[slot]
			if die != null and is_instance_valid(die):
				die.batch_band = -1
				die.batch_slot = -1
			owners[slot] = null
		band.free = []
		band.high = 0
		mm.visible_instance_count = 0
	batched_count = 0
