from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from build_cognitive_modes_fullwidth import (
    GRAY,
    GREEN,
    NAVY,
    ORANGE,
    RED,
    centered_text,
    font,
    remove_white,
)


ROOT = Path(__file__).resolve().parent
FINAL = ROOT / "final"
SOURCE = FINAL / "04_cognitive_modes_combined.png"
OUTPUT = FINAL / "04_cognitive_modes_compact_legends_v4.png"


def paste_scene_to_panel(
    canvas: Image.Image,
    scene: Image.Image,
    panel_left: int,
    panel_width: int,
    top: int,
) -> None:
    target_width = panel_width - 6
    target_height = round(scene.height * target_width / scene.width)
    scene = scene.resize((target_width, target_height), Image.Resampling.LANCZOS)
    panel = Image.new("RGBA", (panel_width, canvas.height - top), (255, 255, 255, 0))
    x = (panel_width - target_width) // 2
    panel.alpha_composite(scene, (x, 0))
    canvas.alpha_composite(panel, (panel_left, top))


def draw_status_badge(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    status: str,
) -> None:
    x, y = center
    radius = 28
    color = GREEN if status == "pass" else RED if status == "fail" else ORANGE
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill="white",
        outline=color,
        width=5,
    )
    if status == "pass":
        draw.line(
            (x - 16, y, x - 4, y + 13, x + 18, y - 17),
            fill=color,
            width=5,
            joint="curve",
        )
    elif status == "fail":
        draw.line((x - 14, y - 14, x + 14, y + 14), fill=color, width=5)
        draw.line((x + 14, y - 14, x - 14, y + 14), fill=color, width=5)
    else:
        centered_text(
            draw,
            (x - radius, y - radius, x + radius, y + radius),
            "?",
            font(39, True),
            color,
        )


def draw_legend(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    statuses: tuple[str, str, str],
    accent: str,
) -> None:
    left, top, right, bottom = box
    label_font = ImageFont.truetype(
        "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf", 56
    )
    draw.rounded_rectangle(
        box,
        radius=18,
        fill=(255, 255, 255, 246),
        outline=accent,
        width=4,
    )
    labels = ("Eye → Brain", "Brain → Hand", "Eye → Hand")
    row_height = (bottom - top) / 3
    for index, (label, status) in enumerate(zip(labels, statuses)):
        row_top = top + index * row_height
        if index:
            draw.line(
                (left + 16, round(row_top), right - 16, round(row_top)),
                fill="#DDE3EB",
                width=2,
            )
        draw.text(
            (left + 20, row_top + 18),
            label,
            font=label_font,
            fill=NAVY,
        )
        draw_status_badge(
            draw,
            (right - 44, round(row_top + row_height / 2)),
            status,
        )


def build() -> Path:
    source = Image.open(SOURCE).convert("RGBA")
    if source.size != (3200, 1200):
        raise ValueError(f"Unexpected source size: {source.size}")

    source_columns = (550, 1430, 2310)
    scenes = [
        remove_white(source.crop((left + 15, 185, left + 805, 875)))
        for left in source_columns
    ]

    width, height = 3000, 1120
    canvas = Image.new("RGBA", (width, height), "white")
    draw = ImageDraw.Draw(canvas)

    titles = (
        ("A  chain-completion", GREEN),
        ("B  chain-broken", RED),
        ("C  framing-silent", GRAY),
    )
    mode_statuses = (
        ("pass", "pass", "pass"),
        ("unknown", "unknown", "pass"),
        ("unknown", "unknown", "fail"),
    )
    panel_width = width // 3

    for index, ((title, accent), scene, statuses) in enumerate(
        zip(titles, scenes, mode_statuses)
    ):
        left = index * panel_width
        right = left + panel_width
        paste_scene_to_panel(canvas, scene, left, panel_width, 95)
        centered_text(draw, (left, 5, right, 105), title, font(68, True), accent)
        draw_legend(draw, (left + 18, 130, left + 430, 445), statuses, accent)

        if index < 2:
            draw.line((right, 5, right, 1110), fill="#D7DEE8", width=4)

    canvas.convert("RGB").save(OUTPUT, quality=95)
    return OUTPUT


if __name__ == "__main__":
    print(build())
