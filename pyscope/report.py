"""HTML report generation.

Produces a self-contained, interactive HTML report with a bundled SVG
dependency graph.  No external CDNs, remote fonts or network access required.
"""

from __future__ import annotations

import html
import json

from .analysis import AnalysisResult
from .exporters import to_json_dict
from .localization import LANGUAGES

REPORT_TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        "report.title": "PyScope — отчёт об архитектуре кода",
        "report.subtitle": "Статический анализ Python-проекта",
        "report.project_overview": "Обзор проекта",
        "report.file_statistics": "Статистика файлов",
        "report.package_structure": "Структура пакетов",
        "report.dependency_graph": "Граф зависимостей",
        "report.circular_dependencies": "Циклические зависимости",
        "report.complexity": "Сложность",
        "report.largest_files": "Самые большие файлы",
        "report.inventory": "Инвентаризация функций и классов",
        "report.findings": "Рекомендации по архитектуре",
        "report.search": "Поиск",
        "report.module_details": "Подробности модуля",
        "report.export": "Экспорт",
        "report.no_files": "Файлы не найдены",
        "report.skipped": "Пропущено файлов: {count}",
        "report.failed": "Ошибок при анализе: {count}",
        "report.language": "Язык",
        "report.theme": "Тема",
        "report.russian": "Русский",
        "report.english": "English",
        "report.light": "Светлая",
        "report.dark": "Тёмная",
        "report.graph.filter_package": "Фильтр по пакету",
        "report.graph.show_all": "Все",
        "report.graph.cycles": "Циклы",
        "report.graph.nodes": "Модули",
        "report.graph.edges": "Зависимости",
        "report.graph.no_graph": "Граф пуст — внутренних зависимостей не обнаружено.",
        "report.graph.node_modules": "модулей",
        "report.graph.node_deps": "зависимостей",
        "report.graph.click": "Кликните по узлу для выделения зависимостей.",
        "report.cycle.none": "Циклических зависимостей не обнаружено.",
        "report.cycle.explanation": "Циклы показаны красным на графе. Разорвите цикл, перенеся общий код в отдельный модуль.",
        "report.cycle.title": "Цикл",
        "report.table.module": "Модуль",
        "report.table.imports": "Импорты",
        "report.table.classification": "Классификация",
        "report.table.line": "Строка",
        "report.finding.severity": "Критичность",
        "report.finding.category": "Категория",
        "report.finding.recommendation": "Рекомендация",
        "report.finding.no_findings": "Рекомендаций по архитектуре не обнаружено.",
        "report.metric.complexity": "Сложность",
        "report.metric.lines": "Строк",
        "report.metric.args": "Аргументов",
        "report.metric.methods": "Методов",
        "report.metric.nesting": "Вложенность",
        "report.metric.returns": "return",
        "report.metric.annotations": "Аннотации",
        "report.metric.docstring": "docstring",
        "report.inventory.no_items": "Нет элементов.",
        "report.export.json": "JSON",
        "report.export.dot": "DOT (Graphviz)",
        "report.export.mermaid": "Mermaid",
        "report.export.download": "Скачать",
        "report.overview.total_files": "Всего файлов",
        "report.overview.total_modules": "Модулей",
        "report.overview.total_lines": "Строк кода",
        "report.overview.classes": "Классов",
        "report.overview.functions": "Функций",
        "report.overview.cycles": "Циклов",
        "report.overview.findings": "Рекомендаций",
        "report.module.imports_title": "Импорты",
        "report.module.classes_title": "Классы",
        "report.module.functions_title": "Функции",
        "report.module.no_classes": "Нет классов.",
        "report.module.no_functions": "Нет функций.",
        "report.module.no_imports": "Нет импортов.",
        "report.module.label_path": "Путь",
        "report.module.label_module": "Модуль",
        "report.module.label_lines": "Строк",
        "report.module.label_code": "Кода",
        "report.module.label_comments": "Комментариев",
        "report.module.label_imports": "Импортов",
        "report.module.label_classes": "Классов",
        "report.module.label_functions": "Функций",
        "report.nav.overview": "Обзор",
        "report.nav.files": "Файлы",
        "report.nav.graph": "Граф",
        "report.nav.insights": "Рекомендации",
        "report.nav.inventory": "Инвентаризация",
        "report.packages.files": "Файлов",
        "report.packages.lines": "Строк",
        "report.packages.classes": "Классов",
        "report.packages.functions": "Функций",
        "report.inventory.type": "Тип",
        "report.inventory.name": "Имя",
        "report.inventory.line": "Строка",
        "report.largest.classes": "Классов",
        "report.largest.functions": "Функций",
        "report.files.lines": "Строк",
        "report.files.code": "Кода",
        "report.files.error": "Ошибка",
    },
    "en": {
        "report.title": "PyScope — Code Architecture Report",
        "report.subtitle": "Static analysis of a Python project",
        "report.project_overview": "Project Overview",
        "report.file_statistics": "File Statistics",
        "report.package_structure": "Package Structure",
        "report.dependency_graph": "Dependency Graph",
        "report.circular_dependencies": "Circular Dependencies",
        "report.complexity": "Complexity",
        "report.largest_files": "Largest Files",
        "report.inventory": "Function and Class Inventory",
        "report.findings": "Architecture Recommendations",
        "report.search": "Search",
        "report.module_details": "Module Details",
        "report.export": "Export",
        "report.no_files": "No files found",
        "report.skipped": "Skipped files: {count}",
        "report.failed": "Analysis failures: {count}",
        "report.language": "Language",
        "report.theme": "Theme",
        "report.russian": "Русский",
        "report.english": "English",
        "report.light": "Light",
        "report.dark": "Dark",
        "report.graph.filter_package": "Filter by package",
        "report.graph.show_all": "All",
        "report.graph.cycles": "Cycles",
        "report.graph.nodes": "Modules",
        "report.graph.edges": "Dependencies",
        "report.graph.no_graph": "Graph is empty — no internal dependencies detected.",
        "report.graph.node_modules": "modules",
        "report.graph.node_deps": "dependencies",
        "report.graph.click": "Click a node to highlight its dependencies.",
        "report.cycle.none": "No circular dependencies detected.",
        "report.cycle.explanation": "Cycles are shown in red on the graph. Break a cycle by moving shared code into a separate module.",
        "report.cycle.title": "Cycle",
        "report.table.module": "Module",
        "report.table.imports": "Imports",
        "report.table.classification": "Classification",
        "report.table.line": "Line",
        "report.finding.severity": "Severity",
        "report.finding.category": "Category",
        "report.finding.recommendation": "Recommendation",
        "report.finding.no_findings": "No architecture recommendations detected.",
        "report.metric.complexity": "Complexity",
        "report.metric.lines": "Lines",
        "report.metric.args": "Args",
        "report.metric.methods": "Methods",
        "report.metric.nesting": "Nesting",
        "report.metric.returns": "Returns",
        "report.metric.annotations": "Annotations",
        "report.metric.docstring": "Docstring",
        "report.inventory.no_items": "No items.",
        "report.export.json": "JSON",
        "report.export.dot": "DOT (Graphviz)",
        "report.export.mermaid": "Mermaid",
        "report.export.download": "Download",
        "report.overview.total_files": "Total files",
        "report.overview.total_modules": "Modules",
        "report.overview.total_lines": "Lines of code",
        "report.overview.classes": "Classes",
        "report.overview.functions": "Functions",
        "report.overview.cycles": "Cycles",
        "report.overview.findings": "Recommendations",
        "report.module.imports_title": "Imports",
        "report.module.classes_title": "Classes",
        "report.module.functions_title": "Functions",
        "report.module.no_classes": "No classes.",
        "report.module.no_functions": "No functions.",
        "report.module.no_imports": "No imports.",
        "report.module.label_path": "Path",
        "report.module.label_module": "Module",
        "report.module.label_lines": "Lines",
        "report.module.label_code": "Code lines",
        "report.module.label_comments": "Comments",
        "report.module.label_imports": "Imports",
        "report.module.label_classes": "Classes",
        "report.module.label_functions": "Functions",
        "report.nav.overview": "Overview",
        "report.nav.files": "Files",
        "report.nav.graph": "Graph",
        "report.nav.insights": "Insights",
        "report.nav.inventory": "Inventory",
        "report.packages.files": "Files",
        "report.packages.lines": "Lines",
        "report.packages.classes": "Classes",
        "report.packages.functions": "Functions",
        "report.inventory.type": "Type",
        "report.inventory.name": "Name",
        "report.inventory.line": "Line",
        "report.largest.classes": "Classes",
        "report.largest.functions": "Functions",
        "report.files.lines": "Lines",
        "report.files.code": "Code",
        "report.files.error": "Error",
    },
}


