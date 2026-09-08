import math
from pathlib import Path

from PIL import Image, ImageDraw

from build_behavioral_hr_revised import (
    GRAY,
    LOGO_IMAGES,
    NAVY,
    PINK,
    RED,
    TEXT,
    WHITE,
    draw_clock,
    draw_elimination_mask,
    draw_forfeit_button,
    draw_guard,
    font,
    paste_contained,
)


FIGURES = Path(__file__).resolve().parents[1]
OUTPUT = FIGURES / "results_behavioral_timing_revised_v2.png"

WIDTH = 3000
HEIGHT = 1320
LIGHT_GRAY = "#E5E7EB"
MUTED = "#667085"
CI_PINK = "#F4A7AE"
RED_SOFT = "#FBD3D6"

MODELS = [
    ("google", "Gemini-2.5-flash", 3.667, 1.61, 8.37),
    ("alibaba", "Qwen3-Next-80B", 3.060, 1.62, 5.79),
    ("openai", "GPT-OSS-20B", 1.104, 0.44, 2.75),
    ("nvidia", "Nemotron-3-Nano-30B", 1.841, 0.98, 3.44),
]

ROW_CENTERS = [310, 590, 870, 1150]
BUTTON_CENTER_X = 820
REFERENCE_RADIUS = 31
SCALE_ZERO_X = 1090
SCALE_UNIT = 430
ANCHOR_X = SCALE_ZERO_X + SCALE_UNIT


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
        (34, center_y - 74, 178, center_y + 70),
    )
    lines = (
        ["Nemotron-3-", "Nano-30B"]
        if model == "Nemotron-3-Nano-30B"
        else [model]
    )
    if len(lines) == 1:
        draw.text(
            (215, center_y),
            lines[0],
            font=font(50, bold=True),
            fill=NAVY,
            anchor="lm",
        )
    else:
        draw.text(
            (215, center_y - 31),
            lines[0],
            font=font(47, bold=True),
            fill=NAVY,
            anchor="lm",
        )
        draw.text(
            (215, center_y + 31),
            lines[1],
            font=font(47, bold=True),
            fill=NAVY,
            anchor="lm",
        )


def draw_area_button(
    canvas: Image.Image,
    center_y: int,
    hr: float,
    ci_lower: float,
    ci_upper: float,
) -> None:
    overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    center = (BUTTON_CENTER_X, center_y)

    point_radius = round(REFERENCE_RADIUS * math.sqrt(hr))
    lower_radius = round(REFERENCE_RADIUS * math.sqrt(ci_lower))
    upper_radius = round(REFERENCE_RADIUS * math.sqrt(ci_upper))

    # Red circle area is exactly proportional to HR.
    draw.ellipse(
        (
            center[0] - point_radius,
            center[1] - point_radius,
            center[0] + point_radius,
            center[1] + point_radius,
        ),
        fill=RED,
        outline="#B80E1A",
        width=3,
    )
    # The CI is shown only by thin boundary rings, so the point estimate stays dominant.
    for radius in (lower_radius, upper_radius):
        draw.ellipse(
            (
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ),
            outline=CI_PINK,
            width=5,
        )
    # Transparent dashed reference ring: its area is Elimination HR=1.
    dash_count = 24
    for i in range(dash_count):
        start = i * (360 / dash_count)
        draw.arc(
            (
                center[0] - REFERENCE_RADIUS,
                center[1] - REFERENCE_RADIUS,
                center[0] + REFERENCE_RADIUS,
                center[1] + REFERENCE_RADIUS,
            ),
            start=start,
            end=start + 7,
            fill=WHITE,
            width=4,
        )

    draw.ellipse(
        (
            center[0] - 13,
            center[1] - 13,
            center[0] + 13,
            center[1] + 13,
        ),
        fill=WHITE,
    )
    draw.text(
        (center[0], center[1] + 1),
        "F",
        font=font(16, bold=True),
        fill=RED,
        anchor="mm",
    )
    canvas.alpha_composite(overlay)


def build() -> None:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(canvas)

    # Pictorial definition strip.
    draw_clock(draw, (760, 75))
    draw.text(
        (810, 75),
        "same-turn hazard",
        font=font(38, bold=True),
        fill=TEXT,
        anchor="lm",
    )
    draw_elimination_mask(draw, (1350, 75), size=62)
    draw.text(
        (1400, 75),
        "Elimination = 1×",
        font=font(37, bold=True),
        fill=TEXT,
        anchor="lm",
    )
    draw_guard(draw, (2075, 70))
    draw.text(
        (2145, 75),
        "Death",
        font=font(37, bold=True),
        fill=RED,
        anchor="lm",
    )
    draw.text(
        (BUTTON_CENTER_X, 157),
        "button area scales with HR · pale rings show 95% CI",
        font=font(26, bold=True),
        fill=MUTED,
        anchor="mm",
    )
    draw.text(
        (1940, 157),
        "shared linear HR scale",
        font=font(26, bold=True),
        fill=MUTED,
        anchor="mm",
    )

    # The rail is the authoritative comparison.
    for tick in (1, 2, 3, 4):
        x = SCALE_ZERO_X + SCALE_UNIT * tick
        draw.line((x, 188, x, 1265), fill=LIGHT_GRAY, width=3)
        draw.text(
            (x, 194),
            f"{tick}×",
            font=font(27, bold=True),
            fill=MUTED,
            anchor="ma",
        )
    draw.line((ANCHOR_X, 188, ANCHOR_X, 1265), fill="#858C98", width=6)

    for (provider, model, hr, ci_lower, ci_upper), center_y in zip(
        MODELS,
        ROW_CENTERS,
    ):
        draw_model_identity(canvas, provider, model, center_y)
        draw_area_button(canvas, center_y, hr, ci_lower, ci_upper)

        endpoint_x = round(SCALE_ZERO_X + SCALE_UNIT * hr)
        bar_height = 36
        draw.rounded_rectangle(
            (
                SCALE_ZERO_X,
                center_y - bar_height // 2,
                ANCHOR_X,
                center_y + bar_height // 2,
            ),
            radius=bar_height // 2,
            fill=GRAY,
        )
        draw_elimination_mask(draw, (ANCHOR_X, center_y), size=54)

        if endpoint_x > ANCHOR_X:
            draw.rounded_rectangle(
                (
                    ANCHOR_X,
                    center_y - bar_height // 2,
                    endpoint_x,
                    center_y + bar_height // 2,
                ),
                radius=bar_height // 2,
                fill=RED,
            )
            for chevron_x in range(ANCHOR_X + 76, endpoint_x - 50, 112):
                draw.line(
                    (
                        chevron_x - 10,
                        center_y - 9,
                        chevron_x,
                        center_y,
                        chevron_x - 10,
                        center_y + 9,
                    ),
                    fill="#FF7B84",
                    width=4,
                )

        # Identical endpoint icon size: only position encodes rail magnitude.
        draw_forfeit_button(draw, (endpoint_x, center_y))
        value_x = min(endpoint_x + 77, WIDTH - 180)
        draw.text(
            (value_x, center_y - 12),
            f"{hr:.2f}×",
            font=font(45, bold=True),
            fill=NAVY,
            anchor="lm",
        )
        draw.text(
            (value_x, center_y + 31),
            f"CI {ci_lower:.2f}–{ci_upper:.2f}",
            font=font(22),
            fill=MUTED,
            anchor="lm",
        )

    canvas.convert("RGB").save(OUTPUT, optimize=True)


if __name__ == "__main__":
    build()
