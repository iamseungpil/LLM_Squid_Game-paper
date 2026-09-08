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


def draw_left_arrowhead(
    draw: ImageDraw.ImageDraw,
    tip: tuple[int, int],
    color: str,
    size: int = 30,
) -> None:
    x, y = tip
    draw.polygon(
        ((x, y), (x + size, y - size // 2), (x + size, y + size // 2)),
        fill=color,
    )


def draw_orthogonal_compare(
    draw: ImageDraw.ImageDraw,
    placed_box: tuple[int, int, int, int],
    source_size: tuple[int, int],
) -> None:
    elimination = transformed_box((25, 354, 1401, 632), placed_box, source_size)
    death = transformed_box((25, 632, 1401, 924), placed_box, source_size)

    # The two complete rows use the same outline weight and geometry.
    draw.rounded_rectangle(elimination, radius=18, outline=TEAL, width=18)
    draw.rounded_rectangle(death, radius=18, outline=RED, width=18)

    compare_box = (2470, 1085, 2835, 1215)
    draw.rounded_rectangle(compare_box, radius=30, fill=WHITE, outline=NAVY, width=6)
    centered_text(draw, compare_box, "COMPARE", font(48, True), NAVY)

    target_x = elimination[2] + 8
    elbow_x = 2405
    upper_y = (elimination[1] + elimination[3]) // 2
    lower_y = (death[1] + death[3]) // 2

    # Each connector leaves the box horizontally, turns exactly 90 degrees,
    # then turns 90 degrees again to point left at its row.
    for start_y, target_y, color in (
        (1125, upper_y, TEAL),
        (1175, lower_y, RED),
    ):
        draw.line(
            (
                compare_box[0],
                start_y,
                elbow_x,
                start_y,
                elbow_x,
                target_y,
                target_x,
                target_y,
            ),
            fill=color,
            width=14,
            joint="curve",
        )
        draw_left_arrowhead(draw, (target_x, target_y), color)


def draw_repetition_in_gap(draw: ImageDraw.ImageDraw) -> None:
    centered_text(draw, (2940, 585, 3460, 755), "×30", font(112, True), TEAL)
    centered_text(
        draw,
        (2945, 735, 3455, 845),
        "SESSIONS / CELL",
        font(52, True),
        NAVY,
    )
    # The arrow remains entirely inside the whitespace between panels A and B.
    draw_arrow(draw, (2965, 925), (3435, 925), color=TEAL, width=18)


def fspd_definition_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    rounded_box(draw, box, fill=WHITE, outline=TEAL, width=8, radius=32)

    band_bottom = top + 205
    draw.rounded_rectangle(
        (left + 4, top + 4, right - 4, band_bottom),
        radius=28,
        fill=PALE_TEAL,
    )
    draw.rectangle((left + 4, top + 105, right - 4, band_bottom), fill=PALE_TEAL)
    draw.line((left + 4, band_bottom, right - 4, band_bottom), fill=TEAL, width=5)
    centered_text(
        draw,
        (left + 30, top + 15, right - 30, top + 115),
        "FSPD",
        font(78, True),
        NAVY,
    )
    centered_text(
        draw,
        (left + 30, top + 110, right - 30, band_bottom - 12),
        "Functional Self-Preservation Drive",
        font(34, True),
        NAVY,
    )

    pill_left, pill_right = left + 55, left + 515
    pill_specs = (
        ("BEHAVIORAL", BEHAVIORAL, PALE_BLUE, top + 265),
        ("VERBAL", VERBAL, PALE_RED, top + 385),
        ("COGNITIVE", COGNITIVE, PALE_PURPLE, top + 505),
    )
    node = (left + 625, top + 445)
    for label, accent, pale, y in pill_specs:
        pill = (pill_left, y, pill_right, y + 82)
        draw.rounded_rectangle(pill, radius=22, fill=pale, outline=accent, width=4)
        centered_text(draw, pill, label, font(31, True), accent)
        pill_y = (pill[1] + pill[3]) // 2
        draw.line((pill_right, pill_y, node[0], node[1]), fill=accent, width=9)

    draw.ellipse(
        (node[0] - 18, node[1] - 18, node[0] + 18, node[1] + 18),
        fill=TEAL,
    )
    draw_arrow(
        draw,
        (node[0] + 20, node[1]),
        (left + 760, node[1]),
        color=TEAL,
        width=12,
    )
    centered_text(
        draw,
        (left + 755, top + 265, right - 45, top + 620),
        "Convergence\nacross all three\nchannels",
        font(51, True),
        NAVY,
    )

    question_box = (left + 55, bottom - 225, right - 55, bottom - 45)
    draw.rounded_rectangle(
        question_box,
        radius=28,
        fill=PALE_TEAL,
        outline=TEAL,
        width=5,
    )
    centered_text(
        draw,
        question_box,
        "Do LLMs exhibit this\nconvergent pattern?",
        font(47, True),
        NAVY,
    )
    draw.rounded_rectangle(box, radius=32, outline=TEAL, width=8)


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
    draw_orthogonal_compare(draw, matrix_box, matrix.size)
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
    fspd_definition_card(canvas, (4600, 1980, 6330, 2920))

    output = FINAL / "19_overview_fspd_convergence_matrix_v9.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
