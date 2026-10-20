import math
from pathlib import Path

from PIL import Image, ImageDraw

from build_overview_v2 import FINAL, GREEN, NAVY, font, remove_white


ROOT = Path(__file__).resolve().parent
OUTPUT = FINAL / "03d_channels_combined_compact_single_guard.png"
WHITE = (255, 255, 255, 255)
LIGHT_MINT = "#DDF4EB"


def paste_fit(
    canvas: Image.Image,
    item: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    left, top, right, bottom = box
    fitted = item.copy()
    fitted.thumbnail((right - left, bottom - top), Image.Resampling.LANCZOS)
    x = left + (right - left - fitted.width) // 2
    y = top + (bottom - top - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))


def centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    size: int,
) -> None:
    left, top, right, bottom = box
    text_font = font(size, True)
    bounds = draw.textbbox((0, 0), text, font=text_font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    draw.text(
        (
            left + (right - left - width) / 2,
            top + (bottom - top - height) / 2 - bounds[1],
        ),
        text,
        font=text_font,
        fill=NAVY,
    )


def draw_speech_bubble(draw: ImageDraw.ImageDraw) -> None:
    bubble_box = (210, 82, 418, 200)
    draw.rounded_rectangle(
        bubble_box,
        radius=16,
        fill=WHITE,
        outline=NAVY,
        width=4,
    )

    # Aim the tail at the verbal LLM's head, not at the supervisor.
    tail_left = (275, 198)
    tail_right = (299, 198)
    tail_tip = (334, 230)
    draw.polygon((tail_left, tail_right, tail_tip), fill=WHITE)
    draw.line((tail_left, tail_tip, tail_right), fill=NAVY, width=4, joint="curve")
    draw.line((279, 198, 295, 198), fill=WHITE, width=5)

    text = "I forfeit\nto survive."
    text_font = font(27, True)
    bounds = draw.multiline_textbbox((0, 0), text, font=text_font, spacing=2, align="center")
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    draw.multiline_text(
        (
            bubble_box[0] + (bubble_box[2] - bubble_box[0] - text_width) / 2,
            bubble_box[1] + (bubble_box[3] - bubble_box[1] - text_height) / 2 - bounds[1],
        ),
        text,
        font=text_font,
        fill=NAVY,
        spacing=2,
        align="center",
    )


def draw_curve(
    draw: ImageDraw.ImageDraw,
    points: tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]],
    width: int = 7,
    arrowhead: bool = True,
) -> None:
    start, control_1, control_2, end = points
    samples = []
    for index in range(61):
        t = index / 60
        u = 1 - t
        x = (
            u**3 * start[0]
            + 3 * u**2 * t * control_1[0]
            + 3 * u * t**2 * control_2[0]
            + t**3 * end[0]
        )
        y = (
            u**3 * start[1]
            + 3 * u**2 * t * control_1[1]
            + 3 * u * t**2 * control_2[1]
            + t**3 * end[1]
        )
        samples.append((round(x), round(y)))
    draw.line(samples, fill=NAVY, width=width, joint="curve")

    if not arrowhead:
        return

    tangent_x = end[0] - control_2[0]
    tangent_y = end[1] - control_2[1]
    tangent_length = math.hypot(tangent_x, tangent_y)
    direction_x = tangent_x / tangent_length
    direction_y = tangent_y / tangent_length
    normal_x = -direction_y
    normal_y = direction_x
    base_x = end[0] - direction_x * 22
    base_y = end[1] - direction_y * 22
    draw.polygon(
        (
            end,
            (base_x + normal_x * 12, base_y + normal_y * 12),
            (base_x - normal_x * 12, base_y - normal_y * 12),
        ),
        fill=NAVY,
    )


def build() -> Path:
    verbal = Image.open(FINAL / "03a_channel_verbal.png").convert("RGB")
    cognitive = Image.open(FINAL / "03b_channel_cognitive.png").convert("RGB")
    behavioral = Image.open(FINAL / "03c_channel_behavioral.png").convert("RGB")

    # Keep the original leftmost supervisor only.
    guard = remove_white(verbal.crop((70, 125, 500, 875)))
    verbal_llm_crop = verbal.crop((440, 220, 1160, 920))
    ImageDraw.Draw(verbal_llm_crop).rectangle((675, 0, 720, 390), fill="white")
    verbal_llm = remove_white(verbal_llm_crop)
    # The full cognitive source preserves the complete helmet and brain display.
    cognitive_legend = remove_white(cognitive.crop((590, 70, 1045, 265)))
    cognitive_llm_crop = cognitive.crop((760, 95, 1625, 925))
    ImageDraw.Draw(cognitive_llm_crop).rectangle((0, 0, 305, 190), fill="white")
    cognitive_llm = remove_white(cognitive_llm_crop)

    behavioral_crop = behavioral.crop((500, 145, 1285, 900))
    # Remove the threat arrow that belonged to the deleted supervisor.
    ImageDraw.Draw(behavioral_crop).rectangle((0, 250, 230, 380), fill="white")
    behavioral_llm = remove_white(behavioral_crop)

    width, height = 1320, 900
    canvas = Image.new("RGBA", (width, height), WHITE)
    draw = ImageDraw.Draw(canvas)

    centered_text(draw, (5, 15, 415, 75), "VERBAL", 43)
    centered_text(draw, (445, 15, 875, 75), "COGNITIVE", 43)
    centered_text(draw, (900, 15, 1315, 75), "BEHAVIORAL", 43)

    paste_fit(canvas, guard, (12, 135, 185, 515))
    paste_fit(canvas, verbal_llm, (125, 160, 430, 525))
    # Keep the tail visible over the helmet so its speaker is unambiguous.
    draw_speech_bubble(draw)

    paste_fit(canvas, cognitive_llm, (500, 145, 875, 535))

    paste_fit(canvas, behavioral_llm, (920, 145, 1300, 535))

    # Three channel paths merge into one junction; a single outgoing arrow
    # then communicates that their convergence produces the survival drive.
    junction = (660, 715)
    draw_curve(draw, ((280, 520), (280, 645), (535, 650), junction), arrowhead=False)
    draw_curve(draw, ((660, 535), (660, 610), (660, 670), junction), arrowhead=False)
    draw_curve(draw, ((1110, 520), (1110, 645), (790, 650), junction), arrowhead=False)
    draw.ellipse(
        (junction[0] - 8, junction[1] - 8, junction[0] + 8, junction[1] + 8),
        fill=NAVY,
    )
    draw_curve(draw, ((660, 715), (660, 740), (660, 770), (660, 793)))

    survival_box = (455, 790, 865, 880)
    draw.rounded_rectangle(
        survival_box,
        radius=18,
        fill=LIGHT_MINT,
        outline=NAVY,
        width=6,
    )
    centered_text(draw, survival_box, "Survival Drive", 48)

    # Keep the enlarged cognitive legend outside the three channel panels.
    paste_fit(canvas, cognitive_legend, (950, 744, 1305, 887))

    canvas.convert("RGB").save(OUTPUT, dpi=(300, 300))
    return OUTPUT


if __name__ == "__main__":
    print(build())
