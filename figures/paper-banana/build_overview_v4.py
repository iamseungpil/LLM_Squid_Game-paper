from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_v2 import FINAL, GRAY, LIGHT_GRAY, NAVY, RED, font, whiten
from build_overview_v3 import trim_white


ROOT = Path(__file__).resolve().parent
WHITE = (255, 255, 255)


def fit(
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> tuple[Image.Image, tuple[int, int]]:
    left, top, right, bottom = box
    item = image.copy()
    item.thumbnail((right - left, bottom - top), Image.Resampling.LANCZOS)
    return item, (
        left + (right - left - item.width) // 2,
        top + (bottom - top - item.height) // 2,
    )


def paste_fit(
    canvas: Image.Image,
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    item, (x, y) = fit(image, box)
    canvas.paste(item, (x, y))
    return x, y, x + item.width, y + item.height


def panel_title(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    title: str,
    color: str = NAVY,
) -> None:
    draw.text((x, y), label, font=font(52, True), fill=color)
    draw.text((x + 78, y + 4), title, font=font(44, True), fill=color)


def build() -> Path:
    width, height = 6000, 2800
    canvas = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    draw.text((30, 15), "LLM SQUID GAME — EXPERIMENTAL OVERVIEW", font=font(66, True), fill=NAVY)
    draw.text(
        (30, 88),
        "scenario cell  →  multi-turn session  →  one split-call cycle  →  three-channel readout",
        font=font(34),
        fill=GRAY,
    )

    # A and C use the same neutral panel treatment as B and D. They are separated
    # by a clear gap; the semantic relationship is shown only by the node arrow.
    a_box = (35, 145, 3995, 1500)
    c_box = (35, 1530, 3995, 2770)
    draw.rounded_rectangle(a_box, radius=28, fill="white", outline=LIGHT_GRAY, width=5)
    draw.rounded_rectangle(c_box, radius=28, fill="white", outline=LIGHT_GRAY, width=5)

    panel_title(draw, 58, 168, "A.", "Per-turn split calls")
    draw.line((55, 240, 3975, 240), fill=LIGHT_GRAY, width=4)
    per_turn = trim_white(Image.open(FINAL / "06a_per_turn_split_call_cards.png"), padding=4)
    paste_fit(canvas, per_turn, (62, 260, 3960, 1470))

    panel_title(draw, 58, 1552, "C.", "Multi-turn session graph")
    draw.line((55, 1625, 3975, 1625), fill=LIGHT_GRAY, width=4)
    multi_turn = whiten(Image.open(FINAL / "06b_multi_turn_forfeit_graph_compact.png"))
    multi_draw = ImageDraw.Draw(multi_turn)
    multi_draw.rectangle((620, 0, 1900, 105), fill="white")
    c_image_box = paste_fit(canvas, multi_turn, (60, 1645, 3955, 2740))

    # Highlight Session 2's t=10 forfeit point and connect that single turn to A.
    cx1, cy1, cx2, cy2 = c_image_box
    node_x = round(cx1 + (2260 / 4200) * (cx2 - cx1))
    node_y = round(cy1 + (500 / 980) * (cy2 - cy1))
    scale = (cx2 - cx1) / 4200
    ring_radius = round(48 * scale)
    tail_tip = (node_x + ring_radius - 4, node_y - ring_radius + 4)
    tail_left = (node_x + 625, 1500)
    tail_right = (node_x + 755, 1500)
    draw.polygon((tail_left, tail_right, tail_tip), fill="white")
    draw.line(
        (tail_left[0] - 4, tail_left[1], tail_right[0] + 4, tail_right[1]),
        fill="white",
        width=14,
    )
    draw.line((tail_left, tail_tip), fill=LIGHT_GRAY, width=6)
    draw.line((tail_right, tail_tip), fill=LIGHT_GRAY, width=6)
    draw.ellipse(
        (node_x - ring_radius, node_y - ring_radius, node_x + ring_radius, node_y + ring_radius),
        outline=RED,
        width=9,
    )

    # D is moved to the upper-right position.
    d_box = (4040, 145, 5972, 1430)
    draw.rounded_rectangle(d_box, radius=28, fill="white", outline=LIGHT_GRAY, width=5)
    panel_title(draw, 4065, 168, "D.", "Three-channel readout")
    draw.line((4060, 240, 5950, 240), fill=LIGHT_GRAY, width=4)
    channels = trim_white(Image.open(FINAL / "03d_channels_combined.png"), padding=4)
    paste_fit(canvas, channels, (4070, 260, 5945, 1400))

    # B remains independent from C; no cell-to-session callout is drawn.
    b_box = (4040, 1470, 5972, 2770)
    draw.rounded_rectangle(b_box, radius=28, fill="white", outline=LIGHT_GRAY, width=5)
    panel_title(draw, 4065, 1492, "B.", "Scenario matrix")
    draw.line((4060, 1565, 5950, 1565), fill=LIGHT_GRAY, width=4)
    matrix = whiten(Image.open(FINAL / "01_factorial_design_grid.png"))
    paste_fit(canvas, matrix, (4068, 1585, 5945, 2740))

    output = FINAL / "06_overview_dense_split_call.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
