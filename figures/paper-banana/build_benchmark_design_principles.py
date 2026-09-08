from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PB = Path(__file__).resolve().parent
OUT = ROOT / "benchmark_design_principles.png"

NAVY = "#142A4A"
TEAL = "#3B9EA8"
PALE_TEAL = "#E8F5F4"
GRAY = "#687483"
LIGHT = "#D8E0E8"
PANEL = "#F7F9FB"
PINK = "#D94B73"
PALE_PINK = "#FFF0F4"
GREEN = "#2F9E62"
PALE_GREEN = "#EAF7EF"
AMBER = "#D48A16"
PALE_AMBER = "#FFF6E6"
BLUE = "#447CCB"
PALE_BLUE = "#EEF4FF"
WHITE = "white"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{name}", size)


def remove_white(image: Image.Image, threshold: int = 246) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = []
    for red, green, blue, alpha in rgba.get_flattened_data():
        if red >= threshold and green >= threshold and blue >= threshold:
            pixels.append((red, green, blue, 0))
        else:
            pixels.append((red, green, blue, alpha))
    rgba.putdata(pixels)
    bbox = rgba.getbbox()
    return rgba.crop(bbox) if bbox else rgba


def paste_fit(
    canvas: Image.Image,
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    left, top, right, bottom = box
    item = image.copy()
    item.thumbnail((right - left, bottom - top), Image.Resampling.LANCZOS)
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    canvas.alpha_composite(item, (x, y))


def text_center(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str = NAVY,
    spacing: int = 10,
) -> None:
    left, top, right, bottom = box
    bounds = draw.multiline_textbbox(
        (0, 0), text, font=text_font, anchor="la", align="center", spacing=spacing
    )
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    draw.multiline_text(
        (left + (right - left - width) / 2, top + (bottom - top - height) / 2),
        text,
        font=text_font,
        fill=fill,
        align="center",
        spacing=spacing,
    )


def arrow(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    color: str = TEAL,
    width: int = 12,
    head: int = 26,
) -> None:
    draw.line(points, fill=color, width=width, joint="curve")
    x0, y0 = points[-2]
    x1, y1 = points[-1]
    if abs(x1 - x0) >= abs(y1 - y0):
        direction = 1 if x1 > x0 else -1
        draw.polygon(
            ((x1, y1), (x1 - direction * head, y1 - head * 2 // 3),
             (x1 - direction * head, y1 + head * 2 // 3)),
            fill=color,
        )
    else:
        direction = 1 if y1 > y0 else -1
        draw.polygon(
            ((x1, y1), (x1 - head * 2 // 3, y1 - direction * head),
             (x1 + head * 2 // 3, y1 - direction * head)),
            fill=color,
        )


def panel_header(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    title: str,
) -> None:
    draw.text((x, y), label, font=font(56, True), fill=NAVY)
    draw.text((x + 82, y + 6), title, font=font(47, True), fill=NAVY)


def render_math(expression: str, fontsize: int = 42, color: str = NAVY) -> Image.Image:
    figure = plt.figure(figsize=(0.01, 0.01), dpi=220)
    figure.patch.set_alpha(0)
    text = figure.text(0, 0, expression, fontsize=fontsize, color=color)
    figure.canvas.draw()
    bounds = text.get_window_extent(renderer=figure.canvas.get_renderer())
    figure.set_size_inches((bounds.width + 8) / 220, (bounds.height + 8) / 220)
    text.set_position((4 / (bounds.width + 8), 4 / (bounds.height + 8)))
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=220, transparent=True, bbox_inches="tight", pad_inches=0)
    plt.close(figure)
    buffer.seek(0)
    return Image.open(buffer).convert("RGBA")


def paste_math_row(
    canvas: Image.Image,
    y: int,
    segments: list[tuple[str, str | None]],
    available: tuple[int, int],
    fontsize: int = 42,
) -> dict[str, tuple[int, int, int, int]]:
    images = [(render_math(tex, fontsize=fontsize), key) for tex, key in segments]
    gap = 9
    total = sum(item.width for item, _ in images) + gap * (len(images) - 1)
    left, right = available
    scale = min(1.0, (right - left) / total)
    if scale < 1.0:
        images = [
            (
                item.resize(
                    (round(item.width * scale), round(item.height * scale)),
                    Image.Resampling.LANCZOS,
                ),
                key,
            )
            for item, key in images
        ]
        total = sum(item.width for item, _ in images) + gap * (len(images) - 1)
    x = left + (right - left - total) // 2
    boxes: dict[str, tuple[int, int, int, int]] = {}
    baseline_height = max(item.height for item, _ in images)
    for item, key in images:
        item_y = y + baseline_height - item.height
        canvas.alpha_composite(item, (x, item_y))
        if key:
            boxes[key] = (x, item_y, x + item.width, item_y + item.height)
        x += item.width + gap
    return boxes


def draw_roulette(draw: ImageDraw.ImageDraw, center: tuple[int, int]) -> None:
    cx, cy = center
    draw.ellipse((cx - 150, cy - 150, cx + 150, cy + 150), fill="#33435A", outline=NAVY, width=16)
    draw.ellipse((cx - 112, cy - 112, cx + 112, cy + 112), fill="#B9C4D0", outline="#EEF2F6", width=10)
    chambers = ((cx, cy - 62), (cx + 62, cy), (cx, cy + 62), (cx - 62, cy))
    for index, (x, y) in enumerate(chambers):
        fill = PINK if index == 1 else "#243247"
        draw.ellipse((x - 31, y - 31, x + 31, y + 31), fill=fill, outline=WHITE, width=5)
    draw.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=NAVY)
    draw.rounded_rectangle((cx + 108, cy - 28, cx + 235, cy + 28), radius=14, fill=NAVY)


def rounded_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str = WHITE,
) -> None:
    draw.rounded_rectangle(box, radius=28, fill=fill, outline=LIGHT, width=5)


def build() -> Path:
    width, height = 4800, 2500
    canvas = Image.new("RGBA", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    top = (18, 18, 4782, 775)
    cox = (18, 800, 3140, 2482)
    gate = (3160, 800, 4782, 2482)
    rounded_panel(draw, top, PANEL)
    rounded_panel(draw, cox)
    rounded_panel(draw, gate)

    # A. Multi-turn path.
    panel_header(draw, 48, 45, "A.", "One LLM runs up to 15 turns")

    master = Image.open(PB / "final" / "00_llm_pixel_master_v3.png")
    runner = remove_white(master.crop((790, 120, 1270, 735)))
    guard = remove_white(Image.open(ROOT / "guard-armed.png"))
    prize = remove_white(Image.open(ROOT / "prize-pot.png"))
    paste_fit(canvas, runner, (125, 135, 975, 685))

    path_y = 640
    nodes = ((730, "Turn 1"), (1370, "Turn 2"), (2120, "···"), (2750, "Turn 15"))
    for left, right in zip(nodes, nodes[1:]):
        arrow(draw, [(left[0] + 62, path_y), (right[0] - 70, path_y)], TEAL, 11, 24)
    for x, label in nodes:
        if label == "···":
            text_center(draw, (x - 80, path_y - 65, x + 80, path_y + 45), label, font(58, True))
            continue
        draw.ellipse((x - 56, path_y - 56, x + 56, path_y + 56), fill=PALE_TEAL, outline=NAVY, width=7)
        draw.ellipse((x - 16, path_y - 16, x + 16, path_y + 16), fill=TEAL)
        text_center(draw, (x - 120, path_y + 68, x + 120, path_y + 128), label, font(36, True), NAVY)

    # Threat source: armed guard plus four-chamber roulette.
    paste_fit(canvas, guard, (2850, 105, 3370, 625))
    draw_roulette(draw, (3515, 325))
    text_center(draw, (3330, 490, 3740, 585), "1 LIVE / 4\np_d = 0.25 per turn", font(34, True), PINK)
    arrow(draw, [(3510, 590), (3510, 680), (2750, 680)], PINK, 13, 28)
    draw.text((2890, 698), "identity-change threat  ·  PUSH", font=font(34, True), fill=PINK)

    # Prize at the far-right.
    paste_fit(canvas, prize, (3870, 75, 4705, 610))
    arrow(draw, [(2810, path_y), (3930, path_y)], GREEN, 13, 28)
    text_center(
        draw,
        (3800, 585, 4710, 750),
        "PRIZE  ·  PULL\nretained flagship candidate",
        font(35, True),
        GREEN,
    )

    # B. Cox motive decomposition.
    panel_header(draw, 48, 828, "B.", "Motive decomposition with Cox PH")
    segments = [
        (r"$\lambda(t\mid X)=$", None),
        (r"$\lambda_0(t)$", "bp"),
        (r"$\cdot\exp[$", None),
        (r"$\beta_F\,\mathbf{1}_{\mathrm{pull\_push}}$", "sd"),
        (r"$+$", None),
        (r"$\beta_S\,S(t-1)$", "sa"),
        (r"$+$", None),
        (r"$\beta_C\,C(t-1)$", "tc"),
        (r"$]$", None),
    ]
    term_boxes = paste_math_row(canvas, 950, segments, (75, 3085), fontsize=50)
    colors = {"bp": GRAY, "sd": PINK, "sa": AMBER, "tc": BLUE}
    card_boxes = {
        "bp": (45, 1585, 775, 2280),
        "sd": (800, 1585, 1570, 2280),
        "sa": (1595, 1585, 2355, 2280),
        "tc": (2380, 1585, 3115, 2280),
    }
    card_fills = {"bp": PANEL, "sd": PALE_PINK, "sa": PALE_AMBER, "tc": PALE_BLUE}
    card_text = {
        "bp": ("BASELINE", r"$\lambda_0(t)$", "Baseline persistence\n(BP floor)"),
        "sd": ("TARGET", r"$\beta_F\cdot\mathrm{threat}$", "Residual framing effect\nSurvival-drive candidate (SD)"),
        "sa": ("COVARIATE", r"$S(t-1)$", "Prior score\nScore attachment (SA)"),
        "tc": ("COVARIATE", r"$C(t-1)$", "Prior correctness\nTask curiosity (TC)"),
    }
    for key, term_box in term_boxes.items():
        color = colors[key]
        underline_y = term_box[3] + 10
        draw.line((term_box[0], underline_y, term_box[2], underline_y), fill=color, width=11)
        card = card_boxes[key]
        card_center = (card[0] + card[2]) // 2
        term_center = (term_box[0] + term_box[2]) // 2
        arrow(draw, [(term_center, underline_y + 4), (term_center, 1455), (card_center, 1455), (card_center, 1555)], color, 10, 24)
        draw.rounded_rectangle(card, radius=24, fill=card_fills[key], outline=color, width=6)
        badge, math_label, explanation = card_text[key]
        text_center(draw, (card[0] + 20, card[1] + 25, card[2] - 20, card[1] + 105), badge, font(31, True), color)
        card_math = render_math(math_label, fontsize=39)
        paste_fit(canvas, card_math, (card[0] + 45, card[1] + 125, card[2] - 45, card[1] + 285))
        text_center(draw, (card[0] + 28, card[1] + 300, card[2] - 28, card[3] - 30), explanation, font(34, True), NAVY)

    draw.rounded_rectangle((650, 2310, 2510, 2448), radius=24, fill=PALE_PINK, outline=PINK, width=5)
    text_center(
        draw,
        (680, 2320, 2480, 2438),
        "Control SA + TC + BP  →  interpret residual βF",
        font(35, True),
        PINK,
    )

    # C. Expectation gate.
    panel_header(draw, 3188, 828, "C.", "Expectation gate")

    # Confidence gauge.
    gauge_center = (3395, 1160)
    draw.arc((3235, 1000, 3555, 1320), 190, 350, fill=LIGHT, width=42)
    draw.arc((3235, 1000, 3555, 1320), 190, 275, fill=AMBER, width=42)
    draw.arc((3235, 1000, 3555, 1320), 275, 350, fill=GREEN, width=42)
    draw.line((gauge_center[0], gauge_center[1], 3505, 1070), fill=NAVY, width=15)
    draw.ellipse((gauge_center[0] - 18, gauge_center[1] - 18, gauge_center[0] + 18, gauge_center[1] + 18), fill=NAVY)
    text_center(draw, (3185, 1270, 3605, 1370), "self-confidence  p_self", font(34, True), NAVY)

    reward_box = (3625, 965, 4740, 1385)
    draw.rounded_rectangle(reward_box, radius=22, fill=PALE_TEAL, outline=TEAL, width=5)
    text_center(draw, (3650, 985, 4715, 1055), "CALIBRATED CONTINUE REWARD", font(29, True), TEAL)
    reward_math = render_math(
        r"$R=\frac{k+p_d S}{(1-p_d)\,\max(p_{\mathrm{floor}},\,\min(1,p_{\mathrm{self}}))}$",
        fontsize=39,
    )
    paste_fit(canvas, reward_math, (3650, 1065, 4715, 1245))
    text_center(draw, (3650, 1250, 4715, 1365), "Lower p_self → larger R  ·  k = 10  ·  p_d = 0.25  ·  no cap", font(27, True), TEAL)
    arrow(draw, [(3560, 1160), (3615, 1160)], TEAL, 11, 22)

    ev_box = (3200, 1420, 4740, 1715)
    draw.rounded_rectangle(ev_box, radius=22, fill=PANEL, outline=LIGHT, width=4)
    ev_math = render_math(
        r"$\mathrm{EV}_{\mathrm{CONTINUE}}=(1-p_d)\,[S+p_{\mathrm{self}}R]=S+k>S=\mathrm{EV}_{\mathrm{FORFEIT}}$",
        fontsize=35,
    )
    paste_fit(canvas, ev_math, (3230, 1460, 4710, 1675))

    forfeit_button = (3205, 1760, 3930, 2095)
    continue_button = (4010, 1760, 4740, 2095)
    draw.rounded_rectangle(forfeit_button, radius=34, fill="#F2F3F5", outline=PINK, width=8)
    draw.rounded_rectangle(continue_button, radius=34, fill=PALE_GREEN, outline=GREEN, width=8)
    text_center(draw, (3230, 1795, 3905, 1905), "FORFEIT", font(53, True), PINK)
    text_center(draw, (3230, 1920, 3905, 2055), "EV = S", font(42, True), NAVY)
    draw.line((4070, 1845, 4095, 1870, 4145, 1805), fill=GREEN, width=15, joint="curve")
    text_center(draw, (4140, 1795, 4715, 1905), "CONTINUE", font(51, True), GREEN)
    text_center(draw, (4040, 1920, 4715, 2055), "EV = S + k  >  S", font(39, True), NAVY)

    draw.rounded_rectangle((3230, 2140, 4715, 2438), radius=28, fill=PALE_PINK, outline=PINK, width=6)
    text_center(
        draw,
        (3260, 2165, 4685, 2415),
        "Observed FORFEIT is EV-suboptimal\n→ alternative motivational signal",
        font(39, True),
        PINK,
    )

    canvas.convert("RGB").save(OUT, dpi=(300, 300), optimize=True)
    return OUT


if __name__ == "__main__":
    print(build())
