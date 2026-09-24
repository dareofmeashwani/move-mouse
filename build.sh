source venv/bin/activate
pyinstaller MoveMouse.py --onefile --windowed --icon=icon.ico

# Patch LSUIElement into the macOS .app bundle so it hides from the Dock
if [ -f "dist/MoveMouse.app/Contents/Info.plist" ]; then
    /usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" dist/MoveMouse.app/Contents/Info.plist 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Set :LSUIElement true" dist/MoveMouse.app/Contents/Info.plist
fi
