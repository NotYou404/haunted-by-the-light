rm -rf __main__.dist

python -m nuitka \
    -o "Haunted by the Light" \
    --standalone \
    --include-data-dir=hbtl/assets=assets/ \
    --include-data-files=hbtl/licenses.txt=licenses.txt \
    --noinclude-data-files=*.aseprite \
    --noinclude-data-files=*.tiled-project \
    --noinclude-data-files=*.tiled-session \
    --noinclude-data-files=*.tmx \
    --noinclude-data-files=*.unused \
    --windows-icon-from-ico=appicon.ico \
    --windows-console-mode=disable \
    --show-progress \
    --show-memory \
    --noinclude-setuptools-mode=nofollow \
    --noinclude-pytest-mode=nofollow \
    --noinclude-unittest-mode=nofollow \
    --noinclude-IPython-mode=nofollow \
    hbtl/__main__.py
