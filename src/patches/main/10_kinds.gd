# Dice Rush Extended - main.gd patch: the new dice kinds behave like the original ones
# (counts, prices, names, shop cards, tooltips, saving).

var _suppress_label_updates: = false
var _labels_dirty_while_suppressed: = false


func _product_count(kind: String) -> int:
	match kind:
		"cat": return cat_count
		"50_50": return dice_50_count
		"d4": return dice_d4_count
		"npc": return npc_count
		"accountant": return accountant_count
	if kind in SPECIAL_DICE_KINDS:
		return int(special_dice_counts.get(kind, 0))
	if bdr.is_custom(kind):
		return bdr.count(kind)
	return int(extra_counts.get(kind, 0))


func _owned_die_count(kind: String) -> int:
	match kind:
		"cat": return cat_count
		"50_50": return dice_50_count
		"d4": return dice_d4_count
		"crypto", "diamond", "pi": return int(special_dice_counts.get(kind, 0))
	if bdr.is_custom(kind):
		return bdr.count(kind)
	return int(extra_counts.get(kind, 0))


func _set_owned_die_count(kind: String, value: int) -> void :
	var sanitized: = maxi(0, value)
	match kind:
		"50_50": dice_50_count = maxi(1, sanitized)
		"d4": dice_d4_count = sanitized
		"crypto", "diamond", "pi": special_dice_counts[kind] = sanitized
		"cat": cat_count = sanitized
		_:
			if bdr.is_custom(kind):
				bdr.set_count(kind, sanitized)
			else:
				extra_counts[kind] = sanitized
	_invalidate_eco()


func _physical_dice_count() -> int:
	var result: = dice_50_count + dice_d4_count + cat_count
	for kind in extra_counts:
		result = _safe_add_int64(result, maxi(0, int(extra_counts.get(kind, 0))))
	for kind in SPECIAL_DICE_KINDS:
		result = _safe_add_int64(result, maxi(0, int(special_dice_counts.get(kind, 0))))
	return _safe_add_int64(result, bdr.total_custom_dice())


func _product_name(kind: String) -> String:
	match kind:
		"cat": return _cat_text("name")
		"50_50": return GameSession.text("die_50")
		"d4": return GameSession.text("die_d4")
		"npc": return GameSession.text("worker")
		"3x4": return GameSession.text("die_3x4")
		"d2": return GameSession.text("die_d2")
		"777": return GameSession.text("die_777")
		"prehistoric": return GameSession.text("prehistoric")
		"golden": return GameSession.text("golden")
		"npc_die": return GameSession.text("npc_die")
		"crypto": return _lucky_text("crypto_die")
		"diamond": return _lucky_text("diamond_die")
		"pi": return _lucky_text("pi_die")
		"accountant": return _lucky_text("accountant")
	if bdr.is_custom(kind):
		return bdr.display_name(kind)
	return kind


func _product_card_title(kind: String) -> String:
	match kind:
		"cat": return _cat_text("name")
		"50_50": return "50/50"
		"d4": return "D4"
		"npc": return GameSession.text("worker")
		"3x4": return "3×4=12"
		"d2": return "D²"
		"777": return "777"
		"prehistoric": return GameSession.text("card_prehistoric")
		"golden": return GameSession.text("card_golden")
		"npc_die": return GameSession.text("card_npc_die")
		"crypto": return _lucky_text("crypto_die")
		"diamond": return _lucky_text("diamond_die")
		"pi": return _lucky_text("pi_die")
		"accountant": return _lucky_text("accountant")
	if bdr.is_custom(kind):
		return bdr.card_title(kind)
	return kind


func _lucky_kind_icon_path(kind: String) -> String:
	match kind:
		"50_50": return ART + "магаизн 5050.png"
		"d4": return DICE_ART + "d4.png"
		"3x4": return DICE_ART + "three_by_four.png"
		"d2": return DICE_ART + "d_squared.png"
		"777": return DICE_ART + "dice_777.png"
		"prehistoric": return DICE_ART + "prehistoric.png"
		"golden": return DICE_ART + "golden.png"
		"npc_die": return DICE_ART + "npc_die.png"
		"crypto": return DICE_ART + "crypto.png"
		"diamond": return DICE_ART + "diamond.png"
		"pi": return DICE_ART + "pi.png"
		"accountant": return ART + "lucky_dice/accountant.png"
		"cat": return "res://assets/dice/cat/idle.png"
	if bdr.is_custom(kind):
		return bdr.icon_path(kind)
	return DICE_ART + "50_50.png"


