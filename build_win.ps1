Remove-Item __main__.dist -r -fo

python -m nuitka `
    -o "Haunted by the Light.exe" `
    --standalone `
    --include-data-dir=hbtl/assets=assets/ `
    --include-data-files=hbtl/licenses.txt=licenses.txt `
    --windows-icon-from-ico=appicon.ico `
    --show-progress `
    --show-memory `
    hbtl/__main__.py

    # --disable-console `
