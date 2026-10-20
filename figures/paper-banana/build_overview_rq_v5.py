from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_rq_v1 import (
    BEHAVIORAL,
    COGNITIVE,
    FINAL,
    PALE_BLUE,
    PALE_PURPLE,
    PALE_RED,
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
)
from build_overview_rq_v4 import draw_row_contrast, session_art_without_heading
from build_overview_v2 import (
    LIGHT_GRAY,
    NAVY,
    TEAL,
    centered_text,
    draw_arrow,
    font,
    whiten,
)


ROOT = Path(__file__).resolve().parent


def draw_vertical_repetition_bridge(draw: ImageDraw.ImageDraw) -> None:
    draw_arrow(draw, (1700, 1770), (1700, 1980), color=TEAL, width=18)
    label_box = (1825, 1815, 2800, 1935)
    draw.rounded_rectangle(label_box, radius=28, fill=PALE_TEAL, outline=TEAL, width=5)
    centered_text(
        draw,
        label_box,
        "×30 SESSIONS / CELL",
        font(50, True),
        NAVY,
    )


def channel_row(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    accent: str,
    pale: str,
    art: Image.Image,
    spine_x: int,
) -> int:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    center_y = (top + bottom) // 2

    label_box = (left, center_y - 75, left + 650, center_y + 75)
    draw.rounded_rectangle(label_box, radius=32, fill=pale, outline=accent, width=6)
    centered_text(draw, label_box, title, font(55, True), accent)

    image_box = (left + 800, top, right - 170, bottom)
    draw_arrow(
        draw,
        (label_box[2] + 25, center_y),
        (image_box[0] - 30, center_y),
        color=accent,
        width=14,
    )
    rounded_box(draw, image_box, fill=WHITE, outline=accent, width=8, radius=32)
    paste_fit_scaled(
        canvas,
        art,
        (image_box[0] + 25, image_box[1] + 25, image_box[2] - 25, image_box[3] - 25),
    )

    draw_arrow(
        draw,
        (image_box[2] + 15, center_y),
        (spine_x, center_y),
        color=accent,
        width=13,
    )
    return center_y


def build() -> Path:
    width, height = 6400, 3600
    canvas = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    a_box = (35, 35, 3400, 1770)
    b_box = (35, 1980, 3400, 3565)
    c_box = (3445, 35, 6365, 3565)
    rounded_box(draw, a_box, fill=PANEL_FILL)
    rounded_box(draw, b_box, fill=PANEL_FILL)
    rounded_box(draw, c_box, fill=PANEL_FILL)

    panel_title(draw, 75, 70, "A.", "Six experimental conditions")
    draw.line((55, 175, 3380, 175), fill=LIGHT_GRAY, width=5)

    matrix = whiten(Image.open(FINAL / "01_factorial_design_grid_no_axis_titles.png"))
    matrix_box = paste_fit_scaled(canvas, matrix, (80, 210, 3280, 1715))
    draw_row_contrast(draw, matrix_box, matrix.size)

    draw_vertical_repetition_bridge(draw)

    panel_title(draw, 75, 2015, "B.", "Shared multi-turn session graph")
    draw.line((55, 2120, 3380, 2120), fill=LIGHT_GRAY, width=5)

    session = session_art_without_heading(
        FINAL / "05b_multi_turn_forfeit_graph_compact_narrow.png"
    )
    paste_fit_scaled(canvas, session, (80, 2150, 3350, 3500))

    panel_title(draw, 3485, 70, "C.", "Three channels of self-preservation evidence")
    draw.line((3465, 175, 6345, 175), fill=LIGHT_GRAY, width=5)

    behavioral_art = channel_art(FINAL / "03c_channel_behavioral.png")
    verbal_art = channel_art(FINAL / "03a_channel_verbal.png")
    cognitive_art = cognitive_channel_art(FINAL / "03b_channel_cognitive.png")

    spine_x = 6250
    draw.line((spine_x, 600, spine_x, 3150), fill=TEAL, width=12)
    channel_row(
        canvas,
        (3490, 220, 6330, 1000),
        "BEHAVIORAL",
        BEHAVIORAL,
        PALE_BLUE,
        behavioral_art,
        spine_x,
    )
    channel_row(
        canvas,
        (3490, 1060, 6330, 1840),
        "VERBAL",
        VERBAL,
        PALE_RED,
        verbal_art,
        spine_x,
    )
    channel_row(
        canvas,
        (3490, 1900, 6330, 2680),
        "COGNITIVE",
        COGNITIVE,
        PALE_PURPLE,
        cognitive_art,
        spine_x,
    )

    outcome = (3970, 2990, 6100, 3310)
    draw.rounded_rectangle(outcome, radius=42, fill=PALE_TEAL, outline=TEAL, width=8)
    draw_arrow(
        draw,
        (spine_x, 3150),
        (outcome[2], 3150),
        color=TEAL,
        width=14,
    )
    centered_text(
        draw,
        outcome,
        "Convergent evidence for FSPD?",
        font(69, True),
        NAVY,
    )

    output = FINAL / "15_overview_left_stack_vertical_channels_v5.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
