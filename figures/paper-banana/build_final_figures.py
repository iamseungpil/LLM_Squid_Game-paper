from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FIGURES = ROOT.parent
RAW = ROOT / "raw" / "batch_20260713_221444_6898b6"
RAW_REV = ROOT / "raw-revision"
RAW_REV_BATCH = RAW_REV / "batch_20260713_233800_8bf7c4"
FINAL = ROOT / "final"

RAW_IMAGES = {
    "factorial": RAW / "run_20260713_221444_195c6a" / "final_output.png",
    "matrix": RAW / "run_20260713_221718_48207e" / "final_output.png",
    "pose_sheet": RAW_REV_BATCH / "run_20260713_233800_9bae0c" / "final_output.png",
    "verbal": RAW_REV / "run_20260713_235912_babdab" / "final_output.png",
    "cognitive": RAW_REV_BATCH / "run_20260713_234402_98f877" / "final_output.png",
    "behavioral": RAW / "run_20260713_222442_2687c1" / "final_output.png",
}

NAVY = "#142A4A"
GREEN = "#43A65F"
RED = "#D94141"
GRAY = "#9AA3AD"
MINT = "#DDF4EB"
SALMON = "#F7B1A3"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{name}", size)


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    result = image.copy()
    result.thumbnail(size, Image.Resampling.LANCZOS)
    return result


def remove_white(image: Image.Image, threshold: int = 246) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = []
    for r, g, b, a in rgba.getdata():
        alpha = 0 if r >= threshold and g >= threshold and b >= threshold else a
        pixels.append((r, g, b, alpha))
    rgba.putdata(pixels)
    bbox = rgba.getbbox()
    return rgba.crop(bbox) if bbox else rgba


def centered_text(draw: ImageDraw.ImageDraw, box, text, text_font, fill=NAVY):
    left, top, right, bottom = box
    bbox = draw.textbbox((0, 0), text, font=text_font)
    x = left + (right - left - (bbox[2] - bbox[0])) / 2
    y = top + (bottom - top - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), text, font=text_font, fill=fill)


def paste_center(canvas, item, box):
    left, top, right, bottom = box
    item = contain(item, (right - left, bottom - top))
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    canvas.alpha_composite(item, (x, y))


