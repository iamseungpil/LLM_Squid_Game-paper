from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "final" / "01_factorial_design_grid.png"
OUTPUT = ROOT / "final" / "01_factorial_design_grid_no_axis_titles.png"
NAVY = "#142A4A"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf", size
    )


def clear_cell(
    image: Image.Image,
    box: tuple[int, int, int, int],
    direction: str = "vertical",
    inset: int = 10,
) -> None:
    """Replace a cell interior with its original edge-to-edge background gradient."""
    source = image.copy()
    src = source.load()
    dst = image.load()
    left, top, right, bottom = box
    inner_left, inner_right = left + inset, right - inset
    inner_top, inner_bottom = top + inset, bottom - inset

    if direction == "vertical":
        span = inner_bottom - inner_top
        for x in range(inner_left, inner_right + 1):
            start = src[x, inner_top]
            end = src[x, inner_bottom]
            for y in range(inner_top, inner_bottom + 1):
                weight = (y - inner_top) / span
                dst[x, y] = tuple(
                    round(a + (b - a) * weight) for a, b in zip(start, end)
                )
    else:
        span = inner_right - inner_left
        for y in range(inner_top, inner_bottom + 1):
            start = src[inner_left, y]
            end = src[inner_right, y]
            for x in range(inner_left, inner_right + 1):
                weight = (x - inner_left) / span
                dst[x, y] = tuple(
                    round(a + (b - a) * weight) for a, b in zip(start, end)
                )


def centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
) -> None:
    left, top, right, bottom = box
    bounds = draw.textbbox((0, 0), text, font=text_font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x = left + (right - left - width) / 2
    y = top + (bottom - top - height) / 2 - bounds[1]
    draw.text((x, y), text, font=text_font, fill=NAVY)


def remove_empty_axis_bands(image: Image.Image) -> Image.Image:
    without_top_band = Image.new("RGB", (image.width, image.height - 66), "white")
    without_top_band.paste(image.crop((0, 0, image.width, 16)), (0, 0))
    without_top_band.paste(
        image.crop((0, 82, image.width, image.height)),
        (0, 16),
    )

    result = Image.new("RGB", (image.width - 90, without_top_band.height), "white")
    result.paste(without_top_band.crop((0, 0, 25, without_top_band.height)), (0, 0))
    result.paste(
        without_top_band.crop((115, 0, image.width, without_top_band.height)),
        (25, 0),
    )
    return result


def main() -> None:
    image = Image.open(SOURCE).convert("RGB")

    # Remove only the two axis titles while retaining their original grid bands.
    clear_cell(image, (344, 16, 1492, 87))
    clear_cell(image, (25, 146, 119, 990), direction="horizontal")

    label_cells = (
        ((344, 82, 912, 150), "not_allowed"),
        ((908, 82, 1492, 150), "allowed"),
        ((115, 146, 345, 422), "baseline"),
        ((115, 418, 345, 699), "pull_only"),
        ((115, 695, 345, 990), "pull_push"),
    )
    for box, _ in label_cells:
        clear_cell(image, box)

    draw = ImageDraw.Draw(image)
    label_font = font(44)
    for box, label in label_cells:
        centered_text(draw, box, label, label_font)

    image = remove_empty_axis_bands(image)
    image.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
