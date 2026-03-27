@echo off
setlocal EnableExtensions

set "ROOT_DIR=%~dp0"
pushd "%ROOT_DIR%"

echo ==========================================
echo Duty Reminder - one click setup/build/start
echo ==========================================

echo [1/7] Check uv...
set "UV_EXE="
where uv >nul 2>nul
if not errorlevel 1 set "UV_EXE=uv"

if "%UV_EXE%"=="" (
  echo uv not found, installing...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 ^| iex"
  if errorlevel 1 (
    echo uv install failed. Please install manually: https://docs.astral.sh/uv/
    popd
    exit /b 1
  )
)

if "%UV_EXE%"=="" if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV_EXE=%USERPROFILE%\.local\bin\uv.exe"
if "%UV_EXE%"=="" if exist "%USERPROFILE%\AppData\Local\Programs\uv\uv.exe" set "UV_EXE=%USERPROFILE%\AppData\Local\Programs\uv\uv.exe"
if "%UV_EXE%"=="" (
  where uv >nul 2>nul
  if not errorlevel 1 set "UV_EXE=uv"
)

if "%UV_EXE%"=="" (
  echo uv.exe still not found. Re-open terminal and run again.
  popd
  exit /b 1
)

echo [2/7] Create/update backend virtualenv (auto-install Python 3.11 via uv)...
set "UV_PYTHON_PREFERENCE=only-managed"
set "UV_PYTHON_DOWNLOADS=automatic"
"%UV_EXE%" venv --python 3.11 --clear "code\backend\.venv"
if errorlevel 1 (
  echo Failed to create virtualenv - or install managed Python.
  popd
  exit /b 1
)

echo [3/7] Install backend dependencies from requirements.txt...
"%UV_EXE%" pip install --python "code\backend\.venv\Scripts\python.exe" -r "code\backend\requirements.txt"
if errorlevel 1 (
  echo Failed to install backend dependencies from requirements.txt.
  popd
  exit /b 1
)

echo [4/7] Prepare backend environment file...
if not exist "code\backend\.env" (
  copy /Y "code\backend\.env.example" "code\backend\.env" >nul
  echo Created code\backend\.env
) else (
  echo code\backend\.env already exists, skip.
)

echo [5/7] Install frontend dependencies (skip if already installed)...
cd /d "%ROOT_DIR%code\frontend"
if not exist node_modules (
  if exist package-lock.json (
    call npm ci
  ) else (
    call npm install
  )
  if errorlevel 1 (
    echo Failed to install frontend dependencies.
    popd
    exit /b 1
  )
) else (
  echo node_modules exists, skip npm install.
)

echo [6/7] Build frontend (set FORCE_FRONTEND_BUILD=1 to rebuild)...
if "%FORCE_FRONTEND_BUILD%"=="1" (
  call npm run build
  if errorlevel 1 (
    echo Frontend build failed.
    popd
    exit /b 1
  )
) else (
  if not exist dist\index.html (
    call npm run build
    if errorlevel 1 (
      echo Frontend build failed.
      popd
      exit /b 1
    )
  ) else (
    echo dist already exists, skip frontend build.
  )
)

echo [7/7] Start backend service...
cd /d "%ROOT_DIR%code\backend"
start "Duty Reminder API" cmd /k ""%ROOT_DIR%code\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 2 >nul
start "" "http://127.0.0.1:8000"

echo.
echo Done: setup + build + start.
echo URL: http://127.0.0.1:8000
echo.
echo Tip: edit code\backend\.env for mail settings.

popd
exit /b 0
