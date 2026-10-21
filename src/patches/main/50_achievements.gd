## The Judgement card bonus also counts the Dice Rush Extended achievements.
func _achievement_income_percent() -> int:
	var power: = _achievement_income_power()
	if power <= 0.0:
		return 0
	return roundi(float(AchievementService.unlocked_count() + bdr.achievements.unlocked_count()) * power)
