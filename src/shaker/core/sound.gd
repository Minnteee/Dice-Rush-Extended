extends RefCounted
## Dice Shaker sound effects: small 16-bit WAV files in res://shaker/audio/ (made by
## tools/shaker/gen_sounds.py), played on the game's "SFX" bus so the volume setting applies.

const ROOT := "res://shaker/audio/"
const MAX_PLAYERS := 10

static var _streams: Dictionary = {}
static var _players: Array = []
static var _last: Dictionary = {}


static func play(sound_name: String, volume: float = 1.0) -> void:
	var stream := _stream(sound_name)
	if stream == null:
		return
	var now := Time.get_ticks_msec()
	if now - int(_last.get(sound_name, -1000)) < 35:
		return
	_last[sound_name] = now
	var player := _free_player()
	if player == null:
		return
	player.stream = stream
	player.volume_db = linear_to_db(clampf(volume, 0.01, 1.5))
	player.pitch_scale = randf_range(0.95, 1.05)
	player.play()


static func _free_player() -> AudioStreamPlayer:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return null
	var alive: Array = []
	for player in _players:
		if is_instance_valid(player):
			alive.append(player)
	_players = alive
	for player in _players:
		if not (player as AudioStreamPlayer).playing:
			return player
	if _players.size() >= MAX_PLAYERS:
		return _players[0]
	var created := AudioStreamPlayer.new()
	created.bus = "SFX"
	created.process_mode = Node.PROCESS_MODE_ALWAYS
	tree.root.add_child(created)
	_players.append(created)
	return created


static func _stream(sound_name: String) -> AudioStream:
	if _streams.has(sound_name):
		return _streams[sound_name]
	var stream := _read_wav(ROOT + sound_name + ".wav")
	_streams[sound_name] = stream
	return stream


## Minimal reader for 16-bit PCM mono/stereo WAV files.
static func _read_wav(path: String) -> AudioStreamWAV:
	if not FileAccess.file_exists(path):
		return null
	var bytes := FileAccess.get_file_as_bytes(path)
	if bytes.size() < 44 or bytes.slice(0, 4).get_string_from_ascii() != "RIFF" or bytes.slice(8, 12).get_string_from_ascii() != "WAVE":
		return null
	var channels := 1
	var rate := 44100
	var bits := 16
	var data := PackedByteArray()
	var offset := 12
	while offset + 8 <= bytes.size():
		var chunk := bytes.slice(offset, offset + 4).get_string_from_ascii()
		var size := bytes.decode_u32(offset + 4)
		if chunk == "fmt ":
			channels = bytes.decode_u16(offset + 10)
			rate = bytes.decode_u32(offset + 12)
			bits = bytes.decode_u16(offset + 22)
		elif chunk == "data":
			data = bytes.slice(offset + 8, offset + 8 + size)
		offset += 8 + size + (size % 2)
	if bits != 16 or data.is_empty():
		return null
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = rate
	stream.stereo = channels == 2
	stream.data = data
	return stream
