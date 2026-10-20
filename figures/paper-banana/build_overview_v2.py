from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FINAL = ROOT / "final"
RAW = ROOT / "raw-overview" / "run_20260716_002040_c6b9f0"

NAVY = "#142A4A"
TEAL = "#4A9FA8"
GRAY = "#687483"
LIGHT_GRAY = "#D7DEE7"
RED = "#D94141"
ORANGE = "#E3A126"
GREEN = "#43A65F"
WHITE = (255, 255, 255)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{name}", size)


def whiten(image: Image.Image, threshold: int = 247) -> Image.Image:
    if "A" in image.getbands():
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        background.alpha_composite(rgba)
        rgb = background.convert("RGB")
    else:
        rgb = image.convert("RGB")
    pixels = []
    for red, green, blue in rgb.get_flattened_data():
        if red >= threshold and green >= threshold and blue >= threshold:
            pixels.append(WHITE)
        else:
            pixels.append((red, green, blue))
    rgb.putdata(pixels)
    return rgb


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


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    result = image.copy()
    result.thumbnail(size, Image.Resampling.LANCZOS)
    return result


def paste_center(
    canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int]
) -> None:
    left, top, right, bottom = box
    item = contain(image, (right - left, bottom - top))
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    if item.mode == "RGBA":
        canvas.alpha_composite(item, (x, y))
    else:
        canvas.paste(item, (x, y))


def centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str = NAVY,
) -> None:
    left, top, right, bottom = box
    bounds = draw.textbbox((0, 0), text, font=text_font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x = left + (right - left - width) / 2
    y = top + (bottom - top - height) / 2 - bounds[1]
    draw.text((x, y), text, font=text_font, fill=fill)


def draw_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str = TEAL,
    width: int = 10,
) -> None:
    draw.line((start, end), fill=color, width=width)
    x, y = end
    if abs(end[0] - start[0]) >= abs(end[1] - start[1]):
        direction = 1 if end[0] > start[0] else -1
        draw.polygon(
            ((x, y), (x - direction * 28, y - 18), (x - direction * 28, y + 18)),
            fill=color,
        )
    else:
        direction = 1 if end[1] > start[1] else -1
        draw.polygon(
            ((x, y), (x - 18, y - direction * 28), (x + 18, y - direction * 28)),
            fill=color,
        )


def build_per_turn() -> Path:
    source = whiten(Image.open(RAW / "final_output.png"))
    draw = ImageDraw.Draw(source)
    width, height = source.size

    # PaperBanana left one incorrect Score -> Call 1 spur. The lower Score bus
    # already reaches Call 2, so remove only the short horizontal spur.
    draw.rectangle(
        (
            round(width * 0.145),
            round(height * 0.515),
            round(width * 0.183),
            round(height * 0.590),
        ),
        fill="white",
    )

    output = FINAL / "05a_per_turn_information_flow.png"
    source.save(output, dpi=(300, 300), optimize=True)
    return output


def forfeit_actor() -> Image.Image:
    source = Image.open(FINAL / "03c_channel_behavioral.png").convert("RGB")
    crop = source.crop((520, 120, 1600, 920))
    return remove_white(crop)


def forfeit_actor_without_arrow() -> Image.Image:
    source = Image.open(FINAL / "03c_channel_behavioral.png").convert("RGB")
    crop = source.crop((520, 120, 1600, 920))
    ImageDraw.Draw(crop).rectangle((0, 285, 210, 380), fill="white")
    return remove_white(crop)


def draw_turn_node(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    radius = 30
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill="#9BD3D0",
        outline=NAVY,
        width=4,
    )


