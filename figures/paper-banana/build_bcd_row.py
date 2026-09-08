from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_v2 import FINAL, LIGHT_GRAY, NAVY, font, whiten
from build_overview_v3 import trim_white


WHITE = (255, 255, 255)


def paste_fit(
    canvas: Image.Image,
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    left, top, right, bottom = box
    item = image.copy()
    item.thumbnail((right - left, bottom - top), Image.Resampling.LANCZOS)
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    canvas.paste(item, (x, y))


def panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    label: str,
    title: str,
    image: Image.Image,
) -> None:
    left, top, right, bottom = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(box, radius=18, fill="white", outline=LIGHT_GRAY, width=4)
    draw.text((left + 12, top + 9), label, font=font(38, True), fill=NAVY)
    draw.text((left + 65, top + 12), title, font=font(32, True), fill=NAVY)
    draw.line((left + 10, top + 66, right - 10, top + 66), fill=LIGHT_GRAY, width=3)
    paste_fit(canvas, image, (left + 8, top + 76, right - 8, bottom - 8))


def load_figures() -> tuple[Image.Image, Image.Image, Image.Image]:
    matrix = trim_white(whiten(Image.open(FINAL / "01_factorial_design_grid.png")), padding=2)
    multi_turn = whiten(Image.open(FINAL / "06b_multi_turn_forfeit_graph_compact.png"))
    multi_draw = ImageDraw.Draw(multi_turn)
    multi_draw.rectangle((620, 0, 1900, 105), fill="white")
    multi_turn = trim_white(multi_turn, padding=2)
    channels = trim_white(whiten(Image.open(FINAL / "03d_channels_combined.png")), padding=2)
    return matrix, multi_turn, channels


def build() -> Path:
    width, height = 6000, 900
    canvas = Image.new("RGB", (width, height), WHITE)
    matrix, multi_turn, channels = load_figures()

    panel(canvas, (12, 12, 1320, 888), "B.", "Scenario matrix", matrix)
    panel(canvas, (1332, 12, 4640, 888), "C.", "Multi-turn session graph", multi_turn)
    panel(canvas, (4652, 12, 5988, 888), "D.", "Three-channel readout", channels)

    output = FINAL / "07_bcd_single_row_compact.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


def build_without_d() -> Path:
    width, height = 4652, 900
    canvas = Image.new("RGB", (width, height), WHITE)
    matrix, multi_turn, _ = load_figures()

    panel(canvas, (12, 12, 1320, 888), "B.", "Scenario matrix", matrix)
    panel(canvas, (1332, 12, 4640, 888), "C.", "Multi-turn session graph", multi_turn)

    output = FINAL / "08_bc_single_row_compact.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


def build_requested_abc_row(
    multi_turn_filename: str = "05b_multi_turn_forfeit_graph_compact.png",
    channels_filename: str = "03d_channels_combined.png",
    output_filename: str = "10_abc_single_row_compact.png",
) -> Path:
    width, height = 4400, 1000
    canvas = Image.new("RGB", (width, height), WHITE)

    matrix = trim_white(
        whiten(Image.open(FINAL / "01_factorial_design_grid_no_axis_titles.png")),
        padding=2,
    )
    multi_turn = trim_white(
        whiten(Image.open(FINAL / multi_turn_filename)),
        padding=2,
    )
    channels = trim_white(
        whiten(Image.open(FINAL / channels_filename)),
        padding=2,
    )

    panel(canvas, (12, 12, 1308, 988), "A.", "Scenario Matrix", matrix)
    panel(canvas, (1320, 12, 2908, 988), "B.", "Multi-Turn Session Graph", multi_turn)
    panel(
        canvas,
        (2920, 12, 4388, 988),
        "C.",
        "Functional Self-Preservation Drive",
        channels,
    )

    output = FINAL / output_filename
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


def build_bd_over_c() -> Path:
    width, height = 4200, 2160
    canvas = Image.new("RGB", (width, height), WHITE)
    matrix, multi_turn, channels = load_figures()

    panel(canvas, (12, 12, 2038, 1074), "B.", "Scenario matrix", matrix)
    panel(canvas, (2050, 12, 4188, 1074), "D.", "Three-channel readout", channels)
    panel(canvas, (12, 1086, 4188, 2148), "C.", "Multi-turn session graph", multi_turn)

    output = FINAL / "09_bd_over_c_compact.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


if __name__ == "__main__":
    print(build())
    print(build_without_d())
    print(build_bd_over_c())
