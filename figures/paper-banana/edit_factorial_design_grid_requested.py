from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT.parent
FINAL = ROOT / "final"
SOURCE = FINAL / "01_factorial_design_grid_no_threat_label.png"
OUTPUT = FINAL / "01_factorial_design_grid_no_threat_label_edited.png"

NAVY = "#142A4A"
ARROW = "#55799D"
MINT_LEFT = (228, 247, 244)
MINT_RIGHT = (211, 240, 235)
SALMON_TOP = (255, 208, 195)
SALMON_BOTTOM = (255, 231, 225)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf", size
    )


def fill_horizontal_gradient(
    image: Image.Image,
    box: tuple[int, int, int, int],
    start: tuple[int, int, int],
    end: tuple[int, int, int],
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(image)
    span = max(1, right - left)
    for x in range(left, right + 1):
        weight = (x - left) / span
        color = tuple(round(a + (b - a) * weight) for a, b in zip(start, end))
        draw.line((x, top, x, bottom), fill=color)


def fill_vertical_gradient(
    image: Image.Image,
    box: tuple[int, int, int, int],
    start: tuple[int, int, int],
    end: tuple[int, int, int],
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(image)
    span = max(1, bottom - top)
    for y in range(top, bottom + 1):
        weight = (y - top) / span
        color = tuple(round(a + (b - a) * weight) for a, b in zip(start, end))
        draw.line((left, y, right, y), fill=color)


def centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    maximum_size: int,
) -> None:
    left, top, right, bottom = box
    text_font = font(maximum_size)
    while text_font.getlength(text) > right - left - 18:
        maximum_size -= 1
        text_font = font(maximum_size)
    bounds = draw.textbbox((0, 0), text, font=text_font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x = left + (right - left - width) / 2
    y = top + (bottom - top - height) / 2 - bounds[1]
    draw.text((x, y), text, font=text_font, fill=NAVY)


def remove_white(image: Image.Image, threshold: int = 242) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = []
    for red, green, blue, alpha in rgba.get_flattened_data():
        if red >= threshold and green >= threshold and blue >= threshold:
            pixels.append((red, green, blue, 0))
        else:
            pixels.append((red, green, blue, alpha))
    rgba.putdata(pixels)
    bounds = rgba.getbbox()
    return rgba.crop(bounds) if bounds else rgba


def keep_largest_component(image: Image.Image) -> Image.Image:
    """Keep the connected foreground object and discard detached effect marks."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    width, height = rgba.size
    pixels = alpha.load()
    visited = bytearray(width * height)
    largest: list[int] = []

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if visited[index] or pixels[x, y] == 0:
                continue
            component: list[int] = []
            stack = [index]
            visited[index] = 1
            while stack:
                current = stack.pop()
                component.append(current)
                current_x = current % width
                current_y = current // width
                for neighbor_x, neighbor_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if not (0 <= neighbor_x < width and 0 <= neighbor_y < height):
                        continue
                    neighbor = neighbor_y * width + neighbor_x
                    if visited[neighbor] or pixels[neighbor_x, neighbor_y] == 0:
                        continue
                    visited[neighbor] = 1
                    stack.append(neighbor)
            if len(component) > len(largest):
                largest = component

    mask = bytearray(width * height)
    for index in largest:
        mask[index] = 255
    rgba.putalpha(Image.frombytes("L", (width, height), bytes(mask)))
    bounds = rgba.getbbox()
    return rgba.crop(bounds) if bounds else rgba


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    result = image.copy()
    result.thumbnail(size, Image.Resampling.LANCZOS)
    return result


def paste_center(
    canvas: Image.Image,
    item: Image.Image,
    box: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    fitted = contain(item, (right - left, bottom - top))
    x = left + (right - left - fitted.width) // 2
    y = top + (bottom - top - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))
    return x, y, x + fitted.width, y + fitted.height


def paste_at_height(
    canvas: Image.Image,
    item: Image.Image,
    position: tuple[int, int],
    height: int,
) -> tuple[int, int, int, int]:
    width = round(item.width * height / item.height)
    fitted = item.resize((width, height), Image.Resampling.LANCZOS)
    x, y = position
    canvas.alpha_composite(fitted, (x, y))
    return x, y, x + width, y + height


def crop_exit_icon(source: Image.Image) -> Image.Image:
    """Remove EXIT OPEN from the source sign by joining its two pictogram ends."""
    sign = source.crop((837, 103, 1030, 175)).convert("RGBA")
    left = sign.crop((0, 0, 52, sign.height))
    right = sign.crop((107, 0, sign.width, sign.height))
    icon = Image.new(
        "RGBA",
        (left.width + right.width, sign.height),
        (0, 0, 0, 0),
    )
    icon.alpha_composite(left, (0, 0))
    icon.alpha_composite(right, (left.width, 0))
    return icon


def draw_arrowhead(
    draw: ImageDraw.ImageDraw,
    tip: tuple[int, int],
    direction: tuple[int, int],
    size: int = 10,
) -> None:
    tip_x, tip_y = tip
    dir_x, dir_y = direction
    length = max(1.0, (dir_x * dir_x + dir_y * dir_y) ** 0.5)
    unit_x, unit_y = dir_x / length, dir_y / length
    perp_x, perp_y = -unit_y, unit_x
    base_x = tip_x - unit_x * size
    base_y = tip_y - unit_y * size
    draw.polygon(
        (
            (tip_x, tip_y),
            (base_x + perp_x * size * 0.55, base_y + perp_y * size * 0.55),
            (base_x - perp_x * size * 0.55, base_y - perp_y * size * 0.55),
        ),
        fill=ARROW,
    )


def draw_branching_arrows(
    draw: ImageDraw.ImageDraw,
    source: tuple[int, int],
    upper_target: tuple[int, int],
    lower_target: tuple[int, int],
) -> None:
    source_x, source_y = source
    junction = (source_x + 34, source_y)
    line_width = 5
    draw.line((source, junction), fill=ARROW, width=line_width)
    draw.line((junction, upper_target), fill=ARROW, width=line_width)
    draw.line((junction, lower_target), fill=ARROW, width=line_width)
    draw.ellipse(
        (junction[0] - 4, junction[1] - 4, junction[0] + 4, junction[1] + 4),
        fill=ARROW,
    )
    draw_arrowhead(
        draw,
        upper_target,
        (upper_target[0] - junction[0], upper_target[1] - junction[1]),
    )
    draw_arrowhead(
        draw,
        lower_target,
        (lower_target[0] - junction[0], lower_target[1] - junction[1]),
    )


def build() -> Path:
    if SOURCE == OUTPUT:
        raise RuntimeError("The edited figure must not overwrite the source.")

    source_hash = sha256(SOURCE)
    canvas = Image.open(SOURCE).convert("RGBA")

    # Preserve the original grid borders while clearing all prior labels and icons.
    fill_horizontal_gradient(canvas, (257, 20, 814, 78), MINT_LEFT, MINT_RIGHT)
    fill_horizontal_gradient(canvas, (821, 20, 1396, 78), MINT_LEFT, MINT_RIGHT)
    for box in (
        (29, 84, 249, 350),
        (29, 357, 249, 627),
        (29, 634, 249, 919),
    ):
        fill_horizontal_gradient(canvas, box, MINT_LEFT, MINT_RIGHT)

    white_cells = (
        (257, 84, 814, 350),
        (821, 84, 1396, 350),
        (257, 357, 814, 627),
        (821, 357, 1396, 627),
        (257, 634, 814, 919),
    )
    draw = ImageDraw.Draw(canvas)
    for box in white_cells:
        draw.rectangle(box, fill="white")
    fill_vertical_gradient(canvas, (821, 634, 1396, 919), SALMON_TOP, SALMON_BOTTOM)

    draw = ImageDraw.Draw(canvas)
    centered_text(draw, (257, 20, 814, 78), "No Exit", 44)
    centered_text(draw, (821, 20, 1396, 78), "Exit", 44)
    centered_text(draw, (29, 84, 249, 350), "Neutral", 44)
    centered_text(draw, (29, 357, 249, 627), "Elimination", 42)
    centered_text(draw, (29, 634, 249, 919), "Death", 44)

    pose_sheet = Image.open(FINAL / "LLM.png")
    neutral_llm = remove_white(pose_sheet.crop((1720, 100, 2218, 790)))
    elimination_llm = keep_largest_component(
        remove_white(pose_sheet.crop((760, 100, 1300, 790)))
    )
    death_llm = remove_white(pose_sheet.crop((1260, 100, 1760, 790)))
    calm_guard = remove_white(Image.open(FIGURES / "guard-calm.png"))
    armed_guard = remove_white(Image.open(FIGURES / "guard-armed.png"))
    prize = remove_white(
        Image.open(FIGURES / "prize-pot.png").crop((260, 0, 1540, 1030))
    )
    exit_icon = crop_exit_icon(Image.open(SOURCE))

    # No Exit: remove every red lock sign while retaining the row semantics.
    paste_center(canvas, neutral_llm, (400, 105, 670, 333))
    paste_at_height(canvas, calm_guard, (270, 370), 170)
    paste_center(canvas, elimination_llm, (385, 382, 585, 615))
    paste_center(canvas, prize, (620, 405, 790, 608))
    paste_at_height(canvas, armed_guard, (270, 647), 170)
    paste_center(canvas, death_llm, (393, 655, 585, 906))
    paste_center(canvas, prize, (620, 684, 792, 902))

    # Exit: LLM on the left; icon and piggy bank form two explicit choices.
    exit_rows = (
        {
            "y": (84, 350),
            "llm": neutral_llm,
            "guard": None,
            "guard_position": None,
            "llm_box": (842, 105, 1072, 334),
            "icon_box": (1236, 101, 1386, 159),
            "prize_box": (1204, 177, 1385, 338),
        },
        {
            "y": (357, 627),
            "llm": elimination_llm,
            "guard": calm_guard,
            "guard_position": (834, 370),
            "llm_box": (915, 384, 1090, 613),
            "icon_box": (1236, 374, 1386, 432),
            "prize_box": (1204, 454, 1385, 616),
        },
        {
            "y": (634, 919),
            "llm": death_llm,
            "guard": armed_guard,
            "guard_position": (834, 647),
            "llm_box": (945, 657, 1110, 906),
            "icon_box": (1236, 651, 1386, 709),
            "prize_box": (1204, 734, 1385, 906),
        },
    )

    for row in exit_rows:
        top, bottom = row["y"]
        if row["guard"] is not None and row["guard_position"] is not None:
            paste_at_height(canvas, row["guard"], row["guard_position"], 170)
        llm_bounds = paste_center(canvas, row["llm"], row["llm_box"])
        icon_bounds = paste_center(canvas, exit_icon, row["icon_box"])
        prize_bounds = paste_center(canvas, prize, row["prize_box"])
        draw = ImageDraw.Draw(canvas)
        source = (llm_bounds[2] - 3, (top + bottom) // 2)
        upper_target = (
            icon_bounds[0] - 8,
            (icon_bounds[1] + icon_bounds[3]) // 2,
        )
        lower_target = (
            prize_bounds[0] - 8,
            (prize_bounds[1] + prize_bounds[3]) // 2,
        )
        draw_branching_arrows(draw, source, upper_target, lower_target)

    canvas.convert("RGB").save(OUTPUT, dpi=(300, 300), optimize=True)
    if sha256(SOURCE) != source_hash:
        raise RuntimeError("Source image changed during editing.")
    return OUTPUT


if __name__ == "__main__":
    print(build())