def _t(key: str, language: str, **kwargs: str) -> str:
    table = REPORT_TRANSLATIONS.get(language, REPORT_TRANSLATIONS["ru"])
    message = table.get(key, key)
    if kwargs:
        try:
            message = message.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return message


CSS = """
:root{
  --bg:#ffffff;--fg:#1a1a1a;--muted:#666666;--border:#d9d9d9;
  --card:#f7f7f7;--accent:#2563eb;--accent-hover:#1d4ed8;
  --danger:#b91c1c;--warn:#b45309;--success:#15803d;--info:#1d4ed8;
  --cycle:#dc2626;--cycle-bg:#fdecea;--edge:#9ca3af;--edge-active:#2563eb;
  --code-bg:#f3f4f6;--table-head:#f2f2f2;--shadow:0 1px 2px rgba(0,0,0,0.06);
}
[data-theme="dark"]{
  --bg:#0f172a;--fg:#e2e8f0;--muted:#94a3b8;--border:#334155;
  --card:#1e293b;--accent:#3b82f6;--accent-hover:#60a5fa;
  --danger:#f87171;--warn:#fbbf24;--success:#4ade80;--info:#60a5fa;
  --cycle:#f87171;--cycle-bg:#450a0a;--edge:#475569;--edge-active:#3b82f6;
  --code-bg:#0b1120;--table-head:#1e293b;--shadow:0 1px 2px rgba(0,0,0,0.4);
}
* { box-sizing: border-box; }
html, body { margin:0; padding:0; background:var(--bg); color:var(--fg);
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  line-height:1.5; }
a { color:var(--accent); text-decoration:none; }
a:hover { text-decoration:underline; }
button { cursor:pointer; background:var(--card); border:1px solid var(--border);
  color:var(--fg); padding:0.45rem 0.9rem; border-radius:6px; font-size:0.9rem; }
button:hover { background:var(--border); }
button.primary { background:var(--accent); color:#fff; border-color:var(--accent); }
button.primary:hover { background:var(--accent-hover); }
button.small { padding:0.25rem 0.55rem; font-size:0.8rem; }
button.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.toolbar{ display:flex; gap:0.5rem; align-items:center; flex-wrap:wrap; margin-bottom:1rem; }
.select, input { background:var(--card); border:1px solid var(--border); color:var(--fg);
  padding:0.4rem 0.6rem; border-radius:6px; font-size:0.9rem; }
.header{ padding:1.5rem 1rem; border-bottom:1px solid var(--border); }
.header h1{ margin:0 0 0.5rem 0; font-size:1.5rem; }
.header .sub{ color:var(--muted); font-size:0.95rem; }
.container{ max-width:1200px; margin:0 auto; padding:0 1rem 2rem; }
.section{ margin-bottom:2rem; }
.section h2{ font-size:1.25rem; margin:0 0 1rem 0; padding-bottom:0.4rem;
  border-bottom:2px solid var(--border); }
.grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:0.75rem; }
.card{ background:var(--card); border:1px solid var(--border); border-radius:8px;
  padding:0.9rem 1rem; box-shadow:var(--shadow); }
.card .value{ font-size:1.75rem; font-weight:700; color:var(--fg); }
.card .label{ color:var(--muted); font-size:0.85rem; margin-top:0.25rem; }
.card.primary .value{ color:var(--accent); }
.card.danger .value{ color:var(--danger); }
.card.warn .value{ color:var(--warn); }
table{ width:100%; border-collapse:collapse; font-size:0.88rem; margin-bottom:1rem; }
th, td{ border:1px solid var(--border); padding:0.5rem 0.7rem; text-align:left;
  background:var(--card); }
th{ background:var(--table-head); color:var(--fg); font-size:0.8rem; }
tr:nth-child(even) td{ background:#fafafa; }
[data-theme="dark"] tr:nth-child(even) td{ background:#16213a; }
.badge{ display:inline-block; padding:0.1rem 0.5rem; border-radius:4px;
  font-size:0.75rem; font-weight:700; text-transform:uppercase; }
.badge.high{ background:var(--cycle-bg); color:var(--danger); border:1px solid var(--danger); }
.badge.medium{ background:#fdf3e7; color:var(--warn); border:1px solid var(--warn); }
.badge.low{ background:#eef7f0; color:var(--success); border:1px solid var(--success); }
.badge.info{ background:#eef4fb; color:var(--info); border:1px solid var(--info); }
[data-theme="dark"] .badge.low{ background:#0b2217; }
[data-theme="dark"] .badge.info{ background:#0b1a2b; }
.empty{ color:var(--muted); padding:2rem; text-align:center; }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  font-size:0.85rem; background:var(--code-bg); padding:0.15rem 0.4rem; border-radius:4px; }
ul{ margin:0.5rem 0 0.5rem 1.2rem; color:var(--fg); }
li{ margin-bottom:0.35rem; }
.finding{ border:1px solid var(--border); border-radius:8px; padding:0.75rem 1rem;
  margin-bottom:0.75rem; background:var(--card); }
.finding .head{ display:flex; justify-content:space-between; gap:0.5rem; margin-bottom:0.4rem; }
.finding .title{ font-weight:700; }
.finding .meta{ color:var(--muted); font-size:0.8rem; display:flex; gap:0.6rem; flex-wrap:wrap; }
.finding p{ margin:0.4rem 0 0 0; color:var(--fg); }
.finding .rec{ margin-top:0.4rem; }
.finding .rec b{ color:var(--fg); }
.graph-wrap{ position:relative; border:1px solid var(--border); border-radius:8px;
  background:var(--bg); overflow:hidden; min-height:520px; }
svg.graph{ width:100%; height:560px; display:block; cursor:grab; }
svg.graph:active{ cursor:grabbing; }
.node{ cursor:pointer; stroke-width:1.5px; }
.node circle{ fill:#fff; stroke:var(--edge); stroke-width:1.5px; }
.node text{ font-size:10px; fill:var(--fg); pointer-events:none; }
.node.active circle{ stroke:var(--accent); stroke-width:2.5px; fill:var(--accent); }
.node.active text{ fill:#fff; font-weight:700; }
.node.cycle circle{ fill:var(--cycle-bg); stroke:var(--cycle); }
.node.cycle.active circle{ fill:var(--cycle); stroke:#fff; }
.edge{ fill:none; stroke:var(--edge); stroke-width:1.2px; opacity:0.55; }
.edge.active{ stroke:var(--edge-active); stroke-width:2.2px; opacity:1; }
.edge.cycle{ stroke:var(--cycle); opacity:0.9; }
.legend{ display:flex; gap:0.75rem; align-items:center; flex-wrap:wrap; margin-top:0.5rem; font-size:0.85rem; color:var(--muted); }
.legend .swatch{ width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:0.4rem; }
.tabs{ display:flex; gap:0.25rem; margin-bottom:1rem; border-bottom:1px solid var(--border); }
.tabs button{ border-bottom:3px solid transparent; margin-bottom:-1px; }
.tabs button.active{ border-bottom-color:var(--accent); color:var(--accent); font-weight:700; }
.tabpanel{ display:none; }
.tabpanel.active{ display:block; }
.kv{ width:100%; border-collapse:collapse; font-size:0.86rem; }
.kv td{ padding:0.35rem 0.6rem; border:1px solid var(--border); background:var(--card); }
.kv td.k{ width:35%; color:var(--muted); font-weight:600; }
details{ border:1px solid var(--border); border-radius:8px; padding:0.5rem; margin-bottom:0.5rem;
  background:var(--card); }
summary{ font-weight:700; cursor:pointer; list-style:none; }
summary::-webkit-details-marker{ display:none; }
code{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:0.85rem;
  background:var(--code-bg); padding:0.1rem 0.3rem; border-radius:3px; }
.smallnote{ color:var(--muted); font-size:0.8rem; }
"""

