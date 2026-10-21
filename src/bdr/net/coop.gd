extends Node
## Dice Rush Extended - coop for 2 players.
##  * The game only runs on the HOST (money, rolls, events, workers ...).
##  * The CLIENT gets a full snapshot of the table when it joins, then a stream of world events
##    (spawn / remove / roll / popups / effects), positions (workers, moving dice, cursor) and the
##    game state (counters, talents, cards ...). Everything the client does (clicks, purchases,
##    talents, lucky cubes, tarot, events) is sent to the host, which executes it for both.
##  * Transport: ENet over IP (LAN, Hamachi, port forwarding) on a fixed port. When Steam is
##    available it is used to invite friends (lobby + overlay); the connection itself stays IP.

const I18N := preload("res://bdr/core/i18n.gd")
const PROTOCOL := 2
const DEFAULT_PORT := 47777
const CONNECT_TIMEOUT := 12.0
const EVENTS_EVERY := 0.05
const STATUS_EVERY := 0.1
const STATE_EVERY := 0.5
const CURSOR_EVERY := 0.05
const LAUNCH_META := "bdr_coop_launch"
const MESSAGE_META := "bdr_coop_message"
const NPC_ANIMS := ["idle", "walk_right", "walk_left", "walk_down", "walk_up", "attack"]

const EV_SPAWN := 1
const EV_REMOVE := 2
const EV_ROLL := 3
const EV_POPUP := 4
const EV_MOVE := 5
const EV_RING := 6
const EV_TOAST := 7
const EV_EVENT := 8

signal status_changed
signal reply_received(kind: String, data: Variant)

var game: Node
var main: Node
var role := ""
var peer: MultiplayerPeer
var partner_id := 0
var partner_ready := false
var partner_in_menu := false
var partner_cursor := Vector2(-1.0, -1.0)
var partner_name := ""
var host_port := DEFAULT_PORT
var host_address := ""
var host_in_menu := false
var host_cursor := Vector2(-1.0, -1.0)
var _next_nid := 1
var _by_nid: Dictionary = {}
var _events := StreamPeerBuffer.new()
var _event_count := 0
var _t_events := 0.0
var _t_status := 0.0
var _t_state := 0.0
var _t_cursor := 0.0
var _t_connect := 0.0
var _state_hash := 0
var _last_sent_cursor := Vector2(-1.0, -1.0)
var _last_sent_design := -1
## mouse design (index) of the guest / of the host, shown on the other screen
var partner_cursor_design := 0
var host_cursor_design := 0
## tests / screenshots only: a fixed world position used instead of the mouse (x < 0 = off)
var test_cursor := Vector2(-1.0, -1.0)


func local_cursor_position() -> Vector2:
	return test_cursor if test_cursor.x >= 0.0 else main.get_global_mouse_position()
var _last_partner_cursor := Vector2(-1.0, -1.0)
var _npc_targets: Array = []
var _motion_targets: Dictionary = {}
var _steam: Object = null
var _lobby_id := 0
var _signals_connected := false


# ---------------------------------------------------------------- launch info (survives the scene change)
static func launch() -> Dictionary:
	if GameSession.has_meta(LAUNCH_META):
		return GameSession.get_meta(LAUNCH_META)
	return {}


static func set_launch(data: Dictionary) -> void:
	GameSession.set_meta(LAUNCH_META, data)


static func clear_launch() -> void:
	if GameSession.has_meta(LAUNCH_META):
		GameSession.remove_meta(LAUNCH_META)


static func take_message() -> String:
	if not GameSession.has_meta(MESSAGE_META):
		return ""
	var text := str(GameSession.get_meta(MESSAGE_META))
	GameSession.remove_meta(MESSAGE_META)
	return text


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	name = "BDRCoop"
	process_mode = Node.PROCESS_MODE_ALWAYS
	_events.big_endian = false
	if Engine.has_singleton("Steam"):
		_steam = Engine.get_singleton("Steam")


func is_host() -> bool:
	return role == "host"


func is_client() -> bool:
	return role == "client" or str(launch().get("mode", "")) == "client"


## True while two players are connected.
func is_active() -> bool:
	return role != "" and partner_ready


func local_in_menu() -> bool:
	return bool(main.bdr.overlay_open()) or main.upgrade_overlay.visible \
		or (is_instance_valid(main.dog_shrine_controller) and main.dog_shrine_controller.visible) \
		or _menu_controller_open()


