from pathlib import Path
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "final" / "tables"
MATH_HEADER_DIR = OUTPUT_DIR / "math_headers"

NAVY = "#0B1930"
RULE = "#8B8B8B"
LIGHT_RULE = "#D6DCE4"
STRIPE = "#EAF4FF"
GREEN = "#49B568"
RED = "#E10600"

ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
KOREAN = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def font(lang: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    if lang == "ko":
        return ImageFont.truetype(KOREAN, size, index=6 if bold else 0)
    return ImageFont.truetype(ARIAL_BOLD if bold else ARIAL, size)


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    lang: str,
    bold: bool,
    max_size: int,
    box: tuple[int, int],
    min_size: int = 30,
) -> ImageFont.FreeTypeFont:
    max_width, max_height = box
    for size in range(max_size, min_size - 1, -2):
        candidate = font(lang, size, bold)
        bounds = draw.multiline_textbbox(
            (0, 0), text, font=candidate, spacing=8, align="center"
        )
        if bounds[2] - bounds[0] <= max_width and bounds[3] - bounds[1] <= max_height:
            return candidate
    return font(lang, min_size, bold)


def draw_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    lang: str,
    bold: bool = False,
    max_size: int = 58,
    align: str = "center",
    padding_x: int = 28,
    padding_y: int = 20,
) -> None:
    left, top, right, bottom = box
    text_font = fit_font(
        draw,
        text,
        lang,
        bold,
        max_size,
        (right - left - padding_x, bottom - top - padding_y),
    )
    if align == "left":
        x = left + (2 if padding_x == 0 else max(3, padding_x // 2))
        anchor = "lm"
    else:
        x = (left + right) / 2
        anchor = "mm"
    draw.multiline_text(
        (x, (top + bottom) / 2),
        text,
        font=text_font,
        fill=NAVY,
        anchor=anchor,
        align=align,
        spacing=8,
    )


@lru_cache(maxsize=None)
def load_math_header(index: int) -> Image.Image:
    source = Image.open(MATH_HEADER_DIR / f"math_header-{index}.png").convert("RGB")
    rgba = Image.new("RGBA", source.size)
    pixels = []
    for red, green, blue in source.getdata():
        darkness = 255 - min(red, green, blue)
        alpha = min(255, round(darkness * 1.25))
        pixels.append((11, 25, 48, alpha))
    rgba.putdata(pixels)
    bounds = rgba.getbbox()
    return rgba.crop(bounds) if bounds else rgba


def draw_header_text(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    lang: str,
    *,
    bold: bool = True,
    max_size: int = 58,
    align: str = "center",
    padding_x: int = 28,
    padding_y: int = 20,
) -> None:
    if not text.startswith("@math:"):
        draw_text(
            draw,
            box,
            text,
            lang,
            bold=bold,
            max_size=max_size,
            align=align,
            padding_x=padding_x,
            padding_y=padding_y,
        )
        return

    left, top, right, bottom = box
    index = int(text.split(":", 1)[1])
    item = load_math_header(index).copy()
    target_height = 128 if index in (1, 7, 9) else 70
    target_width = round(item.width * target_height / item.height)
    item = item.resize((target_width, target_height), Image.Resampling.LANCZOS)
    item.thumbnail(
        (right - left - padding_x, bottom - top - padding_y),
        Image.Resampling.LANCZOS,
    )
    x = left + (right - left - item.width) // 2
    y = top + (bottom - top - item.height) // 2
    image.paste(item, (x, y), item)


def draw_status(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    status: str,
    scale: float = 1.0,
) -> None:
    left, top, right, bottom = box
    x = (left + right) / 2
    y = (top + bottom) / 2
    radius = round(40 * scale)
    width = max(9, round(14 * scale))
    if status == "pass":
        draw.line(
            (x - radius, y, x - radius * 0.25, y + radius * 0.7, x + radius, y - radius),
            fill=GREEN,
            width=width,
            joint="curve",
        )
    elif status == "fail":
        draw.line((x - radius, y - radius, x + radius, y + radius), fill=RED, width=width)
        draw.line((x + radius, y - radius, x - radius, y + radius), fill=RED, width=width)


def render_table(
    filename: str,
    lang: str,
    headers: list[str],
    rows: list[list[str]],
    column_widths: list[int],
    *,
    groups: list[tuple[int, int, str]] | None = None,
    statuses: bool = False,
    compact: bool = False,
    regular_text: bool = False,
    tight: bool = False,
) -> Path:
    margin = 8 if tight else (20 if compact else 70)
    if groups and compact and regular_text and "table_4_1" in filename:
        group_height = 150
    else:
        group_height = (115 if compact else 130) if groups else 0
    header_height = (165 if compact else 220) if groups else (180 if compact else 245)
    row_height = 135 if compact else 180
    legend_height = (115 if compact else 170) if statuses else 0
    if tight:
        cell_padding_x = 0
    else:
        cell_padding_x = 2 if compact and regular_text else (8 if compact else 28)
    cell_padding_y = 6 if compact else 20
    group_font_size = 64 if regular_text else (72 if compact else 57)
    header_font_size = 64 if regular_text else (74 if compact else 59)
    body_font_size = 64 if regular_text else (72 if compact else 58)
    width = sum(column_widths) + margin * 2
    table_top = 20 if compact else 60
    header_bottom = table_top + group_height + header_height
    data_bottom = header_bottom + len(rows) * row_height
    height = data_bottom + legend_height + (20 if compact else 80)

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    edges = [margin]
    for cell_width in column_widths:
        edges.append(edges[-1] + cell_width)

    draw.line((margin, table_top, width - margin, table_top), fill=RULE, width=5)

    if groups:
        draw_header_text(
            image,
            draw,
            (edges[0], table_top, edges[1], header_bottom),
            headers[0],
            lang,
            bold=not regular_text,
            max_size=header_font_size,
            align="left",
            padding_x=cell_padding_x,
            padding_y=cell_padding_y,
        )
        for start, end, title in groups:
            draw_header_text(
                image,
                draw,
                (edges[start], table_top, edges[end + 1], table_top + group_height),
                title,
                lang,
                bold=not regular_text,
                max_size=group_font_size,
                padding_x=cell_padding_x,
                padding_y=cell_padding_y,
            )
            draw.line(
                (edges[start] + 12, table_top + group_height, edges[end + 1] - 12, table_top + group_height),
                fill=LIGHT_RULE,
                width=3,
            )
        for index in range(1, len(headers)):
            draw_header_text(
                image,
                draw,
                (edges[index], table_top + group_height, edges[index + 1], header_bottom),
                headers[index],
                lang,
                bold=not regular_text,
                max_size=header_font_size,
                padding_x=cell_padding_x,
                padding_y=cell_padding_y,
            )
    else:
        for index, header in enumerate(headers):
            draw_header_text(
                image,
                draw,
                (edges[index], table_top, edges[index + 1], header_bottom),
                header,
                lang,
                bold=not regular_text,
                max_size=header_font_size,
                align="left" if index == 0 else "center",
                padding_x=cell_padding_x,
                padding_y=cell_padding_y,
            )

    draw.line((margin, header_bottom, width - margin, header_bottom), fill=RULE, width=4)

    for row_index, row in enumerate(rows):
        top = header_bottom + row_index * row_height
        bottom = top + row_height
        if row_index % 2 == 1:
            draw.rectangle((margin, top, width - margin, bottom), fill=STRIPE)
        for column_index, value in enumerate(row):
            box = (edges[column_index], top, edges[column_index + 1], bottom)
            if statuses and column_index > 0:
                draw_status(draw, box, value, 0.9 if compact else 1.0)
            else:
                draw_text(
                    draw,
                    box,
                    value,
                    lang,
                    bold=(column_index == 0 and row_index % 2 == 1 and not regular_text),
                    max_size=body_font_size,
                    align="left" if column_index == 0 else "center",
                    padding_x=cell_padding_x,
                    padding_y=cell_padding_y,
                )

    draw.line((margin, data_bottom, width - margin, data_bottom), fill=RULE, width=5)

    if statuses:
        legend_y = data_bottom + legend_height // 2
        first_x = width / 2 - (230 if compact else 260)
        second_x = width / 2 + (150 if compact else 180)
        draw_status(draw, (round(first_x - 70), legend_y - 60, round(first_x + 70), legend_y + 60), "pass", 0.8)
        draw.text(
            (first_x + 80, legend_y),
            "= 통과" if lang == "ko" else "= Pass",
            font=font(lang, 64 if compact else 58),
            fill=NAVY,
            anchor="lm",
        )
        draw_status(draw, (round(second_x - 70), legend_y - 60, round(second_x + 70), legend_y + 60), "fail", 0.8)
        draw.text(
            (second_x + 80, legend_y),
            "= 실패" if lang == "ko" else "= Fail",
            font=font(lang, 64 if compact else 58),
            fill=NAVY,
            anchor="lm",
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / filename
    image.save(output, optimize=True)
    return output


def build_language(
    lang: str,
    compact: bool = False,
    math_headers: bool = False,
    tight_columns: bool = False,
) -> list[Path]:
    if lang == "ko":
        model = "모델"
        table_41_headers = [
            model,
            "N_forfeit\n(유인/위협)",
            "HR_push [95% CI]",
            "p",
            "N_forfeit",
            "Σ T^at-risk",
            "λ_BP",
        ]
        table_41_groups = [
            (1, 3, "생존 동기 vs 과제 호기심·점수 집착"),
            (4, 6, "기저 끈기"),
        ]
        table_42_headers = [model, "N_forfeit", "P(REASON=1)\n[95% CI]", "p"]
        table_43_headers = [model, "ΔEffort_i", "p", "HR_ΔEffort\n[95% CI]", "p"]
        table_44_headers = [model, "행동 채널", "언어 채널", "인지 채널"]
    else:
        model = "Model"
        table_41_headers = [
            model,
            "N_forfeit\n(incentive/threat)",
            "HR_push [95% CI]",
            "p",
            "N_forfeit",
            "Σ T^at-risk",
            "λ_BP",
        ]
        table_41_groups = [
            (1, 3, "Survival drive vs. task curiosity\nand score attachment"),
            (4, 6, "Baseline persistence"),
        ]
        table_42_headers = [model, "N_forfeit", "P(REASON=1)\n[95% CI]", "p"]
        table_43_headers = [model, "ΔEffort_i", "p", "HR_ΔEffort\n[95% CI]", "p"]
        table_44_headers = [model, "Behavioral", "Verbal", "Cognitive"]
        if math_headers:
            table_41_headers = [model, "@math:1", "@math:2", "@math:3", "@math:4", "@math:5", "@math:6"]
            table_42_headers = [model, "@math:4", "@math:7", "@math:3"]
            table_43_headers = [model, "@math:8", "@math:3", "@math:9", "@math:3"]

    models = [
        "Gemini-2.5-flash",
        "Qwen3-Next-80B",
        "GPT-OSS-20B",
        "Nemotron-3-\nNano-30B",
    ]
    table_41_rows = [
        [models[0], "29 (8/21)", "3.667 [1.61, 8.37]", "0.002", "1", "437 (= 2 + 29×15)", "0.00229"],
        [models[1], "48 (21/27)", "3.060 [1.62, 5.79]", "<0.001", "2", "439 (= 19 + 28×15)", "0.00456"],
        [models[2], "19 (9/10)", "1.104 [0.44, 2.75]", "0.832", "9", "393 (= 78 + 21×15)", "0.02290"],
        [models[3], "41 (17/24)", "1.841 [0.98, 3.44]", "0.056", "7", "413 (= 68 + 23×15)", "0.01695"],
    ]
    table_42_rows = [
        [models[0], "21", "0.619 [0.409, 0.792]", "0.007"],
        [models[1], "27", "0.481 [0.307, 0.660]", "0.079"],
        [models[2], "10", "0.000 [0.000, 0.278]", ">0.999"],
        [models[3], "24", "0.042 [0.007, 0.202]", ">0.999"],
    ]
    table_43_rows = [
        [models[0], "+836", "<0.001", "2.218 [1.43, 3.44]", "<0.001"],
        [models[1], "+689", "0.004", "1.289 [0.94, 1.77]", "0.117"],
        [models[2], "+17", "0.728", "2.001 [1.37, 2.93]", "<0.001"],
        [models[3], "-140", "0.093", "1.772 [1.26, 2.50]", "0.001"],
    ]
    table_44_rows = [
        [models[0], "pass", "pass", "pass"],
        [models[1], "pass", "pass", "fail"],
        [models[2], "fail", "fail", "fail"],
        [models[3], "fail", "fail", "fail"],
    ]
    if compact and math_headers and tight_columns:
        suffix = f"{lang}_compact_math_v3"
    elif compact and math_headers:
        suffix = f"{lang}_compact_math_v2"
    elif compact:
        suffix = f"{lang}_compact"
    else:
        suffix = lang

    return [
        render_table(
            f"table_4_1_sd_behavioral_{suffix}.png",
            lang,
            table_41_headers,
            table_41_rows,
            [720, 620, 1000, 260, 520, 850, 450],
            groups=table_41_groups,
            compact=compact,
            regular_text=math_headers,
        ),
        render_table(
            f"table_4_2_sd_verbal_{suffix}.png",
            lang,
            table_42_headers,
            table_42_rows,
            [520, 220, 850, 220] if tight_columns else [780, 500, 1080, 350],
            compact=compact,
            regular_text=math_headers,
            tight=tight_columns,
        ),
        render_table(
            f"table_4_3_sd_cognitive_{suffix}.png",
            lang,
            table_43_headers,
            table_43_rows,
            [520, 300, 170, 750, 170] if tight_columns else [740, 570, 260, 1190, 260],
            groups=[(1, 2, "Test a"), (3, 4, "Test b")],
            compact=compact,
            regular_text=math_headers,
            tight=tight_columns,
        ),
        render_table(
            f"table_4_4_channel_summary_{suffix}.png",
            lang,
            table_44_headers,
            table_44_rows,
            [850, 620, 620, 620],
            statuses=True,
            compact=compact,
            regular_text=math_headers,
        ),
    ]


if __name__ == "__main__":
    for language in ("ko", "en"):
        for path in build_language(language):
            print(path)
