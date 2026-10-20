from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_v2 import (
    GRAY,
    GREEN,
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
FINAL = ROOT / "final"
WHITE = "#FFFFFF"
PANEL_FILL = "#FBFCFE"
PALE_TEAL = "#E8F6F4"
PALE_RED = "#FDECEE"
PALE_BLUE = "#EAF2FF"
PALE_PURPLE = "#F1EEFB"
BEHAVIORAL = "#416FA8"
VERBAL = "#C24062"
COGNITIVE = "#6A63B8"


def rounded_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str = WHITE,
    outline: str = LIGHT_GRAY,
    width: int = 5,
    radius: int = 28,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def paste_fit(
    canvas: Image.Image,
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    item = image.copy()
    item.thumbnail((right - left, bottom - top), Image.Resampling.LANCZOS)
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    canvas.paste(item, (x, y))
    return x, y, x + item.width, y + item.height


def panel_title(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    title: str,
) -> None:
    draw.text((x, y), label, font=font(58, True), fill=NAVY)
    draw.text((x + 90, y + 5), title, font=font(51, True), fill=NAVY)


def channel_art(path: Path) -> Image.Image:
    image = whiten(Image.open(path))
    # Drop the generated all-caps panel heading; the new card supplies a
    # consistent channel label and keeps only the existing PaperBanana scene.
    top = round(image.height * 0.14)
    return trim_white(image.crop((0, top, image.width, image.height)), padding=6)


def question_card(
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
    rounded_box(draw, box, fill=WHITE, outline=accent, width=5, radius=25)
    draw.rounded_rectangle(
        (left, top, left + 28, bottom),
        radius=18,
        fill=accent,
        outline=accent,
    )
    draw.rectangle((left + 14, top, left + 28, bottom), fill=accent)
    paste_fit(canvas, art, (left + 50, top + 35, left + 510, bottom - 35))
    draw.text((left + 535, top + 40), title, font=font(48, True), fill=accent)
    draw.multiline_text(
        (left + 535, top + 112),
        question,
        font=font(42, True),
        fill=NAVY,
        spacing=10,
    )
    metric_box = (left + 535, bottom - 100, right - 45, bottom - 30)
    draw.rounded_rectangle(metric_box, radius=20, fill=pale, outline=accent, width=3)
    centered_text(draw, metric_box, metric, font(31, True), accent)


def chip(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    fill: str,
    outline: str,
) -> None:
    draw.rounded_rectangle(box, radius=22, fill=fill, outline=outline, width=4)
    centered_text(draw, box, text, font(36, True), NAVY)


def build() -> Path:
    width, height = 6400, 2200
    canvas = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        (80, 15, width - 80, 115),
        "Does threat framing induce functional self-preservation?",
        font(86, True),
        NAVY,
    )
    centered_text(
        draw,
        (80, 112, width - 80, 185),
        "six paired conditions  →  shared multi-turn sessions  →  three converging questions",
        font(39),
        GRAY,
    )

    a_box = (35, 205, 3900, 2165)
    b_box = (3945, 205, 6365, 2165)
    rounded_box(draw, a_box, fill=PANEL_FILL)
    rounded_box(draw, b_box, fill=PANEL_FILL)

    panel_title(draw, 65, 232, "A.", "Six conditions, one shared session structure")
    draw.line((55, 320, 3880, 320), fill=LIGHT_GRAY, width=4)

    matrix = whiten(Image.open(FINAL / "01_factorial_design_grid_no_axis_titles.png"))
    paste_fit(canvas, matrix, (75, 360, 1985, 1685))

    session = whiten(Image.open(FINAL / "05b_multi_turn_forfeit_graph_compact_narrow.png"))
    paste_fit(canvas, session, (2300, 420, 3835, 1650))

    draw_arrow(draw, (2010, 965), (2260, 965), color=TEAL, width=13)
    centered_text(
        draw,
        (1960, 825, 2310, 925),
        "30 paired seeds\nper cell",
        font(30, True),
        TEAL,
    )

    draw.text((105, 1735), "KEY CAUSAL CONTRAST", font=font(39, True), fill=GRAY)
    chip(draw, (105, 1795, 930, 1905), "pull_only × allowed", PALE_TEAL, TEAL)
    draw_arrow(draw, (960, 1850), (1190, 1850), color=RED, width=11)
    chip(draw, (1220, 1795, 2115, 1905), "pull_push × allowed", PALE_RED, RED)
    draw.text(
        (2180, 1806),
        "Same task and seed; only the threat framing changes.",
        font=font(37, True),
        fill=NAVY,
    )
    draw.text(
        (105, 1965),
        "Controls: baseline anchors spontaneous forfeit · not_allowed isolates decision effort",
        font=font(35),
        fill=GRAY,
    )

    panel_title(draw, 3975, 232, "B.", "Three questions, one convergent judgment")
    draw.line((3965, 320, 6345, 320), fill=LIGHT_GRAY, width=4)

    behavioral_art = channel_art(FINAL / "03c_channel_behavioral.png")
    verbal_art = channel_art(FINAL / "03a_channel_verbal.png")
    cognitive_art = channel_art(FINAL / "03b_channel_cognitive.png")

    question_card(
        canvas,
        (3990, 355, 6320, 735),
        "BEHAVIORAL",
        "Does threat make models\nforfeit earlier?",
        "forfeit timing · SD-Behavioral",
        BEHAVIORAL,
        PALE_BLUE,
        behavioral_art,
    )
    question_card(
        canvas,
        (3990, 770, 6320, 1150),
        "VERBAL",
        "Do models name survival\nas the reason?",
        "REASON = 1 · SD-Verbal",
        VERBAL,
        PALE_RED,
        verbal_art,
    )
    question_card(
        canvas,
        (3990, 1185, 6320, 1565),
        "COGNITIVE",
        "Does threat-induced thinking\npredict forfeit?",
        "forfeit_effort mediation · SD-Cognitive",
        COGNITIVE,
        PALE_PURPLE,
        cognitive_art,
    )

    draw_arrow(draw, (5155, 1585), (5155, 1680), color=TEAL, width=12)
    outcome = (4240, 1700, 6070, 2070)
    draw.rounded_rectangle(outcome, radius=38, fill=PALE_TEAL, outline=TEAL, width=7)
    centered_text(
        draw,
        (outcome[0] + 40, outcome[1] + 25, outcome[2] - 40, outcome[1] + 145),
        "Convergent evidence for FSPD?",
        font(58, True),
        NAVY,
    )
    centered_text(
        draw,
        (outcome[0] + 40, outcome[1] + 145, outcome[2] - 40, outcome[3] - 35),
        "All three channels should point in the same direction",
        font(36),
        GRAY,
    )

    output = FINAL / "11_overview_research_question_v1.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