func _menu_controller_open() -> bool:
	var menu = main.menu_controller
	if menu == null:
		return false
	for key in ["pause_menu", "settings_menu", "achievement_menu"]:
		var node = menu.get(key)
		if node is CanvasItem and (node as CanvasItem).visible:
			return true
	return false


## In coop the table keeps running while only one player is in a menu.
func world_runs_during_menus() -> bool:
	if not is_active():
		return false
	return not (local_in_menu() and partner_in_menu)


# ---------------------------------------------------------------- network ids of the dice
func nid_of(die: DiceActor) -> int:
	if not is_instance_valid(die):
		return 0
	if die.net_id <= 0:
		die.net_id = _next_nid
		_next_nid += 1
		_by_nid[die.net_id] = die
	return die.net_id


func die_by_nid(nid: int) -> DiceActor:
	var die = _by_nid.get(nid)
	if die != null and is_instance_valid(die):
		return die
	_by_nid.erase(nid)
	return null


func register_die(die: DiceActor, nid: int) -> void:
	if nid <= 0 or not is_instance_valid(die):
		return
	die.net_id = nid
	_by_nid[nid] = die
	_next_nid = maxi(_next_nid, nid + 1)


func _assign_all_nids() -> void:
	for die in main.dice:
		if is_instance_valid(die):
			nid_of(die)


# ---------------------------------------------------------------- hosting
func start_host(port: int = DEFAULT_PORT) -> bool:
	stop(false)
	var enet := ENetMultiplayerPeer.new()
	var err := enet.create_server(port, 1)
	if err != OK:
		game.toast(I18N.f("coop.error_port", {"port": str(port)}))
		return false
	peer = enet
	host_port = port
	multiplayer.multiplayer_peer = peer
	_connect_signals()
	role = "host"
	_assign_all_nids()
	_steam_presence(true)
	game.toast(I18N.f("coop.hosting", {"port": str(port)}))
	status_changed.emit()
	return true


func local_addresses() -> Array[String]:
	var hamachi: Array[String] = []
	var lan: Array[String] = []
	for address in IP.get_local_addresses():
		var text := str(address)
		if text.contains(":") or text.begins_with("127.") or text.begins_with("169.254."):
			continue
		if text.begins_with("25.") or text.begins_with("26."):
			# Hamachi (25.x) and Radmin VPN (26.x) first
			hamachi.append(text)
		else:
			lan.append(text)
	hamachi.append_array(lan)
	return hamachi


# ---------------------------------------------------------------- joining
func start_client(address: String, port: int = DEFAULT_PORT) -> void:
	stop(false)
	host_address = address
	host_port = port
	var enet := ENetMultiplayerPeer.new()
	var err := enet.create_client(address, port)
	if err != OK:
		_client_failed(I18N.f("coop.error_connect", {"address": address}))
		return
	peer = enet
	multiplayer.multiplayer_peer = peer
	_connect_signals()
	role = "client"
	_t_connect = 0.0
	status_changed.emit()


func _client_failed(message: String) -> void:
	stop(false)
	clear_launch()
	AchievementService.set_progress_suppressed(false)
	GameSession.set_meta(MESSAGE_META, message)
	get_tree().paused = false
	get_tree().change_scene_to_file.call_deferred(main.START_MENU_SCENE)


func _connect_signals() -> void:
	if _signals_connected:
		return
	_signals_connected = true
	multiplayer.peer_connected.connect(_on_peer_connected)
	multiplayer.peer_disconnected.connect(_on_peer_disconnected)
	multiplayer.connected_to_server.connect(_on_connected_to_server)
	multiplayer.connection_failed.connect(_on_connection_failed)
	multiplayer.server_disconnected.connect(_on_server_disconnected)


func stop(notify: bool = true) -> void:
	if peer != null:
		if multiplayer.multiplayer_peer == peer:
			multiplayer.multiplayer_peer = null
		peer.close()
	peer = null
	var was_active := is_active()
	role = ""
	partner_id = 0
	partner_ready = false
	partner_in_menu = false
	partner_cursor = Vector2(-1.0, -1.0)
	_events.clear()
	_event_count = 0
	_steam_presence(false)
	if notify and was_active:
		game.toast(I18N.t("coop.ended"))
	status_changed.emit()


func _on_peer_connected(id: int) -> void:
	if not is_host():
		return
	if partner_id != 0 and partner_id != id:
		(peer as ENetMultiplayerPeer).disconnect_peer(id)
		return
	partner_id = id


