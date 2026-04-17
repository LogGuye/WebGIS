from pathlib import Path
media = Path('media/properties')
svgs = [p for p in media.iterdir() if p.suffix.lower() == '.svg']
jpg_stems = {p.stem for p in media.iterdir() if p.suffix.lower() == '.jpg'}
print('jpg stem examples:', sorted(list(jpg_stems))[:10])
for svg in svgs[:10]:
    stem = svg.stem
    base = stem.split('_')[0]
    match = stem if stem in jpg_stems else base if base in jpg_stems else None
    print(svg.name, '->', match)
