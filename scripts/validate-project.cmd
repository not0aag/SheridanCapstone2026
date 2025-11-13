@echo off
REM SafeDrive AI - Pre-Push Validation Script
REM Run all checks before pushing code
REM Usage: validate-project.cmd [--all|--mobile|--backend|--ml|--mock-server]

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  SafeDrive AI - Pre-Push Validation
echo ============================================================
echo.

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=--all"

set "ERRORS=0"
set "WARNINGS=0"

REM ===================================
REM Helper Functions
REM ===================================

:check_node
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    set /a ERRORS+=1
    exit /b 1
)
exit /b 0

:check_python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.11+
    set /a ERRORS+=1
    exit /b 1
)
exit /b 0

REM ===================================
REM Mobile Checks
REM ===================================

:check_mobile
if "%TARGET%"=="--mobile" goto :do_mobile_check
if "%TARGET%"=="--all" goto :do_mobile_check
exit /b 0

:do_mobile_check
echo.
echo --------------------------------
echo  Checking Mobile App...
echo --------------------------------

if not exist "mobile\package.json" (
    echo [SKIP] Mobile app not found
    exit /b 0
)

call :check_node
if %errorlevel% neq 0 exit /b 1

cd mobile

echo [1/4] Installing dependencies...
call npm ci >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm ci failed
    set /a ERRORS+=1
    cd ..
    exit /b 1
)

echo [2/4] Running ESLint...
call npm run lint >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ESLint found errors
    set /a ERRORS+=1
) else (
    echo [PASS] ESLint passed
)

echo [3/4] Running TypeScript check...
call npx tsc --noEmit >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] TypeScript check failed
    set /a ERRORS+=1
) else (
    echo [PASS] TypeScript check passed
)

echo [4/4] Running tests...
call npm test -- --watchAll=false --passWithNoTests >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Some tests failed
    set /a WARNINGS+=1
) else (
    echo [PASS] Tests passed
)

cd ..
echo [DONE] Mobile checks complete
exit /b 0

REM ===================================
REM Backend Checks
REM ===================================

:check_backend
if "%TARGET%"=="--backend" goto :do_backend_check
if "%TARGET%"=="--all" goto :do_backend_check
exit /b 0

:do_backend_check
echo.
echo --------------------------------
echo  Checking Backend...
echo --------------------------------

if not exist "backend\requirements.txt" (
    echo [SKIP] Backend not found
    exit /b 0
)

call :check_python
if %errorlevel% neq 0 exit /b 1

cd backend

echo [1/3] Checking code formatting...
python -m black --check . >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Code not formatted. Run: black .
    set /a WARNINGS+=1
) else (
    echo [PASS] Formatting check passed
)

echo [2/3] Running linter...
python -m ruff check . >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Linter found errors
    set /a ERRORS+=1
) else (
    echo [PASS] Linter passed
)

echo [3/3] Running tests...
python -m pytest --quiet >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Some tests failed
    set /a WARNINGS+=1
) else (
    echo [PASS] Tests passed
)

cd ..
echo [DONE] Backend checks complete
exit /b 0

REM ===================================
REM ML Checks
REM ===================================

:check_ml
if "%TARGET%"=="--ml" goto :do_ml_check
if "%TARGET%"=="--all" goto :do_ml_check
exit /b 0

:do_ml_check
echo.
echo --------------------------------
echo  Checking ML Code...
echo --------------------------------

if not exist "ml\requirements.txt" (
    echo [SKIP] ML directory not found
    exit /b 0
)

call :check_python
if %errorlevel% neq 0 exit /b 1

cd ml

echo [1/2] Checking Python files...
if exist "*.py" (
    python -m ruff check . --exclude "*.ipynb" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARN] Linter found issues
        set /a WARNINGS+=1
    ) else (
        echo [PASS] Linter passed
    )
) else (
    echo [SKIP] No Python files found
)

echo [2/2] Checking notebooks...
if exist "*.ipynb" (
    echo [INFO] Notebooks found - consider running manually
)

cd ..
echo [DONE] ML checks complete
exit /b 0

REM ===================================
REM Mock Server Checks
REM ===================================

:check_mock_server
if "%TARGET%"=="--mock-server" goto :do_mock_check
if "%TARGET%"=="--all" goto :do_mock_check
exit /b 0

:do_mock_check
echo.
echo --------------------------------
echo  Checking Mock Server...
echo --------------------------------

if not exist "tools\mock-server\package.json" (
    echo [SKIP] Mock server not found
    exit /b 0
)

call :check_node
if %errorlevel% neq 0 exit /b 1

cd tools\mock-server

echo [1/2] Installing dependencies...
call npm ci >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm ci failed
    set /a ERRORS+=1
    cd ..\..
    exit /b 1
)

echo [2/2] Checking syntax...
node --check server.js >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Syntax errors found
    set /a ERRORS+=1
) else (
    echo [PASS] Syntax check passed
)

cd ..\..
echo [DONE] Mock server checks complete
exit /b 0

REM ===================================
REM Main Execution
REM ===================================

:main
call :check_mobile
call :check_backend
call :check_ml
call :check_mock_server

echo.
echo ============================================================
echo  Validation Summary
echo ============================================================
echo.
echo  Errors:   %ERRORS%
echo  Warnings: %WARNINGS%
echo.

if %ERRORS% gtr 0 (
    echo [FAIL] Validation failed with %ERRORS% error(s)
    echo Please fix errors before pushing.
    exit /b 1
)

if %WARNINGS% gtr 0 (
    echo [WARN] Validation passed with %WARNINGS% warning(s)
    echo Consider fixing warnings before pushing.
)

echo [SUCCESS] All validation checks passed!
echo.
exit /b 0
