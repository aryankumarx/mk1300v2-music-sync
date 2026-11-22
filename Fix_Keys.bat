@echo off
title Ant Esports MK1300 V2 Keymap Repair
color 0A
cd /d "%~dp0"

echo =======================================================
echo     Ant Esports MK1300 V2 - One-Click Key Repair
echo =======================================================
echo.
echo Running keymap restoration...
python restore_full_keymap.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo =======================================================
    echo  SUCCESS! All keys and RGB lighting have been restored.
    echo =======================================================
) else (
    echo =======================================================
    echo  FAILED! Make sure keyboard is plugged in and try again.
    echo =======================================================
)
echo.
pause
