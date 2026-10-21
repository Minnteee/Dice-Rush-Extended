# Dice Rush Extended - main.gd patch: big-number economy.
# The original game stores money in a 64-bit integer (max ~9.2 quintillion). With 100 new dice
# that limit is reached quickly, so money, prices and payouts use 64-bit floats now
# (practically unlimited, shown as K M B T q Q s S O N d, then aa, ab ... - never "e").

const BDR_MONEY_CAP: = 1.0e300
const BDRNumFmt: = preload("res://bdr/core/numfmt.gd")
const BDR_SUFFIXES: = [[33, "d"], [30, "N"], [27, "O"], [24, "S"], [21, "s"], [18, "Q"], [15, "q"], [12, "T"], [9, "B"], [6, "M"], [3, "K"]]

var money: float = 0.0
var total_money_earned: float = 0.0
var next_golden_coin: float = 100.0
var golden_bone_storm_bank_snapshot: float = 0.0
var _lucky_price_memo: = PackedFloat64Array([1000.0])
var _accountant_price_memo: = PackedFloat64Array([1000.0])


func _format_number(value: Variant) -> String:
	return BDRNumFmt.compact(value)


func _bdr_money_text(value: Variant, show_plus: bool = false) -> String:
	return "%s%s%s" % ["+" if show_plus else "", _format_number(value), GameSession.currency_symbol()]


## Saves values below 9e18 as plain integers (compatible with the original game).
func _bdr_money_to_save(value: float) -> String:
	if value < 9.0e18:
		return str(int(maxf(0.0, value)))
	var exponent: = int(floor(log(value) / log(10.0)))
	var mantissa: = value / pow(10.0, exponent)
	return "%.15fe%d" % [mantissa, exponent]


func _bdr_parse_money(value: Variant) -> float:
	if value is int or value is float:
		return maxf(0.0, float(value))
	var text: = str(value).strip_edges()
	if text.is_empty():
		return 0.0
	return maxf(0.0, text.to_float())


func _bdr_int_stat(value: float) -> int:
	return int(minf(maxf(value, 0.0), 9.0e18))


func _add_money(amount: float) -> void :
	if amount > 0.0:
		var money_before: = money
		money = minf(BDR_MONEY_CAP, money + amount)
		total_money_earned = minf(BDR_MONEY_CAP, total_money_earned + amount)
		var guard: = 0
		while total_money_earned >= next_golden_coin and guard < 4096:
			golden_coins += 1
			_fs_gold_earned += 1
			next_golden_coin = _next_talent_gold_threshold(next_golden_coin)
			guard += 1
		_fs_income_dirty = true
		if money_before < QUADRILLION_STORY_THRESHOLD and money >= QUADRILLION_STORY_THRESHOLD:
			_show_quadrillion_story.call_deferred()
	_request_all_labels_update()


func _next_talent_gold_threshold(current: float) -> float:
	if current <= 0.0:
		return 100.0
	# Dice Rush Extended: after the original range the steps get smaller, so the bigger
	# talent tree stays reachable with the new high tier dice.
	if current >= 1.0e12:
		return ceilf(current * 1.3)
	return current + ceilf(current / 2.0)


func _spend_money(amount: float, label: Label) -> bool:
	if money < amount or amount < 0.0:
		_flash_label(label)
		GameSession.play_sfx("denied")
		return false
	money -= amount
	GameSession.play_sfx("purchase")
	return true


func _percentage_bonus_amount(value: float, percent: int) -> float:
	if value <= 0.0 or percent <= 0:
		return 0.0
	return value * float(percent) / 100.0


func _apply_dog_effect_multiplier(value: float, multiplier: float) -> float:
	if value <= 0.0 or multiplier <= 0.0:
		return 0.0
	return minf(BDR_MONEY_CAP, value * multiplier)


