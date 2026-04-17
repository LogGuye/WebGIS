import shutil
from pathlib import Path
root = Path('media')
seed = root / 'seed'
media_props = root / 'properties'
mapping = {
    'apartment.jpg': media_props / 'apartment-1.jpg',
    'house.jpg': media_props / 'house-1.jpg',
    'land.jpg': media_props / 'land-3.jpg',
}
seed.mkdir(exist_ok=True)
for name, src in mapping.items():
    target = seed / name
    shutil.copy(src, target)
    print(f'copied {src} -> {target}')
