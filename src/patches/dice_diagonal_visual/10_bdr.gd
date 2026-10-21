# Dice Rush Extended: cube landmarks for the new dice textures.

static var extra_landmarks: Dictionary = {}
static var extra_seams: Dictionary = {}


static func register_landmarks(kind: String, points: Array, seam: Color) -> void:
	extra_landmarks[kind] = points
	extra_seams[kind] = seam


static func _landmarks_for(kind: String) -> Array:
	if LANDMARKS.has(kind):
		return LANDMARKS[kind]
	if extra_landmarks.has(kind):
		return extra_landmarks[kind]
	return LANDMARKS["d2"]


func configure(sprite: Sprite2D, kind: String) -> void:
	_sprite = sprite
	_kind = kind
	_source_visible = true
	var points: Array = _landmarks_for(kind)
	var texture_size: = sprite.texture.get_size()
	_projection = Vector3((points[1].x - points[3].x) * 0.5, 
		(points[2].y - points[0].y) * 0.5, points[5].y - points[2].y)
	if kind == "d2":
		_projection = Vector3(450.0, 310.0, 400.0)
	_projection_offset = (points[0] + points[5]) * 0.5 - texture_size * 0.5
	_rest_vertices = PackedVector2Array([points[2], points[1], points[0], points[3], 
		points[5], points[6], points[0] + points[5] - points[2], points[4]])
	for index in _rest_vertices.size():
		_rest_vertices[index] -= texture_size * 0.5


func _ensure_mesh() -> void :
	if is_instance_valid(_mesh_instance):
		return
	_material = ShaderMaterial.new()
	_material.shader = SHADER
	_material.set_shader_parameter("projection", _projection)
	_material.set_shader_parameter("projection_offset", _projection_offset)
	_material.set_shader_parameter("seam_color", SEAM_COLORS.get(_kind, extra_seams.get(_kind, Color("036fe5"))))
	_material.set_shader_parameter("spin_angle", _angle)
	_mesh_instance = MeshInstance2D.new()
	_mesh_instance.name = "DiagonalFlightVisual"
	_mesh_instance.texture = _sprite.texture
	_mesh_instance.material = _material
	_mesh_instance.mesh = _shared_mesh()
	_mesh_instance.visible = false
	_sprite.get_parent().add_child(_mesh_instance)


func _shared_mesh() -> ArrayMesh:
	var cache_key: = "%s:%s" % [_kind, _sprite.texture.get_size()]
	if _mesh_cache.has(cache_key):
		return _mesh_cache[cache_key] as ArrayMesh
	var vertices: = PackedVector2Array()
	var uvs: = PackedVector2Array()
	var custom: = PackedFloat32Array()
	var indices: = PackedInt32Array()
	var points: Array = _landmarks_for(_kind)
	var texture_size: = _sprite.texture.get_size()
	var source_faces: = [[points[2], points[1], points[0], points[3]], 
		[points[3], points[2], points[5], points[4]], 
		[points[2], points[1], points[6], points[5]]]
	for face_index in FACE_INDICES.size():
		var base_index: = vertices.size()
		for local_index in 4:
			var model_index: int = FACE_INDICES[face_index][local_index]
			var corner: Vector3 = MODEL_VERTICES[model_index]
			vertices.append(_rest_vertices[model_index])
			uvs.append(source_faces[face_index % 3][local_index] / texture_size)
			custom.append_array(PackedFloat32Array([corner.x, corner.y, corner.z, float(face_index)]))
		indices.append_array(PackedInt32Array([base_index, base_index + 1, base_index + 2, 
			base_index, base_index + 2, base_index + 3]))
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_CUSTOM0] = custom
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh: = ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays, [], {}, 
		Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT)
	var extent: = maxf(texture_size.x, texture_size.y)
	mesh.custom_aabb = AABB(Vector3( - extent, - extent, -1.0), Vector3(extent * 2.0, extent * 2.0, 2.0))
	_mesh_cache[cache_key] = mesh
	return mesh