func _lucky_kind_name(kind: String) -> String:
	match kind:
		"50_50": return GameSession.text("die_50")
		"d4": return GameSession.text("die_d4")
		"3x4": return GameSession.text("die_3x4")
		"d2": return GameSession.text("die_d2")
		"777": return GameSession.text("die_777")
		"prehistoric": return GameSession.text("prehistoric")
		"golden": return GameSession.text("golden")
		"npc_die": return GameSession.text("npc_die")
		"accountant": return _lucky_text("accountant")
		"crypto": return _lucky_text("crypto_die")
		"diamond": return _lucky_text("diamond_die")
		"pi": return _lucky_text("pi_die")
		"cat": return _cat_text("name")
	if bdr.is_custom(kind):
		return bdr.display_name(kind)
	return kind


func _dice_talent_icon_path(kind: String) -> String:
	match kind:
		"50_50": return ART + "магаизн 5050.png"
		"d4": return DICE_ART + "d4.png"
		"3x4": return DICE_ART + "three_by_four.png"
		"d2": return DICE_ART + "d_squared.png"
		"777": return DICE_ART + "dice_777.png"
		"prehistoric": return DICE_ART + "prehistoric.png"
		"npc_die": return DICE_ART + "npc_die.png"
		"crypto": return DICE_ART + "crypto.png"
		"diamond": return DICE_ART + "diamond.png"
		"pi": return DICE_ART + "pi.png"
	if bdr.is_custom(kind):
		return bdr.icon_path(kind)
	return ART + "скилз/ChatGPT Image 19 авг. 2026 г., 13_14_37.png"


func _npc_can_roll(kind: String) -> bool:
	if kind == "cat":
		return false
	if kind == "50_50":
		return true
	if kind == "golden":
		return false
	if kind in SPECIAL_DICE_KINDS:
		return int(special_dice_counts.get(kind, 0)) > 0
	if bdr.is_custom(kind):
		return bdr.npc_can_roll(kind)
	return bool(upgrades.get(kind, false))


func _price_progress_count(kind: String, owned_count: int = -1) -> int:
	var current_owned: = _owned_die_count(kind) if owned_count < 0 else maxi(0, owned_count)
	if not _is_offerable_kind(kind):
		return current_owned
	var donated: = maxi(0, int(dog_shrine_donated_counts.get(kind, 0)))
	var death_power: = _dog_card_effect_power("l_death")
	var counted_donations: = donated if death_power <= 0.0 else floori(float(donated) / (1.0 + death_power))
	if current_owned > MAX_INT64 - counted_donations:
		return MAX_INT64
	return current_owned + counted_donations


func _is_offerable_kind(kind: String) -> bool:
	return kind in DOG_SHRINE_DICE_KINDS or bdr.is_custom_die(kind)


func _visible_shop_card_order() -> Array[String]:
	var result: Array[String] = []
	for kind in bdr.shop_order():
		var container: = shop_card_containers.get(kind) as Control
		if is_instance_valid(container) and container.visible:
			result.append(kind)
	return result


## Creates the shop card of a new dice / staff type the first time it is needed.
func _ensure_custom_shop_card(kind: String) -> void:
	if shop_card_containers.has(kind) or not is_instance_valid(shop_list):
		return
	var card: = Control.new()
	card.size = SHOP_CARD_SIZE
	card.visible = false
	shop_list.add_child(card)
	special_shop_cards[kind] = card
	shop_card_containers[kind] = card
	var callback: Callable = _buy_custom_die.bind(kind) if bdr.is_custom_die(kind) else bdr.staff_buy_callable(kind)
	_make_shop_card(card, kind, _product_card_title(kind), Rect2(Vector2.ZERO, SHOP_CARD_SIZE), _lucky_kind_icon_path(kind), Color.WHITE, callback)
	card.position = _shop_card_grid_position(maxi(0, shop_visible_kinds.size()))
	_fit_all_ui_text.call_deferred()