func _on_peer_disconnected(id: int) -> void:
	if not is_host() or id != partner_id:
		return
	partner_id = 0
	partner_ready = false
	partner_in_menu = false
	partner_cursor = Vector2(-1.0, -1.0)
	game.toast(I18N.t("coop.partner_left"))
	status_changed.emit()


func _on_connected_to_server() -> void:
	_hello.rpc_id(1, PROTOCOL, str(game.MOD_VERSION), _player_name())


func _on_connection_failed() -> void:
	_client_failed(I18N.f("coop.error_connect", {"address": host_address}))


func _on_server_disconnected() -> void:
	_client_failed(I18N.t("coop.host_left"))


func _player_name() -> String:
	if _steam != null and bool(_steam.call("isSteamRunning")):
		return str(_steam.call("getPersonaName"))
	return OS.get_environment("USERNAME")


# ---------------------------------------------------------------- per frame
func _process(delta: float) -> void:
	if role.is_empty():
		return
	if role == "client" and not partner_ready:
		_t_connect += delta
		if _t_connect > CONNECT_TIMEOUT:
			_client_failed(I18N.f("coop.error_connect", {"address": host_address}))
		return
	if not partner_ready:
		return
	if is_host():
		_host_process(delta)
	else:
		_client_process(delta)


func _host_process(delta: float) -> void:
	# keep the table running unless both players are in a menu
	if get_tree().paused and world_runs_during_menus():
		get_tree().paused = false
	_t_events += delta
	if _t_events >= EVENTS_EVERY:
		_t_events = 0.0
		_flush_events()
	_t_status += delta
	if _t_status >= STATUS_EVERY:
		_t_status = 0.0
		_status.rpc_id(partner_id, _build_status())
	_t_state += delta
	if _t_state >= STATE_EVERY:
		_t_state = 0.0
		var state: Dictionary = main._coop_state()
		var state_hash := hash(state)
		if state_hash != _state_hash:
			_state_hash = state_hash
			var raw := var_to_bytes(state)
			_state.rpc_id(partner_id, raw.compress(FileAccess.COMPRESSION_ZSTD), raw.size())
	if partner_cursor.x >= 0.0 and _last_partner_cursor.x >= 0.0 and partner_cursor != _last_partner_cursor:
		main._coop_remote_hover(_last_partner_cursor, partner_cursor)
	_last_partner_cursor = partner_cursor


func _client_process(delta: float) -> void:
	if get_tree().paused:
		get_tree().paused = false
	_t_cursor += delta
	if _t_cursor >= CURSOR_EVERY:
		_t_cursor = 0.0
		var cursor: Vector2 = local_cursor_position()
		var menu := local_in_menu()
		var design: int = game.shop.local_cursor_design()
		if cursor != _last_sent_cursor or menu != partner_in_menu or design != _last_sent_design:
			_last_sent_cursor = cursor
			_last_sent_design = design
			_cursor.rpc_id(1, cursor.x, cursor.y, menu, design)
	_update_puppets(delta)


# ---------------------------------------------------------------- host: world events
func _put_string(text: String) -> void:
	var bytes := text.to_utf8_buffer()
	_events.put_u16(mini(bytes.size(), 65535))
	_events.put_data(bytes.slice(0, 65535))


func on_spawn(die: DiceActor) -> void:
	if not (is_host() and partner_ready):
		return
	var nid := nid_of(die)
	_events.put_u8(EV_SPAWN)
	_events.put_u32(nid)
	_put_string(die.die_kind)
	_events.put_float(die.position.x)
	_events.put_float(die.position.y)
	_event_count += 1


func on_remove(die: DiceActor) -> void:
	if not is_instance_valid(die) or die.net_id <= 0:
		return
	var nid := die.net_id
	_by_nid.erase(nid)
	die.net_id = 0
	if not (is_host() and partner_ready):
		return
	_events.put_u8(EV_REMOVE)
	_events.put_u32(nid)
	_event_count += 1


func on_roll(die: DiceActor, target: Vector2, animated: bool, interactive: bool) -> void:
	if not (is_host() and partner_ready):
		return
	_events.put_u8(EV_ROLL)
	_events.put_u32(nid_of(die))
	_events.put_float(target.x)
	_events.put_float(target.y)
	_events.put_u8((1 if animated else 0) | (2 if interactive else 0))
	_events.put_u8(clampi(die.last_face, 0, 255))
	_events.put_float(die.last_roll_duration)
	_event_count += 1