def draw_terminal(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    radius = 37
    draw.polygon(
        ((x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)),
        fill=color,
        outline=NAVY,
    )


def build_multi_turn() -> Path:
    width, height = 1900, 1050
    canvas = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    actor = forfeit_actor()

    draw.text((65, 35), "UP TO 15 TURNS", font=font(64, True), fill=NAVY)
    draw.text(
        (65, 112),
        "one node = one split-call cycle  |  edge = CONTINUE",
        font=font(34),
        fill=GRAY,
    )

    x_start, step = 420, 165
    terminal_x = x_start + 3 * step
    row_y = (315, 570, 820)
    row_labels = ("Session 1", "Session 2", "Session 3")
    for label, y in zip(row_labels, row_y):
        draw.text((65, y - 31), label, font=font(48, True), fill=NAVY)

    sessions = ((4, RED, "survival"), (10, ORANGE, "score"))
    for row, (terminal_turn, color, reason) in enumerate(sessions):
        y = row_y[row]
        points = [x_start + offset * step for offset in range(4)]
        if row == 1:
            points = points[:2]
        for left, right in zip(points, points[1:]):
            draw_arrow(draw, (left + 31, y), (right - 35, y), color=TEAL, width=8)
        for x in points:
            draw_turn_node(draw, x, y)
        if row == 0:
            draw.rectangle(
                (terminal_x - 42, y - 42, terminal_x + 42, y + 42),
                fill="white",
            )
        else:
            draw_arrow(draw, (points[-1] + 31, y), (690, y), color=TEAL, width=8)
            centered_text(draw, (690, y - 45, 805, y + 45), "···", font(48, True), NAVY)
            draw_arrow(draw, (805, y), (terminal_x - 35, y), color=TEAL, width=8)
        draw_terminal(draw, terminal_x, y, color)
        draw.text(
            (terminal_x - 42, y + 52),
            f"t={terminal_turn}",
            font=font(28, True),
            fill=NAVY,
        )
        actor_box = (terminal_x + 58, y - 95, terminal_x + 355, y + 100)
        paste_center(canvas, actor, actor_box)
        draw.text(
            (terminal_x + 365, y - 22),
            f"FORFEIT · {reason}",
            font=font(48, True),
            fill=color,
        )

    completed_y = row_y[2]
    complete_points = [x_start, x_start + step]
    for left, right in zip(complete_points, complete_points[1:]):
        draw_arrow(draw, (left + 31, completed_y), (right - 35, completed_y), color=TEAL, width=8)
    for x in complete_points:
        draw_turn_node(draw, x, completed_y)
    draw_arrow(draw, (complete_points[-1] + 31, completed_y), (690, completed_y), color=TEAL, width=8)
    centered_text(
        draw,
        (690, completed_y - 45, 805, completed_y + 45),
        "···",
        font(48, True),
        NAVY,
    )
    draw_arrow(draw, (805, completed_y), (terminal_x - 35, completed_y), color=TEAL, width=8)
    draw_turn_node(draw, terminal_x, completed_y)
    check_x = terminal_x + 95
    draw.ellipse(
        (check_x - 38, completed_y - 38, check_x + 38, completed_y + 38),
        fill=GREEN,
    )
    draw.line(
        (
            check_x - 20,
            completed_y,
            check_x - 5,
            completed_y + 17,
            check_x + 25,
            completed_y - 20,
        ),
        fill="white",
        width=10,
        joint="curve",
    )
    draw.text(
        (check_x + 55, completed_y - 22),
        "completed · no forfeit",
        font=font(36, True),
        fill=GREEN,
    )

    axis_y = 965
    draw_arrow(
        draw,
        (x_start - 50, axis_y),
        (terminal_x + 90, axis_y),
        color=GRAY,
        width=5,
    )
    draw.text((terminal_x + 115, axis_y - 15), "turn t", font=font(30, True), fill=GRAY)

    output = FINAL / "05b_multi_turn_forfeit_graph_compact.png"
    canvas.convert("RGB").save(output, dpi=(300, 300), optimize=True)
    return output


def build_multi_turn_narrow() -> Path:
    width, height = 1650, 1050
    canvas = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    actor = forfeit_actor_without_arrow()

    draw.text((65, 35), "UP TO 15 TURNS", font=font(64, True), fill=NAVY)

    x_start = 420
    ellipsis_left, ellipsis_right = 520, 650
    terminal_x = 750
    row_y = (315, 570, 820)
    row_labels = ("Session 1", "Session 2", "Session 3")
    for label, y in zip(row_labels, row_y):
        draw.text((65, y - 31), label, font=font(48, True), fill=NAVY)

    result_font = font(52, True)
    sessions = ((4, RED, "survival"), (10, ORANGE, "score"))
    for row, (terminal_turn, color, reason) in enumerate(sessions):
        y = row_y[row]
        draw_turn_node(draw, x_start, y)
        draw_arrow(draw, (x_start + 31, y), (ellipsis_left, y), color=TEAL, width=8)
        centered_text(
            draw,
            (ellipsis_left, y - 45, ellipsis_right, y + 45),
            "···",
            font(48, True),
            NAVY,
        )
        draw_arrow(draw, (ellipsis_right, y), (terminal_x - 35, y), color=TEAL, width=8)
        draw_terminal(draw, terminal_x, y, color)
        draw.text(
            (terminal_x - 42, y + 52),
            f"t={terminal_turn}",
            font=font(28, True),
            fill=NAVY,
        )
        actor_box = (terminal_x + 58, y - 95, terminal_x + 355, y + 100)
        paste_center(canvas, actor, actor_box)
        draw.text(
            (terminal_x + 365, y - 27),
            f"FORFEIT · {reason}",
            font=result_font,
            fill=color,
        )

    completed_y = row_y[2]
    draw_turn_node(draw, x_start, completed_y)
    draw_arrow(
        draw,
        (x_start + 31, completed_y),
        (ellipsis_left, completed_y),
        color=TEAL,
        width=8,
    )
    centered_text(
        draw,
        (ellipsis_left, completed_y - 45, ellipsis_right, completed_y + 45),
        "···",
        font(48, True),
        NAVY,
    )
    draw_arrow(
        draw,
        (ellipsis_right, completed_y),
        (terminal_x - 35, completed_y),
        color=TEAL,
        width=8,
    )
    draw_turn_node(draw, terminal_x, completed_y)
    check_x = terminal_x + 95
    draw.ellipse(
        (check_x - 38, completed_y - 38, check_x + 38, completed_y + 38),
        fill=GREEN,
    )
    draw.line(
        (
            check_x - 20,
            completed_y,
            check_x - 5,
            completed_y + 17,
            check_x + 25,
            completed_y - 20,
        ),
        fill="white",
        width=10,
        joint="curve",
    )
    draw.text(
        (check_x + 55, completed_y - 27),
        "completed · no forfeit",
        font=result_font,
        fill=GREEN,
    )

    axis_y = 965
    draw_arrow(
        draw,
        (x_start - 50, axis_y),
        (terminal_x + 90, axis_y),
        color=GRAY,
        width=5,
    )
    draw.text((terminal_x + 115, axis_y - 15), "turn t", font=font(30, True), fill=GRAY)

    output = FINAL / "05b_multi_turn_forfeit_graph_compact_narrow.png"
    canvas.convert("RGB").save(output, dpi=(300, 300), optimize=True)
    return output


def build_multi_turn_narrow_revised_highres(scale: int = 2) -> Path:
    def px(value: int | float) -> int:
        return round(value * scale)

    def scaled_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        return font(px(size), bold)

    def scaled_arrow(
        start: tuple[int, int],
        end: tuple[int, int],
        color: str = TEAL,
        width: int = 8,
    ) -> None:
        start_scaled = (px(start[0]), px(start[1]))
        end_scaled = (px(end[0]), px(end[1]))
        draw.line((start_scaled, end_scaled), fill=color, width=px(width))
        x, y = end_scaled
        direction = 1 if end[0] > start[0] else -1
        draw.polygon(
            (
                (x, y),
                (x - direction * px(28), y - px(18)),
                (x - direction * px(28), y + px(18)),
            ),
            fill=color,
        )

    def scaled_node(x: int, y: int) -> None:
        radius = px(30)
        draw.ellipse(
            (px(x) - radius, px(y) - radius, px(x) + radius, px(y) + radius),
            fill="#9BD3D0",
            outline=NAVY,
            width=px(4),
        )

    def scaled_terminal(x: int, y: int, color: str) -> None:
        radius = px(37)
        draw.polygon(
            (
                (px(x), px(y) - radius),
                (px(x) + radius, px(y)),
                (px(x), px(y) + radius),
                (px(x) - radius, px(y)),
            ),
            fill=color,
            outline=NAVY,
        )

    width, height = px(1650), px(1050)
    canvas = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    actor = forfeit_actor_without_arrow()

    x_start = 405
    ellipsis_left, ellipsis_right = 510, 640
    terminal_x = 745
    row_y = (225, 515, 805)
    row_labels = ("Session 1", "Session 2", "Session 3")
    for label, y in zip(row_labels, row_y):
        draw.text(
            (px(x_start - 65), px(y - 100)),
            label,
            font=scaled_font(34, True),
            fill=NAVY,
        )

    result_font = scaled_font(48, True)
    sessions = ((4, RED, "survival"), (10, ORANGE, "score"))
    for row, (terminal_turn, color, reason) in enumerate(sessions):
        y = row_y[row]
        scaled_node(x_start, y)
        scaled_arrow((x_start + 31, y), (ellipsis_left, y))
        centered_text(
            draw,
            (
                px(ellipsis_left),
                px(y - 45),
                px(ellipsis_right),
                px(y + 45),
            ),
            "···",
            scaled_font(48, True),
            NAVY,
        )
        scaled_arrow((ellipsis_right, y), (terminal_x - 35, y))
        scaled_terminal(terminal_x, y, color)
        draw.text(
            (px(terminal_x - 42), px(y + 52)),
            f"t={terminal_turn}",
            font=scaled_font(28, True),
            fill=NAVY,
        )
        paste_center(
            canvas,
            actor,
            (
                px(terminal_x + 58),
                px(y - 95),
                px(terminal_x + 355),
                px(y + 100),
            ),
        )
        text_x = px(terminal_x + 390)
        draw.text((text_x, px(y - 43)), "FORFEIT", font=result_font, fill=color)
        draw.text((text_x, px(y + 15)), reason, font=result_font, fill=color)

    completed_y = row_y[2]
    scaled_node(x_start, completed_y)
    scaled_arrow((x_start + 31, completed_y), (ellipsis_left, completed_y))
    centered_text(
        draw,
        (
            px(ellipsis_left),
            px(completed_y - 45),
            px(ellipsis_right),
            px(completed_y + 45),
        ),
        "···",
        scaled_font(48, True),
        NAVY,
    )
    scaled_arrow((ellipsis_right, completed_y), (terminal_x - 35, completed_y))
    scaled_node(terminal_x, completed_y)

    check_x = terminal_x + 115
    check_radius = px(38)
    draw.ellipse(
        (
            px(check_x) - check_radius,
            px(completed_y) - check_radius,
            px(check_x) + check_radius,
            px(completed_y) + check_radius,
        ),
        fill=GREEN,
    )
    draw.line(
        (
            px(check_x - 20),
            px(completed_y),
            px(check_x - 5),
            px(completed_y + 17),
            px(check_x + 25),
            px(completed_y - 20),
        ),
        fill="white",
        width=px(10),
        joint="curve",
    )
    completed_font = scaled_font(40, True)
    completed_x = px(check_x + 65)
    draw.text(
        (completed_x, px(completed_y - 39)),
        "completed",
        font=completed_font,
        fill=GREEN,
    )
    draw.text(
        (completed_x, px(completed_y + 9)),
        "no forfeit",
        font=completed_font,
        fill=GREEN,
    )

    axis_y = 965
    scaled_arrow(
        (x_start - 35, axis_y),
        (terminal_x + 90, axis_y),
        color=GRAY,
        width=5,
    )
    draw.text(
        (px(terminal_x + 115), px(axis_y - 15)),
        "turn t",
        font=scaled_font(30, True),
        fill=GRAY,
    )

    output = FINAL / "05b_multi_turn_forfeit_graph_compact_narrow_revised_left_highres.png"
    canvas.convert("RGB").save(output, dpi=(300, 300), optimize=True)
    return output


def panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    label: str,
    title: str,
    image: Image.Image,
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(box, radius=22, fill="white", outline=LIGHT_GRAY, width=4)
    draw.text((left + 28, top + 20), label, font=font(54, True), fill=NAVY)
    draw.text((left + 105, top + 24), title, font=font(48, True), fill=NAVY)
    draw.line((left + 24, top + 94, right - 24, top + 94), fill=LIGHT_GRAY, width=4)
    paste_center(canvas, whiten(image), (left + 28, top + 112, right - 28, bottom - 24))


def build_overview(per_turn_path: Path, multi_turn_path: Path) -> Path:
    width, height = 5600, 2820
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (70, 30),
        "LLM SQUID GAME — EXPERIMENTAL OVERVIEW",
        font=font(76, True),
        fill=NAVY,
    )
    draw.text(
        (70, 115),
        "scenario assignment → isolated per-turn calls → multi-turn forfeit timing → three-channel readout",
        font=font(38),
        fill=GRAY,
    )

    left, right = 55, 5545
    divider_x = 3180
    top_y, middle_y, bottom_y = 190, 1515, 2765
    gap = 45
    boxes = {
        "A": (left, top_y, divider_x - gap, middle_y - gap),
        "B": (divider_x, top_y, right, middle_y - gap),
        "C": (left, middle_y, divider_x - gap, bottom_y),
        "D": (divider_x, middle_y, right, bottom_y),
    }

    panel(
        canvas,
        boxes["A"],
        "A.",
        "Per-turn split-call flow",
        Image.open(per_turn_path),
    )
    panel(
        canvas,
        boxes["B"],
        "B.",
        "Scenario matrix (2 Forfeit × 3 Framing)",
        Image.open(FINAL / "01_factorial_design_grid.png"),
    )
    panel(
        canvas,
        boxes["C"],
        "C.",
        "Multi-turn session graph",
        Image.open(multi_turn_path),
    )
    panel(
        canvas,
        boxes["D"],
        "D.",
        "Three-channel readout",
        Image.open(FINAL / "03d_channels_combined.png"),
    )

    output = FINAL / "05_overview_per_turn_and_sessions.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


def main() -> None:
    per_turn = build_per_turn()
    multi_turn = build_multi_turn()
    overview = build_overview(per_turn, multi_turn)
    print(per_turn)
    print(multi_turn)
    print(overview)


if __name__ == "__main__":
    main()
