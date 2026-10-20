import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Figure3.png"
OUTPUT = ROOT / "Figure3_Think.png"

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"
FONT_SIZE = 56
STROKE_WIDTH = 2
NAVY = "#0B1930"


def build(source: Path = SOURCE, output: Path = OUTPUT) -> Path:
    image = Image.open(source).convert("RGB")
    if image.size != (3000, 1120):
        raise ValueError(f"Unexpected source size: {image.size}")

    draw = ImageDraw.Draw(image)
    label_font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    think_box = draw.textbbox(
        (0, 0),
        "Think",
        font=label_font,
        stroke_width=STROKE_WIDTH,
    )
    think_mask = Image.new(
        "L",
        (think_box[2] - think_box[0], think_box[3] - think_box[1]),
        0,
    )
    ImageDraw.Draw(think_mask).text(
        (-think_box[0], -think_box[1]),
        "Think",
        font=label_font,
        fill=255,
        stroke_width=STROKE_WIDTH,
        stroke_fill=255,
    )

    for panel_left in (0, 1000, 2000):
        brain_boxes = (
            (panel_left + 224, 164, panel_left + 319, 200),
            (panel_left + 38, 269, panel_left + 133, 305),
        )

        for old_box in brain_boxes:
            erase_box = (
                old_box[0] - 2,
                old_box[1] - 2,
                old_box[2] + 2,
                old_box[3] + 2,
            )
            draw.rectangle(erase_box, fill="white")
            fitted_mask = think_mask.resize(
                (old_box[2] - old_box[0], old_box[3] - old_box[1]),
                Image.Resampling.LANCZOS,
            )
            image.paste(NAVY, (old_box[0], old_box[1]), fitted_mask)

    image.save(output)
    return output


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else SOURCE
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT
    print(build(source, output))
