@echo off
title NexusNotice AI - Smart Notice Management & Recommendation System
echo ======================================================================
echo    AI-POWERED SMART NOTICE MANAGEMENT & RECOMMENDATION SYSTEM
echo ======================================================================
echo.
echo Initializing server with PaddleOCR, Sentence Transformers, FAISS, Gemini & Claude...
echo.

set PYDANTIC_DISABLE_PLUGINS=1

if exist "..\.venv\Scripts\python.exe" (
    ..\.venv\Scripts\python.exe run.py
) else if exist ".\.venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe run.py
) else (
    python run.py
)

pause