JS = r"""
const DATA = JSON.parse(document.getElementById('pyscope-data').textContent);
const CFG = JSON.parse(document.getElementById('pyscope-config').textContent);
const LANG = (localStorage.getItem('pyscope-lang') || CFG.language || 'ru');
const savedTheme = localStorage.getItem('pyscope-theme');
if (savedTheme) { 
  document.documentElement.setAttribute('data-theme', savedTheme);
  if (document.body) document.body.setAttribute('data-theme', savedTheme);
}
const TR = __TRANSLATIONS__;

function t(key, args){ let m = (TR[LANG] && TR[LANG][key]) ? TR[LANG][key] : key; if(args){ try{ Object.keys(args).forEach(k=>{ m=m.replace(new RegExp('{'+k+'}','g'), args[k]); }); }catch(e){} } return m; }
function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function $(sel){ return document.querySelector(sel); }
function $$(sel){ return document.querySelectorAll(sel); }
function setLang(lang){ localStorage.setItem('pyscope-lang',lang); location.reload(); }
function setTheme(theme){ document.documentElement.setAttribute('data-theme',theme); localStorage.setItem('pyscope-theme',theme); }
function renderText(){ $$('[data-i18n]').forEach(el=>{ const k=el.getAttribute('data-i18n'); const a = el.dataset.i18nArgs ? JSON.parse(el.dataset.i18nArgs) : {}; el.textContent = t(k,a); }); }

function download(name, text, type){ const blob=new Blob([text],{type:type}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=name; document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url); }

function renderOverview(){ const s = DATA.summary || {}; const container=$('#overview-cards'); container.innerHTML='';
  const cards=[['report.overview.total_files',s.files||0,''],['report.overview.total_modules',s.modules||0,''],
    ['report.overview.total_lines',s.lines||0,''],['report.overview.classes',s.classes||0,''],
    ['report.overview.functions',s.functions||0,''],['report.overview.cycles',s.cycles||0,'danger'],
    ['report.overview.findings',s.findings||0,'']];
  cards.forEach(([key,val,cls])=>{ const c=document.createElement('div'); c.className='card'+(cls?' '+cls:'');
    c.innerHTML='<div class="value">'+val+'</div><div class="label" data-i18n="'+key+'">'+t(key)+'</div>';
    container.appendChild(c); });
  const skipped=s.skipped||0, failed=s.failed||0;
  const notice=[]; if(skipped) notice.push('<div class="empty" style="display:inline-block;margin-right:1rem;">'+t('report.skipped',{count:skipped})+'</div>');
  if(failed) notice.push('<div class="empty" style="display:inline-block;">'+t('report.failed',{count:failed})+'</div>');
  $('#overview-notice').innerHTML = notice.join(' ');
}

function renderFiles(){ const files = DATA.files || []; const tb = $('#files-body'); tb.innerHTML='';
  files.forEach(f=>{ const tr=document.createElement('tr');
    tr.innerHTML='<td><span class="mono">'+esc(f.path)+'</span></td>'+
      '<td>'+esc(f.module||'-')+'</td>'+
      '<td>'+f.line_count+'</td><td>'+f.code_line_count+'</td>'+
      '<td>'+(f.syntax_error?'<span class="badge danger">'+esc(f.syntax_error)+'</span>':'-')+'</td>';
    tb.appendChild(tr); });
}

function renderPackages(){ const files = DATA.files||[]; const pkgs={};
  files.forEach(f=>{ const mod=f.module||''; const top=mod.split('.')[0]||'(root)';
    if(!pkgs[top]) pkgs[top]={files:0,lines:0,classes:0,functions:0};
    pkgs[top].files++; pkgs[top].lines+=f.line_count||0;
    pkgs[top].classes+=(f.classes||[]).length; pkgs[top].functions+=(f.functions||[]).length;
  });
  const tb=$('#packages-body'); tb.innerHTML='';
  Object.entries(pkgs).sort().forEach(([name,info])=>{ const tr=document.createElement('tr');
    tr.innerHTML='<td><span class="mono">'+esc(name)+'</span></td>'+
      '<td>'+info.files+'</td><td>'+info.lines+'</td><td>'+info.classes+'</td><td>'+info.functions+'</td>';
    tb.appendChild(tr); });
}

function renderGraph(){ const graph = DATA.dependency_graph || {}; const edges = graph.edges || [];
  const modules = graph.modules || {}; const cycleMods = new Set((graph.cycles||[]).flat());
  const wrap = $('#graph-svg'); wrap.innerHTML='';
  if(!edges.length){ wrap.innerHTML='<div class="empty">'+t('graph.no_graph')+'</div>'; return; }
  const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('class','graph'); svg.setAttribute('tabindex','0');
  const defs = document.createElementNS('http://www.w3.org/2000/svg','defs');
  const marker = document.createElementNS('http://www.w3.org/2000/svg','marker');
  marker.setAttribute('id','arrow'); marker.setAttribute('viewBox','0 0 10 10');
  marker.setAttribute('refX','9'); marker.setAttribute('refY','5'); marker.setAttribute('markerWidth','6'); marker.setAttribute('markerHeight','6'); marker.setAttribute('orient','auto');
  const path = document.createElementNS('http://www.w3.org/2000/svg','path');
  path.setAttribute('d','M 0 0 L 10 5 L 0 10 z'); path.setAttribute('fill','var(--edge)');
  marker.appendChild(path); defs.appendChild(marker); svg.appendChild(defs);
  const g = document.createElementNS('http://www.w3.org/2000/svg','g');
  svg.appendChild(g);
  $('#graph-viewport').appendChild(svg);

  const modList = Object.keys(modules).sort();
  const cols = Math.ceil(Math.sqrt(modList.length)) || 1;
  const cellW = 210, cellH = 100;
  const pos = {}; modList.forEach((m,i)=>{ const r=Math.floor(i/cols), c=i%cols; pos[m]={x:c*cellW+105,y:r*cellH+55}; });
  const edgeSet = new Set();
  edges.forEach(e=>{ if(e.classification!=='internal') return; const key=e.source+'|'+e.target; if(edgeSet.has(key)) return; edgeSet.add(key);
    const s=pos[e.source], t=pos[e.target]; if(!s||!t) return;
    const isCycle = cycleMods.has(e.source) && cycleMods.has(e.target);
    const el = document.createElementNS('http://www.w3.org/2000/svg','path');
    const mx=(s.x+t.x)/2, my=(s.y+t.y)/2;
    el.setAttribute('d','M '+s.x+' '+s.y+' Q '+mx+' '+(my-70)+' '+t.x+' '+t.y);
    el.setAttribute('class','edge'+(isCycle?' cycle':''));
    el.setAttribute('marker-end','url(#arrow)');
    el.dataset.source=e.source; el.dataset.target=e.target;
    g.appendChild(el);
  });
  modList.forEach(m=>{ const p=pos[m]; const isCycle=cycleMods.has(m);
    const node = document.createElementNS('http://www.w3.org/2000/svg','g');
    node.setAttribute('class','node'+(isCycle?' cycle':'')); node.dataset.mod=m;
    const deg = ((modules[m]&&modules[m].imports?modules[m].imports.length:0)+(modules[m]&&modules[m].exports?modules[m].exports.length:0));
    const r = 24 + Math.min(14, Math.max(0, deg));
    const circle = document.createElementNS('http://www.w3.org/2000/svg','circle');
    circle.setAttribute('cx',p.x); circle.setAttribute('cy',p.y); circle.setAttribute('r',r);
    node.appendChild(circle);
    const text = document.createElementNS('http://www.w3.org/2000/svg','text');
    text.setAttribute('x',p.x); text.setAttribute('y',p.y+4); text.setAttribute('text-anchor','middle');
    text.textContent = m.length>16?m.slice(0,13)+'...':m;
    node.appendChild(text);
    const title=document.createElementNS('http://www.w3.org/2000/svg','title');
    title.textContent = m+'\\nimports: '+(modules[m]&&modules[m].imports?modules[m].imports.length:0)+' / depended on by: '+(modules[m]&&modules[m].exports?modules[m].exports.length:0);
    node.appendChild(title);
    g.appendChild(node);
  });
  let activeMod = null;
  function highlight(mod){
    activeMod = mod;
    $$('.node').forEach(n=>{ n.classList.toggle('active', n.dataset.mod===mod); });
    $$('.edge').forEach(e=>{
      const show = !mod || e.dataset.source===mod || e.dataset.target===mod;
      e.classList.toggle('active', show);
      e.style.opacity = show? (mod?1:0.55) : 0.12;
    });
  }
  $$('.node').forEach(n=>{ n.addEventListener('click',()=>{ highlight(n.dataset.mod); }); });
  svg.addEventListener('click',()=>{ highlight(null); });
  let scale=1, tx=0, ty=0, dragging=false, startX=0,startY=0;
  function applyTransform(){ g.setAttribute('transform','translate('+tx+','+ty+') scale('+scale+')'); }
  svg.addEventListener('mousedown',e=>{ if(e.target.tagName==='svg'){ dragging=true; startX=e.clientX-tx; startY=e.clientY-ty; } });
  window.addEventListener('mousemove',e=>{ if(!dragging) return; tx=e.clientX-startX; ty=e.clientY-startY; applyTransform(); });
  window.addEventListener('mouseup',()=>{ dragging=false; });
  svg.addEventListener('wheel',e=>{ e.preventDefault(); const ds = e.deltaY>0?0.9:1.1; scale=Math.min(3,Math.max(0.4,scale*ds)); applyTransform(); },{passive:false});
  applyTransform();
  const legend = $('#graph-legend'); legend.innerHTML='';
  const items=[['cycle',t('graph.cycles'),'var(--cycle)'],['node',t('graph.nodes'),'var(--edge)'],['edge',t('graph.edges'),'var(--edge-active)']];
  items.forEach(([cls,label,color])=>{ const d=document.createElement('div'); d.className='legend-item';
    d.innerHTML='<span class="swatch" style="background:'+color+';'+(cls==='cycle'?'border:1px solid var(--cycle);':'')+'"></span>'+esc(label);
    legend.appendChild(d); });
  $('#graph-clickhint').textContent = t('graph.click');
  // package filter
  const sel=$('#pkg-filter');
  if(sel){
    const pkgs=new Set(); Object.keys(modules).forEach(m=>{ pkgs.add(m.split('.')[0]||'(root)'); });
    sel.innerHTML='<option data-i18n="report.graph.show_all">'+t('report.graph.show_all')+'</option>';
    [...pkgs].sort().forEach(p=>{ const o=document.createElement('option'); o.value=p; o.textContent=p; sel.appendChild(o); });
    sel.addEventListener('change',()=>{ const val=sel.value; $$('.node').forEach(n=>{ const m=n.dataset.mod; const top=m.split('.')[0]||'(root)'; n.style.display = (val===t('report.graph.show_all')||val==='Все'||top===val)?'':'none'; }); });
  }
}

function renderCycles(){ const cycles = (DATA.dependency_graph||{}).cycles || []; const container=$('#cycles-list'); container.innerHTML='';
if(!cycles.length){ container.innerHTML='<div class="empty">'+t('cycle.none')+'</div>'; return; }
cycles.forEach(cycle=>{     const d=document.createElement('div'); d.className='finding';
  d.innerHTML='<div class="head"><span class="title">'+t('report.cycle.title')+'</span><span class="badge high">'+t('finding.severity')+': high</span></div>'+
    '<p class="mono">'+esc(cycle.join(' → '))+'</p>'+
    '<p class="smallnote">'+t('cycle.explanation')+'</p>';
  container.appendChild(d); });
}

function renderComplexity(){ let items=[];
(DATA.files||[]).forEach(f=>{
  (f.functions||[]).forEach(fn=> items.push({kind:'function',file:f.path,name:fn.name,line:fn.line,complexity:fn.complexity}));
  (f.classes||[]).forEach(c=>{ c.methods.forEach(m=> items.push({kind:'method',file:f.path,name:c.name+'.'+m.name,line:m.line,complexity:m.complexity})); });
});
items.sort((a,b)=>b.complexity-a.complexity);
const tb=$('#complexity-body'); tb.innerHTML='';
items.slice(0,15).forEach(it=>{ const tr=document.createElement('tr');
  tr.innerHTML='<td>'+esc(it.kind)+'</td><td><span class="mono">'+esc(it.file)+'</span></td>'+
    '<td>'+esc(it.name)+'</td><td>'+it.line+'</td><td>'+it.complexity+'</td>';
  tb.appendChild(tr); });
}

function renderLargest(){ const files=(DATA.files||[]).slice().sort((a,b)=>(b.line_count||0)-(a.line_count||0));
  const tb=$('#largest-body'); tb.innerHTML='';
  files.slice(0,10).forEach(f=>{ const tr=document.createElement('tr');
    tr.innerHTML='<td><span class="mono">'+esc(f.path)+'</span></td><td>'+f.line_count+'</td><td>'+f.code_line_count+'</td><td>'+(f.classes||[]).length+'</td><td>'+(f.functions||[]).length+'</td>';
    tb.appendChild(tr); });
}

function renderInventory(){ const container=$('#inventory-body'); container.innerHTML='';
(DATA.files||[]).forEach(f=>{
  const sec=document.createElement('div'); sec.className='finding';
  let h='<div class="head"><span class="title">'+esc(f.path)+'</span><span class="mono">'+esc(f.module||'-')+'</span></div>';
  h+='<div class="meta"><b>'+t('report.module.label_classes')+':</b> '+(f.classes||[]).length+
    ' <b>'+t('report.module.label_functions')+':</b> '+(f.functions||[]).length+'</div>';
  if((f.classes||[]).length){ h+='<h4 style="margin:.4rem 0 .2rem 0">'+t('report.module.classes_title')+'</h4><ul>';
    f.classes.forEach(c=>{ h+='<li><b>'+esc(c.name)+'</b> '+t('report.metric.methods')+': '+c.public_method_count+'</li>'; });
    h+='</ul>'; } else { h+='<p class="empty">'+t('report.module.no_classes')+'</p>'; }
  if((f.functions||[]).length){ h+='<h4 style="margin:.4rem 0 .2rem 0">'+t('report.module.functions_title')+'</h4><ul>';
    f.functions.forEach(fn=>{ h+='<li><b>'+esc(fn.name)+'</b> '+t('report.metric.complexity')+': '+fn.complexity+'</li>'; });
    h+='</ul>'; } else { h+='<p class="empty">'+t('report.module.no_functions')+'</p>'; }
  sec.innerHTML=h; container.appendChild(sec);
});
}

function renderFindings(){ const findings = DATA.findings||[]; const container=$('#findings-list'); container.innerHTML='';
if(!findings.length){ container.innerHTML='<div class="empty">'+t('finding.no_findings')+'</div>'; return; }
findings.forEach(f=>{ const d=document.createElement('div'); d.className='finding';
  d.innerHTML='<div class="head"><span class="title">'+esc(f.title)+'</span><span class="badge '+ (f.severity||'low') +'">'+t('finding.severity')+': '+(f.severity||'low')+'</span></div>'+
    '<div class="meta"><span class="badge">'+esc(f.category||'')+'</span>'+
    (f.file?' <span class="mono">'+esc(f.file)+'</span>': '') +
    (f.line?' <span class="mono">line '+f.line+'</span>': '')+'</div>'+
    '<p>'+esc(f.explanation||'')+'</p>'+
    '<p class="rec"><b>'+t('finding.recommendation')+':</b> '+esc(f.recommendation||'')+'</p>';
  container.appendChild(d); });
}

function renderModuleDetails(){ const files = DATA.files||[]; const container=$('#module-details-body'); container.innerHTML='';
files.forEach(f=>{
  const det=document.createElement('details'); det.className='finding';
  const summ=document.createElement('summary'); summ.textContent = esc(f.path)+' ('+esc(f.module||'-')+')';
  det.appendChild(summ);
  let body='<div class="kv">';
  body+='<tr><td class="k">'+t('report.module.label_path')+'</td><td><span class="mono">'+esc(f.path)+'</span></td></tr>';
  body+='<tr><td class="k">'+t('report.module.label_module')+'</td><td>'+esc(f.module||'-')+'</td></tr>';
  body+='<tr><td class="k">'+t('report.module.label_lines')+'</td><td>'+f.line_count+'</td></tr>';
  body+='<tr><td class="k">'+t('report.module.label_code')+'</td><td>'+f.code_line_count+'</td></tr>';
  body+='<tr><td class="k">'+t('report.module.label_comments')+'</td><td>'+f.comment_count+'</td></tr>';
  body+='<tr><td class="k">'+t('report.module.label_imports')+'</td><td>'+(f.imports||[]).length+'</td></tr>';
  body+='<tr><td class="k">'+t('report.module.label_classes')+'</td><td>'+(f.classes||[]).length+'</td></tr>';
  body+='<tr><td class="k">'+t('report.module.label_functions')+'</td><td>'+(f.functions||[]).length+'</td></tr>';
  body+='</div>';
  if((f.imports||[]).length){ body+='<h4 style="margin:.5rem 0 .25rem 0">'+t('report.module.imports_title')+'</h4><table><tr><th>'+t('report.table.module')+'</th><th>'+t('report.table.classification')+'</th><th>'+t('report.table.line')+'</th></tr>';
    f.imports.forEach(imp=>{ body+='<tr><td><span class="mono">'+esc(imp.module)+'</span></td><td>'+esc(imp.classification||'unresolved')+'</td><td>'+imp.line+'</td></tr>'; });
    body+='</table>'; } else { body+='<p class="empty">'+t('report.module.no_imports')+'</p>'; }
  const bd=document.createElement('div'); bd.innerHTML=body; det.appendChild(bd);
  container.appendChild(det);
});
}

function showTab(id){ $$('.tabpanel').forEach(el=>el.classList.remove('active')); $$('.tabs button').forEach(el=>el.classList.remove('active'));
  $( '#tab-'+id ).classList.add('active'); event.target.classList.add('active');
}

window.addEventListener('DOMContentLoaded',()=>{
  renderText(); renderOverview(); renderFiles(); renderPackages();
  renderGraph(); renderCycles(); renderComplexity(); renderLargest();
  renderInventory(); renderFindings(); renderModuleDetails();
  const langSel=$('#lang-select'); if(langSel){ langSel.value=LANG; langSel.addEventListener('change',()=>setLang(langSel.value)); }
  const themeSel=$('#theme-select'); if(themeSel){ themeSel.value=CFG.theme||'light'; themeSel.addEventListener('change',()=>setTheme(themeSel.value)); }
});
"""

