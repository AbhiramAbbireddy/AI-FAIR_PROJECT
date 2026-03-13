@echo off
REM Quick restart of Streamlit app
echo Closing existing Streamlit sessions...
taskkill /F /IM streamlit.exe 2>nul
timeout /t 2

echo.
echo Starting Streamlit with fresh environment...
python run_streamlit.py

pause
