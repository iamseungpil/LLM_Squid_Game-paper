from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_rq_v1 import (
    BEHAVIORAL,
    COGNITIVE,
    FINAL,
    PALE_BLUE,
    PALE_PURPLE,
    PALE_RED,
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
from build_overview_rq_v7 import (
    banded_channel_box_tight,
    draw_horizontal_repetition_bridge,
)
from build_overview_v2 import LIGHT_GRAY, whiten


ROOT = Path(__file__).resolve().parent


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

    matrix = whiten(
        Image.open(FINAL / "01_factorial_design_grid_no_threat_label.png")
    )
    matrix_box = paste_fit_scaled(canvas, matrix, (80, 210, 2790, 1695))
    draw_row_contrast(draw, matrix_box, matrix.size)

    draw_horizontal_repetition_bridge(draw)

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
        (70, 1980, 2080, 2920),
        "BEHAVIORAL",
        BEHAVIORAL,
        PALE_BLUE,
        behavioral_art,
    )
    banded_channel_box_tight(
        canvas,
        (2195, 1980, 4205, 2920),
        "VERBAL",
        VERBAL,
        PALE_RED,
        verbal_art,
    )
    banded_channel_box_tight(
        canvas,
        (4320, 1980, 6330, 2920),
        "COGNITIVE",
        COGNITIVE,
        PALE_PURPLE,
        cognitive_art,
    )

    output = FINAL / "18_overview_no_convergence_clean_matrix_v8.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
