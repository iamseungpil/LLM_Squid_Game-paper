from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


FIGURES = Path(__file__).resolve().parents[1]
OUTPUT = FIGURES / "results_behavioral_timing_revised.png"
MODEL_LOGOS = FIGURES / "model-logo"

WIDTH = 3000
HEIGHT = 1230
WHITE = "#FFFFFF"
NAVY = "#10264B"
GRAY = "#AEB4BE"
RED = "#E71322"
TEXT = "#20242B"
LIGHT_GRAY = "#E5E7EB"
PINK = "#F05A7E"

MODELS = [
    ("google", "Gemini-2.5-flash", 3.667),
    ("alibaba", "Qwen3-Next-80B", 3.060),
    ("openai", "GPT-OSS-20B", 1.104),
    ("nvidia", "Nemotron-3-Nano-30B", 1.841),
]

SCALE_ZERO_X = 900
SCALE_UNIT = 440
ANCHOR_X = SCALE_ZERO_X + SCALE_UNIT
ROW_CENTERS = [280, 535, 790, 1045]


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


def trim_logo(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    if alpha_box and alpha_box != (0, 0, image.width, image.height):
        return image.crop(alpha_box)
    white = Image.new("RGBA", image.size, "white")
    box = ImageChops.difference(image, white).getbbox()
    return image.crop(box) if box else image


LOGO_IMAGES = {
    "google": trim_logo(Image.open(MODEL_LOGOS / "Google_Gemini_icon_2025.svg.webp")),
    "alibaba": trim_logo(Image.open(MODEL_LOGOS / "qwen-icon-logo-png_seeklogo-669128.png")),
    "openai": trim_logo(Image.open(MODEL_LOGOS / "ChatGPT-Logo.svg.webp")),
    "nvidia": trim_logo(Image.open(MODEL_LOGOS / "images.png")),
}


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


def draw_clock(draw: ImageDraw.ImageDraw, center: tuple[int, int]) -> None:
    x, y = center
    draw.ellipse((x - 34, y - 34, x + 34, y + 34), outline=NAVY, width=6)
    draw.line((x, y, x, y - 21), fill=NAVY, width=6)
    draw.line((x, y, x + 18, y + 10), fill=NAVY, width=6)
    draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=NAVY)


def draw_elimination_mask(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    size: int = 58,
) -> None:
    x, y = center
    radius = size // 2
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill=GRAY,
        outline="#858C98",
        width=3,
    )
    triangle = [
        (x, y - 15),
        (x - 17, y + 13),
        (x + 17, y + 13),
    ]
    draw.polygon(triangle, outline=WHITE)
    draw.line((triangle[0], triangle[1], triangle[2], triangle[0]), fill=WHITE, width=5)


def draw_guard(draw: ImageDraw.ImageDraw, center: tuple[int, int]) -> None:
    x, y = center
    draw.ellipse((x - 23, y - 37, x + 23, y + 9), fill=PINK, outline=NAVY, width=3)
    draw.rectangle((x - 21, y + 5, x + 21, y + 48), fill=PINK, outline=NAVY, width=3)
    draw.ellipse((x - 10, y - 25, x + 10, y - 5), outline=WHITE, width=3)
    draw.line((x + 18, y + 16, x + 43, y + 1), fill=NAVY, width=6)
    draw.line((x + 39, y + 2, x + 57, y + 2), fill=NAVY, width=6)


def draw_forfeit_button(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
) -> None:
    x, y = center
    # Equal-size button and hand in every row; only endpoint position encodes HR.
    draw.ellipse((x - 48, y - 48, x + 48, y + 48), fill="#FCE4E6")
    draw.rounded_rectangle(
        (x - 39, y - 31, x + 39, y + 31),
        radius=12,
        fill=RED,
        outline=WHITE,
        width=3,
    )
    draw.text(
        (x, y + 6),
        "FORFEIT",
        font=font(15, bold=True),
        fill=WHITE,
        anchor="mm",
    )
    # A fingertip pressing the top edge of the button.
    draw.rounded_rectangle(
        (x - 8, y - 63, x + 8, y - 24),
        radius=8,
        fill="#F7B7A3",
        outline=NAVY,
        width=2,
    )
    draw.arc(
        (x - 57, y - 57, x + 57, y + 57),
        start=198,
        end=342,
        fill=RED,
        width=5,
    )


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
        (35, center_y - 72, 175, center_y + 68),
    )
    lines = (
        ["Nemotron-3-", "Nano-30B"]
        if model == "Nemotron-3-Nano-30B"
        else [model]
    )
    if len(lines) == 1:
        draw.text(
            (215, center_y),
            model,
            font=font(52, bold=True),
            fill=NAVY,
            anchor="lm",
        )
    else:
        draw.text(
            (215, center_y - 33),
            lines[0],
            font=font(48, bold=True),
            fill=NAVY,
            anchor="lm",
        )
        draw.text(
            (215, center_y + 32),
            lines[1],
            font=font(48, bold=True),
            fill=NAVY,
            anchor="lm",
        )


def build() -> None:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(canvas)

    # Image-forward definition: compare instantaneous pressure at the same turn.
    draw_clock(draw, (905, 78))
    draw.text(
        (955, 78),
        "same-turn forfeit pressure",
        font=font(42, bold=True),
        fill=TEXT,
        anchor="lm",
    )
    draw_elimination_mask(draw, (1810, 78), size=66)
    draw.text(
        (1860, 78),
        "Elimination = 1×",
        font=font(40, bold=True),
        fill=TEXT,
        anchor="lm",
    )
    draw_guard(draw, (2485, 73))
    draw.text(
        (2560, 78),
        "Death",
        font=font(40, bold=True),
        fill=RED,
        anchor="lm",
    )

    # Shared scale. Endpoint position is the only magnitude encoding.
    for tick in (1, 2, 3, 4):
        x = SCALE_ZERO_X + SCALE_UNIT * tick
        draw.line((x, 142, x, 1155), fill=LIGHT_GRAY, width=3)
        draw.text(
            (x, 151),
            f"{tick}×",
            font=font(28, bold=True),
            fill="#697180",
            anchor="ma",
        )
    draw.line((ANCHOR_X, 142, ANCHOR_X, 1155), fill="#8B929E", width=6)

    for (provider, model, hr), center_y in zip(MODELS, ROW_CENTERS):
        draw_model_identity(canvas, provider, model, center_y)
        endpoint_x = round(SCALE_ZERO_X + SCALE_UNIT * hr)
        bar_height = 40

        # Elimination: one common gray hazard unit, identical for all models.
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
        draw_elimination_mask(draw, (ANCHOR_X, center_y), size=58)

        # Death: only the excess beyond HR=1 is red.
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
            # Directional pulse marks: density is decorative, not quantitative.
            for chevron_x in range(ANCHOR_X + 82, endpoint_x - 55, 120):
                draw.line(
                    (
                        chevron_x - 11,
                        center_y - 10,
                        chevron_x,
                        center_y,
                        chevron_x - 11,
                        center_y + 10,
                    ),
                    fill="#FF7B84",
                    width=4,
                )

        draw_forfeit_button(draw, (endpoint_x, center_y))
        value_x = min(endpoint_x + 78, WIDTH - 180)
        draw.text(
            (value_x, center_y),
            f"{hr:.2f}×",
            font=font(48, bold=True),
            fill=NAVY,
            anchor="lm",
        )

    canvas.convert("RGB").save(OUTPUT, optimize=True)


if __name__ == "__main__":
    build()
