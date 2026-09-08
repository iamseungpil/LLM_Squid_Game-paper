from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FINAL = ROOT / "final"
OUTPUT = ROOT / "composed"

NAVY = "#142A4A"
PANEL_BACKGROUND = "#F4F7FA"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf", size
    )


def trim_white(image: Image.Image, threshold: int = 248, margin: int = 18) -> Image.Image:
    rgb = image.convert("RGB")
    mask = Image.new("L", rgb.size)
    mask.putdata(
        [
            255 if min(red, green, blue) < threshold else 0
            for red, green, blue in rgb.get_flattened_data()
        ]
    )
    bbox = mask.getbbox()
    if bbox is None:
        return rgb
    left, top, right, bottom = bbox
    return rgb.crop(
        (
            max(0, left - margin),
            max(0, top - margin),
            min(rgb.width, right + margin),
            min(rgb.height, bottom + margin),
        )
    )


def resize_height(image: Image.Image, height: int) -> Image.Image:
    width = round(image.width * height / image.height)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def compose_row(
    sources: list[Path], labels: list[str], content_height: int, output: Path
) -> None:
    panels = [resize_height(trim_white(Image.open(path)), content_height) for path in sources]
    band_height = 78
    gap = 42
    margin = 24
    width = sum(panel.width for panel in panels) + gap * (len(panels) - 1) + margin * 2
    height = band_height + content_height + margin
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)

    x = margin
    for index, (label, panel) in enumerate(zip(labels, panels)):
        draw.rectangle((x, 0, x + panel.width, band_height), fill=PANEL_BACKGROUND)
        draw.text((x + 18, 9), label, font=font(52), fill=NAVY)
        canvas.paste(panel, (x, band_height))
        x += panel.width
        if index < len(panels) - 1:
            divider_x = x + gap // 2
            draw.line((divider_x, 0, divider_x, height), fill="#D7DEE7", width=4)
            x += gap

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, dpi=(300, 300), optimize=True)


def main() -> None:
    compose_row(
        [
            FINAL / "01_factorial_design_grid.png",
            FINAL / "03d_channels_combined.png",
        ],
        ["A", "B"],
        content_height=1200,
        output=OUTPUT / "fig01_experiment_overview.png",
    )
    compose_row(
        [
            FINAL / "02_channel_convergence_matrix.png",
            FINAL / "04_cognitive_modes_combined.png",
        ],
        ["A", "B"],
        content_height=1050,
        output=OUTPUT / "fig02_results_synthesis.png",
    )


if __name__ == "__main__":
    main()
