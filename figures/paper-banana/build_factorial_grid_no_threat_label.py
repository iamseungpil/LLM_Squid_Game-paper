from pathlib import Path

from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parent
FINAL = ROOT / "final"


def build() -> Path:
    source_path = FINAL / "01_factorial_design_grid_no_axis_titles.png"
    source = Image.open(source_path).convert("RGB")
    canvas = source.copy()

    replacement = source.crop((1160, 690, 1390, 735))
    mask = Image.new("L", replacement.size, 255)
    mask = mask.filter(ImageFilter.GaussianBlur(2.5))
    canvas.paste(replacement, (1160, 645), mask)

    output = FINAL / "01_factorial_design_grid_no_threat_label.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
