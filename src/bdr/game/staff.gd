extends RefCounted
## Dice Rush Extended - 10 new staff types. They are hired in the shop like workers and accountants
## (growing price, limit) and each one has its own job on the table.

const I18N := preload("res://bdr/core/i18n.gd")
const NumFmt := preload("res://bdr/core/numfmt.gd")

const ORDER := ["staff_mechanic", "staff_janitor", "staff_chef", "staff_banker", "staff_merchant",
	"staff_mage", "staff_scientist", "staff_dj", "staff_miner", "staff_monk"]
## First hiring price of each staff type (later hires cost GROWTH times more each).
## Balance (v1.0): the prices follow the dice tiers, so the strong staff arrives late.
const BASE_PRICE := {"staff_mechanic": 5.0e4, "staff_janitor": 5.0e6, "staff_chef": 5.0e9, "staff_banker": 5.0e11,
	"staff_merchant": 5.0e13, "staff_mage": 5.0e16, "staff_scientist": 5.0e19, "staff_dj": 5.0e22,
	"staff_miner": 5.0e25, "staff_monk": 5.0e28}
const GROWTH := 1.6
const BASE_LIMIT := 10
const ART := "res://bdr/art/staff/"

# job intervals in seconds for ONE staff member (more members = shorter interval)
const MECHANIC_INTERVAL := 5.0
const JANITOR_INTERVAL := 6.0
const MAGE_INTERVAL := 30.0
const MAGE_MIN_INTERVAL := 3.0
const SCIENTIST_INTERVAL := 600.0
const DJ_INTERVAL := 120.0
const DJ_MIN_INTERVAL := 20.0
const DJ_DROP_SECONDS := 6.0
const MINER_INTERVAL := 20.0

var game: Node
var main: Node
var rng := RandomNumberGenerator.new()
var _timers: Dictionary = {}
var _dj_drop_left := 0.0
var _tmp: Array = []


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	rng.randomize()


func has(kind: String) -> bool:
	return BASE_PRICE.has(kind)


func count(kind: String) -> int:
	return game.count(kind)


func limit(_kind: String) -> int:
	var result := BASE_LIMIT
	if main._is_talent_owned("bdr_staff_limit_1"):
		result += 10
	if main._is_talent_owned("bdr_staff_limit_2"):
		result += 15
	return result


func price(kind: String, owned: int) -> float:
	return minf(1.0e300, float(BASE_PRICE.get(kind, 1.0e9)) * pow(GROWTH, float(maxi(0, owned))))


## Staff types show up in the shop once the player has earned a quarter of their first price.
func is_available(kind: String) -> bool:
	if not has(kind):
		return false
	return count(kind) > 0 or float(main.total_money_earned) >= float(BASE_PRICE[kind]) * 0.25


func name_of(kind: String) -> String:
	return I18N.t("staff.%s.name" % kind.trim_prefix("staff_"))


func icon_path(kind: String) -> String:
	return ART + kind.trim_prefix("staff_") + ".png"


func buy(kind: String) -> void:
	if not is_available(kind):
		GameSession.play_sfx("denied")
		return
	if game.is_coop_client():
		game.coop_request("buy", [kind])
		return
	var owned := count(kind)
	if owned >= limit(kind):
		main._flash_label(main.price_labels.get(kind))
		GameSession.play_sfx("denied")
		return
	var cost: float = main._next_price(kind, owned)
	if not main._spend_money(cost, main.price_labels.get(kind)):
		return
	game.set_count(kind, owned + 1)
	game.stat("staff_hired", 1)
	game.stat("hired_" + kind, 1)
	main._invalidate_eco()
	main._update_all_labels()


func total_staff() -> int:
	var total := 0
	for kind in ORDER:
		total += count(kind)
	return total


func kinds_hired() -> int:
	var total := 0
	for kind in ORDER:
		if count(kind) > 0:
			total += 1
	return total


# ---------------------------------------------------------------- passive effects
func global_multiplier() -> float:
	var multiplier := 1.0 + 0.03 * float(count("staff_banker"))
	if _dj_drop_left > 0.0:
		multiplier *= 2.0
	return multiplier


func family_percent(family: String) -> float:
	if family == "food" or family == "animal":
		return 10.0 * float(count("staff_chef"))
	return 0.0


func sell_bonus() -> float:
	return 0.03 * float(count("staff_merchant"))


func price_discount() -> float:
	return minf(0.15, 0.01 * float(count("staff_merchant")))


func offering_bonus() -> float:
	return 0.08 * float(count("staff_monk"))


func dj_active() -> bool:
	return _dj_drop_left > 0.0


func dj_left() -> float:
	return _dj_drop_left


## Coop client: the beat drop of the host's DJs (for the HUD and the multiplier display).
func coop_set_dj(seconds: float) -> void:
	_dj_drop_left = maxf(0.0, seconds)


