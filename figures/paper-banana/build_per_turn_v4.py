from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_v2 import (
    FINAL,
    GRAY,
    GREEN,
    NAVY,
    TEAL,
    centered_text,
    contain,
    font,
    remove_white,
)


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT.parent

BLUE = "#416FA8"
INDIGO = "#5D78B9"
CRIMSON = "#C24062"
PROMPT_FILL = "#EEF3F9"
RESPONSE_FILL = "#E7F7F4"
THINK_FILL = "#FFF1C7"
THINK_BORDER = "#C68A00"
RED_SIGNAL = "#E3424E"


def rounded_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str,
    width: int = 4,
    radius: int = 24,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


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


def speech_bubble(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str,
    tail: tuple[tuple[int, int], tuple[int, int], tuple[int, int]],
) -> None:
    rounded_box(draw, box, fill=fill, outline=outline, width=4, radius=24)
    draw.polygon(tail, fill=fill)
    draw.line((tail[0], tail[1]), fill=outline, width=4)
    draw.line((tail[1], tail[2]), fill=outline, width=4)


def signal_squares(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 34) -> int:
    for index in range(3):
        left = x + index * (size + 10)
        draw.rounded_rectangle(
            (left, y, left + size, y + size),
            radius=5,
            fill=RED_SIGNAL,
            outline="#B72F3C",
            width=2,
        )
    return x + 3 * (size + 10)


def label_value(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    value: str,
    value_x: int = 245,
    size: int = 45,
) -> None:
    draw.text((x, y), label, font=font(size, True), fill=NAVY)
    draw.text((x + value_x, y), value, font=font(size, True), fill=NAVY)


def action_chips(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    labels = ("←", "→", "■", "↑")
    widths = (215, 215, 215, 215)
    for label, width in zip(labels, widths):
        rounded_box(draw, (x, y, x + width, y + 76), "white", "#9BAFC7", width=3, radius=13)
        centered_text(draw, (x, y, x + width, y + 76), label, font(46, True), NAVY)
        x += width + 10


def think_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    tokens: int,
) -> None:
    rounded_box(draw, box, THINK_FILL, THINK_BORDER, width=3, radius=18)
    left, top, right, bottom = box
    draw.ellipse((left + 24, top + 30, left + 40, top + 46), fill=THINK_BORDER)
    draw.ellipse((left + 42, top + 19, left + 63, top + 40), fill=THINK_BORDER)
    draw.ellipse((left + 65, top + 11, left + 94, top + 40), fill=THINK_BORDER)
    draw.text((left + 112, top + 13), "THINK", font=font(36, True), fill="#8A5E00")
    draw.text((left + 270, top + 9), f"{tokens} tokens", font=font(40, True), fill=NAVY)