func on_popup(at: Vector2, text: String, positive: bool) -> void:
	if not (is_host() and partner_ready):
		return
	_events.put_u8(EV_POPUP)
	_events.put_float(at.x)
	_events.put_float(at.y)
	_events.put_u8(1 if positive else 0)
	_put_string(text)
	_event_count += 1


func on_move(die: DiceActor) -> void:
	if not (is_host() and partner_ready) or not is_instance_valid(die):
		return
	_events.put_u8(EV_MOVE)
	_events.put_u32(nid_of(die))
	_events.put_float(die.position.x)
	_events.put_float(die.position.y)
	_event_count += 1


func on_ring(center: Vector2, radius: float, color: Color) -> void:
	if not (is_host() and partner_ready):
		return
	_events.put_u8(EV_RING)
	_events.put_float(center.x)
	_events.put_float(center.y)
	_events.put_float(radius)
	_events.put_u32(color.to_rgba32())
	_event_count += 1


func on_toast(text: String) -> void:
	if not (is_host() and partner_ready):
		return
	_events.put_u8(EV_TOAST)
	_put_string(text)
	_event_count += 1


## Random event messages (start / finish / object clicked), see events.gd.
func on_event_message(data: Array) -> void:
	if not (is_host() and partner_ready):
		return
	var raw := var_to_bytes(data)
	_events.put_u8(EV_EVENT)
	_events.put_u32(raw.size())
	_events.put_data(raw)
	_event_count += 1


func _flush_events() -> void:
	if _event_count <= 0:
		return
	_world.rpc_id(partner_id, _events.data_array)
	_events.clear()
	_event_count = 0


func _build_status() -> Dictionary:
	var npc_data := PackedFloat32Array()
	for npc in main.npcs:
		if not is_instance_valid(npc):
			continue
		npc_data.append(npc.position.x)
		npc_data.append(npc.position.y)
		npc_data.append(float(maxi(0, NPC_ANIMS.find(str(npc._current_animation)))))
	var moving := PackedFloat32Array()
	var movers: Array = game.mech.moving_dice()
	movers.append_array(main._cats)
	for die in movers:
		if is_instance_valid(die) and (die.special_motion or die.die_kind == "cat"):
			moving.append(float(nid_of(die)))
			moving.append(die.position.x)
			moving.append(die.position.y)
	var status := {
		"m": float(main.money),
		"t": float(main.total_money_earned),
		"g": int(main.golden_coins),
		"c": local_cursor_position(),
		"cd": game.shop.local_cursor_design(),
		"menu": local_in_menu(),
		"npc": npc_data,
		"mv": moving,
		"gl": float(main.golden_bone_luck_time_left),
		"gs": float(main.golden_bone_storm_time_left),
		"lb": float(game.lucky.boost_left()),
		"dj": float(game.staff.dj_left()),
	}
	var bone = main.golden_bone_offer_button
	if bone != null and is_instance_valid(bone):
		status["bone"] = [float(main.golden_bone_offer_time_left), bone.position.x, bone.position.y]
	return status


# ---------------------------------------------------------------- RPC: client -> host
@rpc("any_peer", "call_remote", "reliable")
func _hello(protocol: int, mod_version: String, player_name: String) -> void:
	if not is_host():
		return
	var sender := multiplayer.get_remote_sender_id()
	if sender != partner_id:
		return
	if protocol != PROTOCOL or mod_version != str(game.MOD_VERSION):
		_reply.rpc_id(sender, "error", I18N.f("coop.error_version", {"version": str(game.MOD_VERSION)}))
		return
	partner_name = player_name
	_assign_all_nids()
	var raw := var_to_bytes(main._coop_snapshot())
	_events.clear()
	_event_count = 0
	_snapshot.rpc_id(sender, raw.compress(FileAccess.COMPRESSION_ZSTD), raw.size())
	partner_ready = true
	_state_hash = 0
	game.toast(I18N.f("coop.partner_joined", {"name": player_name}))
	status_changed.emit()


@rpc("any_peer", "call_remote", "unreliable_ordered")
func _cursor(x: float, y: float, in_menu: bool, design: int) -> void:
	if not is_host() or multiplayer.get_remote_sender_id() != partner_id:
		return
	partner_cursor = Vector2(x, y)
	partner_in_menu = in_menu
	partner_cursor_design = design


@rpc("any_peer", "call_remote", "reliable")
func _request(action: String, args: Array) -> void:
	if not is_host() or multiplayer.get_remote_sender_id() != partner_id or not partner_ready:
		return
	main._coop_handle_request(action, args)


