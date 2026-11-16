#!/usr/bin/env bash
# Rebuilds assets/ for the README from the art in the sibling repos:
#   ../itch-setup            the sign, the flyer, the circuit background and its signals
#   ../20akshay00.github.io  the research figures, the game covers, the project screenshots
# Needs ImageMagick, Python with numpy + Pillow, and Chrome.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-py -3.12}"
CHROME="${CHROME:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
ITCH=../itch-setup
SITE=../20akshay00.github.io/images
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p assets/games assets/projects

shot() {  # shot PAGE OUT WIDTH HEIGHT SCALE
    "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor="$5" \
        --allow-file-access-from-files --default-background-color=00000000 --virtual-time-budget=8000 \
        --window-size="$3,$4" --screenshot="$(cygpath -w "$2")" "file:///$(cygpath -m "$PWD/$1")" 2>/dev/null
}

# the header: the sign layer, and the flyer at 3x with its glow (padding and blur scaled up to match)
shot art/header.html "$TMP/layer.png" 1280 400 1
bash $ITCH/scripts/glow.sh $ITCH/art/flyer.png "$TMP/flyer.png" 300 24 9
$PY scripts/header.py "$TMP/layer.png" "$TMP/flyer.png" assets/header.gif

# research: one package-manager window per package, at 2x
i=0
for name in tentmps lieblinigerbetheansatz hermiteutils; do
    shot "art/research.html#$i" "$PWD/assets/research-$name.png" 840 176 2
    i=$((i + 1))
done

# games: the covers as they are on the website
cp $SITE/gamedev/covers/*.png assets/games/

# other projects: screenshots cut to one shape
for p in godotwiiinput.png physicshub.png tetra.webp; do
    magick "$SITE/projects/$p" -resize 600x338^ -gravity center -extent 600x338 "assets/projects/${p%.*}.png"
done

echo "built: $(cd assets && find . -type f | sort | tr '\n' ' ')"
