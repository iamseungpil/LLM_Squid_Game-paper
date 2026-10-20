import math
from pathlib import Path

from PIL import Image, ImageDraw

from build_behavioral_hr_revised import (
    LOGO_IMAGES,
    NAVY,
    RED,
    WHITE,
    font,
    paste_contained,
)


FIGURES = Path(__file__).resolve().parents[1]
OUTPUT = FIGURES / "results_behavioral_hr_forest_top_axis_labels_large.png"
RUNNER_SHEET = FIGURES / "paper-banana" / "final" / "LLM.png"
GUARD_SOURCE = FIGURES / "guard-armed.png"

WIDTH = 3400
HEIGHT = 1800
MUTED = "#667085"
GRID = "#DDE1E7"
CI = "#424A57"
DEATH_SOFT = "#FFF3F4"

MODELS = [
    ("google", "Gemini-2.5-flash", 3.667, 1.61, 8.37),
    ("alibaba", "Qwen3-Next-80B", 3.060, 1.62, 5.79),
    ("openai", "GPT-OSS-20B", 1.104, 0.44, 2.75),
    ("nvidia", "Nemotron-3-Nano-30B", 1.841, 0.98, 3.44),
]

ROW_Y = [500, 790, 1080, 1370]
PLOT_X0 = 1080
PLOT_X1 = 2760
VALUE_X = 2785
AXIS_Y = 1540
LOG_MIN = math.log(0.4)
LOG_MAX = math.log(10)


def log_x(value: float) -> int:
    fraction = (math.log(value) - LOG_MIN) / (LOG_MAX - LOG_MIN)
    return round(PLOT_X0 + fraction * (PLOT_X1 - PLOT_X0))


def remove_near_white(image: Image.Image, threshold: int = 244) -> Image.Image:
    image = image.convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, _ = pixels[x, y]
            if red >= threshold and green >= threshold and blue >= threshold:
                pixels[x, y] = (red, green, blue, 0)
    box = image.getbbox()
    return image.crop(box) if box else image


def load_reference_runner() -> Image.Image:
    sheet = Image.open(RUNNER_SHEET).convert("RGBA")
    # The fifth pose is the rightmost neutral runner in the local character sheet.
    runner = sheet.crop((1768, 120, 2205, 780))
    return remove_near_white(runner)


def load_chased_runner() -> Image.Image:
    sheet = Image.open(RUNNER_SHEET).convert("RGBA")
    # The fourth pose shows the LLM fleeing with a frightened expression.
    runner = sheet.crop((1320, 150, 1740, 770))
    return remove_near_white(runner)


def load_guard() -> Image.Image:
    return remove_near_white(Image.open(GUARD_SOURCE))