TEMPLATE = r"""<!DOCTYPE html>
<html lang="{lang}" dir="{dir}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
{css}
</style>
</head>
<body data-theme="{theme}">
<div class="header">
  <h1 data-i18n="report.title">{title}</h1>
  <div class="sub" data-i18n="report.subtitle">{subtitle}</div>
  <div class="toolbar" style="margin-top:0.75rem;">
    <label style="font-size:0.85rem;color:var(--muted);" data-i18n="report.language"></label>
    <select id="lang-select" class="select" style="margin-left:0.3rem;">
      <option value="ru" data-i18n="report.russian">Русский</option>
      <option value="en" data-i18n="report.english">English</option>
    </select>
    <label style="font-size:0.85rem;color:var(--muted);margin-left:1rem;" data-i18n="report.theme"></label>
    <select id="theme-select" class="select" style="margin-left:0.3rem;">
      <option value="light" data-i18n="report.light">Светлая</option>
      <option value="dark" data-i18n="report.dark">Тёмная</option>
    </select>
  </div>
</div>
<div class="container">
  <div class="toolbar">
    <button class="primary small" onclick="download('pyscope-report.json', document.getElementById('pyscope-data').textContent, 'application/json')" data-i18n="report.export.download"></button>
    <button class="small" onclick="download('pyscope-graph.dot', generateDot(), 'text/plain')" data-i18n="report.export.dot"></button>
    <button class="small" onclick="download('pyscope-graph.mmd', generateMermaid(), 'text/plain')" data-i18n="report.export.mermaid"></button>
    <span class="smallnote" style="margin-left:auto;" data-i18n="report.security">PyScope — статический анализ. Код проекта не выполняется.</span>
  </div>

  <div class="tabs">
    <button class="active" data-i18n="report.nav.overview" onclick="showTab('overview')">Обзор</button>
    <button data-i18n="report.nav.files" onclick="showTab('files')">Файлы</button>
    <button data-i18n="report.nav.graph" onclick="showTab('graph')">Граф</button>
    <button data-i18n="report.nav.insights" onclick="showTab('insights')">Рекомендации</button>
    <button data-i18n="report.nav.inventory" onclick="showTab('inventory')">Инвентаризация</button>
  </div>

  <div id="tab-overview" class="tabpanel active">
    <h2 data-i18n="report.project_overview">Обзор проекта</h2>
    <div id="overview-cards" class="grid"></div>
    <div id="overview-notice" class="toolbar" style="margin-top:1rem;"></div>
    <h3 data-i18n="report.package_structure">Структура пакетов</h3>
    <table>
      <tr><th data-i18n="report.table.module">Модуль</th><th data-i18n="report.packages.files">Файлов</th><th data-i18n="report.packages.lines">Строк</th><th data-i18n="report.packages.classes">Классов</th><th data-i18n="report.packages.functions">Функций</th></tr>
      <tbody id="packages-body"></tbody>
    </table>
  </div>

  <div id="tab-files" class="tabpanel">
    <h2 data-i18n="report.file_statistics">Статистика файлов</h2>
    <table>
      <tr><th data-i18n="report.table.module">Модуль</th><th data-i18n="report.table.imports">Импорты</th><th data-i18n="report.files.lines">Строк</th><th data-i18n="report.files.code">Кода</th><th data-i18n="report.files.error">Ошибка</th></tr>
      <tbody id="files-body"></tbody>
    </table>
  </div>

  <div id="tab-graph" class="tabpanel">
    <h2 data-i18n="report.dependency_graph">Граф зависимостей</h2>
    <div class="toolbar" style="margin-bottom:0.5rem;">
      <label data-i18n="report.graph.filter_package"></label>
      <select id="pkg-filter" class="select"><option data-i18n="report.graph.show_all">Все</option></select>
    </div>
    <div class="graph-wrap" id="graph-viewport"><div id="graph-svg"></div></div>
    <div id="graph-clickhint" class="smallnote" style="margin-top:0.4rem;"></div>
    <div class="legend" id="graph-legend"></div>
  </div>

  <div id="tab-insights" class="tabpanel">
    <h2 data-i18n="report.findings">Рекомендации по архитектуре</h2>
    <div id="findings-list"></div>
    <h3 data-i18n="report.circular_dependencies">Циклические зависимости</h3>
    <div id="cycles-list"></div>
    <h3 data-i18n="report.complexity">Сложность</h3>
    <table>
      <tr><th data-i18n="report.inventory.type">Тип</th><th data-i18n="report.table.module">Модуль</th><th data-i18n="report.inventory.name">Имя</th><th data-i18n="report.inventory.line">Строка</th><th data-i18n="report.metric.complexity">Сложность</th></tr>
      <tbody id="complexity-body"></tbody>
    </table>
    <h3 data-i18n="report.largest_files">Самые большие файлы</h3>
    <table>
      <tr><th data-i18n="report.table.module">Модуль</th><th data-i18n="report.metric.lines">Строк</th><th data-i18n="report.files.code">Кода</th><th data-i18n="report.largest.classes">Классов</th><th data-i18n="report.largest.functions">Функций</th></tr>
      <tbody id="largest-body"></tbody>
    </table>
  </div>

  <div id="tab-inventory" class="tabpanel">
    <h2 data-i18n="report.inventory">Инвентаризация функций и классов</h2>
    <div id="inventory-body"></div>
  </div>

  <h2 data-i18n="report.module_details">Подробности модуля</h2>
  <div id="module-details-body"></div>
</div>

<script id="pyscope-config" type="application/json">{"language":"{lang}","theme":"{theme}"}</script>
<script id="pyscope-data" type="application/json">{data}</script>
<script>const __TRANSLATIONS__ = {tr};</script>
<script>{js}</script>
<script>
function generateDot(){ const g=DATA.dependency_graph||{}; let lines=['digraph pyscope {','  rankdir=LR;','  node [shape=box];'];
  (g.edges||[]).forEach(e=>{ if(e.classification!=='internal') return; lines.push('  "'+escJs(e.source)+'" -> "'+escJs(e.target)+'";'); });
  lines.push('}'); return lines.join('\\n'); }
function generateMermaid(){ const g=DATA.dependency_graph||{}; let lines=['flowchart LR'];
  (g.edges||[]).forEach(e=>{ if(e.classification!=='internal') return; const s=escJs(e.source).replace(/[^a-zA-Z0-9]/g,'_'); const tg=escJs(e.target).replace(/[^a-zA-Z0-9]/g,'_'); lines.push('    '+s+' --> '+tg); });
  return lines.join('\\n'); }
function escJs(s){ return String(s).replace(/\\/g,'\\\\').replace(/"/g,'\\"'); }
</script>
</body>
</html>
"""