## Host -> client answer to a request (lucky rewards, tarot cards, errors ...).
func reply(kind: String, data: Variant) -> void:
	if is_host() and partner_ready:
		_reply.rpc_id(partner_id, kind, data)


## Client -> host.
func request(action: String, args: Array) -> void:
	if role == "client" and partner_ready:
		_request.rpc_id(1, action, args)


# ---------------------------------------------------------------- RPC: host -> client
@rpc("authority", "call_remote", "reliable")
func _snapshot(bytes: PackedByteArray, raw_size: int) -> void:
	var data = bytes_to_var(bytes.decompress(raw_size, FileAccess.COMPRESSION_ZSTD))
	if data is not Dictionary:
		_client_failed(I18N.t("coop.error_snapshot"))
		return
	_by_nid.clear()
	main._coop_client_load(data)
	partner_ready = true
	status_changed.emit()


@rpc("authority", "call_remote", "reliable")
func _state(bytes: PackedByteArray, raw_size: int) -> void:
	if not partner_ready:
		return
	var data = bytes_to_var(bytes.decompress(raw_size, FileAccess.COMPRESSION_ZSTD))
	if data is Dictionary:
		main._coop_apply_state(data)


@rpc("authority", "call_remote", "unreliable_ordered")
func _status(data: Dictionary) -> void:
	if not partner_ready:
		return
	main._coop_apply_status(data)
	host_cursor = data.get("c", Vector2(-1.0, -1.0))
	host_cursor_design = int(data.get("cd", 0))
	host_in_menu = bool(data.get("menu", false))
	partner_in_menu = host_in_menu
	var npc_data: PackedFloat32Array = data.get("npc", PackedFloat32Array())
	_npc_targets.clear()
	for index in range(0, npc_data.size() - 2, 3):
		_npc_targets.append([Vector2(npc_data[index], npc_data[index + 1]), int(npc_data[index + 2])])
	var moving: PackedFloat32Array = data.get("mv", PackedFloat32Array())
	_motion_targets.clear()
	for index in range(0, moving.size() - 2, 3):
		_motion_targets[int(moving[index])] = Vector2(moving[index + 1], moving[index + 2])


@rpc("authority", "call_remote", "reliable")
func _world(bytes: PackedByteArray) -> void:
	if not partner_ready:
		return
	var buffer := StreamPeerBuffer.new()
	buffer.big_endian = false
	buffer.data_array = bytes
	while buffer.get_position() < buffer.get_size():
		var code := buffer.get_u8()
		match code:
			EV_SPAWN:
				var nid := buffer.get_u32()
				var kind := _get_string(buffer)
				var at := Vector2(buffer.get_float(), buffer.get_float())
				main._coop_client_spawn(nid, kind, at)
			EV_REMOVE:
				var die := die_by_nid(buffer.get_u32())
				if die != null:
					main._coop_client_remove(die)
			EV_ROLL:
				var nid := buffer.get_u32()
				var target := Vector2(buffer.get_float(), buffer.get_float())
				var flags := buffer.get_u8()
				var face := buffer.get_u8()
				var duration := buffer.get_float()
				var die := die_by_nid(nid)
				if die != null:
					main._coop_client_roll(die, target, (flags & 1) != 0, (flags & 2) != 0, face, duration)
			EV_POPUP:
				var at := Vector2(buffer.get_float(), buffer.get_float())
				var positive := buffer.get_u8() != 0
				var text := _get_string(buffer)
				if main._can_show_reward_popup(positive):
					main._show_reward(at, text, positive)
			EV_MOVE:
				var die := die_by_nid(buffer.get_u32())
				var at := Vector2(buffer.get_float(), buffer.get_float())
				if die != null:
					game.teleport_die(die, at)
			EV_RING:
				var center := Vector2(buffer.get_float(), buffer.get_float())
				var radius := buffer.get_float()
				var color := Color.hex(buffer.get_u32())
				game.fx_ring(center, radius, color)
			EV_TOAST:
				game.toast(_get_string(buffer))
			EV_EVENT:
				var size := buffer.get_u32()
				var chunk: Array = buffer.get_data(size)
				var message = bytes_to_var(chunk[1])
				if message is Array:
					game.events.coop_message(message)
			_:
				return


