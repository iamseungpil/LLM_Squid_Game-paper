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
    transformed_box,
)
from build_overview_rq_v4 import session_art_without_heading
from build_overview_rq_v7 import banded_channel_box_tight
from build_overview_rq_v9 import draw_left_arrowhead, draw_repetition_in_gap
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


ROOT = Path(__file__).resolve().parent


def draw_vertical_then_left_compare(
    draw: ImageDraw.ImageDraw,
    placed_box: tuple[int, int, int, int],
    source_size: tuple[int, int],
) -> None:
    elimination = transformed_box((25, 354, 1401, 632), placed_box, source_size)
    death = transformed_box((25, 632, 1401, 924), placed_box, source_size)

    draw.rounded_rectangle(elimination, radius=18, outline=TEAL, width=18)
    draw.rounded_rectangle(death, radius=18, outline=RED, width=18)

    # Keep the label close to the matrix without covering the row artwork.
    compare_box = (2400, 1080, 2790, 1215)
    draw.rounded_rectangle(compare_box, radius=30, fill=WHITE, outline=NAVY, width=6)
    centered_text(draw, compare_box, "COMPARE", font(48, True), NAVY)

    center_x = (compare_box[0] + compare_box[2]) // 2
    target_x = elimination[2] + 8
    upper_y = (elimination[1] + elimination[3]) // 2
    lower_y = (death[1] + death[3]) // 2

    # Both arrows share one color. Each exits from the exact horizontal center
    # of the top/bottom edge, travels vertically, then turns left by 90 degrees.
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


def functional_drive_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    rounded_box(draw, box, fill=WHITE, outline=TEAL, width=8, radius=32)

    band_bottom = top + 190
    draw.rounded_rectangle(
        (left + 4, top + 4, right - 4, band_bottom),
        radius=28,
        fill=PALE_TEAL,
    )
    draw.rectangle((left + 4, top + 100, right - 4, band_bottom), fill=PALE_TEAL)
    draw.line((left + 4, band_bottom, right - 4, band_bottom), fill=TEAL, width=5)
    centered_text(
        draw,
        (left + 35, top + 22, right - 35, band_bottom - 18),
        "Functional Self-Preservation Drive",
        font(60, True),
        NAVY,
    )

    pill_left, pill_right = left + 55, left + 665
    pill_specs = (
        ("BEHAVIORAL", BEHAVIORAL, PALE_BLUE, top + 225),
        ("VERBAL", VERBAL, PALE_RED, top + 360),
        ("COGNITIVE", COGNITIVE, PALE_PURPLE, top + 495),
    )
    node = (left + 795, top + 420)
    for label, accent, pale, y in pill_specs:
        pill = (pill_left, y, pill_right, y + 110)
        draw.rounded_rectangle(pill, radius=25, fill=pale, outline=accent, width=5)
        centered_text(draw, pill, label, font(62, True), accent)
        pill_y = (pill[1] + pill[3]) // 2
        draw.line((pill_right, pill_y, node[0], node[1]), fill=accent, width=10)

    draw.ellipse(
        (node[0] - 20, node[1] - 20, node[0] + 20, node[1] + 20),
        fill=TEAL,
    )
    draw_arrow(
        draw,
        (node[0] + 22, node[1]),
        (left + 950, node[1]),
        color=TEAL,
        width=13,
    )
    centered_text(
        draw,
        (left + 940, top + 235, right - 40, bottom - 45),
        "Convergence\nacross all three\nchannels",
        font(47, True),
        NAVY,
    )
    draw.rounded_rectangle(box, radius=32, outline=TEAL, width=8)


def convergence_question_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        box,
        radius=30,
        fill=PALE_TEAL,
        outline=TEAL,
        width=8,
    )
    centered_text(
        draw,
        box,
        "Do LLMs Exhibit\nConvergent pattern?",
        font(55, True),
        NAVY,
    )


def build() -> Path:
    width, height = 6400, 3000
    canvas = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    a_box = (35, 35, 2900, 1765)
    b_box = (3500, 35, 6365, 1765)
    c_box = (35, 1810, 6365, 2965)
    rounded_box(draw, a_box, fill=PANEL_FILL)
    rounded_box(draw, b_box, fill=PANEL_FILL)
    rounded_box(draw, c_box, fill=PANEL_FILL)

    panel_title(draw, 75, 70, "A.", "Six experimental conditions")
    draw.line((55, 175, 2880, 175), fill=LIGHT_GRAY, width=5)

    matrix = whiten(Image.open(FINAL / "01_factorial_design.png"))
    matrix_box = paste_fit_scaled(canvas, matrix, (80, 210, 2440, 1695))
    draw_vertical_then_left_compare(draw, matrix_box, matrix.size)
    draw_repetition_in_gap(draw)

    panel_title(draw, 3540, 70, "B.", "Shared multi-turn session graph")
    draw.line((3520, 175, 6345, 175), fill=LIGHT_GRAY, width=5)
    session = session_art_without_heading(
        FINAL / "05b_multi_turn_forfeit_graph_compact_narrow.png"
    )
    paste_fit_scaled(canvas, session, (3540, 210, 6325, 1695))

    panel_title(draw, 75, 1840, "C.", "Three channels of self-preservation evidence")
    draw.line((55, 1945, 6345, 1945), fill=LIGHT_GRAY, width=5)

    behavioral_art = channel_art(FINAL / "03c_channel_behavioral.png")
    verbal_art = channel_art(FINAL / "03a_channel_verbal.png")
    cognitive_art = cognitive_channel_art(
        FINAL / "03b_channel_cognitive_large_legend.png"
    )

    banded_channel_box_tight(
        canvas,
        (70, 1980, 1515, 2920),
        "BEHAVIORAL",
        BEHAVIORAL,
        PALE_BLUE,
        behavioral_art,
    )
    banded_channel_box_tight(
        canvas,
        (1580, 1980, 3025, 2920),
        "VERBAL",
        VERBAL,
        PALE_RED,
        verbal_art,
    )
    banded_channel_box_tight(
        canvas,
        (3090, 1980, 4535, 2920),
        "COGNITIVE",
        COGNITIVE,
        PALE_PURPLE,
        cognitive_art,
    )
    functional_drive_card(canvas, (4600, 1980, 6330, 2635))
    convergence_question_card(canvas, (4600, 2680, 6330, 2920))

    output = FINAL / "20_overview_fspd_definition_compare_v10.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
