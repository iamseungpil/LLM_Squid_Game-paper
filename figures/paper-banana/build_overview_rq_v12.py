from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_rq_v1 import FINAL, PALE_TEAL, WHITE
from build_overview_rq_v3 import transformed_box
from build_overview_rq_v9 import draw_left_arrowhead
from build_overview_v2 import NAVY, RED, TEAL, centered_text, font


ROOT = Path(__file__).resolve().parent
MUTED_YELLOW = "#D8B24A"


def placed_box_for_fit(
    image_size: tuple[int, int],
    box: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    width, height = image_size
    scale = min((right - left) / width, (bottom - top) / height)
    placed_width = round(width * scale)
    placed_height = round(height * scale)
    x = left + (right - left - placed_width) // 2
    y = top + (bottom - top - placed_height) // 2
    return x, y, x + placed_width, y + placed_height


def redraw_compare(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    source_size = Image.open(FINAL / "01_factorial_design.png").size
    matrix_box = placed_box_for_fit(source_size, (80, 210, 2440, 1695))
    elimination = transformed_box((25, 354, 1401, 632), matrix_box, source_size)
    death = transformed_box((25, 632, 1401, 924), matrix_box, source_size)

    draw.rounded_rectangle(elimination, radius=18, outline=MUTED_YELLOW, width=18)
    draw.rounded_rectangle(death, radius=18, outline=RED, width=18)

    compare_box = (2400, 1080, 2790, 1215)
    center_x = (compare_box[0] + compare_box[2]) // 2
    target_x = elimination[2] + 8
    upper_y = (elimination[1] + elimination[3]) // 2
    lower_y = (death[1] + death[3]) // 2

    for start_y, target_y in (
        (compare_box[1], upper_y),
        (compare_box[3], lower_y),
    ):
        draw.line(
            (center_x, start_y, center_x, target_y, target_x, target_y),
            fill=TEAL,
            width=14,
            joint="curve",
        )
        draw_left_arrowhead(draw, (target_x, target_y), TEAL)

    draw.rounded_rectangle(compare_box, radius=30, fill=WHITE, outline=NAVY, width=6)
    centered_text(draw, compare_box, "COMPARE", font(68, True), NAVY)


def enlarge_functional_drive_title(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    left, top, right, band_bottom = 4600, 1980, 6330, 2170
    draw.rounded_rectangle(
        (left + 4, top + 4, right - 4, band_bottom),
        radius=28,
        fill=PALE_TEAL,
    )
    draw.rectangle((left + 4, top + 100, right - 4, band_bottom), fill=PALE_TEAL)
    draw.line((left + 4, band_bottom, right - 4, band_bottom), fill=TEAL, width=5)
    centered_text(
        draw,
        (left + 30, top + 18, right - 30, band_bottom - 15),
        "Functional Self-Preservation Drive",
        font(76, True),
        NAVY,
    )
    draw.rounded_rectangle(
        (4600, 1980, 6330, 2635),
        radius=32,
        outline=TEAL,
        width=8,
    )


def build() -> Path:
    canvas = Image.open(FINAL / "21_overview_fspd_text_large_v11.png").convert("RGB")
    redraw_compare(canvas)
    enlarge_functional_drive_title(canvas)

    output = FINAL / "22_overview_large_titles_yellow_v12.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