func _buy_custom_die(kind: String) -> void :
	if not bdr.is_unlocked(kind):
		_flash_label(price_labels.get(kind))
		GameSession.play_sfx("denied")
		return
	if not _dice_table_has_capacity():
		_flash_label(price_labels.get(kind))
		GameSession.play_sfx("denied")
		return
	if bdr.is_coop_client():
		bdr.coop_request("buy", [kind])
		return
	var count: = bdr.count(kind)
	var price: float = _next_price(kind, _price_progress_count(kind, count))
	if price < 0.0:
		_flash_label(price_labels.get(kind))
		return
	if not _spend_money(price, price_labels.get(kind)):
		return
	bdr.set_count(kind, count + 1)
	_spawn_die(kind, _random_spawn_position())
	bdr.on_purchased(kind, 1)
	if not _suppress_label_updates:
		_report_achievement_snapshot()
	_update_all_labels()


func _buy_shop_product(kind: String, single_purchase: Callable, bulk_requested: bool = false) -> int:
	var bulk_allowed: = kind in SHIFT_BULK_DICE_KINDS or bdr.is_custom_die(kind)
	var requested_count: = SHIFT_DICE_BUY_COUNT if bulk_requested and bulk_allowed else 1
	var purchased: = 0
	for _purchase_index in range(requested_count):
		var count_before: = _product_count(kind)
		single_purchase.call()
		var count_after: = _product_count(kind)
		if count_after <= count_before:
			break
		purchased += count_after - count_before
	return purchased


## Applies the regular payout multipliers to a payout that does not come from a normal landing
## (e.g. the racing car hitting the wall).
func _bdr_apply_multipliers(die: DiceActor, amount: float) -> float:
	if amount <= 0.0:
		return 0.0
	var payout: = amount
	var eco: Array = _eco_kind(die.die_kind)
	var percent: int = eco[2]
	if percent > 0:
		payout *= 1.0 + float(percent) / 100.0
	var achievement_percent: = _achievement_income_percent()
	if achievement_percent > 0:
		payout *= 1.0 + float(achievement_percent) / 100.0
	var lucky_level: int = eco[3]
	if lucky_level > 1:
		payout *= float(lucky_level)
	if accountant_count > 0:
		payout = _apply_accountant_bonus(payout)
	if golden_bone_luck_time_left > 0.0:
		payout *= float(_golden_bone_luck_multiplier())
	payout *= float(eco[4]) * bdr.global_multiplier() * die.pending_mult
	die.pending_mult = 1.0
	return minf(payout, BDR_MONEY_CAP)


func _update_all_labels() -> void :
	if _suppress_label_updates:
		_labels_dirty_while_suppressed = true
		return
	_invalidate_eco()
	_refresh_cat_shop_ui()
	_refresh_accountant_ui()
	if money_value_label:
		money_value_label.text = _format_number(money)
		UITextFitterScript.fit(money_value_label)
	if money_symbol_label:
		money_symbol_label.text = GameSession.currency_symbol()
		UITextFitterScript.fit(money_symbol_label)
	var workers_limit: = _worker_limit()
	var dice_table_full: = not _dice_table_has_capacity()
	var demo_dice_limit: = DiceRushEdition.DEMO_MAX_DICE_PER_KIND if _edition_demo else -1
	_update_product_label("50_50", dice_50_count, demo_dice_limit, _next_price("50_50", _price_progress_count("50_50", dice_50_count)), dice_table_full)
	_update_product_label("d4", dice_d4_count, demo_dice_limit, _next_price("d4", _price_progress_count("d4", dice_d4_count)), dice_table_full)
	_update_product_label("npc", npc_count, workers_limit, _next_price("npc", npc_count) if npc_count < workers_limit else 0)
	for kind in extra_counts:
		var count: int = extra_counts[kind]
		if kind in ["golden", "npc_die"]:
			var talent_card: = special_shop_cards.get(kind) as Control
			if talent_card:
				talent_card.visible = _is_talent_owned(kind)
		var maximum: = _dice_limit(kind)
		_update_product_label(kind, count, maximum if maximum < MAX_INT64 else -1, _next_price(kind, _price_progress_count(kind, count)), dice_table_full)
	for kind in SPECIAL_DICE_KINDS:
		var card: = special_shop_cards.get(kind) as Control
		var unlocked: = bool(special_dice_unlocked.get(kind, false))
		if card:
			card.visible = unlocked
		if unlocked:
			var count: = int(special_dice_counts.get(kind, 0))
			_update_product_label(kind, count, demo_dice_limit, _next_price(kind, _price_progress_count(kind, count)), dice_table_full)
	for kind in bdr.shop_product_kinds():
		var visible_card: bool = bdr.is_unlocked(kind)
		if visible_card:
			_ensure_custom_shop_card(kind)
		var custom_card: = special_shop_cards.get(kind) as Control
		if custom_card:
			custom_card.visible = visible_card
		if visible_card:
			var custom_count: = _product_count(kind)
			var custom_limit: int = bdr.product_limit(kind)
			var custom_price: float = _next_price(kind, _price_progress_count(kind, custom_count)) if (custom_limit < 0 or custom_count < custom_limit) else 0.0
			_update_product_label(kind, custom_count, custom_limit, custom_price, dice_table_full and bdr.is_custom_die(kind))
	if is_instance_valid(dog_shrine_controller) and dog_shrine_controller.visible and not dog_shrine_entry_draining:
		dog_shrine_controller.set_inventory(_dog_shrine_inventory_items(), _dog_shrine_offerings_left(), false)
	if gold_label:
		gold_label.text = str(golden_coins)
		UITextFitterScript.fit(gold_label)
	if upgrade_overlay and upgrade_overlay.visible:
		if upgrade_page == "tree":
			for key in upgrades:
				_update_talent_node(key)
			for key in talents:
				_update_talent_node(key)
			_refresh_talent_focus_navigation()
		else:
			_refresh_lucky_ui()
	_refresh_shop_layout()
	bdr.on_labels_updated()


