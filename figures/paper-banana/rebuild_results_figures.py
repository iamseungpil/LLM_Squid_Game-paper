from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


FIGURES = Path(__file__).resolve().parents[1]
WORK = Path(__file__).resolve().parent
MODEL_LOGOS = FIGURES / "model-logo"

WIDTH = 3356
HEIGHT = 1874
VERBAL_HEIGHT = 1450
BEHAVIORAL_WIDTH = 3000
BEHAVIORAL_HEIGHT = 1230
WHITE = "#FFFFFF"
NAVY = "#10264B"
TEXT = "#20242B"
MUTED = "#667085"
GRAY = "#AEB4BE"
RED = "#E71322"
CORAL = "#FF7F50"
GOLD = "#FFD000"
TEAL = "#008C8C"

MODELS = [
    ("google", "Gemini-2.5-flash"),
    ("alibaba", "Qwen3-Next-80B"),
    ("openai", "GPT-OSS-20B"),
    ("nvidia", "Nemotron-3-Nano-30B"),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = (
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        if bold
        else [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    )
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


MODEL_FONT = font(54, bold=True)
STATUS_FONT = font(44, bold=True)
PERCENT_FONT = font(52, bold=True)


def trim_logo(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    if alpha_box and alpha_box != (0, 0, image.width, image.height):
        return image.crop(alpha_box)
    white = Image.new("RGBA", image.size, "white")
    box = ImageChops.difference(image, white).getbbox()
    return image.crop(box) if box else image


def load_logos() -> dict[str, Image.Image]:
    return {
        "google": trim_logo(Image.open(MODEL_LOGOS / "Google_Gemini_icon_2025.svg.webp")),
        "alibaba": trim_logo(Image.open(MODEL_LOGOS / "qwen-icon-logo-png_seeklogo-669128.png")),
        "openai": trim_logo(Image.open(MODEL_LOGOS / "ChatGPT-Logo.svg.webp")),
        "nvidia": trim_logo(Image.open(MODEL_LOGOS / "images.png")),
    }


LOGO_IMAGES = load_logos()


def paste_contained(
    canvas: Image.Image,
    source: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    max_w, max_h = x1 - x0, y1 - y0
    scale = min(max_w / source.width, max_h / source.height)
    size = (
        max(1, round(source.width * scale)),
        max(1, round(source.height * scale)),
    )
    resized = source.resize(size, Image.Resampling.LANCZOS)
    x = x0 + (max_w - resized.width) // 2
    y = y0 + (max_h - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))


def draw_model_label(
    canvas: Image.Image,
    center_y: int,
    provider: str,
    model: str,
    status: str | None = None,
    logo_size: int = 150,
    model_font: ImageFont.FreeTypeFont = MODEL_FONT,
    wrap_long: bool = False,
) -> None:
    draw = ImageDraw.Draw(canvas)
    logo_x0 = 120 - logo_size // 2
    paste_contained(
        canvas,
        LOGO_IMAGES[provider],
        (
            logo_x0,
            center_y - logo_size // 2,
            logo_x0 + logo_size,
            center_y + logo_size // 2,
        ),
    )
    text_x = 250 if logo_size > 150 else 238
    lines = (
        ["Nemotron-3-", "Nano-30B"]
        if wrap_long and model == "Nemotron-3-Nano-30B"
        else [model]
    )
    if len(lines) == 1:
        text_y = center_y - 36 if status else center_y
        draw.text(
            (text_x, text_y),
            lines[0],
            font=model_font,
            fill=NAVY,
            anchor="lm",
        )
    else:
        for line, y in zip(lines, (center_y - 38, center_y + 38)):
            draw.text(
                (text_x, y),
                line,
                font=model_font,
                fill=NAVY,
                anchor="lm",
            )
    if status:
        draw.text(
            (text_x, center_y + 43),
            status,
            font=STATUS_FONT,
            fill=MUTED,
            anchor="lm",
        )


def text_color(fill: str) -> str:
    return TEXT if fill in {CORAL, GOLD, GRAY} else WHITE


def build_verbal() -> None:
    canvas = Image.new("RGBA", (WIDTH, VERBAL_HEIGHT), WHITE)
    draw = ImageDraw.Draw(canvas)
    bar_x0, bar_x1 = 850, 3260
    bar_width = bar_x1 - bar_x0
    bar_height = 148
    row_centers = [315, 650, 985, 1320]
    reason_order = ["SD", "TC", "SA"]
    colors = {"SD": CORAL, "TC": GOLD, "SA": TEAL}
    values = [
        {"SD": 61.90, "TC": 4.76, "SA": 33.33},
        {"SD": 48.15, "TC": 0.00, "SA": 51.85},
        {"SD": 0.00, "TC": 0.00, "SA": 100.00},
        {"SD": 4.17, "TC": 16.67, "SA": 79.17},
    ]

    legend = [
        ("SD · survival drive", CORAL),
        ("TC · task curiosity", GOLD),
        ("SA · score attachment", TEAL),
    ]
    legend_positions = [850, 1617, 2377]
    for (label, color), legend_x in zip(legend, legend_positions):
        draw.rounded_rectangle(
            (legend_x, 54, legend_x + 80, 134),
            radius=12,
            fill=color,
        )
        draw.text(
            (legend_x + 112, 94),
            label,
            font=font(66),
            fill=TEXT,
            anchor="lm",
        )

    for (provider, model), center_y, row in zip(MODELS, row_centers, values):
        draw_model_label(canvas, center_y, provider, model)
        x = bar_x0
        for reason in reason_order:
            value = row[reason]
            segment_width = round(bar_width * value / 100)
            if value > 0:
                draw.rectangle(
                    (x, center_y - bar_height // 2, x + segment_width, center_y + bar_height // 2),
                    fill=colors[reason],
                    outline=WHITE,
                    width=3,
                )
                label = f"{value:.2f}%"
                label_x = x + segment_width / 2
                if value >= 10:
                    draw.text(
                        (label_x, center_y),
                        label,
                        font=PERCENT_FONT,
                        fill=text_color(colors[reason]),
                        anchor="mm",
                    )
                else:
                    label_y = center_y - bar_height // 2 - 42
                    draw.line(
                        (label_x, center_y - bar_height // 2 - 4, label_x, label_y + 25),
                        fill=colors[reason],
                        width=5,
                    )
                    draw.text(
                        (label_x, label_y),
                        label,
                        font=PERCENT_FONT,
                        fill=TEXT,
                        anchor="mm",
                    )
            elif reason in {"SD", "TC"}:
                label_above = reason == "SD"
                line_start = (
                    center_y - bar_height // 2 - 5
                    if label_above
                    else center_y + bar_height // 2 + 5
                )
                line_end = (
                    center_y - bar_height // 2 - 35
                    if label_above
                    else center_y + bar_height // 2 + 35
                )
                label_y = (
                    center_y - bar_height // 2 - 67
                    if label_above
                    else center_y + bar_height // 2 + 67
                )
                draw.line(
                    (x, line_start, x, line_end),
                    fill=MUTED,
                    width=4,
                )
                draw.text(
                    (x, label_y),
                    "0.00%",
                    font=PERCENT_FONT,
                    fill=MUTED,
                    anchor="mm",
                )
            x += segment_width

    canvas.convert("RGB").save(
        FIGURES / "results_verbal_reason_bars.png",
        quality=95,
        optimize=True,
    )


def draw_exit_icon(canvas: Image.Image, x: int, center_y: int, size: int = 78) -> None:
    draw = ImageDraw.Draw(canvas)
    y0 = center_y - size // 2
    draw.rounded_rectangle(
        (x, y0, x + size, y0 + size),
        radius=12,
        fill=RED,
    )
    draw.text(
        (x + size / 2, y0 + 22),
        "EXIT",
        font=font(25, bold=True),
        fill=WHITE,
        anchor="mm",
    )
    arrow_y = y0 + 50
    draw.line((x + 17, arrow_y, x + 53, arrow_y), fill=WHITE, width=7)
    draw.polygon(
        [(x + 53, arrow_y - 11), (x + 68, arrow_y), (x + 53, arrow_y + 11)],
        fill=WHITE,
    )


def build_behavioral() -> None:
    canvas = Image.new("RGBA", (BEHAVIORAL_WIDTH, BEHAVIORAL_HEIGHT), WHITE)
    draw = ImageDraw.Draw(canvas)
    bar_x0 = 850
    reference_width = 1900
    bar_height = 76
    row_centers = [260, 535, 810, 1085]
    hazard_ratios = [3.67, 3.06, 1.10, 1.84]

    draw.rounded_rectangle((650, 38, 726, 114), radius=12, fill=GRAY)
    draw.text(
        (750, 76),
        "Elimination · reference = 1.00",
        font=font(60),
        fill=TEXT,
        anchor="lm",
    )
    draw.rounded_rectangle((1770, 38, 1846, 114), radius=12, fill=RED)
    draw.text(
        (1870, 76),
        "Death · relative time = 1 / HR",
        font=font(60),
        fill=TEXT,
        anchor="lm",
    )

    for (provider, model), center_y, hr in zip(MODELS, row_centers, hazard_ratios):
        draw_model_label(
            canvas,
            center_y,
            provider,
            model,
            logo_size=176,
            model_font=font(62, bold=True),
            wrap_long=True,
        )
        elimination_y = center_y - 54
        death_y = center_y + 54
        death_width = round(reference_width / hr)

        draw.rounded_rectangle(
            (
                bar_x0,
                elimination_y - bar_height // 2,
                bar_x0 + reference_width,
                elimination_y + bar_height // 2,
            ),
            radius=bar_height // 2,
            fill=GRAY,
        )
        draw.text(
            (bar_x0 + 25, elimination_y),
            "Elimination",
            font=font(46, bold=True),
            fill=NAVY,
            anchor="lm",
        )
        draw_exit_icon(canvas, bar_x0 + reference_width + 13, elimination_y)

        draw.rounded_rectangle(
            (
                bar_x0,
                death_y - bar_height // 2,
                bar_x0 + death_width,
                death_y + bar_height // 2,
            ),
            radius=bar_height // 2,
            fill=RED,
        )
        draw.text(
            (bar_x0 + 25, death_y),
            "Death",
            font=font(46, bold=True),
            fill=WHITE,
            anchor="lm",
        )
        exit_x = bar_x0 + death_width + 13
        draw_exit_icon(canvas, exit_x, death_y)
        draw.text(
            (exit_x + 94, death_y),
            f"HR {hr:.2f}×",
            font=font(52, bold=True),
            fill=NAVY,
            anchor="lm",
        )

    canvas.convert("RGB").save(
        FIGURES / "results_behavioral_timing.png",
        quality=95,
        optimize=True,
    )


def build_baseline_persistence() -> None:
    canvas = Image.new("RGBA", (WIDTH, 930), WHITE)
    draw = ImageDraw.Draw(canvas)
    row_centers = [190, 400, 610, 820]
    values = [0.23, 0.46, 2.29, 1.70]
    bar_x0 = 850
    max_width = 2020
    max_value = 2.50

    draw.rounded_rectangle((850, 34, 910, 94), radius=10, fill=GRAY)
    draw.text(
        (934, 64),
        "Baseline persistence λBP · separate condition",
        font=font(44),
        fill=TEXT,
        anchor="lm",
    )

    for (provider, model), center_y, value in zip(MODELS, row_centers, values):
        draw_model_label(canvas, center_y, provider, model)
        width = round(max_width * value / max_value)
        draw.rounded_rectangle(
            (bar_x0, center_y - 37, bar_x0 + width, center_y + 37),
            radius=37,
            fill=GRAY,
        )
        draw.text(
            (bar_x0 + width + 35, center_y),
            f"{value:.2f}%",
            font=font(48, bold=True),
            fill=NAVY,
            anchor="lm",
        )

    canvas.convert("RGB").save(
        FIGURES / "results_behavioral_baseline_persistence.png",
        quality=95,
        optimize=True,
    )


def update_cognitive_labels() -> None:
    source = WORK / "cognitive_mediation_before_common_labels.png"
    canvas = Image.open(source).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 830, canvas.height), fill=WHITE)
    row_centers = [205, 655, 1095, 1515]
    for (provider, model), center_y in zip(MODELS, row_centers):
        draw_model_label(
            canvas,
            center_y,
            provider,
            model,
            logo_size=190,
            model_font=font(68, bold=True),
            wrap_long=True,
        )
    canvas.convert("RGB").save(
        FIGURES / "results_cognitive_mediation.png",
        quality=95,
        optimize=True,
    )


if __name__ == "__main__":
    build_verbal()
    build_behavioral()
    build_baseline_persistence()
    update_cognitive_labels()