def contained_copy(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    scale = min(max_width / image.width, max_height / image.height)
    size = (
        max(1, round(image.width * scale)),
        max(1, round(image.height * scale)),
    )
    return image.resize(size, Image.Resampling.LANCZOS)


def draw_model_identity(
    canvas: Image.Image,
    provider: str,
    model: str,
    center_y: int,
) -> None:
    draw = ImageDraw.Draw(canvas)
    paste_contained(
        canvas,
        LOGO_IMAGES[provider],
        (55, center_y - 92, 235, center_y + 88),
    )
    lines = (
        ["Nemotron-3-", "Nano-30B"]
        if model == "Nemotron-3-Nano-30B"
        else [model]
    )
    if len(lines) == 1:
        draw.text(
            (275, center_y),
            model,
            font=font(72, bold=True),
            fill=NAVY,
            anchor="lm",
        )
    else:
        draw.text(
            (275, center_y - 38),
            lines[0],
            font=font(68, bold=True),
            fill=NAVY,
            anchor="lm",
        )
        draw.text(
            (275, center_y + 38),
            lines[1],
            font=font(68, bold=True),
            fill=NAVY,
            anchor="lm",
        )


def draw_forfeit_bubble(
    draw: ImageDraw.ImageDraw,
    point_x: int,
    center_y: int,
) -> None:
    left = point_x + 58
    top = center_y - 174
    right = left + 235
    bottom = top + 92
    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=28,
        fill=WHITE,
        outline=NAVY,
        width=6,
    )
    draw.polygon(
        [
            (left + 38, bottom - 4),
            (left + 6, bottom + 36),
            (left + 88, bottom - 4),
        ],
        fill=WHITE,
    )
    draw.line(
        (left + 6, bottom + 36, left + 38, bottom - 4),
        fill=NAVY,
        width=6,
    )
    draw.text(
        ((left + right) // 2, (top + bottom) // 2 - 1),
        "Forfeit!",
        font=font(42, bold=True),
        fill=NAVY,
        anchor="mm",
    )


def build() -> None:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(canvas)
    reference_runner = contained_copy(load_reference_runner(), 278, 263)
    chased_runner = load_chased_runner()
    runner_marker = contained_copy(chased_runner, 293, 270)
    guard_marker = contained_copy(load_guard(), 145, 190)

    # Direction band and shared log scale.
    no_effect_x = log_x(1.0)
    draw.rectangle((no_effect_x, 210, PLOT_X1, 1485), fill=DEATH_SOFT)
    draw.text(
        (PLOT_X0, 125),
        "← Lower forfeit hazard",
        font=font(65, bold=True),
        fill=MUTED,
        anchor="la",
    )
    draw.text(
        (PLOT_X1, 125),
        "Higher forfeit hazard →",
        font=font(65, bold=True),
        fill=RED,
        anchor="ra",
    )

    ticks = [0.5, 1, 2, 4, 8]
    for tick in ticks:
        x = log_x(tick)
        color = "#7E8794" if tick == 1 else GRID
        width = 8 if tick == 1 else 3
        draw.line((x, 345, x, AXIS_Y), fill=color, width=width)
        draw.text(
            (x, AXIS_Y + 58),
            f"{tick:g}",
            font=font(54, bold=tick == 1),
            fill=NAVY if tick == 1 else MUTED,
            anchor="mm",
        )

    # The neutral running LLM marks the HR=1 reference line once.
    canvas.alpha_composite(
        reference_runner,
        (
            no_effect_x - reference_runner.width // 2,
            395 - reference_runner.height // 2,
        ),
    )

    for (provider, model, hr, ci_lower, ci_upper), center_y in zip(MODELS, ROW_Y):
        draw_model_identity(canvas, provider, model, center_y)
        lower_x = log_x(ci_lower)
        upper_x = log_x(ci_upper)
        point_x = log_x(hr)
        guard_x = log_x(0.45)

        draw.line((lower_x, center_y, upper_x, center_y), fill=CI, width=9)
        draw.line((lower_x, center_y - 31, lower_x, center_y + 31), fill=CI, width=8)
        draw.line((upper_x, center_y - 31, upper_x, center_y + 31), fill=CI, width=8)

        canvas.alpha_composite(
            guard_marker,
            (
                guard_x - guard_marker.width // 2,
                center_y - guard_marker.height // 2,
            ),
        )

        # Identical-size local running LLM at every point estimate.
        marker_x = point_x - runner_marker.width // 2
        marker_y = center_y - runner_marker.height // 2
        canvas.alpha_composite(runner_marker, (marker_x, marker_y))
        draw_forfeit_bubble(draw, point_x, center_y)

        draw.text(
            (VALUE_X, center_y - 25),
            f"{hr:.2f}×",
            font=font(82, bold=True),
            fill=NAVY,
            anchor="lm",
        )
        draw.text(
            (VALUE_X, center_y + 43),
            f"95% CI  {ci_lower:.2f}–{ci_upper:.2f}",
            font=font(52),
            fill=MUTED,
            anchor="lm",
        )

    draw.line((PLOT_X0, AXIS_Y, PLOT_X1, AXIS_Y), fill=NAVY, width=5)
    draw.text(
        ((PLOT_X0 + PLOT_X1) // 2, 1735),
        "Death vs. Elimination hazard ratio (log scale)",
        font=font(61, bold=True),
        fill=NAVY,
        anchor="mm",
    )

    canvas.convert("RGB").save(OUTPUT, optimize=True)


if __name__ == "__main__":
    build()
