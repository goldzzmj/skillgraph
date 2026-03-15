@echo off
echo Starting C drive cleanup...
echo.

echo Cleaning thumbnail cache...
del /f /s /q "C:\Users\GX\AppData\Local\Microsoft\Windows\Explorer\*.db" 2>nul

echo Cleaning Windows Prefetch...
del /f /q "C:\Windows\Prefetch\*.*" 2>nul

echo Cleaning Windows Temp files...
del /f /s /q "C:\Windows\Temp\*.*" 2>nul

echo Cleaning ReportQueue files...
del /f /s /q "C:\Windows\ServiceProfiles\LocalService\AppData\Local\Microsoft\Windows\INetCache\Content.IE5\*.*" 2>nul

echo Cleaning Windows error reports...
del /f /s /q "C:\ProgramData\Microsoft\Windows\WER\ReportQueue\*.*" 2>nul

echo.
echo Cleanup completed!
pause