def generate_report(result: AnalysisResult, language: str = "ru", theme: str = "light") -> str:
    """Generate the self-contained HTML report string."""
    data = json.dumps(to_json_dict(result), ensure_ascii=False, indent=2)
    translations = json.dumps(REPORT_TRANSLATIONS, ensure_ascii=False)
    lang = language if language in LANGUAGES else "ru"
    dir_attr = "rtl" if lang == "ru" else "ltr"
    title = _t("report.title", lang)
    subtitle = _t("report.subtitle", lang)
    security = (
        _t("report.security", lang)
        if "report.security" in REPORT_TRANSLATIONS.get(lang, {})
        else "PyScope — static analysis. Project code is not executed."
    )
    REPORT_TRANSLATIONS[lang].setdefault("report.security", security)

    html_doc = TEMPLATE.replace("{css}", CSS).replace("{js}", JS)
    html_doc = html_doc.replace("{tr}", translations)
    # Guard against ``</script>`` sequences inside embedded JSON (XSS/breaking).
    data = data.replace("</script>", "<\\/script>")
    html_doc = html_doc.replace("{data}", data)
    html_doc = html_doc.replace("{lang}", lang)
    html_doc = html_doc.replace("{dir}", dir_attr)
    html_doc = html_doc.replace("{theme}", theme)
    html_doc = html_doc.replace("{title}", html.escape(title))
    html_doc = html_doc.replace("{subtitle}", html.escape(subtitle))
    return html_doc