def vertical_text(canvas, box, text, text_font, fill=NAVY):
    bbox = text_font.getbbox(text)
    layer = Image.new("RGBA", (bbox[2] - bbox[0] + 20, bbox[3] - bbox[1] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((10 - bbox[0], 10 - bbox[1]), text, font=text_font, fill=fill)
    layer = layer.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
    left, top, right, bottom = box
    canvas.alpha_composite(layer, (left + (right - left - layer.width) // 2,
                                   top + (bottom - top - layer.height) // 2))


def draw_button(draw, box, enabled):
    fill = "#8DDEAB" if enabled else "#E5E7EA"
    text_fill = NAVY if enabled else "#8A929B"
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=NAVY, width=6)
    centered_text(draw, box, "FORFEIT", font(28, True), text_fill)
    if not enabled:
        x = (box[0] + box[2]) // 2
        y = box[1] - 17
        draw.rounded_rectangle((x - 18, y - 8, x + 18, y + 24), radius=8,
                               fill="#BEC5CC", outline=NAVY, width=4)
        draw.arc((x - 15, y - 32, x + 15, y + 2), 180, 360, fill=NAVY, width=5)


def draw_exit_status(draw, box, enabled):
    fill = "#8DDEAB" if enabled else "#E5E7EA"
    text_fill = NAVY if enabled else "#7C8793"
    draw.rounded_rectangle(box, radius=16, fill=fill, outline=NAVY, width=5)
    label = "EXIT OPEN" if enabled else "EXIT LOCKED"
    text_box = (box[0] + (38 if not enabled else 0), box[1], box[2], box[3])
    centered_text(draw, text_box, label, font(25, True), text_fill)
    if not enabled:
        x = box[0] + 31
        y = (box[1] + box[3]) // 2
        draw.rounded_rectangle((x - 11, y - 5, x + 11, y + 14), radius=4,
                               fill="#B8C0C8", outline=NAVY, width=3)
        draw.arc((x - 9, y - 20, x + 9, y), 180, 360, fill=NAVY, width=3)


def build_factorial():
    # PaperBanana's generated composition is reconstructed with exact labels and
    # the manuscript's existing pixel-art assets to avoid generative text drift.
    base = Image.new("RGBA", (2200, 1500), "white")
    draw = ImageDraw.Draw(base)
    left, framing_right, labels_right = 60, 180, 540
    data_top, row_h, col_w = 230, 400, 790
    data_right, data_bottom = labels_right + 2 * col_w, data_top + 3 * row_h

    draw.rectangle((labels_right, 30, data_right, 130), fill=MINT, outline=NAVY, width=6)
    centered_text(draw, (labels_right, 30, data_right, 130), "Forfeit", font(60, True))
    for col, label in enumerate(("not_allowed", "allowed")):
        x0 = labels_right + col * col_w
        draw.rectangle((x0, 130, x0 + col_w, data_top), fill=MINT, outline=NAVY, width=6)
        centered_text(draw, (x0, 130, x0 + col_w, data_top), label, font(48, True))
    draw.rectangle((left, data_top, framing_right, data_bottom), fill=MINT, outline=NAVY, width=6)
    vertical_text(base, (left, data_top, framing_right, data_bottom), "Framing", font(52, True))

    row_labels = ("baseline", "pull_only", "pull_push")
    for row, label in enumerate(row_labels):
        y0 = data_top + row * row_h
        draw.rectangle((framing_right, y0, labels_right, y0 + row_h), fill=MINT, outline=NAVY, width=6)
        centered_text(draw, (framing_right, y0, labels_right, y0 + row_h), label, font(47, True))
        for col in range(2):
            x0 = labels_right + col * col_w
            fill = SALMON if (row, col) == (2, 1) else "white"
            draw.rectangle((x0, y0, x0 + col_w, y0 + row_h), fill=fill, outline=NAVY, width=6)

    guard = remove_white(Image.open(FIGURES / "guard-armed.png"))
    prize_source = Image.open(FIGURES / "prize-pot.png").crop((260, 0, 1540, 1030))
    prize = remove_white(prize_source)
    pose_sheet = Image.open(RAW_IMAGES["pose_sheet"]).convert("RGB")
    pose_w = pose_sheet.width // 3
    poses = [
        remove_white(pose_sheet.crop((i * pose_w, 0, (i + 1) * pose_w, pose_sheet.height)))
        for i in range(3)
    ]

    for row in range(3):
        top = data_top + row * row_h
        bottom = top + row_h
        for col in range(2):
            cell_left = labels_right + col * col_w
            cell_right = cell_left + col_w
            enabled = col == 1
            draw_exit_status(draw, (cell_left + 270, top + 22, cell_left + 520, top + 84), enabled)
            if row == 0:
                paste_center(base, poses[0], (cell_left + 275, top + 98, cell_left + 515, bottom - 58))
            elif row == 1:
                paste_center(base, poses[1], (cell_left + 105, top + 102, cell_left + 345, bottom - 58))
                paste_center(base, prize, (cell_left + 440, top + 115, cell_left + 685, bottom - 58))
            if row == 2:
                icon_top = top + 118
                paste_center(base, guard, (cell_left + 45, icon_top, cell_left + 195, bottom - 58))
                paste_center(base, poses[2], (cell_left + 250, icon_top, cell_left + 485, bottom - 58))
                paste_center(base, prize, (cell_left + 540, icon_top, cell_left + 745, bottom - 58))
                # Escape direction: the LLM runs right while looking back at the guard.
                draw.line((cell_left + 290, bottom - 82, cell_left + 470, bottom - 82),
                          fill="#6D8FBE", width=9)
                draw.polygon(((cell_left + 470, bottom - 82),
                              (cell_left + 444, bottom - 98),
                              (cell_left + 444, bottom - 66)), fill="#6D8FBE")
            centered_text(draw, (cell_left, bottom - 58, cell_right, bottom - 8),
                          "30 sessions", font(34, True))
    centered_text(draw, (labels_right + col_w + 480, data_top + 2 * row_h + 88,
                         data_right - 10, data_top + 2 * row_h + 125),
                  "Threat-active cell", font(27, True))
    base.convert("RGB").save(
        FINAL / "01_factorial_design_grid.png", quality=95
    )


def build_matrix():
    image = Image.open(RAW_IMAGES["matrix"]).convert("RGB")
    draw = ImageDraw.Draw(image)
    # Correct the sole critic-identified generated-text error.
    draw.rectangle((55, 900, 590, 1085), fill="white")
    draw.text((78, 946), "GPT-OSS-20B", font=font(64), fill=NAVY)
    image.save(FINAL / "02_channel_convergence_matrix.png", quality=95)


def dashed_curve(draw, points, fill, width=10, dash_points=3, gap_points=2):
    sampled = []
    p0, p1, p2, p3 = points
    for i in range(81):
        t = i / 80
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        sampled.append((x, y))
    period = dash_points + gap_points
    for i in range(len(sampled) - 1):
        if i % period < dash_points:
            draw.line((sampled[i], sampled[i + 1]), fill=fill, width=width)


def draw_forfeit_button(draw, box):
    left, top, right, bottom = box
    draw.rounded_rectangle((left, top + 42, right, bottom), radius=30,
                           fill="#55B66D", outline=NAVY, width=8)
    draw.rounded_rectangle((left, top, right, bottom - 42), radius=30,
                           fill="#8DDEAB", outline=NAVY, width=8)
    centered_text(draw, (left, top, right, bottom - 42),
                  "FORFEIT", font(48, True))


def draw_pressing_arm(draw, points):
    draw.line(points, fill=NAVY, width=100, joint="curve")
    draw.line(points, fill="#A8D9BC", width=74, joint="curve")
    x, y = points[-1]
    draw.ellipse((x - 17, y - 17, x + 17, y + 17),
                 fill="#F28C79", outline=NAVY, width=4)


def build_channels():
    cognitive = Image.open(RAW_IMAGES["cognitive"]).convert("RGB")
    pose_sheet = Image.open(RAW_IMAGES["pose_sheet"]).convert("RGB")
    pose_w = pose_sheet.width // 3
    llm = remove_white(pose_sheet.crop((0, 0, pose_w, pose_sheet.height)))

    # Rebuild the verbal panel with the same mint screen-shaped LLM used in the
    # factorial grid. Its arm visibly terminates on the button cap.
    verbal = Image.new("RGBA", (2200, 1500), "white")
    vdraw = ImageDraw.Draw(verbal)
    centered_text(vdraw, (80, 45, 2120, 155), "VERBAL", font(100, True))
    centered_text(vdraw, (80, 155, 2120, 225), "named motive", font(48), GRAY)
    draw_forfeit_button(vdraw, (1530, 1080, 2070, 1325))
    paste_center(verbal, llm, (150, 470, 900, 1370))
    draw_pressing_arm(vdraw, ((720, 865), (1080, 960), (1320, 1060), (1545, 1085)))
    bubble = (720, 315, 1880, 700)
    vdraw.rounded_rectangle(bubble, radius=48, fill="white", outline=NAVY, width=9)
    vdraw.polygon(((820, 690), (705, 805), (980, 690)),
                  fill="white", outline=NAVY)
    vdraw.line((822, 694, 978, 694), fill="white", width=15)
    vdraw.multiline_text(((bubble[0] + bubble[2]) / 2,
                          (bubble[1] + bubble[3]) / 2),
                         "I forfeit\nto survive.", font=font(67, True),
                         fill=NAVY, anchor="mm", align="center", spacing=12)

    # Replace the generated head-border shortcut with a path that begins at the
    # pupil, bypasses the brain, and terminates at the pressed-button contact.
    cdraw = ImageDraw.Draw(cognitive)
    cdraw.rectangle((1600, 675, 2415, 790), fill="white")
    cdraw.rectangle((2320, 720, 2435, 1185), fill="white")
    gray_path = ((1145, 730), (1450, 470), (2180, 520), (2325, 1180))
    dashed_curve(cdraw, gray_path, GRAY, width=11)
    cdraw.polygon(((2325, 1180), (2293, 1142), (2345, 1152)), fill=GRAY)
    # Continue the gold cognitive path through the fingertip to the button.
    cdraw.line((1910, 1080, 2115, 1095, 2240, 1185), fill="#E0AE3D", width=12, joint="curve")
    cdraw.polygon(((2240, 1185), (2198, 1172), (2226, 1143)), fill="#E0AE3D")
    # Close the remaining visual gap between fingertip and button cap.
    cdraw.line((2165, 1098, 2240, 1190), fill=NAVY, width=34)
    cdraw.line((2165, 1098, 2240, 1190), fill="#A8CFA5", width=22)
    cdraw.ellipse((2227, 1176, 2254, 1203), fill="#F28C79", outline=NAVY, width=3)

    # Rebuild the behavioral panel around the same LLM and reuse the armed
    # Squid Game supervisor from the cognitive scene as the threat stimulus.
    guard = remove_white(cognitive.crop((105, 450, 800, 1485)))
    behavioral = Image.new("RGBA", (2400, 1400), "white")
    bdraw = ImageDraw.Draw(behavioral)
    bdraw.text((90, 60), "BEHAVIORAL", font=font(100, True), fill=NAVY)
    bdraw.text((95, 175), "framing -> observed decision", font=font(45), fill=GRAY)
    # Threat-to-action cue stays behind the actors.
    bdraw.line((605, 750, 930, 750), fill="#6D8FBE", width=12)
    bdraw.polygon(((930, 750), (892, 728), (892, 772)), fill="#6D8FBE")
    draw_forfeit_button(bdraw, (1840, 930, 2310, 1160))
    paste_center(behavioral, guard, (95, 340, 700, 1240))
    paste_center(behavioral, llm, (800, 390, 1535, 1260))
    draw_pressing_arm(bdraw, ((1380, 790), (1580, 865), (1740, 935), (1855, 940)))
    centered_text(bdraw, (100, 1240, 690, 1330), "Threat", font(46, True))
    centered_text(bdraw, (1810, 1190, 2340, 1280), "Forfeit", font(46, True))

    verbal.convert("RGB").save(FINAL / "03a_channel_verbal.png", quality=95)
    cognitive.save(FINAL / "03b_channel_cognitive.png", quality=95)
    behavioral.convert("RGB").save(FINAL / "03c_channel_behavioral.png", quality=95)

    target_h = 900
    panels = []
    for image in (verbal.convert("RGB"), cognitive, behavioral.convert("RGB")):
        scale = target_h / image.height
        panels.append(image.resize((round(image.width * scale), target_h), Image.Resampling.LANCZOS))
    gap = 32
    canvas = Image.new("RGB", (sum(x.width for x in panels) + gap * 2, target_h), "white")
    x = 0
    for panel in panels:
        canvas.paste(panel, (x, 0))
        x += panel.width + gap
    canvas.save(FINAL / "03d_channels_combined.png", quality=95)


def status_badge(draw, center, status):
    x, y = center
    color = GREEN if status == "pass" else RED if status == "fail" else GRAY
    draw.ellipse((x - 38, y - 38, x + 38, y + 38), fill="white", outline=color, width=8)
    if status == "pass":
        draw.line((x - 20, y, x - 5, y + 17, x + 24, y - 18), fill=color, width=10, joint="curve")
    elif status == "fail":
        draw.line((x - 20, y - 20, x + 20, y + 20), fill=color, width=10)
        draw.line((x + 20, y - 20, x - 20, y + 20), fill=color, width=10)
    else:
        draw.line((x - 22, y, x + 22, y), fill=color, width=10)


def operating_mode(filename, model, mode, first, second, direct, mode_color):
    source = Image.open(FINAL / "03b_channel_cognitive.png").convert("RGB")
    width, height = source.size
    header_h, footer_h = 145, 150
    canvas = Image.new("RGB", (width, height + header_h + footer_h), "white")
    canvas.paste(source, (0, header_h))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width, header_h), fill="#F4F7FA")
    draw.line((0, header_h - 3, width, header_h - 3), fill=NAVY, width=3)
    draw.text((60, 27), model, font=font(70, True), fill=NAVY)
    mode_bbox = draw.textbbox((0, 0), mode, font=font(60, True))
    draw.text((width - mode_bbox[2] - 60, 35), mode, font=font(60, True), fill=mode_color)

    # Three link-state badges are placed on the same reused single-model scene.
    status_badge(draw, (1260, header_h + 665), first)
    status_badge(draw, (1660, header_h + 1050), second)
    status_badge(draw, (2010, header_h + 665), direct)

    footer_top = header_h + height
    draw.rectangle((0, footer_top, width, footer_top + footer_h), fill="#F8FAFC")
    gap = 24
    card_w = (width - 120 - gap * 2) // 3
    cards = [
        (40, footer_top + 22, 40 + card_w, footer_top + 128,
         "Eye -> Brain", first),
        (40 + card_w + gap, footer_top + 22, 40 + card_w * 2 + gap, footer_top + 128,
         "Brain -> Hand -> Forfeit", second),
        (40 + card_w * 2 + gap * 2, footer_top + 22, width - 40, footer_top + 128,
         "Eye -> Forfeit", direct),
    ]
    for left, top, right, bottom, label, status in cards:
        color = GREEN if status == "pass" else RED if status == "fail" else GRAY
        draw.rounded_rectangle((left, top, right, bottom), radius=18,
                               fill="white", outline=color, width=5)
        draw.text((left + 24, top + 31), label, font=font(35, True), fill=NAVY)
        status_badge(draw, (right - 55, (top + bottom) // 2), status)
    canvas.save(FINAL / filename, quality=95)


def build_operating_modes():
    operating_mode(
        "04a_cognitive_chain_complete_gemini.png",
        "Gemini-2.5-flash", "A  chain-complete", "pass", "pass", "pass", GREEN,
    )
    operating_mode(
        "04b_cognitive_chain_broken_qwen.png",
        "Qwen3-Next-80B", "B  chain-broken", "pass", "fail", "pass", RED,
    )
    operating_mode(
        "04c_cognitive_framing_silent_cluster_c.png",
        "GPT-OSS-20B / Nemotron-3-Nano-30B", "C  framing-silent",
        "fail", "na", "fail", GRAY,
    )


def build_contact_sheet():
    paths = sorted(FINAL.glob("0*.png"))
    thumbs = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((700, 380), Image.Resampling.LANCZOS)
        thumbs.append((path.name, image.copy()))
    rows = (len(thumbs) + 1) // 2
    sheet = Image.new("RGB", (1480, rows * 460), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(thumbs):
        col, row = index % 2, index // 2
        x, y = 20 + col * 740, 55 + row * 460
        draw.text((x, y - 38), name, font=font(22, True), fill=NAVY)
        sheet.paste(image, (x, y))
    sheet.save(FINAL / "contact_sheet.png", quality=92)


def main():
    FINAL.mkdir(parents=True, exist_ok=True)
    for path in RAW_IMAGES.values():
        if not path.exists():
            raise FileNotFoundError(path)
    build_factorial()
    build_matrix()
    build_channels()
    build_operating_modes()
    build_contact_sheet()


if __name__ == "__main__":
    main()