@rpc("authority", "call_remote", "reliable")
func _reply(kind: String, data: Variant) -> void:
	if kind == "error":
		_client_failed(str(data))
		return
	main._coop_client_reply(kind, data)
	reply_received.emit(kind, data)


func _get_string(buffer: StreamPeerBuffer) -> String:
	var size := buffer.get_u16()
	var chunk: Array = buffer.get_data(size)
	return (chunk[1] as PackedByteArray).get_string_from_utf8()


# ---------------------------------------------------------------- client: puppets
func _update_puppets(delta: float) -> void:
	# workers
	var npcs: Array = main.npcs
	while npcs.size() < _npc_targets.size():
		var npc: NPCActor = main._spawn_npc()
		npc._trailer_mode = true
		npc.position = _npc_targets[npcs.size() - 1][0]
	while npcs.size() > _npc_targets.size():
		var last = npcs.pop_back()
		if is_instance_valid(last):
			last.queue_free()
	var follow := clampf(delta * 12.0, 0.0, 1.0)
	for index in range(mini(npcs.size(), _npc_targets.size())):
		var npc = npcs[index]
		if not is_instance_valid(npc):
			continue
		var target: Vector2 = _npc_targets[index][0]
		npc.position = npc.position.lerp(target, follow)
		npc.z_index = 14 + int(npc.position.y / 100.0)
		npc._play_animation(NPC_ANIMS[clampi(int(_npc_targets[index][1]), 0, NPC_ANIMS.size() - 1)])
	# moving dice (cars, trains, cats ...)
	for nid in _motion_targets:
		var die := die_by_nid(int(nid))
		if die == null:
			continue
		var target: Vector2 = _motion_targets[nid]
		if die.position.distance_squared_to(target) > 0.25:
			game.teleport_die(die, die.position.lerp(target, follow))


# ---------------------------------------------------------------- Steam (invites only)
func steam_available() -> bool:
	return _steam != null and bool(_steam.call("isSteamRunning"))


func _steam_presence(enabled: bool) -> void:
	if not steam_available():
		return
	if enabled:
		var addresses := local_addresses()
		var connect := "+bdr_connect %s:%d" % [addresses[0] if not addresses.is_empty() else "127.0.0.1", host_port]
		_steam.call("setRichPresence", "connect", connect)
		_steam.call("setRichPresence", "status", "Dice Rush Extended - Coop")
	else:
		_steam.call("clearRichPresence")
		if _lobby_id != 0:
			_steam.call("leaveLobby", _lobby_id)
			_lobby_id = 0


## Opens the Steam overlay friend invite (creates a lobby that carries the host IP).
func steam_invite() -> bool:
	if not steam_available() or not is_host():
		return false
	if _lobby_id != 0:
		_steam.call("activateGameOverlayInviteDialog", _lobby_id)
		return true
	if not _steam.is_connected("lobby_created", _on_lobby_created):
		_steam.connect("lobby_created", _on_lobby_created)
	_steam.call("createLobby", 1, 2)
	return true


func _on_lobby_created(result: int, lobby_id: int) -> void:
	if result != 1:
		game.toast(I18N.t("coop.steam_failed"))
		return
	_lobby_id = lobby_id
	var addresses := local_addresses()
	_steam.call("setLobbyData", lobby_id, "bdr_ip", ",".join(addresses))
	_steam.call("setLobbyData", lobby_id, "bdr_port", str(host_port))
	_steam.call("activateGameOverlayInviteDialog", lobby_id)


## Client side: listen for "join game" requests from the Steam friends list / invites.
func listen_for_steam_invites(callback: Callable) -> void:
	if not steam_available():
		return
	if not _steam.is_connected("join_requested", _on_steam_join_requested):
		_steam.connect("join_requested", _on_steam_join_requested.bind(callback))
	if not _steam.is_connected("lobby_joined", _on_steam_lobby_joined):
		_steam.connect("lobby_joined", _on_steam_lobby_joined.bind(callback))


func _on_steam_join_requested(lobby_id: int, _friend_id: int, _callback: Callable) -> void:
	_steam.call("joinLobby", lobby_id)


func _on_steam_lobby_joined(lobby_id: int, _permissions: int, _locked: bool, _response: int, callback: Callable) -> void:
	var ips := str(_steam.call("getLobbyData", lobby_id, "bdr_ip")).split(",", false)
	var port := int(str(_steam.call("getLobbyData", lobby_id, "bdr_port")))
	if ips.is_empty():
		return
	callback.call(ips[0], port if port > 0 else DEFAULT_PORT)