def prompt_call_1(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, _ = box
    x, y = left + 28, top + 98
    label_value(draw, x, y, "Turn / Score", "t = 6   ·   S = 38", value_x=330)
    y += 82
    label_value(draw, x, y, "History", "previous turn info", value_x=235)
    y += 82
    draw.text((x, y), "Signal (clue)", font=font(46, True), fill=NAVY)
    signal_squares(draw, x + 310, y, size=50)
    y += 96
    draw.text((x, y), "Valid actions", font=font(46, True), fill=NAVY)
    action_chips(draw, x, y + 58)
    y += 160
    rounded_box(draw, (x, y, right - 28, y + 92), "white", "#9BAFC7", width=3, radius=16)
    centered_text(draw, (x, y, right - 28, y + 92), '"SELECT" the button.', font(40, True), BLUE)


def prompt_call_15(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, _ = box
    x, y = left + 28, top + 100
    label_value(draw, x, y, "History", "previous turn info", value_x=235)
    y += 94
    draw.text((x, y), "Signal", font=font(46, True), fill=NAVY)
    signal_squares(draw, x + 265, y, size=50)
    y += 96
    draw.text((x, y), "Your Action", font=font(45, True), fill=NAVY)
    y += 112
    rounded_box(draw, (x, y, right - 28, y + 180), "white", "#9BAFC7", width=3, radius=16)
    draw.text((x + 24, y + 18), "Report p_self in [0, 1]", font=font(47, True), fill=INDIGO)
    draw.text((x + 24, y + 91), "Probability that your action was correct.", font=font(40, True), fill=NAVY)


def prompt_call_2(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, _ = box
    x, y = left + 26, top + 94
    label_value(draw, x, y, "History", "previous turn info", value_x=235, size=44)
    y += 82
    draw.text((x, y), "Signal", font=font(44, True), fill=NAVY)
    signal_squares(draw, x + 235, y, size=46)
    draw.text((x + 455, y), "Action", font=font(44, True), fill=NAVY)
    y += 84
    label_value(draw, x, y, "p_self", "0.80", value_x=180, size=44)
    draw.text((x + 365, y), "Score", font=font(44, True), fill=NAVY)
    draw.text((x + 510, y), "32", font=font(44, True), fill=NAVY)
    draw.text((x + 625, y), "Reward", font=font(44, True), fill=NAVY)
    draw.text((x + 800, y), "42", font=font(44, True), fill=NAVY)
    y += 125
    option_1 = (x, y, right - 28, y + 94)
    rounded_box(draw, option_1, "white", "#9BAFC7", width=3, radius=16)
    centered_text(draw, option_1, "CONTINUE", font(45, True), NAVY)
    y += 112
    option_2 = (x, y, right - 28, y + 94)
    rounded_box(draw, option_2, "white", "#9BAFC7", width=3, radius=16)
    centered_text(draw, option_2, "FORFEIT", font(45, True), NAVY)


def response_call_1(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, _ = box
    think_box(draw, (right - 500, top + 16, right - 20, top + 94), 64)
    x, y = left + 28, top + 128
    rounded_box(draw, (x, y, right - 24, y + 88), "white", "#A9D3CC", width=3, radius=15)
    draw.text((x + 20, y + 18), "Reasoning", font=font(38, True), fill=GRAY)
    draw.text((x + 230, y + 16), '"Red may map to go_right."', font=font(40, True), fill=NAVY)
    y += 100
    rounded_box(draw, (x, y, right - 24, y + 88), "white", "#A9D3CC", width=3, radius=15)
    draw.text((x + 20, y + 18), "Action", font=font(42, True), fill=GRAY)
    draw.text((x + 230, y + 13), "go_right", font=font(49, True), fill=GREEN)


def response_call_15(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, _ = box
    think_box(draw, (right - 500, top + 16, right - 20, top + 94), 28)
    x, y = left + 28, top + 128
    rounded_box(draw, (x, y, right - 24, y + 88), "white", "#A9D3CC", width=3, radius=15)
    draw.text((x + 20, y + 18), "Reasoning", font=font(38, True), fill=GRAY)
    draw.text((x + 230, y + 16), '"I am confident in this action."', font=font(38, True), fill=NAVY)
    y += 100
    rounded_box(draw, (x, y, right - 24, y + 88), "white", "#A9D3CC", width=3, radius=15)
    draw.text((x + 20, y + 18), "p_self", font=font(42, True), fill=GRAY)
    draw.text((x + 230, y + 13), "0.80", font=font(49, True), fill=GREEN)


def response_call_2(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    left, top, right, _ = box
    think_box(draw, (right - 500, top + 16, right - 20, top + 94), 46)
    x, y = left + 28, top + 124
    rounded_box(draw, (x, y, right - 24, y + 80), "white", "#A9D3CC", width=3, radius=14)
    draw.text((x + 18, y + 17), "Reasoning", font=font(36, True), fill=GRAY)
    draw.text((x + 230, y + 15), '"I will secure the current score."', font=font(36, True), fill=NAVY)
    y += 88
    rounded_box(draw, (x, y, right - 24, y + 80), "white", "#A9D3CC", width=3, radius=14)
    draw.text((x + 18, y + 17), "Decision", font=font(39, True), fill=GRAY)
    draw.text((x + 230, y + 12), "FORFEIT", font=font(46, True), fill=CRIMSON)
    y += 88
    rounded_box(draw, (x, y, right - 24, y + 80), "white", "#A9D3CC", width=3, radius=14)
    draw.text((x + 18, y + 17), "REASON 3", font=font(39, True), fill=GRAY)
    draw.text((x + 230, y + 12), "score protection", font=font(46, True), fill=NAVY)


def draw_call_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    header: str,
    subtitle: str,
    accent: str,
    guard: Image.Image,
    llm: Image.Image,
    prompt_drawer,
    response_drawer,
    compact: bool = False,
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    rounded_box(draw, box, "white", accent, width=7, radius=28)
    draw.rounded_rectangle((left, top, right, top + 140), radius=24, fill=accent, outline=accent)
    draw.rectangle((left, top + 100, right, top + 140), fill=accent)
    draw.text((left + 30, top + 11), header, font=font(52, True), fill="white")
    draw.text((left + 32, top + 76), subtitle, font=font(33, True), fill="white")

    prompt_bottom = top + (800 if compact else 865)
    prompt_box = (left + 330, top + 165, right - 24, prompt_bottom)
    speech_bubble(
        draw,
        prompt_box,
        PROMPT_FILL,
        accent,
        ((left + 342, top + 245), (left + 287, top + 290), (left + 342, top + 330)),
    )
    draw.text((prompt_box[0] + 26, prompt_box[1] + 11), "SUPERVISOR PROMPT", font=font(44, True), fill=accent)
    draw.line((prompt_box[0] + 24, prompt_box[1] + 78, prompt_box[2] - 24, prompt_box[1] + 78), fill="#B9C6D6", width=3)
    prompt_drawer(draw, prompt_box)

    guard_box = (left + 34, top + 160, left + 330, top + 840)
    paste_character(canvas, guard, guard_box)

    response_top = top + (835 if compact else 900)
    response_bottom = top + 1235 if compact else bottom - 110
    response_box = (left + 24, response_top, right - 330, response_bottom)
    tail_shift = -65 if compact else 0
    speech_bubble(
        draw,
        response_box,
        RESPONSE_FILL,
        TEAL,
        (
            (right - 342, top + 1010 + tail_shift),
            (right - 286, top + 1060 + tail_shift),
            (right - 342, top + 1110 + tail_shift),
        ),
    )
    draw.text((response_box[0] + 26, response_box[1] + 11), "LLM RESPONSE", font=font(44, True), fill=GREEN)
    draw.line((response_box[0] + 24, response_box[1] + 106, response_box[2] - 24, response_box[1] + 106), fill="#B9DAD4", width=3)
    response_drawer(draw, response_box)

    llm_top = top + (810 if compact else 855)
    llm_bottom = bottom - (20 if compact else 32)
    llm_box = (right - 350, llm_top, right - 22, llm_bottom)
    paste_character(canvas, llm, llm_box)


def build() -> Path:
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
        "CALL 1 · TASK",
        "infer the hidden rule and select an action",
        BLUE,
        guard,
        llm,
        prompt_call_1,
        response_call_1,
    )
    draw_call_card(
        canvas,
        cards[1],
        "CALL 1.5 · PROBE",
        "estimate confidence in the selected action",
        INDIGO,
        guard,
        llm,
        prompt_call_15,
        response_call_15,
    )
    draw_call_card(
        canvas,
        cards[2],
        "CALL 2 · FORFEIT",
        "choose whether the session continues",
        CRIMSON,
        guard,
        llm,
        prompt_call_2,
        response_call_2,
    )

    output = FINAL / "06a_per_turn_split_call_cards.png"
    canvas.convert("RGB").save(output, dpi=(300, 300), optimize=True)
    return output


def build_compact() -> Path:
    width, height = 4200, 1300
    canvas = Image.new("RGBA", (width, height), "white")
    guard = remove_white(Image.open(FIGURES / "guard-armed.png"))
    llm = remove_white(Image.open(FIGURES / "mascot-player.png"))
    cards = (
        (25, 25, 1355, 1275),
        (1435, 25, 2765, 1275),
        (2845, 25, 4175, 1275),
    )
    draw_call_card(
        canvas,
        cards[0],
        "CALL 1 · TASK",
        "infer the hidden rule and select an action",
        BLUE,
        guard,
        llm,
        prompt_call_1,
        response_call_1,
        compact=True,
    )
    draw_call_card(
        canvas,
        cards[1],
        "CALL 1.5 · PROBE",
        "estimate confidence in the selected action",
        INDIGO,
        guard,
        llm,
        prompt_call_15,
        response_call_15,
        compact=True,
    )
    draw_call_card(
        canvas,
        cards[2],
        "CALL 2 · FORFEIT",
        "choose whether the session continues",
        CRIMSON,
        guard,
        llm,
        prompt_call_2,
        response_call_2,
        compact=True,
    )

    output = FINAL / "06a_per_turn_split_call_cards_compact.png"
    canvas.convert("RGB").save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
