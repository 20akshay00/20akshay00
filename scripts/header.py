"""The README's animated header: assets/header.gif.

    python header.py LAYER FLYER OUT

LAYER is art/header.html rendered (the sign, transparent, 1280x400). FLYER is the flyer at 3x with its
glow. Under the sign go the itch profile's circuit background and the signals running along its traces
(itch-setup), cropped the same way so the pulses stay on the traces. Over it the flyer floats gently,
facing the sign.
"""
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageSequence

ITCH = Path(__file__).resolve().parents[2] / "itch-setup"
W, H = 1280, 400
CROP = (0, 300)                 # where the header sits on the 1280px background
FRAMES, MS = 240, 50            # 12 s at 20 fps: one loop of the signals
FLYER_AT = (935, 40)            # the flyer's resting top left, over the sign's corner
BOB, SWAY = 7, 4                # how far it floats up and down, and side to side, in pixels


def flyer_at(t):
    """The flyer's top left at GIF frame t: a slow bob (3 per loop) and a slower sway (2 per loop)."""
    p = 2 * math.pi * t / FRAMES
    return (round(FLYER_AT[0] + SWAY * math.sin(2 * p)),
            round(FLYER_AT[1] + BOB * math.sin(3 * p)))


def main(layer, flyer, out):
    bg = Image.open(ITCH / "upload/background.png").convert("RGBA")
    bg = bg.crop((CROP[0], CROP[1], CROP[0] + W, CROP[1] + H))
    layer = Image.open(layer).convert("RGBA")
    flyer = Image.open(flyer).convert("RGBA")

    # the signals tile is 640px, shown at 2x like the background
    signals = [f.convert("RGBA").resize((1280, 1280), Image.NEAREST)
               .crop((CROP[0], CROP[1], CROP[0] + W, CROP[1] + H))
               for f in ImageSequence.Iterator(Image.open(ITCH / "docs/signals.png"))]

    rgb = []
    for t in range(FRAMES):
        im = Image.alpha_composite(bg, signals[t % len(signals)])
        im = Image.alpha_composite(im, layer)
        im.alpha_composite(flyer, flyer_at(t))
        rgb.append(im.convert("RGB"))

    # one palette for every frame (no flicker), from a still and the background with its pulses lit
    sample = Image.new("RGB", (W, H * 2))
    sample.paste(rgb[0], (0, 0))
    lit = Image.alpha_composite(bg, Image.alpha_composite(signals[0], signals[len(signals) // 2]))
    sample.paste(lit.convert("RGB"), (0, H))
    pal = sample.quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = [np.asarray(f.quantize(palette=pal, dither=Image.Dither.NONE)) for f in rgb]

    # each frame draws only what changed since the one before; the rest is transparent (index 255) and
    # lets the frame below show through. The pulses change pixels all over, so cropping to the changed
    # box alone saves almost nothing, but long transparent runs compress well.
    gif = [idx[0]] + [np.where(idx[t] == idx[t - 1], 255, idx[t]).astype(np.uint8) for t in range(1, FRAMES)]
    pal_bytes = pal.getpalette()[:255 * 3] + [0, 0, 0]
    ims = []
    for a in gif:
        im = Image.fromarray(a, "P")
        im.putpalette(pal_bytes)
        im.info["transparency"] = 255
        ims.append(im)
    ims[0].save(out, save_all=True, append_images=ims[1:], duration=MS, loop=0, optimize=False,
                disposal=1, transparency=255)


if __name__ == "__main__":
    main(*sys.argv[1:4])