func _apply_accountant_bonus(value: float) -> float:
	if value <= 0.0 or accountant_count <= 0:
		return value
	return value * (1.0 + float(_accountant_total_bonus_percent()) / 100.0)


func _apply_achievement_income_bonus(amount: float) -> float:
	var percent: = _achievement_income_percent()
	if amount <= 0.0 or percent <= 0:
		return amount
	return amount * (1.0 + float(percent) / 100.0)


# ---------------------------------------------------------------- prices
func _grown_worker_price(previous_price: float) -> float:
	if previous_price < 1.0:
		return previous_price + 1.0
	return maxf(previous_price + 1.0, ceilf(previous_price * 1.55))


func _grown_dice_price(previous_price: float, purchase_number: int) -> float:
	if previous_price < 1.0:
		return previous_price + 1.0
	var numerator: = 115.0
	if purchase_number >= 41:
		numerator = 300.0
	elif purchase_number >= 31:
		numerator = 200.0
	elif purchase_number >= 21:
		numerator = 160.0
	elif purchase_number >= 11:
		numerator = 130.0
	return minf(BDR_MONEY_CAP, maxf(previous_price + 1.0, ceilf(previous_price * numerator / 100.0)))


func _grown_basic_donation_price(previous_price: float, purchase_number: int) -> float:
	if previous_price < 1.0:
		return previous_price + 1.0
	var numerator: = 115.0
	if purchase_number >= 41:
		numerator = 102.0
	elif purchase_number >= 31:
		numerator = 110.0
	elif purchase_number >= 21:
		numerator = 120.0
	elif purchase_number >= 11:
		numerator = 130.0
	return minf(BDR_MONEY_CAP, maxf(previous_price + 1.0, ceilf(previous_price * numerator / 100.0)))


func _grown_dice_price_from_base(base_price: float, owned_count: int) -> float:
	var price: = maxf(1.0, base_price)
	for owned_index in range(maxi(0, owned_count)):
		price = _grown_dice_price(price, owned_index + 2)
		if price >= BDR_MONEY_CAP:
			return BDR_MONEY_CAP
	return price


func _next_price(kind: String, count: int) -> float:
	if count < 0:
		return -1.0
	match kind:
		"cat":
			return float(_cat_price())
		"crypto":
			return _bdr_discount(kind, _grown_dice_price_from_base(float(crypto_market_value), count))
		"accountant":
			return _accountant_price_after(count)
	var custom: float = bdr.custom_next_price(kind, count)
	if custom != -2.0:
		return _bdr_discount(kind, custom)
	var memo = _price_memo.get(kind)
	if memo == null:
		memo = PackedFloat64Array()
		_price_memo[kind] = memo
	if count < memo.size():
		return _bdr_discount(kind, float(memo[count]))
	var prices: Array = []
	match kind:
		"50_50": prices = DICE50_PRICES
		"d4": prices = D4_PRICES
		"npc": prices = NPC_PRICES
		"npc_die": prices = NPC_DIE_PRICES
		"3x4": prices = DICE_3X4_PRICES
		"d2": prices = DICE_D2_PRICES
		"777": prices = DICE_777_PRICES
		"prehistoric": prices = PREHISTORIC_PRICES
		"golden": prices = GOLDEN_PRICES
		"diamond": prices = DIAMOND_PRICES
		"pi": prices = PI_PRICES
	if prices.is_empty():
		return -1.0
	var previous_price: float = float(memo[memo.size() - 1]) if memo.size() > 0 else -1.0
	var price_index: int = memo.size()
	while price_index <= count:
		var candidate: = float(prices[price_index]) if price_index < prices.size() else -1.0
		if candidate < 0.0 or (previous_price >= 0.0 and candidate <= previous_price):
			if kind == "npc":
				candidate = _grown_worker_price(previous_price)
			elif not _edition_demo and kind in BASIC_DONATION_DICE_KINDS:
				candidate = _grown_basic_donation_price(previous_price, price_index + 1)
			else:
				candidate = _grown_dice_price(previous_price, price_index + 1)
		previous_price = minf(candidate, BDR_MONEY_CAP)
		memo.append(previous_price)
		price_index += 1
	_price_memo[kind] = memo
	return _bdr_discount(kind, float(memo[count]))


