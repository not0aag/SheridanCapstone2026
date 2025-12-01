@echo off
setlocal

REM Minimal repo bootstrap (requires GitHub CLI: https://cli.github.com/)
REM Usage: setup_repos.cmd ORG_NAME

if "%~1"=="" (
  echo Usage: %~nx0 ORG_NAME
  exit /b 1
)
set ORG=%~1

where gh >nul 2>nul || (
  echo ERROR: 'gh' not found. Install from https://cli.github.com/ and run: gh auth login
  exit /b 1
)

for %%R in (mobile backend ml infra docs) do (
  gh repo create %ORG%/safedrive-%%R --public --confirm --disable-wiki --description "SafeDrive AI %%R"
)

endlocal
