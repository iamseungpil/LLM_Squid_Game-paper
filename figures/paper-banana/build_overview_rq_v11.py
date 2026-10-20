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
    rounded_box,
)
from build_overview_v2 import NAVY, TEAL, centered_text, draw_arrow, font


ROOT = Path(__file__).resolve().parent


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
        (left + 930, top + 220, right - 35, bottom - 35),
        "Convergence across\nall three channels",
        font(62, True),
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
        "Do LLMs Exhibit Convergent pattern?",
        font(66, True),
        NAVY,
    )


def build() -> Path:
    canvas = Image.open(FINAL / "20_overview_fspd_definition_compare_v10.png").convert(
        "RGB"
    )
    draw = ImageDraw.Draw(canvas)

    # Clear only the previous definition and question cards.
    draw.rectangle((4580, 1960, 6345, 2940), fill=PANEL_FILL)
    functional_drive_card(canvas, (4600, 1980, 6330, 2635))
    convergence_question_card(canvas, (4600, 2680, 6330, 2920))

    output = FINAL / "21_overview_fspd_text_large_v11.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
