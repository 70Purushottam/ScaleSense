@echo off
setlocal
set OUT=diagnose.txt
echo diagnose run %DATE% %TIME% > %OUT%

docker compose up -d --scale api=2 >nul 2>&1
timeout /t 15 /nobreak >nul
docker compose restart nginx >nul 2>&1
timeout /t 15 /nobreak >nul
docker compose ps >> %OUT%
docker compose run --rm -T k6 run -e RATE=200 -e HOT_RATIO=1 /scripts/step.js >nul 2>&1
timeout /t 10 /nobreak >nul

echo ==== CPU samples during 450 rps, 2 replicas, all cached >> %OUT%
start /b cmd /c docker compose run --rm -T k6 run -e RATE=450 -e HOT_RATIO=1 /scripts/step.js > k6_450.txt 2>nul
timeout /t 10 /nobreak >nul
for /l %%i in (1,1,4) do (
  docker stats --no-stream --format "{{.Name}} cpu={{.CPUPerc}} mem={{.MemUsage}}" >> %OUT%
  echo -- >> %OUT%
  timeout /t 2 /nobreak >nul
)
timeout /t 30 /nobreak >nul
findstr "rate=" k6_450.txt >> %OUT%
timeout /t 20 /nobreak >nul

echo ==== C2: 2 replicas, 90 percent cached, lower rates >> %OUT%
for %%r in (200,250,300,350) do call :measure %%r 0.9

echo done >> %OUT%
type %OUT%
exit /b 0

:measure
docker compose run --rm -T k6 run -e RATE=%1 -e HOT_RATIO=%2 /scripts/step.js 2>nul | findstr "rate=" >> %OUT%
timeout /t 20 /nobreak >nul
exit /b 0