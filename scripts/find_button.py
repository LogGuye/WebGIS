from pathlib import Path
for i, line in enumerate(Path('templates/properties/property_list.html').read_text(encoding='utf-8').splitlines(), 1):
    if 'mobileFilterToggle' in line:
        print(i, line)
