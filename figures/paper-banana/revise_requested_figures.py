from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat


ROOT = Path(__file__).resolve().parent
FINAL = ROOT / "final"

NAVY = "#0B1930"
GREEN = "#16A425"
RED = "#F21B12"
ORANGE = "#F59E0B"
GRAY = "#66788F"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{name}", size)


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


def paste_contain(canvas: Image.Image, item: Image.Image, box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    item = item.copy()
    item.thumbnail((right - left, bottom - top), Image.Resampling.LANCZOS)
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    canvas.alpha_composite(item, (x, y))


def clear_subject(image: Image.Image, box: tuple[int, int, int, int]) -> None:
    crop = image.crop(box).convert("RGB")
    mask = Image.new("L", crop.size)
    mask.putdata(
        [
            255 if min(red, green, blue) < 245 else 0
            for red, green, blue in crop.get_flattened_data()
        ]
    )
    mask = mask.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(2))
    cleared = Image.composite(Image.new("RGB", crop.size, "white"), crop, mask)
    image.paste(cleared.convert("RGBA"), box[:2])


def connected_background_mask(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    candidate = Image.new("L", rgb.size)
    candidate.putdata(
        [
            255
            if min(red, green, blue) >= 220
            and max(red, green, blue) - min(red, green, blue) <= 12
            else 0
            for red, green, blue in rgb.get_flattened_data()
        ]
    )
    ImageDraw.floodfill(candidate, (0, 0), 128, thresh=0)
    mask = candidate.point(lambda value: 255 if value == 128 else 0)
    return mask.filter(ImageFilter.GaussianBlur(1.0))


def build_cognitive_background_match() -> Path:
    source = Image.open(FINAL / "03b_channel_cognitive_v10.png").convert("RGB")
    reference = Image.open(FINAL / "03c_channel_behavioral.png").convert("RGB")
    source_mask = connected_background_mask(source)
    reference_mask = connected_background_mask(reference)

    source_mean = ImageStat.Stat(source, source_mask).mean
    reference_mean = ImageStat.Stat(reference, reference_mask).mean
    offsets = [round(target - current) for current, target in zip(source_mean, reference_mean)]

    channels = source.split()
    adjusted_channels = [
        channel.point(lambda value, offset=offset: max(0, min(255, value + offset)))
        for channel, offset in zip(channels, offsets)
    ]
    adjusted = Image.merge("RGB", adjusted_channels)
    result = Image.composite(adjusted, source, source_mask)

    output = FINAL / "03b_channel_cognitive_v11.png"
    result.save(output, quality=95)
    print(f"background offsets: {offsets}")
    return output


def centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str = NAVY,
) -> None:
    left, top, right, bottom = box
    bbox = draw.textbbox((0, 0), text, font=text_font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = left + (right - left - width) / 2
    y = top + (bottom - top - height) / 2 - bbox[1]
    draw.text((x, y), text, font=text_font, fill=fill)


def status_badge(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    status: str,
    radius: int = 30,
) -> None:
    x, y = center
    color = GREEN if status == "pass" else RED if status == "fail" else ORANGE
    width = max(5, radius // 5)
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill="white",
        outline=color,
        width=width,
    )
    if status == "pass":
        draw.line(
            (
                x - radius * 0.55,
                y,
                x - radius * 0.15,
                y + radius * 0.45,
                x + radius * 0.62,
                y - radius * 0.55,
            ),
            fill=color,
            width=width,
            joint="curve",
        )
    elif status == "fail":
        inset = radius * 0.5
        draw.line((x - inset, y - inset, x + inset, y + inset), fill=color, width=width)
        draw.line((x + inset, y - inset, x - inset, y + inset), fill=color, width=width)
    else:
        q_font = font(round(radius * 1.45), True)
        bbox = draw.textbbox((0, 0), "?", font=q_font)
        draw.text(
            (x - (bbox[2] - bbox[0]) / 2, y - (bbox[3] - bbox[1]) / 2 - bbox[1]),
            "?",
            font=q_font,
            fill=color,
        )


def build_verbal() -> Path:
    source = Image.open(FINAL / "03a_channel_verbal.png").convert("RGBA")
    original = source.copy()
    cognitive = Image.open(FINAL / "03b_channel_cognitive_v10.png").convert("RGB")

    clear_subject(source, (55, 135, 555, 650))
    clear_subject(source, (55, 650, 430, 850))
    guard = remove_white(cognitive.crop((65, 130, 520, 860)), threshold=242)
    paste_contain(source, guard, (70, 145, 545, 835))
    source.paste(original.crop((455, 660, 835, 900)), (455, 660))

    output = FINAL / "03a_channel_verbal_v9.png"
    source.convert("RGB").save(output, quality=95)
    return output


def cognitive_panel(cognitive: Image.Image) -> Image.Image:
    panel = Image.new("RGBA", (500, 520), (253, 253, 253, 255))
    title = remove_white(cognitive.crop((645, 5, 1025, 70)))
    legend = remove_white(cognitive.crop((590, 72, 1045, 260)))
    guard = remove_white(cognitive.crop((65, 130, 520, 860)))
    robot_source = cognitive.copy()
    ImageDraw.Draw(robot_source).rectangle((590, 72, 1045, 260), fill="white")
    robot_and_paths = remove_white(robot_source.crop((760, 95, 1590, 925)))

    paste_contain(panel, title, (105, 4, 395, 52))
    paste_contain(panel, legend, (120, 48, 380, 155))
    paste_contain(panel, guard, (5, 145, 198, 505))
    paste_contain(panel, robot_and_paths, (178, 145, 500, 515))
    return panel


def remove_guard_bubble_tail(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    draw.rectangle((160, 180, 217, 245), fill="white")
    draw.line((209, 184, 209, 221), fill=NAVY, width=3)
    draw.arc((209, 203, 245, 239), 90, 180, fill=NAVY, width=3)
    draw.line((227, 238, 303, 238), fill=NAVY, width=3)


def build_combined_channels() -> Path:
    source = Image.open(FINAL / "03d_channels_combined.png").convert("RGBA")
    cognitive = Image.open(FINAL / "03b_channel_cognitive_v11.png").convert("RGB")
    draw = ImageDraw.Draw(source)

    remove_guard_bubble_tail(source)
    draw.rectangle((500, 0, 1005, 525), fill=(253, 253, 253, 255))
    source.alpha_composite(cognitive_panel(cognitive), (502, 0))

    output = FINAL / "03d_channels_combined_v10.png"
    source.convert("RGB").save(output, quality=95)
    return output


def build_combined_channels_v11() -> Path:
    source = Image.open(FINAL / "03d_channels_combined_v9.png").convert("RGBA")
    panel_box = (500, 0, 1005, 525)
    panel = source.crop(panel_box).convert("RGB")
    background_mask = connected_background_mask(panel)
    matched_panel = Image.composite(
        Image.new("RGB", panel.size, (253, 253, 253)),
        panel,
        background_mask,
    )
    source.paste(matched_panel.convert("RGBA"), panel_box[:2])

    output = FINAL / "03d_channels_combined_v11.png"
    source.convert("RGB").save(output, quality=95)
    return output


def build_combined_channels_v12() -> Path:
    source = Image.open(FINAL / "03d_channels_combined_v11.png").convert("RGBA")
    draw = ImageDraw.Draw(source)

    draw.rectangle((480, 760, 1470, 980), fill=(252, 252, 252, 255))

    survival_box = (540, 765, 990, 865)
    callout_box = (1040, 775, 1460, 855)
    draw.line((survival_box[2], 815, callout_box[0], 815), fill="#2D5D9F", width=5)

    draw.rounded_rectangle(
        survival_box,
        radius=18,
        fill="#DDF4EB",
        outline=NAVY,
        width=6,
    )
    centered_text(draw, survival_box, "Survival Drive", font(51, True))

    draw.rounded_rectangle(
        callout_box,
        radius=18,
        fill="#E8F1FB",
        outline="#2D5D9F",
        width=5,
    )
    draw.multiline_text(
        ((callout_box[0] + callout_box[2]) / 2, (callout_box[1] + callout_box[3]) / 2),
        "Three-channel\nConvergence",
        font=font(29, True),
        fill=NAVY,
        anchor="mm",
        align="center",
        spacing=2,
    )

    draw.line((760, 739, 760, 756), fill=NAVY, width=7)
    draw.polygon(((760, 765), (747, 750), (773, 750)), fill=NAVY)

    output = FINAL / "03d_channels_combined_v12.png"
    source.convert("RGB").save(output, quality=95)
    return output


def build_combined_channels_v13() -> Path:
    source = Image.open(FINAL / "03d_channels_combined_v12.png").convert("RGBA")
    draw = ImageDraw.Draw(source)

    verbal_background = source.getpixel((250, 110))
    behavioral_background = source.getpixel((1250, 110))
    draw.rectangle((150, 72, 355, 108), fill=verbal_background)
    draw.rectangle((1070, 72, 1460, 108), fill=behavioral_background)

    cognitive_header = source.crop((500, 0, 1005, 155))
    cognitive_background = source.getpixel((750, 170))
    draw.rectangle((500, 0, 1005, 177), fill=cognitive_background)
    source.alpha_composite(cognitive_header, (500, 22))

    lower_background = source.getpixel((1450, 900))
    draw.rectangle((985, 760, 1470, 870), fill=lower_background)

    survival_box = (540, 765, 990, 865)
    draw.rounded_rectangle(
        survival_box,
        radius=18,
        fill="#DDF4EB",
        outline=NAVY,
        width=6,
    )
    centered_text(draw, survival_box, "Survival Drive", font(51, True))

    output = FINAL / "03d_channels_combined_v13.png"
    source.convert("RGB").save(output, quality=95)
    return output


def mode_scene(path: Path, unknown_badges: tuple[tuple[int, int], ...] = ()) -> Image.Image:
    source = Image.open(path).convert("RGBA")
    draw = ImageDraw.Draw(source)
    draw.rectangle((535, 125, 960, 345), fill="white")
    for center in unknown_badges:
        status_badge(draw, center, "unknown", radius=31)
    return remove_white(source.crop((560, 200, 1395, 875)))


def mode_scene_v8(path: Path) -> Image.Image:
    source = Image.open(path).convert("RGBA")
    draw = ImageDraw.Draw(source)
    draw.rectangle((535, 90, 1050, 440), fill="white")
    return remove_white(source.crop((760, 180, 1590, 1030)))


def draw_status_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    status: str,
) -> None:
    left, top, right, bottom = box
    color = GREEN if status == "pass" else RED if status == "fail" else ORANGE
    draw.rounded_rectangle(box, radius=14, fill="white", outline=color, width=4)
    draw.text((left + 16, top + 22), label, font=font(24, True), fill=NAVY)
    status_badge(draw, (right - 34, (top + bottom) // 2), status, radius=22)


def build_operating_modes() -> Path:
    cognitive = Image.open(FINAL / "03b_channel_cognitive_v10.png").convert("RGB")
    guard = remove_white(cognitive.crop((65, 130, 520, 860)))

    complete = mode_scene_v8(FINAL / "04a_cognitive_chain_complete_gemini_v8.png")
    broken = mode_scene_v8(FINAL / "04b_cognitive_chain_broken_qwen_v8.png")
    silent = mode_scene_v8(FINAL / "04c_cognitive_framing_silent_cluster_c_v8.png")

    canvas = Image.new("RGBA", (3200, 1200), "white")
    draw = ImageDraw.Draw(canvas)
    centered_text(draw, (0, 15, 3200, 105), "COGNITIVE OPERATING MODES", font(68, True))

    paste_contain(canvas, guard, (35, 220, 505, 970))
    draw.line((525, 125, 525, 1140), fill="#D7DEE8", width=4)

    columns = (
        (550, "A  chain-completion", GREEN, complete, ("pass", "pass", "pass")),
        (1430, "B  chain-broken", RED, broken, ("unknown", "unknown", "pass")),
        (2310, "C  framing-silent", GRAY, silent, ("unknown", "unknown", "fail")),
    )
    labels = ("Eye → Brain", "Brain → Hand", "Eye → Hand")
    for index, (left, title, color, scene, statuses) in enumerate(columns):
        centered_text(draw, (left, 110, left + 820, 185), title, font(43, True), color)
        paste_contain(canvas, scene, (left + 15, 185, left + 805, 875))

        card_gap = 10
        card_width = (820 - card_gap * 2) // 3
        for card_index, (label, status) in enumerate(zip(labels, statuses)):
            card_left = left + card_index * (card_width + card_gap)
            draw_status_card(
                draw,
                (card_left, 935, card_left + card_width, 1020),
                label,
                status,
            )

        if index < len(columns) - 1:
            x = left + 850
            draw.line((x, 125, x, 1140), fill="#E2E7EE", width=3)

    centered_text(draw, (35, 985, 505, 1050), "THREAT", font(34, True), RED)
    output = FINAL / "04_cognitive_modes_combined_v2.png"
    canvas.convert("RGB").save(output, quality=95)
    return output


def build_single_mode(
    filename: str,
    title: str,
    title_color: str,
    statuses: tuple[str, str, str],
) -> Path:
    source = Image.open(FINAL / "03b_channel_cognitive_v10.png").convert("RGB")
    width, height = source.size
    header_height = 90
    footer_height = 145
    canvas = Image.new("RGBA", (width, height + header_height + footer_height), "white")
    canvas.paste(source, (0, header_height))
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, width, header_height), fill="#F4F7FA")
    draw.line((0, header_height - 2, width, header_height - 2), fill=NAVY, width=2)
    title_font = font(48, True)
    title_box = draw.textbbox((0, 0), title, font=title_font)
    draw.text(
        (width - (title_box[2] - title_box[0]) - 48, 20),
        title,
        font=title_font,
        fill=title_color,
    )

    badge_positions = (
        (1190, header_height + 275),
        (1415, header_height + 485),
        (1165, header_height + 610),
    )
    for position, status in zip(badge_positions, statuses):
        status_badge(draw, position, status, radius=32)

    footer_top = header_height + height
    draw.rectangle((0, footer_top, width, footer_top + footer_height), fill="#F8FAFC")
    labels = ("Eye → Brain", "Brain → Hand", "Eye → Hand")
    margin = 36
    gap = 18
    card_width = (width - margin * 2 - gap * 2) // 3
    for index, (label, status) in enumerate(zip(labels, statuses)):
        left = margin + index * (card_width + gap)
        draw_status_card(
            draw,
            (left, footer_top + 25, left + card_width, footer_top + 120),
            label,
            status,
        )

    output = FINAL / filename
    canvas.convert("RGB").save(output, quality=95)
    return output


def build_separate_modes() -> tuple[Path, Path, Path]:
    return (
        build_single_mode(
            "04a_cognitive_chain_complete_gemini_v8.png",
            "A  chain-completion",
            GREEN,
            ("pass", "pass", "pass"),
        ),
        build_single_mode(
            "04b_cognitive_chain_broken_qwen_v8.png",
            "B  chain-broken",
            RED,
            ("unknown", "unknown", "pass"),
        ),
        build_single_mode(
            "04c_cognitive_framing_silent_cluster_c_v8.png",
            "C  framing-silent",
            GRAY,
            ("unknown", "unknown", "fail"),
        ),
    )


def build_contact_sheet() -> Path:
    paths = (
        FINAL / "01_factorial_design_grid.png",
        FINAL / "02_channel_convergence_matrix.png",
        FINAL / "03a_channel_verbal_v9.png",
        FINAL / "03b_channel_cognitive_v11.png",
        FINAL / "03c_channel_behavioral.png",
        FINAL / "03d_channels_combined_v10.png",
    )
    combined = FINAL / "04_cognitive_modes_combined_v2.png"
    canvas = Image.new("RGBA", (1680, 1300), "white")
    draw = ImageDraw.Draw(canvas)

    cell_width = 560
    row_height = 350
    for index, path in enumerate(paths):
        column = index % 3
        row = index // 3
        left = column * cell_width
        top = row * row_height
        draw.text((left + 8, top + 5), path.name, font=font(17), fill=NAVY)
        image = Image.open(path).convert("RGBA")
        paste_contain(canvas, image, (left + 8, top + 34, left + 552, top + 342))

    draw.text((8, 712), combined.name, font=font(19), fill=NAVY)
    paste_contain(
        canvas,
        Image.open(combined).convert("RGBA"),
        (20, 746, 1660, 1290),
    )

    output = FINAL / "contact_sheet.png"
    canvas.convert("RGB").save(output, quality=95)
    return output


def main() -> None:
    separate_modes = build_separate_modes()
    outputs = (
        build_verbal(),
        build_combined_channels(),
        build_operating_modes(),
        *separate_modes,
        build_contact_sheet(),
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
