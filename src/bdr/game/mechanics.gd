extends RefCounted
## Dice Rush Extended - mechanics of the 100 new dice.
## base_reward() returns the payout of a landing before the game's multipliers,
## after_landing() runs side effects (rolling other dice, spawning, teleporting...).

const I18N := preload("res://bdr/core/i18n.gd")
const RED_NUMBERS := [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
const FOOD_KINDS := ["candy", "cookie", "donut", "pizza", "burger", "sushi"]
const YT_MILESTONES := [100, 1000, 10000, 100000, 1000000, 10000000, 100000000]
const EFFECT_COOLDOWN_MSEC := 1100

var main: Node
var game: Node
var st: Dictionary = {}          # global mechanic state (saved with the game)
var _tmp: Array[DiceActor] = []
var _near_exclude: DiceActor = null
var _near_filter: Callable
var _motions: Array[Dictionary] = []   # car / train / comet / rocket movements


func setup(game_main: Node, controller: Node) -> void:
	_near_filter = func(die: DiceActor) -> bool: return die != _near_exclude and _rollable(die)
	main = game_main
	game = controller
	reset_state()


func reset_state() -> void:
	st = {"viewers": 0.0, "subs": 0, "yt_next": 0, "blocks": 0, "lines": [], "pizza": 0, "sprinkles": 0,
		"stonks": 1.0, "stonks_timer": 45.0, "pot": 0, "bunny_rolls": 0, "honey": 0, "skulls": 0, "mahjong": []}
	_motions.clear()


func save_state() -> Dictionary:
	var out := st.duplicate(true)
	out["pot"] = str(float(st.get("pot", 0.0)))
	out["subs"] = str(int(st.get("subs", 0)))
	return out


func load_state(data: Variant) -> void:
	reset_state()
	if data is not Dictionary:
		return
	for key in data:
		st[key] = data[key]
	st["pot"] = str(data.get("pot", "0")).to_float()
	st["subs"] = int(str(data.get("subs", "0")))
	st["lines"] = []
	if st.get("mahjong") is not Array:
		st["mahjong"] = []


# ---------------------------------------------------------------- helpers
func _now() -> int:
	return Time.get_ticks_msec()


func _r(p: Dictionary, default: float) -> float:
	return float(p.get("radius", default)) * game.effect_radius_mult()


func _c(p: Dictionary, default: int) -> int:
	return maxi(1, int(round(float(p.get("count", default)) * game.effect_count_mult())))


func _popup(die: Node2D, key: String, params: Dictionary = {}, color_positive: bool = true) -> void:
	if main._can_show_reward_popup(true):
		main._show_reward(die.position + Vector2(0, -26), I18N.f(key, params), color_positive)


func _effect_ready(die: DiceActor) -> bool:
	var now := _now()
	if now - int(die.mstate.get("fx_cd", -100000)) < EFFECT_COOLDOWN_MSEC:
		return false
	die.mstate["fx_cd"] = now
	return true


func _rollable(die: DiceActor) -> bool:
	return is_instance_valid(die) and not die.rolling and not die.special_motion and die.die_kind != "cat"


## Collects up to `limit` resting dice around a point (roughly the nearest ones first).
## The grid search stops early, so this stays cheap even with thousands of dice.
func _near(center: Vector2, radius: float, exclude: DiceActor, limit: int) -> Array[DiceActor]:
	_tmp.clear()
	_near_exclude = exclude
	main._grid.query_nearest(center, radius, limit, _tmp, _near_filter)
	_near_exclude = null
	var result: Array[DiceActor] = []
	for die in _tmp:
		result.append(die)
	return result


func _random_dice(count: int, exclude: DiceActor) -> Array[DiceActor]:
	var picked: Array = []
	main._grid.random_dice(count, main.rng, picked, func(d: DiceActor) -> bool: return d != exclude and _rollable(d))
	var result: Array[DiceActor] = []
	for die in picked:
		result.append(die)
	return result


## Rolls a list of dice with a small stagger; mult > 1 boosts their next payout.
func roll_list(list: Array, mult: float = 1.0, stagger: float = 0.04, origin: Vector2 = Vector2.INF) -> int:
	var started := 0
	for index in range(list.size()):
		var die: DiceActor = list[index]
		if not _rollable(die):
			continue
		if mult > 1.0:
			die.pending_mult = minf(1000.0, maxf(die.pending_mult, 1.0) * mult)
		var delay := stagger * float(index)
		if origin.is_finite():
			delay = clampf(die.position.distance_to(origin) / 900.0, 0.0, 0.6)
		game.queue_roll(die, delay)
		started += 1
	return started


func kinds_owned() -> int:
	return game.kinds_owned_count()


# ---------------------------------------------------------------- spawn / roll hooks
func prepare(die: DiceActor, def: Dictionary) -> void:
	die.faces = def.get("faces_packed", PackedInt32Array())
	die.bdr_tier = int(def.tier)
	var p: Dictionary = def.get("p", {})
	match str(def.mech):
		"fast", "ninja":
			die.roll_speed = float(p.get("speed", 2.5))
		"slow":
			die.roll_speed = 1.0 / float(p.get("slow", 3.0))
		"grow":
			if not die.mstate.has("last_ms"):
				die.mstate["last_ms"] = _now()


func on_roll_started(die: DiceActor, def: Dictionary) -> void:
	if str(def.mech) == "trail":
		die.mstate["trail_from"] = [die.position.x, die.position.y]


# ---------------------------------------------------------------- payouts
func base_reward(die: DiceActor, value: int, def: Dictionary) -> float:
	var pay: float = def.pay
	var p: Dictionary = def.get("p", {})
	var mech: String = def.mech
	var base: float = float(value) * float(pay)
	match mech:
		"pepe":
			if value >= 10:
				_popup(die, "fx.pepe_good")
				game.stat("pepe_good", 1)
			elif value == 0:
				_popup(die, "fx.pepe_sad", {}, false)
		"sixseven":
			if value == 67:
				_popup(die, "fx.sixseven")
				game.stat("sixseven", 1)
			if int(die.mstate.get("last", 0)) == 6 and value == 7:
				base *= 6.7
				_popup(die, "fx.sixseven_combo")
				game.stat("sixseven", 1)
			die.mstate["last"] = value
		"clicker":
			if die.player_rolled:
				base *= float(p.get("mult", 5))
		"dnd":
			if value >= 20:
				base = 20.0 * pay * 20.0
				_popup(die, "fx.nat20")
				game.stat("nat20", 1)
			elif value <= 1:
				base = 0.0
				_popup(die, "fx.nat1", {}, false)
		"twitch":
			var viewers: float = st.get("viewers", 0.0)
			base += viewers * 2.0
			st["viewers"] = minf(1000000.0, viewers + 1.0 + viewers * 0.01)
			if main.rng.randf() < float(p.get("raid_chance", 0.02)):
				base *= 10.0
				roll_list(_random_dice(10, die), 1.0, 0.03)
				_popup(die, "fx.raid")
				game.stat("raids", 1)
		"youtube":
			var subs: int = int(st.get("subs", 0)) + main.rng.randi_range(1, 10)
			st["subs"] = subs
			base += float(subs) / 10.0
			var milestone_index: int = int(st.get("yt_next", 0))
			if milestone_index < YT_MILESTONES.size() and subs >= int(YT_MILESTONES[milestone_index]):
				st["yt_next"] = milestone_index + 1
				base += float(pay) * 1000.0 * float(milestone_index + 1)
				_popup(die, "fx.play_button", {"subs": int(YT_MILESTONES[milestone_index])})
				game.stat("play_buttons", 1)
		"pirate":
			if value == 0:
				_popup(die, "fx.skull", {}, false)
			elif value >= 30:
				_popup(die, "fx.treasure")
			var plunder := 0.0
			var now := _now()
			for other in _near(die.position, _r(p, 150), die, 20):
				if now - other.last_payout_msec < 5000:
					plunder += float(other.last_payout) * float(p.get("plunder", 3)) / 100.0
			base += minf(plunder, float(pay) * 1000.0)
		"combo":
			var now := _now()
			var combo: int = int(die.mstate.get("combo", 0))
			if now - int(die.mstate.get("last_ms", -100000)) <= int(float(p.get("window", 4.0)) * 1000.0):
				combo = mini(combo + 1, int(p.get("max", 10)))
			else:
				combo = 0
			die.mstate["combo"] = combo
			die.mstate["last_ms"] = now
			base *= 1.0 + float(p.get("step", 0.25)) * combo
			if combo >= int(p.get("max", 10)):
				game.stat("console_max", 1)
		"slot":
			var a: int = main.rng.randi_range(0, 2)
			var b: int = main.rng.randi_range(0, 2)
			var c: int = main.rng.randi_range(0, 2)
			var mult := 1.0
			if a == 2 and b == 2 and c == 2:
				mult = 77.0
				_popup(die, "fx.jackpot")
				game.stat("slot_jackpot", 1)
			elif a == b and b == c:
				mult = 10.0
			elif a == b or b == c or a == c:
				mult = 2.0
			base = float(pay) * mult
		"breeder":
			st["bunny_rolls"] = int(st.get("bunny_rolls", 0)) + 1
		"donut":
			if value == 1:
				st["sprinkles"] = int(st.get("sprinkles", 0)) + 1
			if int(st.get("sprinkles", 0)) >= 6:
				st["sprinkles"] = 0
				base *= 36.0
				_popup(die, "fx.donut")
		"godot":
			base *= float(maxi(1, kinds_owned()))
		"tetris":
			base = float(pay)
			st["blocks"] = int(st.get("blocks", 0)) + 1
			if int(st.blocks) >= 10:
				st["blocks"] = int(st.blocks) - 10
				var tetris_count: int = mini(game.count("tetris"), 50)
				base += float(pay) * 10.0 * float(tetris_count)
				var lines: Array = st.get("lines", [])
				var now := _now()
				lines.append(now)
				while not lines.is_empty() and now - int(lines[0]) > 30000:
					lines.pop_front()
				game.stat("tetris_lines", 1)
				if lines.size() >= 4:
					lines.clear()
					base += float(pay) * 100.0 * float(tetris_count)
					_popup(die, "fx.tetris")
					game.stat("tetris_tetris", 1)
				else:
					_popup(die, "fx.line_clear")
				st["lines"] = lines
		"vault":
			var half := base / 2.0
			base = half
			die.mstate["vault"] = minf(9.0e18, float(die.mstate.get("vault", 0.0)) + half)
			die.mstate["rolls"] = int(die.mstate.get("rolls", 0)) + 1
			if int(die.mstate.rolls) >= int(p.get("every", 20)):
				base += float(die.mstate.vault) * float(p.get("mult", 3))
				die.mstate["vault"] = 0.0
				die.mstate["rolls"] = 0
				_popup(die, "fx.vault_open")
				game.stat("vault_open", 1)
		"luckyblock":
			base = _lucky_block(die, pay)
		"stonks":
			base *= float(st.get("stonks", 1.0))
		"every_n":
			st["pizza"] = int(st.get("pizza", 0)) + 1
			if int(st.pizza) % int(p.get("every", 8)) == 0:
				base *= float(p.get("mult", 8))
				_popup(die, "fx.pizza_party")
		"car", "rocket", "comet", "train":
			base = 0.0
		"roulette":
			if value == 0:
				base = float(pay) * 36.0
				_popup(die, "fx.green_zero")
				game.stat("roulette_zero", 1)
			elif value in RED_NUMBERS:
				base = float(pay) * 2.0
			else:
				base = float(pay)
		"bomb":
			var countdown: int = int(die.mstate.get("countdown", 3)) - 1
			if countdown <= 0:
				countdown = 3
				base = float(pay) * float(p.get("mult", 10))
				die.mstate["boom"] = true
				_popup(die, "fx.boom")
				game.stat("bombs", 1)
			else:
				base = float(pay)
			die.mstate["countdown"] = countdown
		"food":
			var others := 0
			for food in FOOD_KINDS:
				if food != die.die_kind and game.count(food) > 0:
					others += 1
			base *= 1.0 + 0.25 * others
		"magic8":
			base = float(pay)
			die.mstate["answer"] = value
		"owl":
			base *= 1.0 + 0.02 * AchievementService.unlocked_count()
		"doge":
			base = float(pay) * pow(10.0, main.rng.randf_range(-1.0, 1.0))
			if main.rng.randf() < 0.01:
				base = float(pay) * 100.0
				_popup(die, "fx.to_the_moon")
				game.stat("doge_moon", 1)
		"troll":
			if value == 0:
				base = 0.0
				_popup(die, "fx.problem", {}, false)
			else:
				base = float(pay)
		"stack":
			var stack: int = 0 if value == 1 else mini(int(die.mstate.get("stack", 0)) + int(p.get("step", 10)), int(p.get("max", 300)))
			die.mstate["stack"] = stack
			base *= 1.0 + float(stack) / 100.0
		"domino":
			base *= 1.0 + float(p.get("step", 5)) * float(die.mstate.get("chain", 0)) / 100.0
		"drain":
			var drained := 0.0
			var now := _now()
			for other in _near(die.position, _r(p, 150), die, 20):
				if now - other.last_payout_msec < 5000:
					drained += float(other.last_payout) * float(p.get("percent", 10)) / 100.0
			base += minf(drained, float(pay) * 1000.0)
		"sus":
			var roll: float = main.rng.randf()
			if roll < 0.05:
				base = 0.0
				_popup(die, "fx.ejected", {}, false)
			elif roll < 0.15:
				die.mstate["meeting"] = true
				_popup(die, "fx.meeting")
		"trail":
			pass
		"grow":
			var now := _now()
			var steps := float(now - int(die.mstate.get("last_ms", now))) / 10000.0
			base *= minf(10.0, 1.0 + 0.05 * floorf(steps))
			die.mstate["last_ms"] = now
		"rickroll":
			if value == 6:
				base = 36.0 * pay
				_popup(die, "fx.rickroll")
				game.stat("rickroll", 1)
			else:
				base = float(maxi(3, value)) * pay
		"moon":
			if game.any_event_active():
				base *= 3.0
		"always_max":
			base = 6.0 * pay
		"keys":
			if main.rng.randf() < float(p.get("chance", 0.333)):
				die.mstate["keys"] = int(die.mstate.get("keys", 0)) + 1
			if int(die.mstate.get("keys", 0)) >= int(p.get("keys", 3)):
				die.mstate["keys"] = 0
				base = float(pay) * float(p.get("mult", 50))
				_popup(die, "fx.treasure")
				game.stat("treasure_open", 1)
			else:
				base = float(pay)
		"chaos":
			base *= minf(3.0, 1.0 + 0.05 * float(main.active_roll_count))
		"skibidi":
			if die.player_rolled:
				die.mstate["brainrot"] = 0
			base *= 1.0 + float(die.mstate.get("brainrot", 0)) / 100.0
		"sigma":
			var grind: int = 0 if die.player_rolled else mini(50, int(die.mstate.get("grind", 0)) + 1)
			die.mstate["grind"] = grind
			base *= 1.0 + 0.1 * grind
		"bee":
			st["honey"] = int(st.get("honey", 0)) + 1
			if int(st.honey) >= int(p.get("jar", 20)):
				st["honey"] = 0
				base *= float(p.get("mult", 30))
				_popup(die, "fx.honey")
		"quantum":
			var a: int = main.rng.randi_range(1, 6)
			var b: int = main.rng.randi_range(1, 6)
			base = float(a + b) * pay
			if a == 6 and b == 6:
				base *= 36.0
				_popup(die, "fx.entangled")
		"skeleton":
			base *= minf(4.0, 1.0 + float(st.get("skulls", 0)) * 0.001)
		"bank":
			base = clampf(float(main.money) * 0.002, float(pay), float(pay) * 50.0)
		"mahjong":
			var history: Array = st.get("mahjong", [])
			history.append(value)
			while history.size() > 3:
				history.pop_front()
			if history.size() == 3 and history[0] == history[1] and history[1] == history[2]:
				base *= 13.0
				history.clear()
				_popup(die, "fx.mahjong")
				game.stat("mahjong", 1)
			st["mahjong"] = history
		"glitch":
			if main.rng.randf() < float(p.get("chance", 0.1)):
				base *= float(p.get("mult", 8))
				_popup(die, "fx.glitch")
		"ohio":
			var roll: float = main.rng.randf()
			if roll < 0.05:
				base *= 20.0
				_popup(die, "fx.ohio_win")
			elif roll < 0.25:
				base = 0.0
				_popup(die, "fx.ohio", {}, false)
			elif roll < 0.35:
				die.mstate["teleport"] = true
			elif roll < 0.36:
				die.mstate["everything"] = true
		"phoenix":
			if bool(die.mstate.get("ashes", false)):
				die.mstate["ashes"] = false
				base *= 10.0
				_popup(die, "fx.rebirth")
				game.stat("phoenix", 1)
			elif value == 1:
				die.mstate["ashes"] = true
				base = 0.0
				_popup(die, "fx.burned", {}, false)
		"copycat":
			var best := 0.0
			var now := _now()
			for other in _near(die.position, _r(p, 200), die, 25):
				if now - other.last_payout_msec < 5000:
					best = maxf(best, other.last_payout)
			base += minf(float(best), float(pay) * 1000.0)
		"galaxy":
			base *= 1.0 + float(game.total_dice_count()) / 1000.0
		"jackpot":
			st["pot"] = minf(float(st.get("pot", 0.0)) + float(pay), 1.0e300)
			if main.rng.randf() < float(p.get("chance", 0.01)):
				base += float(st.pot)
				st["pot"] = 0
				_popup(die, "fx.jackpot")
				game.stat("jackpot", 1)
		"rewind":
			var repeats := 0
			while repeats < int(p.get("max", 3)) and main.rng.randf() < float(p.get("chance", 0.25)):
				repeats += 1
				base += float(main.rng.randi_range(1, 6)) * pay
			if repeats > 0:
				_popup(die, "fx.rewind", {"n": repeats + 1})
		"supernova":
			die.mstate["charge"] = int(die.mstate.get("charge", 0)) + 1
		"builder":
			die.mstate["n"] = int(die.mstate.get("n", 0)) + 1
		"ascend":
			die.mstate["asc"] = mini(int(p.get("max", 900)), int(die.mstate.get("asc", 0)) + int(p.get("step", 1)))
			base *= 1.0 + float(die.mstate.asc) / 100.0
		"infinity":
			base *= (1.0 + 0.05 * AchievementService.unlocked_count()) * (1.0 + 0.04 * kinds_owned())
		"rainbow":
			base *= 1.0 + 0.05 * kinds_owned()
		"cosmic":
			base *= 1.0 + float(game.active_event_count())
			if main.golden_bone_luck_time_left > 0.0:
				base *= 2.0
		"eruption":
			die.mstate["n"] = int(die.mstate.get("n", 0)) + 1
	return minf(base, 1.0e300)


# ---------------------------------------------------------------- side effects
func after_landing(die: DiceActor, reward: float, value: int, def: Dictionary) -> void:
	var p: Dictionary = def.get("p", {})
	var mech: String = def.mech
	match mech:
		"pepe":
			if not bool(die.mstate.get("hopped", false)) and main.rng.randf() < float(p.get("hop_chance", 0.12)):
				die.mstate["hopped"] = true
				game.queue_roll(die, 0.35)
			else:
				die.mstate["hopped"] = false
		"neighbors":
			if _effect_ready(die):
				var list := _near(die.position, _r(p, 120), die, _c(p, 3))
				if roll_list(list, 1.0, 0.0, die.position) > 0:
					game.fx_ring(die.position, _r(p, 120), game.kind_color(die.die_kind))
		"pirate":
			if value == 4 and _effect_ready(die):
				roll_list(_near(die.position, 160.0, die, 1))
		"freeze":
			var frozen := _near(die.position, _r(p, 140), die, 30)
			for other in frozen:
				other.pending_mult = maxf(other.pending_mult, float(p.get("mult", 2)))
			game.fx_ring(die.position, _r(p, 140), Color("9ee8ff"))
		"breeder":
			if int(st.get("bunny_rolls", 0)) >= int(p.get("every", 25)):
				st["bunny_rolls"] = 0
				if game.count(die.die_kind) < int(p.get("max", 200)):
					game.spawn_free(die.die_kind, die.position + Vector2(main.rng.randf_range(-60, 60), main.rng.randf_range(-60, 60)))
					_popup(die, "fx.newborn")
		"godot":
			if value == 6 and _effect_ready(die):
				var others: Array = []
				for other in game.dice_of_kind("godot"):
					if other != die and _rollable(other):
						others.append(other)
						if others.size() >= 20:
							break
				for other in others:
					other.mstate["fx_cd"] = _now()
				roll_list(others, 1.0, 0.05)
				game.fx_lines(die.position, others, Color("478cbf"))
		"zombie":
			if main.rng.randf() * 100.0 < float(p.get("chance", 8)) and game.count("zombie") < int(p.get("max", 300)):
				var victims: Array = []
				for other in _near(die.position, _r(p, 160), die, 12):
					if other.die_kind in ["50_50", "d4"] and other != die:
						if other.die_kind == "50_50" and main.dice_50_count <= 1:
							continue
						victims.append(other)
				if not victims.is_empty():
					var victim: DiceActor = victims[main.rng.randi_range(0, victims.size() - 1)]
					game.convert_die(victim, "zombie")
					_popup(die, "fx.brains")
					game.stat("zombie_bites", 1)
		"lightning":
			if _effect_ready(die):
				var struck := _random_dice(_c(p, 3), die)
				roll_list(struck, 1.0, 0.05)
				game.fx_lines(die.position, struck, Color("fff35a") if die.die_kind == "lightning" else Color("d06ab0"))
		"ghost":
			var spot: Vector2 = main._random_roll_target(die.position)
			game.teleport_die(die, spot)
			if _effect_ready(die):
				roll_list(_near(spot, 150.0, die, _c(p, 2)))
		"auto", "skibidi", "divine":
			pass
		"car":
			_start_motion(die, "car", def)
		"rocket":
			_start_motion(die, "rocket", def)
		"comet":
			_start_motion(die, "comet", def)
		"train":
			_start_motion(die, "train", def)
		"bomb":
			if bool(die.mstate.get("boom", false)):
				die.mstate["boom"] = false
				roll_list(_near(die.position, _r(p, 220), die, _c(p, 30)), 1.0, 0.0, die.position)
				game.fx_ring(die.position, _r(p, 220), Color("ff5a2a"))
		"cone":
			if _effect_ready(die):
				var direction := Vector2.RIGHT.rotated(main.rng.randf_range(0.0, TAU))
				var radius := _r(p, 300)
				var origin := die.position
				var hits: Array = []
				main._grid.query_nearest(origin, radius, _c(p, 25), hits, func(other: DiceActor) -> bool:
					if other == die or not _rollable(other):
						return false
					var offset := other.position - origin
					return offset.length_squared() < 1.0 or absf(direction.angle_to(offset)) <= 0.62)
				roll_list(hits, float(p.get("mult", 1)), 0.0, die.position)
				game.fx_cone(die.position, direction, radius, Color("ff7a1f"))
		"magic8":
			var answer: int = int(die.mstate.get("answer", 1))
			if answer == 1:
				for other in _near(die.position, _r(p, 250), die, 40):
					other.pending_mult = maxf(other.pending_mult, 2.0)
				_popup(die, "fx.yes")
			elif answer == 2:
				_popup(die, "fx.ask_again")
				game.queue_roll(die, 0.3)
			else:
				_popup(die, "fx.no", {}, false)
		"enchant":
			var targets := _random_dice(1, die)
			for other in targets:
				other.pending_mult = minf(1000.0, maxf(other.pending_mult, 1.0) * float(p.get("mult", 10)))
			game.fx_lines(die.position, targets, Color("b48aff"))
		"horn":
			if value == 6 and _effect_ready(die):
				var vikings: Array = []
				for other in game.dice_of_kind(die.die_kind):
					if other != die and _rollable(other):
						other.mstate["fx_cd"] = _now()
						vikings.append(other)
						if vikings.size() >= _c(p, 30):
							break
				roll_list(vikings, 1.0, 0.03)
		"ninja":
			var far: Array = []
			for other in _random_dice(8, die):
				if other.position.distance_to(die.position) > 300.0:
					far.append(other)
					if far.size() >= _c(p, 2):
						break
			roll_list(far)
			game.fx_lines(die.position, far, Color("e8261c"))
		"domino":
			var chain: int = int(die.mstate.get("chain", 0))
			die.mstate["chain"] = 0
			var dominos: Array = game.dice_of_kind("domino")
			if chain < mini(100, dominos.size() - 1):
				var index := dominos.find(die)
				if index >= 0 and dominos.size() > 1:
					var next_die: DiceActor = dominos[(index + 1) % dominos.size()]
					if _rollable(next_die):
						next_die.mstate["chain"] = chain + 1
						game.queue_roll(next_die, float(p.get("delay", 0.12)))
		"sus":
			if bool(die.mstate.get("meeting", false)):
				die.mstate["meeting"] = false
				roll_list(_near(die.position, _r(p, 250), die, _c(p, 40)), 1.0, 0.0, die.position)
				game.fx_ring(die.position, _r(p, 250), Color("e8261c"))
		"trail":
			var from: Array = die.mstate.get("trail_from", [die.position.x, die.position.y])
			var start := Vector2(float(from[0]), float(from[1]))
			_tmp.clear()
			main._grid.query_segment(start, die.position, float(p.get("width", 50)), _tmp)
			var hits: Array = []
			for other in _tmp:
				if other != die and _rollable(other):
					hits.append(other)
					if hits.size() >= _c(p, 25):
						break
			roll_list(hits, 1.0 + float(p.get("bonus", 20)) / 100.0, 0.02)
			game.fx_trail(start, die.position)
		"slash":
			if value == 6 and _effect_ready(die):
				var hits: Array = []
				_tmp.clear()
				var safe: Rect2 = game.board_safe_rect()
				main._grid.query_segment(Vector2(safe.position.x - 60.0, die.position.y), Vector2(safe.end.x + 60.0, die.position.y), float(p.get("width", 40)) * game.dice_scale(), _tmp)
				for other in _tmp:
					if other != die and _rollable(other):
						hits.append(other)
				hits.sort_custom(func(a: DiceActor, b: DiceActor) -> bool: return absf(a.position.x - die.position.x) < absf(b.position.x - die.position.x))
				if hits.size() > _c(p, 40):
					hits.resize(_c(p, 40))
				roll_list(hits, 1.0, 0.0, die.position)
				game.fx_slash(die.position.y)
		"chaos":
			if _effect_ready(die):
				roll_list(_near(die.position, _r(p, 180), die, _c(p, 20)), 1.0, 0.0, die.position)
				game.fx_ring(die.position, _r(p, 180), Color("ff7a1f"))
		"ufo":
			var targets := _random_dice(1, die)
			for other in targets:
				game.teleport_die(other, main._random_roll_target(other.position))
				other.pending_mult = maxf(other.pending_mult, float(p.get("mult", 3)))
				game.queue_roll(other, 0.2)
			game.fx_lines(die.position, targets, Color("8ae0a0"))
		"potion":
			if main.rng.randf() < float(p.get("chance", 0.25)):
				for other in _near(die.position, _r(p, 200), die, 40):
					other.pending_mult = maxf(other.pending_mult, float(p.get("mult", 3)))
				game.fx_ring(die.position, _r(p, 200), Color("7aff5a"))
				_popup(die, "fx.potion")
		"bee":
			roll_list(_near(die.position, 150.0 * game.dice_scale(), die, 1))
		"bonk":
			if _effect_ready(die):
				var bonked := _near(die.position, 260.0 * game.dice_scale(), die, _c(p, 5))
				roll_list(bonked, 1.1, 0.04)
				if not bonked.is_empty():
					_popup(die, "fx.bonk")
		"ohio":
			if bool(die.mstate.get("teleport", false)):
				die.mstate["teleport"] = false
				for other in game.dice_of_kind("ohio"):
					if _rollable(other) or other == die:
						game.teleport_die(other, main._random_roll_target(other.position))
			if bool(die.mstate.get("everything", false)):
				die.mstate["everything"] = false
				roll_list(_random_dice(300, die), 1.0, 0.002)
				_popup(die, "fx.ohio_all")
		"gravity":
			if _effect_ready(die):
				var pulled := _near(die.position, _r(p, 250), die, _c(p, 30))
				for other in pulled:
					var target: Vector2 = other.position.lerp(die.position, 0.6)
					other.pending_mult = maxf(other.pending_mult, 1.0 + 0.01 * pulled.size())
					game.queue_roll(other, 0.05, target)
				game.fx_ring(die.position, _r(p, 250), Color("b45aff"))
		"eruption":
			if int(die.mstate.get("n", 0)) % int(p.get("every", 10)) == 0:
				roll_list(_near(die.position, _r(p, 300), die, _c(p, 50)), float(p.get("mult", 2)), 0.0, die.position)
				game.fx_ring(die.position, _r(p, 300), Color("ff4a1f"))
				_popup(die, "fx.eruption")
		"impact":
			if _effect_ready(die):
				roll_list(_near(die.position, _r(p, 260), die, _c(p, 40)), 1.0 + float(p.get("bonus", 50)) / 100.0, 0.0, die.position)
				game.fx_ring(die.position, _r(p, 260), Color("ff8a2a"))
		"supernova":
			if int(die.mstate.get("charge", 0)) >= int(p.get("charge", 10)):
				die.mstate["charge"] = 0
				roll_list(_random_dice(_c(p, 400), die), float(p.get("mult", 2)), 0.002)
				game.fx_ring(die.position, 900.0, Color("ff8ad8"))
				_popup(die, "fx.supernova")
				game.stat("supernova", 1)
		"builder":
			if int(die.mstate.get("n", 0)) >= int(p.get("every", 30)):
				die.mstate["n"] = 0
				var kind: String = game.random_buildable_kind()
				if not kind.is_empty():
					game.spawn_free(kind, main._random_roll_target(die.position))
					_popup(die, "fx.built")


# ---------------------------------------------------------------- lucky block
func _lucky_block(die: DiceActor, pay: float) -> float:
	# Balance (v1.0): free levels, talent gold and free dice are rare and go through the shared
	# bonus budget of the controller; when the budget is empty the block pays money instead.
	game.stat("luckyblock", 1)
	var roll: float = main.rng.randf()
	if roll < 0.45:
		return float(pay) * main.rng.randi_range(1, 5)
	if roll < 0.60:
		_popup(die, "fx.lb_coins")
		return float(pay) * 10.0
	if roll < 0.62:
		var kind: String = game.random_owned_level_kind()
		if not kind.is_empty() and game.try_bonus("level"):
			main.die_levels[kind] = main._safe_add_int64(main._die_level(kind), 1)
			main._invalidate_eco()
			_popup(die, "fx.lb_level", {"name": game.display_name(kind)})
			return float(pay)
		_popup(die, "fx.lb_coins")
		return float(pay) * 10.0
	if roll < 0.74:
		roll_list(_random_dice(10, die), 1.0, 0.03)
		_popup(die, "fx.lb_rain")
		return float(pay)
	if roll < 0.86:
		return float(pay) * 5.0
	if roll < 0.96:
		roll_list(_near(die.position, 200.0 * game.dice_scale(), die, 25), 1.0, 0.0, die.position)
		game.fx_ring(die.position, 200.0 * game.dice_scale(), Color("ffd23a"))
		_popup(die, "fx.lb_boom")
		return float(pay)
	if roll < 0.985:
		_popup(die, "fx.jackpot")
		return float(pay) * 50.0
	if roll < 0.993:
		if game.try_bonus("gold"):
			main.golden_coins += 1
			_popup(die, "fx.lb_gold")
			main._request_all_labels_update()
			return float(pay)
		_popup(die, "fx.jackpot")
		return float(pay) * 25.0
	var free_kind: String = game.random_buildable_kind()
	if not free_kind.is_empty() and main._dice_table_has_capacity() and game.try_bonus("free_die"):
		game.spawn_free(free_kind, main._random_roll_target(die.position))
		_popup(die, "fx.lb_free_die")
		return float(pay)
	return float(pay) * 15.0


# ---------------------------------------------------------------- moving dice (car, train, comet, rocket)
func _start_motion(die: DiceActor, kind: String, def: Dictionary) -> void:
	var p: Dictionary = def.get("p", {})
	var safe: Rect2 = game.board_safe_rect()
	# A dice in the thin margin between the felt and the safe area (or one that escaped in an
	# older version) first snaps back onto the felt, otherwise the ray could aim far outside.
	if not main._die_position_is_on_playable_felt(die.position):
		game.teleport_die(die, main._clamp_die_position(die.position))
	var start := die.position
	var target := start
	var speed := float(p.get("speed", 620))
	match kind:
		"car":
			var direction := Vector2.RIGHT.rotated(main.rng.randf_range(0.0, TAU))
			target = main._clamp_die_position(_ray_to_rect(start, direction, safe))
		"train":
			var go_right := start.x < safe.get_center().x
			target = main._clamp_die_position(Vector2(safe.end.x if go_right else safe.position.x, start.y))
			speed = 760.0
		"comet":
			target = main._random_roll_target(start)
			for _attempt in range(6):
				if target.distance_to(start) > 420.0:
					break
				target = main._random_roll_target(start)
			speed = 1100.0
		"rocket":
			target = main._random_roll_target(start)
			for _attempt in range(6):
				if target.distance_to(start) > 350.0:
					break
				target = main._random_roll_target(start)
			speed = 0.0
	die.special_motion = true
	main._bdr_unrest_die(die)
	_motions.append({"die": die, "kind": kind, "start": start, "target": target, "speed": speed, "t": 0.0,
		"flight": float(p.get("flight", 2.5)), "hits": 0, "last": start, "def": def, "seen": {}})


func _ray_to_rect(origin: Vector2, direction: Vector2, rect: Rect2) -> Vector2:
	var best := INF
	if absf(direction.x) > 0.0001:
		for x: float in [rect.position.x, rect.end.x]:
			var t := (x - origin.x) / direction.x
			if t > 0.0:
				best = minf(best, t)
	if absf(direction.y) > 0.0001:
		for y: float in [rect.position.y, rect.end.y]:
			var t := (y - origin.y) / direction.y
			if t > 0.0:
				best = minf(best, t)
	if best == INF:
		return origin
	return origin + direction * best


func process_motions(delta: float) -> void:
	if _motions.is_empty():
		return
	for index in range(_motions.size() - 1, -1, -1):
		var motion: Dictionary = _motions[index]
		var die: DiceActor = motion.die
		if not is_instance_valid(die):
			_motions.remove_at(index)
			continue
		var p: Dictionary = (motion.def as Dictionary).get("p", {})
		var kind: String = motion.kind
		motion.t = float(motion.t) + delta
		if kind == "rocket":
			var flight := float(motion.flight)
			var t := clampf(float(motion.t) / flight, 0.0, 1.0)
			var start: Vector2 = motion.start
			var target: Vector2 = motion.target
			die.position = start.lerp(target, t)
			var lift := sin(t * PI) * 900.0
			die.set_visual_lift(lift, t)
			if t >= 1.0:
				die.set_visual_lift(0.0, 1.0)
				_finish_motion(die, motion, index)
				roll_list(_near(die.position, _r(p, 200), die, _c(p, 30)), 1.0, 0.0, die.position)
				game.fx_ring(die.position, _r(p, 200), Color("ff7a1f"))
				_pay_motion(die, motion)
			continue
		var start: Vector2 = motion.start
		var target: Vector2 = motion.target
		var total := maxf(1.0, start.distance_to(target))
		var travelled := minf(total, float(motion.t) * float(motion.speed))
		var previous: Vector2 = motion.last
		var current := start.lerp(target, travelled / total)
		die.position = current
		die.z_index = 12 + int(current.y / 100.0)
		die.rotation = (target - start).angle() if kind == "car" else 0.0
		_tmp.clear()
		main._grid.query_segment(previous, current, float(p.get("width", 46)), _tmp)
		var seen: Dictionary = motion.seen
		var limit := _c(p, 9999)
		for other in _tmp:
			if other == die or seen.has(other.get_instance_id()) or not _rollable(other):
				continue
			if int(motion.hits) >= limit:
				break
			seen[other.get_instance_id()] = true
			motion.hits = int(motion.hits) + 1
			game.queue_roll(other, 0.0)
		motion.last = current
		if kind == "comet" or kind == "train":
			game.fx_trail(previous, current)
		if travelled >= total:
			die.rotation = 0.0
			_finish_motion(die, motion, index)
			_pay_motion(die, motion)
			if kind == "car":
				game.stat("car_walls", 1)
				if main.rng.randf() < float(p.get("gold_chance", 0.02)) and game.try_bonus("gold"):
					main.golden_coins += 1
					_popup(die, "fx.lb_gold")
					main._request_all_labels_update()


func _finish_motion(die: DiceActor, motion: Dictionary, index: int) -> void:
	_motions.remove_at(index)
	die.special_motion = false
	die.rotation = 0.0
	if not main.BOARD_RECT.has_point(die.position):
		die.position = main._clamp_die_position(die.position)
	if die.grid_cell >= 0:
		main._grid.move(die, die.position)
	main._bdr_rest_die(die)


func _pay_motion(die: DiceActor, motion: Dictionary) -> void:
	var def: Dictionary = motion.def
	var amount := float(def.pay) * (1.0 + 0.02 * float(motion.hits)) if str(motion.kind) != "comet" else float(def.pay) * (1.0 + 0.03 * float(motion.hits))
	var reward: float = main._bdr_apply_multipliers(die, amount)
	main._add_money(reward)
	die.last_payout = reward
	die.last_payout_msec = _now()
	if main._can_show_reward_popup(true):
		main._show_reward(die.position, main._bdr_money_text(reward, true), true)


func moving_dice() -> Array:
	var result: Array = []
	for motion in _motions:
		result.append(motion.die)
	return result


# ---------------------------------------------------------------- periodic updates
func process(delta: float) -> void:
	st["viewers"] = maxf(0.0, float(st.get("viewers", 0.0)) * pow(0.99, delta))
	st["stonks_timer"] = float(st.get("stonks_timer", 45.0)) - delta
	if float(st.stonks_timer) <= 0.0:
		st["stonks_timer"] = 45.0
		var market: float = st.get("stonks", 1.0)
		if main.rng.randf() < 0.7:
			market *= main.rng.randf_range(1.05, 1.25)
		else:
			market *= main.rng.randf_range(0.85, 0.95)
		st["stonks"] = clampf(market, 0.5, 20.0)
		if float(st.stonks) >= 10.0:
			game.stat("stonks_high", 1)
	process_motions(delta)


func on_skull() -> void:
	st["skulls"] = int(st.get("skulls", 0)) + 1
