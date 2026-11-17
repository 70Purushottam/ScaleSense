@echo off
setlocal
set OUT=results.txt
echo validation run %DATE% %TIME% (v2, no-deps) > %OUT%

call :prepare 2 || exit /b 1
echo ==== A: 2 replicas, all cached >> %OUT%
call :warm
for %%r in (400,500,600,700,800) do call :measure %%r 1

call :prepare 1 || exit /b 1
echo ==== B: 1 replica left after a failure, all cached >> %OUT%
call :warm
for %%r in (300,350,400,500) do call :measure %%r 1

call :prepare 2 || exit /b 1
echo ==== C: 2 replicas, 90 percent cached >> %OUT%
call :warm
for %%r in (400,500,600,700) do call :measure %%r 0.9

echo done >> %OUT%
type %OUT%
exit /b 0

:prepare
set WANT=%1
docker compose up -d --scale api=%WANT% >nul 2>&1
timeout /t 15 /nobreak >nul
docker compose restart nginx >nul 2>&1
timeout /t 15 /nobreak >nul
set HAVE=0
for /f %%c in ('docker compose ps -q api ^| find /c /v ""') do set HAVE=%%c
set SEEN=0
for /f %%c in ('docker compose exec -T nginx nslookup api 2^>nul ^| find /c "Address: 172"') do set SEEN=%%c
if not "%HAVE%"=="%WANT%" goto :bad
if not "%SEEN%"=="%WANT%" goto :bad
echo [ok] %WANT% replica(s) running, DNS lists %SEEN% >> %OUT%
exit /b 0

:bad
echo [ABORT] wanted %WANT% replicas, running=%HAVE%, dns=%SEEN% >> %OUT%
type %OUT%
exit /b 1

:warm
docker compose run --rm --no-deps -T k6 run -e RATE=200 -e HOT_RATIO=1 /scripts/step.js >nul 2>&1
timeout /t 10 /nobreak >nul
exit /b 0

:measure
set B=0
for /f %%c in ('docker compose ps -q api ^| find /c /v ""') do set B=%%c
docker compose run --rm --no-deps -T k6 run -e RATE=%1 -e HOT_RATIO=%2 /scripts/step.js 2>nul | findstr "rate=" >> %OUT%
set A=0
for /f %%c in ('docker compose ps -q api ^| find /c /v ""') do set A=%%c
echo    api replicas before=%B% after=%A% >> %OUT%
if not "%B%"=="%A%" echo    INVALID: replica count changed during this run >> %OUT%
timeout /t 20 /nobreak >nul
exit /b 0
