const RARITY_COMMON: = "common"


const RARITY_RARE: = "rare"


const RARITY_EPIC: = "epic"


const RARITY_LEGENDARY: = "legendary"


const RARITY_ORDER: = ["common", "rare", "epic", "legendary"]


## Dice Rush Extended: the 40 minor arcana (2-5 common, 6-9 rare, ace and 10 epic).
const COMMON_IDS: Array[String] = [
	"m_wands_2", "m_wands_3", "m_wands_4", "m_wands_5",
	"m_cups_2", "m_cups_3", "m_cups_4", "m_cups_5",
	"m_swords_2", "m_swords_3", "m_swords_4", "m_swords_5",
	"m_pentacles_2", "m_pentacles_3", "m_pentacles_4", "m_pentacles_5",
]


const RARE_IDS: Array[String] = [
	"m_wands_6", "m_wands_7", "m_wands_8", "m_wands_9",
	"m_cups_6", "m_cups_7", "m_cups_8", "m_cups_9",
	"m_swords_6", "m_swords_7", "m_swords_8", "m_swords_9",
	"m_pentacles_6", "m_pentacles_7", "m_pentacles_8", "m_pentacles_9",
]


const EPIC_IDS: Array[String] = [
	"m_wands_1", "m_wands_10", "m_cups_1", "m_cups_10",
	"m_swords_1", "m_swords_10", "m_pentacles_1", "m_pentacles_10",
]


const MINOR_IDS: Array[String] = [
	"m_wands_1", "m_wands_2", "m_wands_3", "m_wands_4", "m_wands_5", "m_wands_6", "m_wands_7", "m_wands_8", "m_wands_9", "m_wands_10",
	"m_cups_1", "m_cups_2", "m_cups_3", "m_cups_4", "m_cups_5", "m_cups_6", "m_cups_7", "m_cups_8", "m_cups_9", "m_cups_10",
	"m_swords_1", "m_swords_2", "m_swords_3", "m_swords_4", "m_swords_5", "m_swords_6", "m_swords_7", "m_swords_8", "m_swords_9", "m_swords_10",
	"m_pentacles_1", "m_pentacles_2", "m_pentacles_3", "m_pentacles_4", "m_pentacles_5", "m_pentacles_6", "m_pentacles_7", "m_pentacles_8", "m_pentacles_9", "m_pentacles_10",
]


const ALL_IDS: = [
	"l_fool", "l_magician", "l_high_priestess", "l_empress", "l_emperor", "l_hierophant", "l_lovers",
	"l_chariot", "l_strength", "l_hermit", "l_wheel_of_fortune", "l_justice", "l_hanged_man", "l_death",
	"l_temperance", "l_devil", "l_tower", "l_star", "l_moon", "l_sun", "l_judgement",
	"m_wands_1", "m_wands_2", "m_wands_3", "m_wands_4", "m_wands_5", "m_wands_6", "m_wands_7", "m_wands_8", "m_wands_9", "m_wands_10",
	"m_cups_1", "m_cups_2", "m_cups_3", "m_cups_4", "m_cups_5", "m_cups_6", "m_cups_7", "m_cups_8", "m_cups_9", "m_cups_10",
	"m_swords_1", "m_swords_2", "m_swords_3", "m_swords_4", "m_swords_5", "m_swords_6", "m_swords_7", "m_swords_8", "m_swords_9", "m_swords_10",
	"m_pentacles_1", "m_pentacles_2", "m_pentacles_3", "m_pentacles_4", "m_pentacles_5", "m_pentacles_6", "m_pentacles_7", "m_pentacles_8", "m_pentacles_9", "m_pentacles_10",
]


const TAROT_ORDER: = ALL_IDS


const CANONICAL_IDS: = ALL_IDS


const BDR_ART_ROOT: = "res://bdr/art/tarot/"


static func rarity(card_id: String) -> String:
	if card_id in LEGENDARY_IDS:
		return RARITY_LEGENDARY
	if card_id in EPIC_IDS:
		return RARITY_EPIC
	if card_id in RARE_IDS:
		return RARITY_RARE
	if card_id in COMMON_IDS:
		return RARITY_COMMON
	return ""


static func ids_for_rarity(rarity_id: String) -> Array:
	match rarity_id:
		RARITY_LEGENDARY:
			return LEGENDARY_IDS
		RARITY_EPIC:
			return EPIC_IDS
		RARITY_RARE:
			return RARE_IDS
		RARITY_COMMON:
			return COMMON_IDS
	return []


static func art_path(card_id: String) -> String:
	if card_id.begins_with("m_"):
		return BDR_ART_ROOT + card_id + ".png"
	var file_name: = str(ART_FILE_BY_ID.get(card_id, ""))
	return ART_ROOT + file_name if not file_name.is_empty() else CARD_BACK_PATH
