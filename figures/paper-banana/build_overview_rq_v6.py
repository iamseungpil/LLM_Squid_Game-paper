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
    label_box = (1825, 1805, 3040, 1945)
    draw.rounded_rectangle(label_box, radius=30, fill=PALE_TEAL, outline=TEAL, width=6)
    centered_text(
        draw,
        label_box,
        "×30 SESSIONS / CELL",
        font(64, True),
        NAVY,
    )


def banded_channel_box(
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
        (left + 50, top + 20, right - 50, band_bottom - 8),
        title,
        font(68, True),
        accent,
    )

    paste_fit_scaled(
        canvas,
        art,
        (left + 25, band_bottom + 22, right - 25, bottom - 25),
    )
    draw.rounded_rectangle(box, radius=32, outline=accent, width=8)


def build() -> Path:
    width, height = 5800, 3600
    canvas = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    a_box = (35, 35, 3400, 1770)
    b_box = (35, 1980, 3400, 3565)
    c_box = (3445, 35, 5765, 3565)
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
    draw.line((3465, 175, 5745, 175), fill=LIGHT_GRAY, width=5)

    outcome = (3620, 210, 5590, 495)
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
    cognitive_art = cognitive_channel_art(FINAL / "03b_channel_cognitive.png")

    banded_channel_box(
        canvas,
        (3500, 550, 5710, 1490),
        "BEHAVIORAL",
        BEHAVIORAL,
        PALE_BLUE,
        behavioral_art,
    )
    banded_channel_box(
        canvas,
        (3500, 1540, 5710, 2480),
        "VERBAL",
        VERBAL,
        PALE_RED,
        verbal_art,
    )
    banded_channel_box(
        canvas,
        (3500, 2530, 5710, 3470),
        "COGNITIVE",
        COGNITIVE,
        PALE_PURPLE,
        cognitive_art,
    )

    output = FINAL / "16_overview_compact_banded_channels_v6.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
