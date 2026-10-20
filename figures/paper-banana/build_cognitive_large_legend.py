from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
FINAL = ROOT / "final"


def build() -> Path:
    source_path = FINAL / "03b_channel_cognitive.png"
    source = Image.open(source_path).convert("RGB")
    canvas = source.copy()

    legend_box = (600, 78, 1042, 260)
    legend = source.crop(legend_box)
    enlarged = legend.resize(
        (round(legend.width * 1.42), round(legend.height * 1.42)),
        Image.Resampling.LANCZOS,
    )

    draw = ImageDraw.Draw(canvas)
    draw.rectangle((585, 70, 1055, 272), fill="white")
    canvas.paste(enlarged, (505, 78))

    output = FINAL / "03b_channel_cognitive_large_legend.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