func _report_achievement_snapshot() -> void :
	var total_dice: = dice_50_count + dice_d4_count
	var dice_types: = 1 if dice_50_count > 0 else 0
	AchievementService.report_stat("own_d4", dice_d4_count)
	AchievementService.report_stat("workers", npc_count)
	AchievementService.report_stat("accountants", accountant_count)
	for kind in extra_counts:
		var count: = int(extra_counts[kind])
		total_dice += count
		if count > 0:
			dice_types += 1
		AchievementService.report_stat("own_%s" % kind, count)
	for kind in SPECIAL_DICE_KINDS:
		var count: = int(special_dice_counts.get(kind, 0))
		total_dice += count
		if count > 0:
			dice_types += 1
		# own_diamond / own_pi are not known to the original achievement file format.
		if kind == "crypto":
			AchievementService.report_stat("own_crypto", maxi(count, 1 if bool(special_dice_unlocked.get(kind, false)) else 0))
	total_dice += bdr.total_custom_dice()
	AchievementService.report_stat("dice_owned", total_dice)
	AchievementService.report_stat("dice_types", dice_types)
	var talent_count: = _balance_owned_talent_count()
	var achievement_talent_count: = 71 if _edition_full and talent_count >= _balance_total_talent_count() else talent_count
	AchievementService.report_stat("talents", mini(achievement_talent_count, 71))
	AchievementService.report_stat("income", _bdr_int_stat(total_money_earned))
	var historical_gold: = 0
	var threshold: = 100.0
	while threshold < next_golden_coin and historical_gold < 100000:
		historical_gold += 1
		threshold = _next_talent_gold_threshold(threshold)
	AchievementService.report_stat("gold_earned", historical_gold)
	if _edition_full:
		var tarot_cards_discovered: = 0
		var tarot_major_arcana_discovered: = 0
		for card_value in DogShrineCards.LEGENDARY_IDS:
			var card_id: = str(card_value)
			if _dog_card_rank(card_id) <= 0:
				continue
			tarot_cards_discovered += 1
			tarot_major_arcana_discovered += 1
		AchievementService.report_stat("dog_shrine_offerings", _dog_shrine_offerings_used())
		AchievementService.report_stat("tarot_cards_discovered", tarot_cards_discovered)
		AchievementService.report_stat("tarot_major_arcana_discovered", tarot_major_arcana_discovered)
	bdr.report_snapshot()


func _balance_owned_talent_count() -> int:
	var result: = 0
	for key in _talent_tree_order():
		if _is_talent_owned(key) and not str(key).begins_with("bdr_"):
			result += 1
	return result


func _balance_total_talent_count() -> int:
	var result: = 0
	for key in _talent_tree_order():
		if not str(key).begins_with("bdr_"):
			result += 1
	return result


func _start_fresh_game(save_immediately: bool) -> void :
	get_tree().paused = false
	_reset_progress_state()
	trailer_first_die = _spawn_die("50_50", Vector2(396, 503))
	game_started = true
	menu_controller.show_game()
	autosave_timer.start()
	bdr.on_new_game()
	_update_all_labels()
	_report_achievement_snapshot()
	if save_immediately:
		_save_game()
