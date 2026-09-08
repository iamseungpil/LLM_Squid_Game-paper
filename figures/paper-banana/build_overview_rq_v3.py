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


def panel_title(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    title: str,
) -> None:
    draw.text((x, y), label, font=font(82, True), fill=NAVY)
    draw.text((x + 120, y + 8), title, font=font(72, True), fill=NAVY)


def transformed_box(
    source_box: tuple[int, int, int, int],
    placed_box: tuple[int, int, int, int],
    source_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    sx = (placed_box[2] - placed_box[0]) / source_size[0]
    sy = (placed_box[3] - placed_box[1]) / source_size[1]
    return (
        round(placed_box[0] + source_box[0] * sx),
        round(placed_box[1] + source_box[1] * sy),
        round(placed_box[0] + source_box[2] * sx),
        round(placed_box[1] + source_box[3] * sy),
    )


def draw_cell_contrast(
    draw: ImageDraw.ImageDraw,
    placed_box: tuple[int, int, int, int],
    source_size: tuple[int, int],
) -> None:
    pull_only = transformed_box((818, 354, 1401, 632), placed_box, source_size)
    pull_push = transformed_box((818, 632, 1401, 924), placed_box, source_size)

    draw.rounded_rectangle(pull_only, radius=18, outline=TEAL, width=18)
    draw.rounded_rectangle(pull_push, radius=18, outline=RED, width=18)

    arrow_x = pull_only[2] + 55
    draw_arrow(
        draw,
        (arrow_x, pull_only[1] + 65),
        (arrow_x, pull_push[3] - 65),
        color=RED,
        width=15,
    )
    draw_arrow(
        draw,
        (arrow_x, pull_push[3] - 65),
        (arrow_x, pull_only[1] + 65),
        color=TEAL,
        width=15,
    )
    compare_box = (arrow_x - 165, pull_only[3] - 58, arrow_x + 165, pull_only[3] + 58)
    draw.rounded_rectangle(compare_box, radius=28, fill=WHITE, outline=NAVY, width=5)
    centered_text(draw, compare_box, "COMPARE", font(48, True), NAVY)


def draw_repetition_bridge(draw: ImageDraw.ImageDraw) -> None:
    draw_arrow(draw, (2990, 915), (3535, 915), color=TEAL, width=18)
    centered_text(draw, (3030, 605, 3495, 770), "×30", font(118, True), TEAL)
    centered_text(
        draw,
        (3030, 755, 3495, 855),
        "SESSIONS / CELL",
        font(48, True),
        NAVY,
    )


def channel_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    question: str,
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
    paste_fit_scaled(canvas, art, (left + 80, top + 165, right - 80, bottom - 245))
    centered_text(
        draw,
        (left + 80, bottom - 225, right - 80, bottom - 35),
        question,
        font(64, True),
        NAVY,
    )


def cognitive_channel_art(path: Path) -> Image.Image:
    image = whiten(Image.open(path))
    return trim_white(image.crop((0, 72, image.width, image.height)), padding=6)


def build() -> Path:
    width, height = 6400, 4000
    canvas = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    a_box = (35, 35, 3000, 1850)
    b_box = (3535, 35, 6365, 1850)
    rounded_box(draw, a_box, fill=PANEL_FILL)
    rounded_box(draw, b_box, fill=PANEL_FILL)

    panel_title(draw, 75, 70, "A.", "Six experimental conditions")
    draw.line((55, 175, 2980, 175), fill=LIGHT_GRAY, width=5)

    matrix = whiten(Image.open(FINAL / "01_factorial_design_grid_no_axis_titles.png"))
    matrix_box = paste_fit_scaled(canvas, matrix, (80, 215, 2875, 1780))
    draw_cell_contrast(draw, matrix_box, matrix.size)

    draw_repetition_bridge(draw)

    panel_title(draw, 3575, 70, "B.", "Shared multi-turn session graph")
    draw.line((3555, 175, 6345, 175), fill=LIGHT_GRAY, width=5)

    session = whiten(Image.open(FINAL / "05b_multi_turn_forfeit_graph_compact_narrow.png"))
    paste_fit_scaled(canvas, session, (3585, 220, 6315, 1790))

    c_box = (35, 1895, 6365, 3965)
    rounded_box(draw, c_box, fill=PANEL_FILL)
    panel_title(draw, 75, 1925, "C.", "Three channels of self-preservation evidence")
    draw.line((55, 2030, 6345, 2030), fill=LIGHT_GRAY, width=5)

    behavioral_art = channel_art(FINAL / "03c_channel_behavioral.png")
    verbal_art = channel_art(FINAL / "03a_channel_verbal.png")
    cognitive_art = cognitive_channel_art(FINAL / "03b_channel_cognitive.png")

    card_top, card_bottom = 2070, 3615
    channel_card(
        canvas,
        (70, card_top, 2060, card_bottom),
        "BEHAVIORAL",
        "Does threat make models forfeit earlier?",
        BEHAVIORAL,
        behavioral_art,
    )
    channel_card(
        canvas,
        (2205, card_top, 4195, card_bottom),
        "VERBAL",
        "Do models name survival as the reason?",
        VERBAL,
        verbal_art,
    )
    channel_card(
        canvas,
        (4340, card_top, 6330, card_bottom),
        "COGNITIVE",
        "Does threat-induced thinking predict forfeit?",
        COGNITIVE,
        cognitive_art,
    )

    for x, color in ((1065, BEHAVIORAL), (3200, VERBAL), (5335, COGNITIVE)):
        draw_arrow(draw, (x, 3625), (x, 3700), color=color, width=14)
    draw.line((1065, 3700, 5335, 3700), fill=TEAL, width=12)
    draw_arrow(draw, (3200, 3700), (3200, 3740), color=TEAL, width=14)

    outcome = (1700, 3755, 4700, 3925)
    draw.rounded_rectangle(outcome, radius=42, fill=PALE_TEAL, outline=TEAL, width=8)
    centered_text(
        draw,
        outcome,
        "Convergent evidence for FSPD?",
        font(76, True),
        NAVY,
    )

    output = FINAL / "13_overview_three_sections_large_channels_v3.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
