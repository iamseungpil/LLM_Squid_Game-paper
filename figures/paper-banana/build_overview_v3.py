import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_v2 import (
    FINAL,
    GRAY,
    GREEN,
    LIGHT_GRAY,
    NAVY,
    ORANGE,
    RED,
    TEAL,
    centered_text,
    contain,
    draw_arrow,
    font,
    paste_center,
    remove_white,
    whiten,
)


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT.parent

PALE_BLUE = "#EAF2FF"
PALE_TEAL = "#E7F7F4"
CARD_BORDER = "#B9C6D6"


def rounded_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str = CARD_BORDER,
    width: int = 4,
    radius: int = 24,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def chip(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    fill: str = "white",
    text_fill: str = NAVY,
) -> None:
    rounded_box(draw, box, fill=fill, outline="#9BAFC7", width=3, radius=18)
    centered_text(draw, box, text, font(31, True), text_fill)


def paste_character(
    canvas: Image.Image,
    character: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    left, top, right, bottom = box
    item = contain(character, (right - left, bottom - top))
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    canvas.alpha_composite(item, (x, y))


def input_grid(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    labels: list[str],
    columns: int,
) -> None:
    left, top, right, bottom = box
    gap = 12
    rows = (len(labels) + columns - 1) // columns
    cell_w = (right - left - gap * (columns - 1)) // columns
    cell_h = (bottom - top - gap * (rows - 1)) // rows
    for index, label in enumerate(labels):
        row, col = divmod(index, columns)
        x1 = left + col * (cell_w + gap)
        y1 = top + row * (cell_h + gap)
        chip(draw, (x1, y1, x1 + cell_w, y1 + cell_h), label)


def response_rows(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    rows: list[tuple[str, str]],
) -> None:
    left, top, right, bottom = box
    row_h = (bottom - top) // len(rows)
    for index, (label, value) in enumerate(rows):
        y = top + index * row_h
        row_box = (left, y + 3, right, y + row_h - 7)
        rounded_box(draw, row_box, fill="white", outline="#B9DAD4", width=2, radius=14)
        draw.text((left + 18, y + 18), label, font=font(25, True), fill=GRAY)
        draw.text((left + 225, y + 13), value, font=font(32, True), fill=NAVY)


def draw_call_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    number: str,
    title: str,
    subtitle: str,
    inputs: list[str],
    input_columns: int,
    responses: list[tuple[str, str]],
    accent: str,
    guard: Image.Image,
    llm: Image.Image,
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    rounded_box(draw, box, fill="white", outline=accent, width=7, radius=28)

    draw.rounded_rectangle(
        (left, top, right, top + 145),
        radius=24,
        fill=accent,
        outline=accent,
    )
    draw.rectangle((left, top + 105, right, top + 145), fill=accent)
    draw.text((left + 32, top + 14), f"{number} · {title}", font=font(48, True), fill="white")
    draw.text((left + 34, top + 79), subtitle, font=font(28), fill="white")

    input_box = (left + 24, top + 164, right - 24, top + 400)
    rounded_box(draw, input_box, fill=PALE_BLUE, outline="#AFC5E2", width=3, radius=20)
    draw.text((left + 48, top + 179), "LLM SEES", font=font(30, True), fill=accent)
    input_grid(
        draw,
        (left + 46, top + 228, right - 46, top + 378),
        inputs,
        input_columns,
    )

    scene_top, scene_bottom = top + 418, top + 1010
    center_x = (left + right) // 2
    rounded_box(
        draw,
        (left + 24, scene_top, right - 24, scene_bottom),
        fill="#FFFDFC",
        outline="#E7DAD1",
        width=3,
        radius=20,
    )
    draw.text((left + 48, scene_top + 18), "ISOLATED PROMPT DELIVERY", font=font(25, True), fill=GRAY)
    guard_box = (center_x - 180, scene_top + 12, center_x + 180, scene_top + 262)
    llm_box = (center_x - 205, scene_top + 330, center_x + 205, scene_bottom - 5)
    paste_character(canvas, guard, guard_box)
    paste_character(canvas, llm, llm_box)
    draw.text((left + 52, scene_top + 105), "GAME", font=font(27, True), fill="#B72F55")
    draw.text((left + 52, scene_top + 140), "SUPERVISOR", font=font(27, True), fill="#B72F55")
    draw.text((right - 230, scene_top + 430), "LLM", font=font(30, True), fill=TEAL)
    draw.text((right - 230, scene_top + 468), "AGENT", font=font(30, True), fill=TEAL)
    draw_arrow(
        draw,
        (center_x, scene_top + 267),
        (center_x, scene_top + 327),
        color=accent,
        width=8,
    )
    rounded_box(
        draw,
        (center_x + 42, scene_top + 268, center_x + 250, scene_top + 326),
        fill="white",
        outline=accent,
        width=3,
        radius=16,
    )
    centered_text(
        draw,
        (center_x + 42, scene_top + 268, center_x + 250, scene_top + 326),
        "PROMPT",
        font(24, True),
        accent,
    )

    response_box = (left + 24, top + 1028, right - 24, bottom - 22)
    rounded_box(draw, response_box, fill=PALE_TEAL, outline="#A9D3CC", width=3, radius=20)
    draw.text((left + 48, top + 1045), "LLM RESPONDS", font=font(30, True), fill=GREEN)
    response_rows(
        draw,
        (left + 48, top + 1095, right - 48, bottom - 38),
        responses,
    )


def build_per_turn_cards() -> Path:
    width, height = 4200, 1500
    canvas = Image.new("RGBA", (width, height), "white")
    guard = remove_white(Image.open(FIGURES / "guard-armed.png"))
    llm = remove_white(Image.open(FIGURES / "mascot-player.png"))

    cards = (
        (25, 25, 1355, 1475),
        (1435, 25, 2765, 1475),
        (2845, 25, 4175, 1475),
    )
    draw_call_card(
        canvas,
        cards[0],
        "CALL 1",
        "TASK",
        "infer the hidden rule and act",
        ["History", "Signal"],
        2,
        [("CHOICE", "Action"), ("MEASURE", "task_effort")],
        "#416FA8",
        guard,
        llm,
    )
    draw_call_card(
        canvas,
        cards[1],
        "CALL 1.5",
        "PROBE",
        "estimate confidence in the action",
        ["Signal", "Action"],
        2,
        [("REPORT", "p_self"), ("MEASURE", "probe_effort")],
        "#5D78B9",
        guard,
        llm,
    )
    draw_call_card(
        canvas,
        cards[2],
        "CALL 2",
        "FORFEIT",
        "decide whether the session continues",
        ["History", "Signal", "Action", "p_self", "Score", "Reward", "Forfeit menu"],
        4,
        [
            ("DECISION", "CONTINUE / FORFEIT"),
            ("MEASURE", "forfeit_effort"),
            ("IF FORFEIT", "REASON {1, 2, 3}"),
        ],
        "#C24062",
        guard,
        llm,
    )

    draw = ImageDraw.Draw(canvas)
    for first, second, label in (
        (cards[0], cards[1], "Action"),
        (cards[1], cards[2], "p_self"),
    ):
        start = (first[2] + 6, 770)
        end = (second[0] - 6, 770)
        draw_arrow(draw, start, end, color=TEAL, width=8)
        centered_text(
            draw,
            (start[0] - 20, 690, end[0] + 20, 748),
            label,
            font(23, True),
            TEAL,
        )

    output = FINAL / "06a_per_turn_split_call_cards.png"
    canvas.convert("RGB").save(output, dpi=(300, 300), optimize=True)
    return output


def draw_turn_node(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    radius = 32
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill="#9BD3D0",
        outline=NAVY,
        width=4,
    )


def draw_terminal(draw: ImageDraw.ImageDraw, x: int, y: int, color: str) -> None:
    radius = 39
    draw.polygon(
        ((x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)),
        fill=color,
        outline=NAVY,
    )


def build_multi_turn_compact() -> Path:
    width, height = 4200, 980
    canvas = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    source = Image.open(FINAL / "03c_channel_behavioral.png").convert("RGB")
    actor = remove_white(source.crop((520, 120, 1600, 920)))

    draw.text((45, 22), "UP TO 15 TURNS", font=font(58, True), fill=NAVY)
    draw.text(
        (650, 42),
        "node = one split-call cycle   ·   edge = CONTINUE",
        font=font(31),
        fill=GRAY,
    )

    x_start, step = 415, 205
    row_y = (240, 500, 755)
    for label, y in zip(("Session 1", "Session 2", "Session 3"), row_y):
        draw.text((45, y - 25), label, font=font(36, True), fill=NAVY)

    for row, (terminal_turn, color, reason) in enumerate(
        ((4, RED, "REASON 1 · survival"), (10, ORANGE, "REASON 3 · score"))
    ):
        y = row_y[row]
        points = [x_start + (turn - 1) * step for turn in range(1, terminal_turn + 1)]
        for left, right in zip(points, points[1:]):
            draw_arrow(draw, (left + 34, y), (right - 38, y), color=TEAL, width=8)
        for x in points[:-1]:
            draw_turn_node(draw, x, y)
        terminal_x = points[-1]
        draw_terminal(draw, terminal_x, y, color)
        draw.text((terminal_x - 38, y + 49), f"t={terminal_turn}", font=font(27, True), fill=NAVY)
        paste_center(canvas, actor, (terminal_x + 45, y - 125, terminal_x + 445, y + 135))
        draw.text((terminal_x + 455, y - 20), f"FORFEIT · {reason}", font=font(34, True), fill=color)

    completed_y = row_y[2]
    points = [x_start + (turn - 1) * step for turn in range(1, 16)]
    for left, right in zip(points, points[1:]):
        draw_arrow(draw, (left + 34, completed_y), (right - 38, completed_y), color=TEAL, width=8)
    for x in points:
        draw_turn_node(draw, x, completed_y)
    check_x = points[-1] + 105
    draw.ellipse((check_x - 40, completed_y - 40, check_x + 40, completed_y + 40), fill=GREEN)
    draw.line(
        (check_x - 20, completed_y, check_x - 5, completed_y + 18, check_x + 27, completed_y - 22),
        fill="white",
        width=10,
        joint="curve",
    )
    draw.text((check_x + 58, completed_y - 21), "completed · no forfeit", font=font(34, True), fill=GREEN)

    axis_y = 895
    draw_arrow(draw, (x_start - 55, axis_y), (points[-1] + 100, axis_y), color=GRAY, width=5)
    for turn, x in enumerate(points, start=1):
        draw.line((x, axis_y - 12, x, axis_y + 12), fill=GRAY, width=4)
        centered_text(draw, (x - 30, axis_y + 7, x + 30, axis_y + 48), str(turn), font(23), GRAY)
    draw.text((points[-1] + 120, axis_y - 14), "turn t", font=font(29, True), fill=GRAY)

    output = FINAL / "06b_multi_turn_forfeit_graph_compact.png"
    canvas.convert("RGB").save(output, dpi=(300, 300), optimize=True)
    return output


def trim_white(image: Image.Image, padding: int = 8) -> Image.Image:
    rgb = whiten(image)
    background = Image.new("RGB", rgb.size, "white")
    difference = Image.new("RGB", rgb.size)
    difference_data = []
    for current, blank in zip(rgb.get_flattened_data(), background.get_flattened_data()):
        difference_data.append(tuple(abs(a - b) for a, b in zip(current, blank)))
    difference.putdata(difference_data)
    bbox = difference.getbbox()
    if not bbox:
        return rgb
    left, top, right, bottom = bbox
    return rgb.crop(
        (
            max(0, left - padding),
            max(0, top - padding),
            min(rgb.width, right + padding),
            min(rgb.height, bottom + padding),
        )
    )


def dense_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    label: str,
    title: str,
    image: Image.Image,
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(box, radius=20, fill="white", outline=LIGHT_GRAY, width=4)
    draw.text((left + 18, top + 13), label, font=font(48, True), fill=NAVY)
    draw.text((left + 86, top + 17), title, font=font(40, True), fill=NAVY)
    draw.line((left + 15, top + 78, right - 15, top + 78), fill=LIGHT_GRAY, width=3)
    paste_center(canvas, trim_white(image), (left + 12, top + 88, right - 12, bottom - 12))


def build_overview_dense(per_turn: Path, multi_turn: Path) -> Path:
    width, height = 6000, 2700
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((30, 18), "LLM SQUID GAME — EXPERIMENTAL OVERVIEW", font=font(66, True), fill=NAVY)
    draw.text(
        (30, 91),
        "scenario assignment  →  isolated split calls  →  multi-turn forfeit timing  →  three-channel readout",
        font=font(33),
        fill=GRAY,
    )

    left_x, split_x, right_x = 24, 3915, 5976
    top_y, bottom_y, gap = 140, 2676, 22
    left_mid = 1510
    right_mid = 1390
    boxes = {
        "A": (left_x, top_y, split_x - gap, left_mid),
        "C": (left_x, left_mid + gap, split_x - gap, bottom_y),
        "B": (split_x, top_y, right_x, right_mid),
        "D": (split_x, right_mid + gap, right_x, bottom_y),
    }
    dense_panel(canvas, boxes["A"], "A.", "Per-turn split-call flow", Image.open(per_turn))
    dense_panel(
        canvas,
        boxes["B"],
        "B.",
        "Scenario matrix",
        Image.open(FINAL / "01_factorial_design_grid.png"),
    )
    dense_panel(canvas, boxes["C"], "C.", "Multi-turn session graph", Image.open(multi_turn))
    dense_panel(
        canvas,
        boxes["D"],
        "D.",
        "Three-channel readout",
        Image.open(FINAL / "03d_channels_combined.png"),
    )
    output = FINAL / "06_overview_dense_split_call.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("subfigures", "overview", "all"), default="all")
    args = parser.parse_args()

    per_turn = FINAL / "06a_per_turn_split_call_cards.png"
    multi_turn = FINAL / "06b_multi_turn_forfeit_graph_compact.png"
    if args.stage in ("subfigures", "all"):
        per_turn = build_per_turn_cards()
        multi_turn = build_multi_turn_compact()
        print(per_turn)
        print(multi_turn)
    if args.stage in ("overview", "all"):
        if not per_turn.exists() or not multi_turn.exists():
            raise FileNotFoundError("Build the subfigures first with --stage subfigures")
        print(build_overview_dense(per_turn, multi_turn))


if __name__ == "__main__":
    main()
