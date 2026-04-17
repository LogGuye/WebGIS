from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

seed_dir = Path('media/seed')
seed_dir.mkdir(parents=True, exist_ok=True)
colors = {'apartment': (52, 152, 219), 'house': (231, 76, 60), 'land': (46, 204, 113)}
font = ImageFont.load_default()
for name, color in colors.items():
    img = Image.new('RGB', (800, 600), color)
    draw = ImageDraw.Draw(img)
    text = f"{name.title()}\nGeoEstate"
    bbox = draw.multiline_textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.multiline_text(((800 - text_w) / 2, (600 - text_h) / 2), text, font=font, fill=(255, 255, 255), align="center")
    target = seed_dir / f"{name}.jpg"
    img.save(target, "JPEG", quality=90)
    print(f"generated {target}")
