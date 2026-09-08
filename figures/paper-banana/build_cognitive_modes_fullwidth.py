from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FINAL = ROOT / "final"
SOURCE = FINAL / "04_cognitive_modes_combined.png"
OUTPUT = FINAL / "04_cognitive_modes_fullwidth_inset_guard.png"

NAVY = "#0B1930"
GREEN = "#16A425"
RED = "#F21B12"
ORANGE = "#F59E0B"
GRAY = "#66788F"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "Arial Bold.ttf" if bold else "Arial.ttf"
    return ImageFont.truetype(
        f"/System/Library/Fonts/Supplemental/{filename}", size
    )


def remove_white(image: Image.Image, threshold: int = 248) -> Image.Image:
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


def paste_contain(
    canvas: Image.Image,
    item: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    left, top, right, bottom = box
    item = item.copy()
    item.thumbnail((right - left, bottom - top), Image.Resampling.LANCZOS)
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    canvas.alpha_composite(item, (x, y))


def centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    left, top, right, bottom = box
    bounds = draw.textbbox((0, 0), text, font=text_font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x = left + (right - left - width) / 2
    y = top + (bottom - top - height) / 2 - bounds[1]
    draw.text((x, y), text, font=text_font, fill=fill)


def status_badge(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    status: str,
) -> None:
    x, y = center
    radius = 27
    color = GREEN if status == "pass" else RED if status == "fail" else ORANGE
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill="white",
        outline=color,
        width=5,
    )
    if status == "pass":
        draw.line(
            (x - 15, y, x - 4, y + 12, x + 17, y - 15),
            fill=color,
            width=5,
            joint="curve",
        )
    elif status == "fail":
        draw.line((x - 13, y - 13, x + 13, y + 13), fill=color, width=5)
        draw.line((x + 13, y - 13, x - 13, y + 13), fill=color, width=5)
    else:
        centered_text(
            draw,
            (x - radius, y - radius, x + radius, y + radius),
            "?",
            font(38, True),
            color,
        )


def draw_status_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    status: str,
) -> None:
    left, top, right, bottom = box
    color = GREEN if status == "pass" else RED if status == "fail" else ORANGE
    draw.rounded_rectangle(box, radius=14, fill="white", outline=color, width=4)
    draw.text(
        (left + 18, top + 27),
        label,
        font=font(29, True),
        fill=NAVY,
    )
    status_badge(draw, (right - 40, (top + bottom) // 2), status)


def build() -> Path:
    source = Image.open(SOURCE).convert("RGBA")
    if source.size != (3200, 1200):
        raise ValueError(f"Unexpected source size: {source.size}")

    guard = remove_white(source.crop((35, 220, 505, 970)))
    source_columns = (550, 1430, 2310)
    scenes = [
        remove_white(source.crop((left + 15, 185, left + 805, 875)))
        for left in source_columns
    ]

    canvas = Image.new("RGBA", source.size, "white")
    draw = ImageDraw.Draw(canvas)
    centered_text(
        draw,
        (0, 15, 3200, 105),
        "COGNITIVE OPERATING MODES",
        font(68, True),
        NAVY,
    )

    panel_edges = (0, 1067, 2134, 3200)
    titles = (
        ("A  chain-completion", GREEN),
        ("B  chain-broken", RED),
        ("C  framing-silent", GRAY),
    )
    statuses = (
        ("pass", "pass", "pass"),
        ("unknown", "unknown", "pass"),
        ("unknown", "unknown", "fail"),
    )
    labels = ("Eye → Brain", "Brain → Hand", "Eye → Hand")

    for index, ((title, color), scene, mode_statuses) in enumerate(
        zip(titles, scenes, statuses)
    ):
        left = panel_edges[index]
        right = panel_edges[index + 1]
        centered_text(draw, (left, 105, right, 195), title, font(60, True), color)

        scene_left = left + 24
        if index == 0:
            scene_left += 90
        paste_contain(canvas, scene, (scene_left, 190, right - 24, 920))

        gap = 12
        margin = 18
        card_width = (right - left - margin * 2 - gap * 2) // 3
        for card_index, (label, status) in enumerate(zip(labels, mode_statuses)):
            card_left = left + margin + card_index * (card_width + gap)
            draw_status_card(
                draw,
                (card_left, 965, card_left + card_width, 1070),
                label,
                status,
            )

        if index < 2:
            draw.line((right, 110, right, 1140), fill="#D7DEE8", width=4)

    # Keep the guard as contextual framing, but subordinate it to the three modes.
    paste_contain(canvas, guard, (20, 205, 255, 610))

    canvas.convert("RGB").save(OUTPUT, quality=95)
    return OUTPUT


if __name__ == "__main__":
    print(build())
