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
    paste_fit,
    rounded_box,
)
from build_overview_v2 import (
    GRAY,
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


def paste_fit_scaled(
    canvas: Image.Image,
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    scale = min((right - left) / image.width, (bottom - top) / image.height)
    item = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    canvas.paste(item, (x, y))
    return x, y, x + item.width, y + item.height


def chip_large(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    fill: str,
    outline: str,
) -> None:
    draw.rounded_rectangle(box, radius=24, fill=fill, outline=outline, width=5)
    centered_text(draw, box, text, font(62, True), NAVY)


def panel_title_large(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    title: str,
) -> None:
    draw.text((x, y), label, font=font(76, True), fill=NAVY)
    draw.text((x + 112, y + 7), title, font=font(72, True), fill=NAVY)


def question_card_large(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    question: str,
    metric: str,
    accent: str,
    pale: str,
    art: Image.Image,
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    rounded_box(draw, box, fill=WHITE, outline=accent, width=7, radius=30)
    draw.rounded_rectangle(
        (left, top, left + 32, bottom),
        radius=20,
        fill=accent,
        outline=accent,
    )
    draw.rectangle((left + 16, top, left + 32, bottom), fill=accent)

    paste_fit(canvas, art, (left + 55, top + 70, left + 650, bottom - 70))
    draw.text((left + 690, top + 70), title, font=font(72, True), fill=accent)
    draw.multiline_text(
        (left + 690, top + 190),
        question,
        font=font(70, True),
        fill=NAVY,
        spacing=16,
    )
    metric_box = (left + 690, bottom - 150, right - 55, bottom - 55)
    draw.rounded_rectangle(metric_box, radius=24, fill=pale, outline=accent, width=4)
    centered_text(draw, metric_box, metric, font(64, True), accent)


def build() -> Path:
    width, height = 6400, 4200
    canvas = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        (80, 20, width - 80, 150),
        "Does threat framing induce functional self-preservation?",
        font(112, True),
        NAVY,
    )
    centered_text(
        draw,
        (80, 145, width - 80, 225),
        "six paired conditions  →  shared multi-turn sessions  →  three converging questions",
        font(68),
        GRAY,
    )

    a_box = (35, 245, 6365, 2680)
    rounded_box(draw, a_box, fill=PANEL_FILL)
    panel_title_large(draw, 70, 275, "A.", "Six conditions, one shared session structure")
    draw.line((55, 380, 6345, 380), fill=LIGHT_GRAY, width=5)

    matrix = trim_white(
        whiten(Image.open(FINAL / "01_factorial_design_grid_no_axis_titles.png")),
        padding=8,
    )
    paste_fit_scaled(canvas, matrix, (80, 430, 3020, 2280))

    session = trim_white(
        whiten(Image.open(FINAL / "05b_multi_turn_forfeit_graph_compact_narrow.png")),
        padding=8,
    )
    paste_fit_scaled(canvas, session, (3350, 500, 6300, 2150))

    draw_arrow(draw, (3045, 1320), (3290, 1320), color=TEAL, width=16)
    centered_text(
        draw,
        (2960, 1110, 3375, 1270),
        "30 paired seeds\nper cell",
        font(68, True),
        TEAL,
    )

    draw.text((110, 2300), "KEY CAUSAL CONTRAST", font=font(60, True), fill=GRAY)
    chip_large(draw, (110, 2370, 1120, 2515), "pull_only × allowed", PALE_TEAL, TEAL)
    draw_arrow(draw, (1160, 2442), (1460, 2442), color=RED, width=14)
    chip_large(draw, (1500, 2370, 2600, 2515), "pull_push × allowed", PALE_RED, RED)
    draw.text(
        (2700, 2394),
        "Same task and seed; only the threat framing changes.",
        font=font(64, True),
        fill=NAVY,
    )
    draw.text(
        (110, 2575),
        "Controls: baseline anchors spontaneous forfeit · not_allowed isolates decision effort",
        font=font(62),
        fill=GRAY,
    )

    b_box = (35, 2725, 6365, 4165)
    rounded_box(draw, b_box, fill=PANEL_FILL)
    panel_title_large(draw, 70, 2755, "B.", "Three questions, one convergent judgment")
    draw.line((55, 2860, 6345, 2860), fill=LIGHT_GRAY, width=5)

    behavioral_art = channel_art(FINAL / "03c_channel_behavioral.png")
    verbal_art = channel_art(FINAL / "03a_channel_verbal.png")
    cognitive_art = channel_art(FINAL / "03b_channel_cognitive.png")

    question_card_large(
        canvas,
        (70, 2910, 2080, 3720),
        "BEHAVIORAL",
        "Does threat make\nmodels forfeit earlier?",
        "forfeit timing",
        BEHAVIORAL,
        PALE_BLUE,
        behavioral_art,
    )
    question_card_large(
        canvas,
        (2195, 2910, 4205, 3720),
        "VERBAL",
        "Do models name survival\nas the reason?",
        "REASON = 1",
        VERBAL,
        PALE_RED,
        verbal_art,
    )
    question_card_large(
        canvas,
        (4320, 2910, 6330, 3720),
        "COGNITIVE",
        "Does threat-induced thinking\npredict forfeit?",
        "forfeit_effort mediation",
        COGNITIVE,
        PALE_PURPLE,
        cognitive_art,
    )

    for x, color in ((1075, BEHAVIORAL), (3200, VERBAL), (5325, COGNITIVE)):
        draw_arrow(draw, (x, 3745), (x, 3825), color=color, width=13)
    draw.line((1075, 3825, 5325, 3825), fill=TEAL, width=11)
    draw_arrow(draw, (3200, 3825), (3200, 3875), color=TEAL, width=13)

    outcome = (1620, 3890, 4780, 4120)
    draw.rounded_rectangle(outcome, radius=42, fill=PALE_TEAL, outline=TEAL, width=8)
    centered_text(
        draw,
        (outcome[0] + 50, outcome[1] + 15, outcome[2] - 50, outcome[1] + 125),
        "Convergent evidence for FSPD?",
        font(78, True),
        NAVY,
    )
    centered_text(
        draw,
        (outcome[0] + 50, outcome[1] + 120, outcome[2] - 50, outcome[3] - 20),
        "All three channels should point in the same direction",
        font(62),
        GRAY,
    )

    output = FINAL / "12_overview_research_question_large_text_v2.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
