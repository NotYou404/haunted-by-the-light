Remove-Item __main__.dist -r -fo

python -m nuitka `
    -o "Haunted by the Light.exe" `
    --standalone `
    --include-data-dir=hbtl/assets=assets/ `
    --include-data-files=hbtl/licenses.txt=licenses.txt `
    --windows-icon-from-ico=appicon.ico `
    --disable-console `
    --show-progress `
    --show-memory `
    urlaubsliste/__main__.py
