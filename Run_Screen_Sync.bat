@echo off
title Ant Esports MK1300 V2 - Screen Ambient Sync
cd /d "%~dp0"
echo ========================================================
echo Starting Ant Esports MK1300 V2 Screen Ambient Sync...
echo Syncing RGB with your current screen display!
echo Press Ctrl+C anytime to stop and restore rainbow effect.
echo ========================================================
python sync_music.py --screen
pause