# ---------------------------------------------------------------- jobs
func process(delta: float) -> void:
	if _dj_drop_left > 0.0:
		_dj_drop_left = maxf(0.0, _dj_drop_left - delta)
		if _dj_drop_left <= 0.0:
			game.invalidate_global_multiplier()
	if total_staff() <= 0:
		return
	_tick("staff_mechanic", MECHANIC_INTERVAL, delta, _job_mechanic)
	_tick("staff_janitor", JANITOR_INTERVAL, delta, _job_janitor)
	_tick("staff_mage", maxf(MAGE_MIN_INTERVAL * count("staff_mage"), MAGE_INTERVAL), delta, _job_mage)
	_tick("staff_scientist", SCIENTIST_INTERVAL, delta, _job_scientist)
	_tick("staff_miner", MINER_INTERVAL, delta, _job_miner)
	var djs := count("staff_dj")
	if djs > 0:
		_tick("staff_dj", maxf(DJ_MIN_INTERVAL * djs, DJ_INTERVAL), delta, _job_dj)


## Runs a job every (interval / members) seconds.
func _tick(kind: String, interval: float, delta: float, job: Callable) -> void:
	var members := count(kind)
	if members <= 0:
		return
	var left := float(_timers.get(kind, interval / float(members))) - delta
	if left <= 0.0:
		job.call()
		left = interval / float(members)
	_timers[kind] = left


func _idle_die(filter: Callable = Callable()) -> DiceActor:
	_tmp.clear()
	main._grid.random_dice(1, rng, _tmp, func(die) -> bool: return is_instance_valid(die) and not die.rolling and die.reserved_by == 0 and (not filter.is_valid() or filter.call(die)))
	return _tmp[0] if not _tmp.is_empty() else null


func _show_worker(kind: String, at: Vector2) -> void:
	game.fx_staff(icon_path(kind), at)


func _job_mechanic() -> void:
	var die := _idle_die(func(d) -> bool: return game.is_custom_die(d.die_kind))
	if die == null:
		die = _idle_die()
	if die == null:
		return
	_show_worker("staff_mechanic", die.position)
	main._start_die_roll(die, 0, Vector2(-1.0, -1.0), false, true)


func _job_janitor() -> void:
	_tmp.clear()
	main._grid.random_dice(3, rng, _tmp, func(die) -> bool: return is_instance_valid(die) and not die.rolling and die.reserved_by == 0 and die.last_payout_msec > 0 and die.last_payout <= 0.0)
	if _tmp.is_empty():
		return
	var picked: Array = _tmp.duplicate()
	_show_worker("staff_janitor", (picked[0] as DiceActor).position)
	for die in picked:
		main._start_die_roll(die, 0, Vector2(-1.0, -1.0), false, true)


func _job_mage() -> void:
	var die := _idle_die()
	if die == null:
		return
	die.pending_mult *= 10.0
	_show_worker("staff_mage", die.position)
	game.fx_ring(die.position, 70.0, Color("b45aff"))
	game.mech._popup(die, "fx.magic", {"n": 10})
	main._start_die_roll(die, 0, Vector2(-1.0, -1.0), false, true)


func _job_scientist() -> void:
	var kind: String = game.random_owned_level_kind()
	if kind.is_empty():
		return
	main.die_levels[kind] = main._die_level(kind) + 1
	main._invalidate_eco()
	game.stat("staff_levels", 1)
	game.toast(I18N.f("staff.scientist_level", {"name": main._lucky_kind_name(kind), "n": main._die_level(kind)}))


func _job_miner() -> void:
	var rate: float = game.income_rate()
	if rate <= 0.0:
		return
	# every miner digs up 1 second of income every MINER_INTERVAL seconds (the job runs once per
	# interval / miners, so the amount per job does not grow with the number of miners)
	var amount := rate * 1.0
	var safe: Rect2 = game.board_safe_rect()
	var at := Vector2(rng.randf_range(safe.position.x, safe.end.x), rng.randf_range(safe.position.y, safe.end.y))
	_show_worker("staff_miner", at)
	game.pay_bonus(amount, at)


func _job_dj() -> void:
	_dj_drop_left = DJ_DROP_SECONDS
	game.invalidate_global_multiplier()
	game.stat("staff_beat_drops", 1)
	game.toast(I18N.f("staff.dj_drop", {"s": int(DJ_DROP_SECONDS)}))
	var safe: Rect2 = game.board_safe_rect()
	_show_worker("staff_dj", safe.get_center())
	game.fx_ring(safe.get_center(), 380.0, Color("ff4fd8"))


# ---------------------------------------------------------------- texts
func tooltip(kind: String) -> String:
	var owned := count(kind)
	var cap := limit(kind)
	var lines: Array[String] = []
	lines.append("[color=#ffd166][font_size=18]%s[/font_size][/color]" % name_of(kind))
	lines.append("")
	lines.append(I18N.t("staff.%s.desc" % kind.trim_prefix("staff_")))
	lines.append("")
	lines.append(I18N.f("staff.hired", {"n": owned, "max": cap}))
	if owned < cap:
		lines.append(I18N.f("staff.next_price", {"v": main._bdr_money_text(main._next_price(kind, owned), false)}))
	else:
		lines.append(I18N.t("staff.full"))
	return "\n".join(lines)
