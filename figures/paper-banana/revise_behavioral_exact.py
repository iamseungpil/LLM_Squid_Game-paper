from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_name("behavioral_edit_imagegen.png")
OUTPUT = ROOT / "results_behavioral_timing.png"

NAVY = "#10264B"
GRAY = "#AEB4BE"
RED = "#DE1220"


def font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


image = Image.open(SOURCE).convert("RGB")
draw = ImageDraw.Draw(image)

# Preserve provider logos/model names at left and exact λBP/HR text at right.
draw.rectangle((390, 0, 1415, image.height), fill="white")
draw.line((404, 54, 404, 905), fill=NAVY, width=2)

# One EXIT sign, reused at every exact endpoint.
exit_icon = Image.open(SOURCE).crop((1325, 108, 1392, 178)).convert("RGB")
exit_icon.thumbnail((58, 58), Image.Resampling.LANCZOS)

start_x = 405
max_width = 900
baseline_fractions = [1.000, 0.500, 0.100, 0.135]
threat_fractions = [0.272, 0.163, 0.091, 0.073]

rows = [
    # baseline label y, baseline bar box, threat label y, threat bar box
    (83, (405, 123, 0, 165), 204, (405, 245, 0, 278)),
    (327, (405, 367, 0, 409), 447, (405, 487, 0, 519)),
    (565, (405, 600, 0, 633), 643, (405, 678, 0, 706)),
    (752, (405, 785, 0, 817), 831, (405, 865, 0, 891)),
]

for index, (baseline_label_y, baseline_box, threat_label_y, threat_box) in enumerate(rows):
    baseline_width = round(max_width * baseline_fractions[index])
    threat_width = round(max_width * threat_fractions[index])

    bx0, by0, _, by1 = baseline_box
    tx0, ty0, _, ty1 = threat_box
    bx1 = bx0 + baseline_width
    tx1 = tx0 + threat_width

    draw.text((421, baseline_label_y), "Baseline", font=font(28), fill=NAVY)
    draw.rounded_rectangle((bx0, by0, bx1, by1), radius=18, fill=GRAY)
    image.paste(exit_icon, (bx1 + 7, (by0 + by1 - exit_icon.height) // 2))

    draw.text((421, threat_label_y), "Threat", font=font(28), fill=NAVY)
    draw.rounded_rectangle((tx0, ty0, tx1, ty1), radius=15, fill=RED)
    image.paste(exit_icon, (tx1 + 7, (ty0 + ty1 - exit_icon.height) // 2))

# Upscale for poster use after exact native-pixel construction.
image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
image.save(OUTPUT, optimize=True)
