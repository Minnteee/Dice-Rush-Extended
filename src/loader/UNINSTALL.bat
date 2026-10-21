@echo off
rem Dice Rush Extended - removes the mod from this game folder (your saves stay untouched).
cd /d "%~dp0"
if exist "override.cfg" del /q "override.cfg"
if exist "DiceRushExtended" rmdir /s /q "DiceRushExtended"
if exist "BetherDiceRush" rmdir /s /q "BetherDiceRush"
echo Dice Rush Extended was removed. Your saves are untouched.
pause
(goto) 2>nul & del "%~f0"
