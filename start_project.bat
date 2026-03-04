@echo off
echo Starting ShopTalk-AI Backend...
start "ShopTalk-AI Backend" cmd /k "cd backend && call .venv\Scripts\activate && uvicorn app.main:app --reload"
echo Backend started in new window.
