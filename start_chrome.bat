@echo off
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="%USERPROFILE%\.reddit-profile-debug" --no-first-run --no-default-browser-check