func _bdr_discount(kind: String, price: float) -> float:
	if price <= 0.0:
		return price
	var factor: float = bdr.price_factor(kind)
	if factor == 1.0:
		return price
	return maxf(1.0, ceilf(price * factor))


func _accountant_price_after(previous_purchases: int) -> float:
	var target: = maxi(0, previous_purchases)
	while _accountant_price_memo.size() <= target:
		var last: float = _accountant_price_memo[_accountant_price_memo.size() - 1]
		_accountant_price_memo.append(minf(BDR_MONEY_CAP, ceilf(last * float(100 + ACCOUNTANT_PRICE_GROWTH_PERCENT) / 100.0)))
	return _accountant_price_memo[target]


# ---------------------------------------------------------------- lucky cube prices
func _grow_lucky_cube_price(price: float) -> float:
	return minf(BDR_MONEY_CAP, ceilf(price * float(LUCKY_PRICE_GROWTH_NUMERATOR) / float(LUCKY_PRICE_GROWTH_DENOMINATOR)))


func _lucky_cube_price_after(previous_purchases: int) -> float:
	var target: = maxi(0, previous_purchases)
	while _lucky_price_memo.size() <= target:
		_lucky_price_memo.append(_grow_lucky_cube_price(_lucky_price_memo[_lucky_price_memo.size() - 1]))
	return _lucky_price_memo[target]


func _lucky_purchase_cost(purchase_count: int) -> float:
	if purchase_count <= 0:
		return 0.0
	var total: = 0.0
	for index in range(purchase_count):
		total += _discount_lucky_price(_lucky_cube_price_after(lucky_cubes_purchased + index))
		if total >= BDR_MONEY_CAP:
			return BDR_MONEY_CAP
	return total


func _discount_lucky_price(base_price: float) -> float:
	var power: = _dog_card_effect_power("l_wheel_of_fortune")
	var divisor: = (1.0 + 0.25 * power) if power > 0.0 else 1.0
	divisor *= bdr.lucky_price_divisor()
	return maxf(1.0, ceilf(base_price / divisor))


func _max_affordable_lucky_cubes(available_money: float) -> int:
	var count: = 0
	var remaining: = maxf(0.0, available_money)
	while count < 1000000:
		var charged_price: = _discount_lucky_price(_lucky_cube_price_after(lucky_cubes_purchased + count))
		if charged_price > remaining or charged_price >= BDR_MONEY_CAP:
			break
		remaining -= charged_price
		count += 1
	return count


func _selected_lucky_purchase_cost() -> float:
	return _lucky_purchase_cost(_selected_lucky_purchase_count())


func _collect_golden_bone_storm_cube(button: TextureButton, percent: int) -> void :
	if not is_instance_valid(button) or button.disabled or golden_bone_storm_time_left <= 0.0:
		return
	button.disabled = true
	var bank: = maxf(0.0, golden_bone_storm_bank_snapshot)
	var reward: = _apply_achievement_income_bonus(maxf(1.0, floorf(bank * float(percent) / 100.0)))
	reward *= bdr.event_reward_multiplier()
	_add_money(reward)
	golden_bone_storm_collected_this_event += 1
	AchievementService.increment_stat("golden_storm_cubes_clicked")
	AchievementService.report_stat("golden_storm_best", golden_bone_storm_collected_this_event)
	_play_payout_sound()
	_show_reward(button.position + button.size * 0.5, "%s  (%d%%)" % [_bdr_money_text(reward, true), percent], true)
	_coop_storm_hit(button)
	golden_bone_storm_buttons.erase(button)
	button.queue_free()
