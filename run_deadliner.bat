@echo off
title Deadliner - Academic Hub
set PYTHONPATH=%~dp0src
python -m deadliner
if errorlevel 1 pause
