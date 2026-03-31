from pathlib import Path
path = Path('templates/properties/property_list.html')
text = path.read_text(encoding='utf-8')
old_button = '<button class="mobile-filter-btn" id="mobileFilterToggle">'
new_button = '<button type="button" class="mobile-filter-btn" id="mobileFilterToggle" aria-controls="filterSidebar" aria-expanded="false">'
if old_button not in text:
    raise SystemExit('button marker not found')
text = text.replace(old_button, new_button, 1)
old_aside = '<aside class="filter-sidebar" id="filterSidebar">'
new_aside = '<aside class="filter-sidebar" id="filterSidebar" role="complementary" aria-hidden="true">'
if old_aside not in text:
    raise SystemExit('aside marker not found')
text = text.replace(old_aside, new_aside, 1)
general_css = """  .filter-sidebar {
    transition: transform var(--transition);
  }

  .filter-panel {
    max-height: 100%;
  }

"""
marker = '  /* Price range inputs */'
if marker not in text:
    raise SystemExit('price range marker missing')
text = text.replace(marker, general_css + marker, 1)
old_media = "  @media (max-width: 1024px) {\n    .list-layout { grid-template-columns: 1fr; }\n    .filter-sidebar { display: none; }\n    .filter-sidebar.open { display: block; }\n  }\n\n"
if old_media not in text:
    raise SystemExit('media block missing')
new_media = "  @media (max-width: 1024px) {\n    .list-layout { grid-template-columns: 1fr; }\n    .filter-sidebar { display: none !important; }\n    body.filter-panel-open .filter-sidebar {\n      display: block !important;\n      position: fixed;\n      top: calc(var(--nav-h) + 16px);\n      left: 10px;\n      right: 10px;\n      margin: 0 auto;\n      width: min(420px, 100%);\n      max-height: calc(100vh - var(--nav-h) - 32px);\n      z-index: 1200;\n      box-shadow: 0 20px 60px rgba(0,0,0,.35);\n      transform: translateY(0);\n    }\n    .filter-panel {\n      max-height: 100%;\n      overflow-y: auto;\n    }\n    .filter-backdrop {\n      position: fixed;\n      inset: 0;\n      background: rgba(0, 0, 0, .45);\n      backdrop-filter: blur(4px);\n      opacity: 0;\n      visibility: hidden;\n      pointer-events: none;\n      transition: opacity var(--transition);\n      z-index: 1180;\n    }\n    body.filter-panel-open .filter-backdrop {\n      opacity: 1;\n      visibility: visible;\n      pointer-events: auto;\n    }\n    body.filter-panel-open {\n      overflow: hidden;\n    }\n  }\n\n"
text = text.replace(old_media, new_media, 1)
old_layout = '  </div><!-- /list-layout -->\n</div><!-- /container -->'
new_layout = '  </div><!-- /list-layout -->\n  <div class="filter-backdrop" id="filterBackdrop" aria-hidden="true"></div>\n</div><!-- /container -->'
if old_layout not in text:
    raise SystemExit('layout closure marker missing')
text = text.replace(old_layout, new_layout, 1)
snippet = Path('script_snippet.txt').read_text(encoding='utf-8')
new_script = """  /* ── Mở sidebar bộ lọc trên mobile ── */
  const mobileToggle = document.getElementById('mobileFilterToggle');
  const sidebar      = document.getElementById('filterSidebar');
  const filterBackdrop = document.getElementById('filterBackdrop');
  const body = document.body;

  const setFilterPanel = (show) => {
    if (!sidebar || !mobileToggle) return;
    sidebar.classList.toggle('open', show);
    body.classList.toggle('filter-panel-open', show);
    sidebar.setAttribute('aria-hidden', String(!show));
    mobileToggle.setAttribute('aria-expanded', String(show));
    mobileToggle.innerHTML = show
      ? '<i class="bi bi-x-lg"></i> Đóng'
      : '<i class="bi bi-sliders"></i> Bộ lọc';
    if (show) {
      const panel = sidebar.querySelector('.filter-panel');
      if (panel) panel.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const closeFilterPanel = () => setFilterPanel(false);
  const toggleFilterPanel = () => setFilterPanel(!(sidebar && sidebar.classList.contains('open')));

  mobileToggle && mobileToggle.addEventListener('click', toggleFilterPanel);
  filterBackdrop && filterBackdrop.addEventListener('click', closeFilterPanel);

  const filterForm = document.getElementById('filterForm');
  filterForm && filterForm.addEventListener('submit', closeFilterPanel);

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeFilterPanel();
  });
"""
if snippet not in text:
    raise SystemExit('script snippet not found')
text = text.replace(snippet, new_script, 1)
path.write_text(text, encoding='utf-8')