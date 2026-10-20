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


def banded_channel_box_tight(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    accent: str,
    pale: str,
    art: Image.Image,
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    rounded_box(draw, box, fill=WHITE, outline=accent, width=8, radius=32)

    band_bottom = top + 165
    draw.rounded_rectangle(
        (left + 4, top + 4, right - 4, band_bottom),
        radius=28,
        fill=pale,
    )
    draw.rectangle((left + 4, top + 90, right - 4, band_bottom), fill=pale)
    draw.line((left + 4, band_bottom, right - 4, band_bottom), fill=accent, width=5)
    centered_text(
        draw,
        (left + 35, top + 20, right - 35, band_bottom - 8),
        title,
        font(68, True),
        accent,
    )

    paste_fit_scaled(
        canvas,
        art,
        (left + 8, band_bottom + 22, right - 8, bottom - 25),
    )
    draw.rounded_rectangle(box, radius=32, outline=accent, width=8)


def draw_horizontal_repetition_bridge(draw: ImageDraw.ImageDraw) -> None:
    draw_arrow(draw, (2880, 900), (3520, 900), color=TEAL, width=18)
    centered_text(draw, (2940, 600, 3460, 755), "×30", font(116, True), TEAL)
    centered_text(
        draw,
        (2940, 745, 3460, 845),
        "SESSIONS / CELL",
        font(58, True),
        NAVY,
    )


def build() -> Path:
    width, height = 6400, 3300
    canvas = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    a_box = (35, 35, 2900, 1765)
    b_box = (3500, 35, 6365, 1765)
    c_box = (35, 1810, 6365, 3265)
    rounded_box(draw, a_box, fill=PANEL_FILL)
    rounded_box(draw, b_box, fill=PANEL_FILL)
    rounded_box(draw, c_box, fill=PANEL_FILL)

    panel_title(draw, 75, 70, "A.", "Six experimental conditions")
    draw.line((55, 175, 2880, 175), fill=LIGHT_GRAY, width=5)

    matrix = whiten(Image.open(FINAL / "01_factorial_design_grid_no_axis_titles.png"))
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

    outcome = (2080, 1975, 4320, 2225)
    draw.rounded_rectangle(outcome, radius=42, fill=PALE_TEAL, outline=TEAL, width=8)
    centered_text(
        draw,
        outcome,
        "Convergent evidence for FSPD?",
        font(82, True),
        NAVY,
    )

    behavioral_art = channel_art(FINAL / "03c_channel_behavioral.png")
    verbal_art = channel_art(FINAL / "03a_channel_verbal.png")
    cognitive_art = cognitive_channel_art(
        FINAL / "03b_channel_cognitive_large_legend.png"
    )

    banded_channel_box_tight(
        canvas,
        (70, 2270, 2080, 3210),
        "BEHAVIORAL",
        BEHAVIORAL,
        PALE_BLUE,
        behavioral_art,
    )
    banded_channel_box_tight(
        canvas,
        (2195, 2270, 4205, 3210),
        "VERBAL",
        VERBAL,
        PALE_RED,
        verbal_art,
    )
    banded_channel_box_tight(
        canvas,
        (4320, 2270, 6330, 3210),
        "COGNITIVE",
        COGNITIVE,
        PALE_PURPLE,
        cognitive_art,
    )

    output = FINAL / "17_overview_compact_banded_channels_v7.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
