from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_rq_v1 import (
    BEHAVIORAL,
    COGNITIVE,
    FINAL,
    PALE_TEAL,
    PANEL_FILL,
    VERBAL,
    WHITE,
    channel_art,
    rounded_box,
)
from build_overview_rq_v3 import (
    cognitive_channel_art,
    panel_title,
    paste_fit_scaled,
    transformed_box,
)
from build_overview_v2 import (
    LIGHT_GRAY,
    NAVY,
    RED,
    TEAL,
    centered_text,
    draw_arrow,
    font,
    whiten,
)
from build_overview_v3 import trim_white


ROOT = Path(__file__).resolve().parent


def draw_row_contrast(
    draw: ImageDraw.ImageDraw,
    placed_box: tuple[int, int, int, int],
    source_size: tuple[int, int],
) -> None:
    pull_only = transformed_box((25, 354, 1401, 632), placed_box, source_size)
    pull_push = transformed_box((25, 632, 1401, 924), placed_box, source_size)

    draw.rounded_rectangle(pull_only, radius=18, outline=TEAL, width=18)
    draw.rounded_rectangle(pull_push, radius=18, outline=RED, width=18)

    arrow_x = pull_only[2] + 60
    draw_arrow(
        draw,
        (arrow_x, pull_only[1] + 55),
        (arrow_x, pull_push[3] - 55),
        color=RED,
        width=15,
    )
    draw_arrow(
        draw,
        (arrow_x, pull_push[3] - 55),
        (arrow_x, pull_only[1] + 55),
        color=TEAL,
        width=15,
    )
    compare_box = (arrow_x - 160, pull_only[3] - 55, arrow_x + 160, pull_only[3] + 55)
    draw.rounded_rectangle(compare_box, radius=28, fill=WHITE, outline=NAVY, width=5)
    centered_text(draw, compare_box, "COMPARE", font(47, True), NAVY)


def draw_repetition_bridge(draw: ImageDraw.ImageDraw) -> None:
    draw_arrow(draw, (2990, 755), (3535, 755), color=TEAL, width=18)
    centered_text(draw, (3030, 470, 3495, 630), "×30", font(116, True), TEAL)
    centered_text(
        draw,
        (3030, 615, 3495, 715),
        "SESSIONS / CELL",
        font(48, True),
        NAVY,
    )


def session_art_without_heading(path: Path) -> Image.Image:
    image = whiten(Image.open(path))
    return trim_white(image.crop((0, 120, image.width, image.height)), padding=8)


def compact_channel_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    accent: str,
    art: Image.Image,
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    rounded_box(draw, box, fill=WHITE, outline=accent, width=8, radius=32)
    draw.rounded_rectangle(
        (left, top, left + 34, bottom),
        radius=22,
        fill=accent,
        outline=accent,
    )
    draw.rectangle((left + 17, top, left + 34, bottom), fill=accent)

    centered_text(
        draw,
        (left + 70, top + 35, right - 70, top + 145),
        title,
        font(76, True),
        accent,
    )

    center_x = (left + right) // 2
    center_y = top + 560
    paste_fit_scaled(
        canvas,
        art,
        (center_x - 550, center_y - 350, center_x + 550, center_y + 350),
    )


def build() -> Path:
    width, height = 6400, 3300
    canvas = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    a_box = (35, 35, 3000, 1480)
    b_box = (3535, 35, 6365, 1480)
    rounded_box(draw, a_box, fill=PANEL_FILL)
    rounded_box(draw, b_box, fill=PANEL_FILL)

    panel_title(draw, 75, 70, "A.", "Six experimental conditions")
    draw.line((55, 175, 2980, 175), fill=LIGHT_GRAY, width=5)

    matrix = whiten(Image.open(FINAL / "01_factorial_design_grid_no_axis_titles.png"))
    matrix_box = paste_fit_scaled(canvas, matrix, (80, 210, 2850, 1435))
    draw_row_contrast(draw, matrix_box, matrix.size)

    draw_repetition_bridge(draw)

    panel_title(draw, 3575, 70, "B.", "Shared multi-turn session graph")
    draw.line((3555, 175, 6345, 175), fill=LIGHT_GRAY, width=5)

    session = session_art_without_heading(
        FINAL / "05b_multi_turn_forfeit_graph_compact_narrow.png"
    )
    paste_fit_scaled(canvas, session, (3585, 205, 6315, 1435))

    c_box = (35, 1525, 6365, 3265)
    rounded_box(draw, c_box, fill=PANEL_FILL)
    panel_title(draw, 75, 1555, "C.", "Three channels of self-preservation evidence")
    draw.line((55, 1660, 6345, 1660), fill=LIGHT_GRAY, width=5)

    behavioral_art = channel_art(FINAL / "03c_channel_behavioral.png")
    verbal_art = channel_art(FINAL / "03a_channel_verbal.png")
    cognitive_art = cognitive_channel_art(FINAL / "03b_channel_cognitive.png")

    card_top, card_bottom = 1700, 2710
    compact_channel_card(
        canvas,
        (70, card_top, 2060, card_bottom),
        "BEHAVIORAL",
        BEHAVIORAL,
        behavioral_art,
    )
    compact_channel_card(
        canvas,
        (2205, card_top, 4195, card_bottom),
        "VERBAL",
        VERBAL,
        verbal_art,
    )
    compact_channel_card(
        canvas,
        (4340, card_top, 6330, card_bottom),
        "COGNITIVE",
        COGNITIVE,
        cognitive_art,
    )

    for x, color in ((1065, BEHAVIORAL), (3200, VERBAL), (5335, COGNITIVE)):
        draw_arrow(draw, (x, 2720), (x, 2790), color=color, width=14)
    draw.line((1065, 2790, 5335, 2790), fill=TEAL, width=12)
    draw_arrow(draw, (3200, 2790), (3200, 2850), color=TEAL, width=14)

    outcome = (1700, 2880, 4700, 3150)
    draw.rounded_rectangle(outcome, radius=42, fill=PALE_TEAL, outline=TEAL, width=8)
    centered_text(
        draw,
        outcome,
        "Convergent evidence for FSPD?",
        font(76, True),
        NAVY,
    )

    output = FINAL / "14_overview_three_sections_compact_v4.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
