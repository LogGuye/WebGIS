from pathlib import Path
path = Path('core/views.py')
data = path.read_text(encoding='utf-8')
data = data.replace('"required": true', '"required": True')
path.write_text(data, encoding='utf-8')
