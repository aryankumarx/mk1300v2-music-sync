@echo off
title Ant Esports MK1300 V2 - Music Album Sync
cd /d "%~dp0"

echo ========================================================
echo Starting Ant Esports MK1300 V2 Music Album Sync...
echo - Playing: Solid dominant album color
echo - Paused: Soft breathing mode (dims only ~30%%)
echo - Press 'R' inside this window to instant-refresh sync
echo - Press Ctrl+C anytime to stop and restore rainbow effect
echo ========================================================
python sync_music.py
pause
