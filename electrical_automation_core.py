#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Автоматизация DXF электрических схем 3DEXPERIENCE.

Алгоритм:
- распознает блоки электрических линий по структуре, а не по BLOCKxx;
- создает слой по тексту внутри блока;
- переводит геометрию линии в ByLayer;
- назначает всем текстовым объектам стиль Arial (arial.ttf);
- формирует CSV соответствий и автономный интерактивный HTML/SVG.

Требование: pip install ezdxf
Запуск: python 3DE_Electrical_Automation.py "scheme.dxf"
"""
from pathlib import Path
import ezdxf, html, json, math, csv, re, os
import pymupdf as fitz
from ezdxf import bbox, disassemble

INVALID_LAYER_CHARS = '<>/\\\":;?*|=,`'

def safe_layer_name(text: str) -> str:
    name = ' '.join(text.strip().split())
    for ch in INVALID_LAYER_CHARS:
        name = name.replace(ch, '_')
    name = name.rstrip('.')
    return (name or 'UNNAMED')[:255]

def text_value(e):
    if e.dxftype() == 'MTEXT':
        return e.plain_text()
    return getattr(e.dxf, 'text', '')

def is_electrical_block(block):
    if block.name.startswith('*'):
        return None
    entities = list(block)
    texts = [text_value(e).strip() for e in entities if e.dxftype() in {'TEXT','MTEXT'} and text_value(e).strip()]
    geometry = [e for e in entities if e.dxftype() in {'POLYLINE','LWPOLYLINE','LINE'}]
    if len(entities) == 3 and len(texts) == 2 and texts[0] == texts[1] and len(geometry) == 1:
        return texts[0], geometry[0].dxftype()
    return None

def ensure_arial(doc):
    if 'Arial' not in doc.styles:
        doc.styles.add('Arial', font='arial.ttf')
    else:
        doc.styles.get('Arial').dxf.font = 'arial.ttf'
    # Assign Arial to all text-like entities in entity database, incl block contents / attribs.
    changed = 0
    for e in list(doc.entitydb.values()):
        if not getattr(e, 'is_alive', True):
            continue
        if e.dxftype() in {'TEXT','MTEXT','ATTRIB','ATTDEF'} and e.dxf.is_supported('style'):
            e.dxf.style = 'Arial'
            changed += 1
    return changed

def transform_dxf(source, target, csv_target=None):
    doc = ezdxf.readfile(source)
    arial_count = ensure_arial(doc)
    msp = doc.modelspace()
    inserts = [e for e in msp if e.dxftype() == 'INSERT']
    by_name = {}
    for e in inserts:
        by_name.setdefault(e.dxf.name, []).append(e)
    mapping = []
    for block in doc.blocks:
        sig = is_electrical_block(block)
        if not sig:
            continue
        electrical_name, geom_type = sig
        layer_name = safe_layer_name(electrical_name)
        if layer_name not in doc.layers:
            doc.layers.add(layer_name)
        for insert in by_name.get(block.name, []):
            insert.dxf.layer = layer_name
            insert.dxf.color = 256
        for e in block:
            e.dxf.layer = layer_name
            if e.dxftype() in {'POLYLINE','LWPOLYLINE','LINE'}:
                e.dxf.color = 256
                if e.dxftype() == 'POLYLINE':
                    for v in e.vertices:
                        v.dxf.layer = layer_name
                        v.dxf.color = 256
        mapping.append((block.name, electrical_name, layer_name, geom_type))
    doc.saveas(target)
    if csv_target:
        with open(csv_target,'w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f,delimiter=';')
            w.writerow(['Исходный блок','Текст электрической линии','Созданный слой','Тип геометрии'])
            w.writerows(mapping)
    return len(mapping), arial_count, mapping

def fmt(x):
    if abs(x) < 1e-9: x=0
    return f'{x:.4f}'.rstrip('0').rstrip('.')

def pt_svg(x,y,max_y):
    return x, max_y-y

def color_css(e, default='#454b52'):
    # Deliberately normalize to a readable monochrome technical drawing.
    return default

def render_entity(e, max_y, cls='base-geom', text_cls='base-text', include_hit=False):
    typ=e.dxftype()
    out=[]
    stroke=color_css(e)
    if typ=='LINE':
        p1=e.dxf.start; p2=e.dxf.end
        x1,y1=pt_svg(p1.x,p1.y,max_y); x2,y2=pt_svg(p2.x,p2.y,max_y)
        out.append(f'<line class="{cls}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}"/>')
        if include_hit:
            out.append(f'<line class="hit" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}"/>')
    elif typ in {'POLYLINE','LWPOLYLINE'}:
        if typ=='POLYLINE':
            pts=[v.dxf.location for v in e.vertices]
            closed=bool(e.is_closed)
        else:
            pts=[type('P',(),{'x':p[0],'y':p[1]}) for p in e.get_points('xy')]
            closed=bool(e.closed)
        s=' '.join(f'{fmt(pt_svg(p.x,p.y,max_y)[0])},{fmt(pt_svg(p.x,p.y,max_y)[1])}' for p in pts)
        tag='polygon' if closed else 'polyline'
        out.append(f'<{tag} class="{cls}" points="{s}"/>')
        if include_hit:
            out.append(f'<{tag} class="hit" points="{s}"/>')
    elif typ=='CIRCLE':
        c=e.dxf.center; x,y=pt_svg(c.x,c.y,max_y)
        out.append(f'<circle class="{cls}" cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(e.dxf.radius)}"/>')
    elif typ=='SOLID':
        pts=[e.dxf.vtx0,e.dxf.vtx1,e.dxf.vtx2,e.dxf.vtx3]
        s=' '.join(f'{fmt(pt_svg(p.x,p.y,max_y)[0])},{fmt(pt_svg(p.x,p.y,max_y)[1])}' for p in pts)
        out.append(f'<polygon class="base-solid" points="{s}"/>')
    elif typ in {'TEXT','MTEXT'}:
        val=text_value(e)
        if not val: return ''
        p=e.dxf.insert
        x,y=pt_svg(p.x,p.y,max_y)
        if typ=='TEXT':
            h=float(e.dxf.height or 2.5)
            rot=float(e.dxf.rotation or 0.0)
        else:
            h=float(e.dxf.char_height or 2.5)
            rot=float(e.dxf.rotation or 0.0) if e.dxf.is_supported('rotation') else 0.0
        val=html.escape(val)
        transform=f' transform="rotate({fmt(-rot)} {fmt(x)} {fmt(y)})"' if abs(rot)>1e-7 else ''
        out.append(f'<text class="{text_cls}" x="{fmt(x)}" y="{fmt(y)}" font-size="{fmt(h)}"{transform}>{val}</text>')
    return ''.join(out)

def generate_html(source, target):
    doc=ezdxf.readfile(source)
    msp=doc.modelspace()
    electrical={}
    for block in doc.blocks:
        sig=is_electrical_block(block)
        if sig:
            electrical[block.name]=sig[0]
    top_inserts=[e for e in msp if e.dxftype()=='INSERT']
    electrical_inserts=[e for e in top_inserts if e.dxf.name in electrical]
    context_inserts=[e for e in top_inserts if e.dxf.name not in electrical]
    all_ext=bbox.extents(msp)
    minx,miny,maxx,maxy=all_ext.extmin.x,all_ext.extmin.y,all_ext.extmax.x,all_ext.extmax.y
    margin=max(maxx-minx,maxy-miny)*0.01
    vx=minx-margin; vy=(maxy-maxy)-margin  # y=0 maps to maxy; ext top maps 0
    vw=(maxx-minx)+2*margin; vh=(maxy-miny)+2*margin

    base=[]
    for e in disassemble.recursive_decompose(context_inserts):
        base.append(render_entity(e,maxy))

    groups=[]
    metadata=[]
    names=[]
    for idx,ins in enumerate(electrical_inserts):
        name=electrical[ins.dxf.name]
        dec=list(disassemble.recursive_decompose([ins]))
        ext=bbox.extents(dec)
        if ext.has_data:
            bx1=ext.extmin.x; bx2=ext.extmax.x
            by1=maxy-ext.extmax.y; by2=maxy-ext.extmin.y
        else:
            bx1=bx2=ins.dxf.insert.x; by1=by2=maxy-ins.dxf.insert.y
        content=''.join(render_entity(e,maxy,cls='electric-line',text_cls='electric-label',include_hit=True) for e in dec)
        safe_id=f'line-{idx}'
        groups.append(f'<g id="{safe_id}" class="electrical-group" data-name="{html.escape(name,quote=True)}" data-block="{html.escape(ins.dxf.name,quote=True)}">{content}</g>')
        metadata.append({'id':safe_id,'name':name,'block':ins.dxf.name,'bbox':[bx1,by1,bx2,by2]})
        names.append(name)

    datalist=''.join(f'<option value="{html.escape(n,quote=True)}"></option>' for n in sorted(set(names), key=lambda s:s.lower()))
    data_json=json.dumps(metadata,ensure_ascii=False)
    full_view=[vx,-margin,vw,vh]
    # Initial viewport: electrical scheme area, not the entire oversized drawing sheet.
    sx1=min(d['bbox'][0] for d in metadata); sy1=min(d['bbox'][1] for d in metadata)
    sx2=max(d['bbox'][2] for d in metadata); sy2=max(d['bbox'][3] for d in metadata)
    sw=max(sx2-sx1,50); sh=max(sy2-sy1,50); sp=max(sw,sh)*0.05
    scheme_view=[sx1-sp,sy1-sp,sw+2*sp,sh+2*sp]
    full_json=json.dumps(full_view)
    scheme_json=json.dumps(scheme_view)
    title=html.escape(source.stem)

    page=f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — интерактивная электрическая схема</title>
<style>
:root{{--ui:#f5f6f7;--line:#3f454b;--accent:#d7442f;--muted:#77818c;}}
*{{box-sizing:border-box}} html,body{{margin:0;height:100%;font-family:Arial,Helvetica,sans-serif;color:#202428;background:#eef1f3}}
body{{display:grid;grid-template-rows:auto 1fr}}
.toolbar{{display:flex;gap:8px;align-items:center;padding:10px 12px;background:white;border-bottom:1px solid #d9dee3;box-shadow:0 1px 4px #0001;z-index:2;flex-wrap:wrap}}
.toolbar strong{{margin-right:8px}} input{{min-width:260px;flex:1;max-width:560px;padding:8px 10px;border:1px solid #bbc4cc;border-radius:7px;font-size:14px}}
button{{padding:8px 12px;border:1px solid #b7c0c8;background:#fff;border-radius:7px;cursor:pointer}} button:hover{{background:#f4f6f8}}#zoomIn,#zoomOut{{font-size:17px;min-width:48px;font-weight:700}}@media (pointer:coarse){{button{{min-height:44px;padding:9px 13px}}#zoomIn,#zoomOut{{min-width:54px;font-size:19px}}}}
#status{{font-size:13px;color:var(--muted)}}
.workspace{{display:grid;grid-template-columns:minmax(0,1fr) 280px;min-height:0}}
.viewer{{position:relative;overflow:hidden;background:white}}
svg{{width:100%;height:100%;display:block;touch-action:none;cursor:grab}} svg.dragging{{cursor:grabbing}}
.base-geom{{fill:none;stroke:#68727b;stroke-width:.55;vector-effect:non-scaling-stroke}}
.base-solid{{fill:#68727b;stroke:none;opacity:.8}}
.base-text{{fill:#39424a;font-family:Arial,Helvetica,sans-serif}}
.electric-line{{fill:none;stroke:#2e3439;stroke-width:.8;vector-effect:non-scaling-stroke;transition:.12s}}
.electric-label{{fill:#222;font-family:Arial,Helvetica,sans-serif;pointer-events:none;transition:.12s}}
.hit{{fill:none;stroke:#000;stroke-opacity:0;stroke-width:12;vector-effect:non-scaling-stroke;pointer-events:stroke;cursor:pointer}}
.electrical-group{{transition:opacity .15s}} .electrical-group.dimmed{{opacity:.10}}
.electrical-group.selected .electric-line{{stroke:var(--accent);stroke-width:2.3}}
.electrical-group.selected .electric-label{{fill:var(--accent);font-weight:700}}
.sidebar{{background:#f8f9fa;border-left:1px solid #d9dee3;padding:14px;overflow:auto}}
.card{{background:white;border:1px solid #dce1e5;border-radius:9px;padding:12px;margin-bottom:12px}}
.card h3{{margin:0 0 8px;font-size:15px}} .value{{font-size:18px;font-weight:700;word-break:break-word}} .small{{font-size:12px;color:var(--muted);word-break:break-word}}
.matches button{{display:block;width:100%;text-align:left;margin:5px 0;border:0;border-radius:5px;padding:6px 8px;background:#f0f2f4}} .matches button:hover{{background:#e7ebee}}
.hint{{font-size:12px;line-height:1.45;color:#66717b}}
@media(max-width:800px){{.workspace{{grid-template-columns:1fr;grid-template-rows:minmax(55vh,1fr) auto}}.sidebar{{border-left:0;border-top:1px solid #d9dee3;max-height:35vh}} input{{min-width:160px}}}}
</style>
</head>
<body>
<div class="toolbar">
<strong>Интерактивная схема</strong>
<input id="search" list="lineNames" placeholder="Введите обозначение линии, например RS485_B">
<datalist id="lineNames">{datalist}</datalist>
<button id="find">Найти</button><button id="zoomIn" title="Приблизить">🔍+</button><button id="zoomOut" title="Отдалить">🔍−</button><button id="reset">Область схемы</button><button id="page">Весь лист</button>
<label style="font-size:13px"><input id="only" type="checkbox" style="min-width:auto;vertical-align:middle"> только найденные</label>
<span id="status">Линий: {len(metadata)}</span>
</div>
<div class="workspace">
<div class="viewer">
<svg id="scheme" viewBox="{' '.join(map(str,scheme_view))}" preserveAspectRatio="xMidYMid meet">
<g id="context">{''.join(base)}</g>
<g id="electrical">{''.join(groups)}</g>
</svg>
</div>
<aside class="sidebar">
<div class="card"><h3>Выбранная линия</h3><div id="selectedName" class="value">—</div><div id="selectedBlock" class="small">Нажмите на линию или воспользуйтесь поиском.</div></div>
<div class="card"><h3>Результаты поиска</h3><div id="matches" class="matches small">Введите часть обозначения линии.</div></div>
<div class="hint">ПК: колесо мыши — масштаб, перетаскивание по свободной области — панорамирование, клик по линии — выделение. Телефон: масштаб двумя пальцами или кнопками 🔍+/🔍−, касание линии — выделение. Файл автономный.</div>
</aside>
</div>
<script>
const lines={data_json}; const fullView={full_json}; const schemeView={scheme_json};
const svg=document.getElementById('scheme'), q=document.getElementById('search'), status=document.getElementById('status'), matches=document.getElementById('matches'), only=document.getElementById('only');
const byId=Object.fromEntries(lines.map(x=>[x.id,x])); let current=[];
function setView(v){{svg.setAttribute('viewBox',v.join(' '));}}
function fit(items){{if(!items.length){{setView(fullView);return}} let x1=Infinity,y1=Infinity,x2=-Infinity,y2=-Infinity; for(const d of items){{x1=Math.min(x1,d.bbox[0]);y1=Math.min(y1,d.bbox[1]);x2=Math.max(x2,d.bbox[2]);y2=Math.max(y2,d.bbox[3]);}} let w=Math.max(x2-x1,20),h=Math.max(y2-y1,20),pad=Math.max(w,h)*.18; setView([x1-pad,y1-pad,w+2*pad,h+2*pad]);}}
function select(items,focus=true){{current=items; const ids=new Set(items.map(x=>x.id)); document.querySelectorAll('.electrical-group').forEach(g=>{{g.classList.toggle('selected',ids.has(g.id)); g.classList.toggle('dimmed', only.checked && items.length && !ids.has(g.id));}}); if(items.length){{document.getElementById('selectedName').textContent=items[0].name; document.getElementById('selectedBlock').textContent='Исходный DXF-блок: '+items[0].block;}} else {{document.getElementById('selectedName').textContent='—';document.getElementById('selectedBlock').textContent='Нажмите на линию или воспользуйтесь поиском.'}} if(focus) fit(items);}}
function norm(s){{
  const lookalikes={{'А':'A','В':'B','С':'C','Е':'E','Н':'H','К':'K','М':'M','О':'O','Р':'P','Т':'T','Х':'X','У':'Y'}};
  return (s||'')
    .normalize('NFKC')
    .trim()
    .toUpperCase()
    .replace(/[‐‑‒–—−]/g,'-')
    .replace(/\\s+/g,'')
    .replace(/[АВСЕНКМОРТХУ]/g,ch=>lookalikes[ch]||ch);
}}
function activate(d,focus=true){{
  q.value=d.name;
  select([d],focus);
  status.textContent=d.name;
}}
function search(){{
  const s=norm(q.value);
  if(!s){{
    select([],false);
    matches.textContent='Введите часть обозначения линии.';
    status.textContent='Линий: '+lines.length;
    return;
  }}
  let found=lines.filter(x=>norm(x.name)===s);
  if(!found.length) found=lines.filter(x=>norm(x.name).includes(s));
  status.textContent='Найдено: '+found.length;
  if(!found.length){{
    matches.textContent='Совпадений нет.';
    select([],false);
    return;
  }}
  matches.innerHTML='';
  found.slice(0,80).forEach(d=>{{
    let b=document.createElement('button');
    b.textContent=d.name;
    b.title=d.block;
    b.onclick=()=>activate(d,true);
    matches.appendChild(b);
  }});
  select(found,true);
}}
document.getElementById('find').onclick=search;
q.addEventListener('keydown',e=>{{if(e.key==='Enter')search()}});
// В datalist выбор значения вызывает input/change, поэтому полный выбор теперь
// сразу запускает подсветку без дополнительного Enter или кнопки «Найти».
q.addEventListener('input',()=>{{
  const s=norm(q.value);
  if(s && lines.some(x=>norm(x.name)===s)) search();
}});
q.addEventListener('change',search);
document.getElementById('reset').onclick=()=>{{
  q.value='';
  matches.textContent='Введите часть обозначения линии.';
  status.textContent='Линий: '+lines.length;
  select([],false);
  setView(schemeView);
}};
document.getElementById('page').onclick=()=>setView(fullView);
only.onchange=()=>select(current,false);

// Клик по самой линии теперь является отдельным действием:
// панорамирование в этот момент не запускается, а объект подсвечивается.
document.querySelectorAll('.electrical-group').forEach(g=>{{
  g.addEventListener('click',e=>{{
    e.preventDefault();
    e.stopPropagation();
    activateGroup(g,false);
  }});
}});
// wheel zoom and drag pan
function view(){{return svg.getAttribute('viewBox').split(/\\s+/).map(Number)}}
function zoomAt(cx,cy,k){{
  const v=view();
  setView([cx-(cx-v[0])*k,cy-(cy-v[1])*k,v[2]*k,v[3]*k]);
}}
function zoomCenter(k){{
  const v=view();
  zoomAt(v[0]+v[2]/2,v[1]+v[3]/2,k);
}}
document.getElementById('zoomIn').onclick=()=>zoomCenter(.78);
document.getElementById('zoomOut').onclick=()=>zoomCenter(1.28);

svg.addEventListener('wheel',e=>{{
  e.preventDefault();
  const v=view(),r=svg.getBoundingClientRect();
  const cx=v[0]+(e.clientX-r.left)/r.width*v[2];
  const cy=v[1]+(e.clientY-r.top)/r.height*v[3];
  zoomAt(cx,cy,e.deltaY<0?.82:1.22);
}},{{passive:false}});

const pointers=new Map();
let drag=null;
let pinch=null;
let tapCandidate=null;

function svgPoint(clientX,clientY){{
  const v=view(),r=svg.getBoundingClientRect();
  return [
    v[0]+(clientX-r.left)/r.width*v[2],
    v[1]+(clientY-r.top)/r.height*v[3]
  ];
}}
function pDist(a,b){{return Math.hypot(a.x-b.x,a.y-b.y)}}
function pMid(a,b){{return {{x:(a.x+b.x)/2,y:(a.y+b.y)/2}}}}

function lineGroupFromTarget(target){{
  return target && target.closest ? target.closest('.electrical-group') : null;
}}

function activateGroup(group,focus=false){{
  if(!group) return;
  const d=byId[group.id];
  if(!d) return;
  matches.innerHTML='';
  activate(d,focus);
}}

svg.addEventListener('pointerdown',e=>{{
  const group=lineGroupFromTarget(e.target);

  // На ПК обычный клик мышью по линии не должен попадать
  // в механику панорамирования / pointer capture.
  // Тогда стандартное событие click срабатывает надежно.
  if(e.pointerType==='mouse' && group){{
    return;
  }}

  pointers.set(e.pointerId,{{
    x:e.clientX,
    y:e.clientY,
    startX:e.clientX,
    startY:e.clientY,
    pointerType:e.pointerType
  }});

  try{{ svg.setPointerCapture(e.pointerId); }}catch(_e){{}}

  if(pointers.size===2){{
    tapCandidate=null;
    const pts=[...pointers.values()];
    const mid=pMid(pts[0],pts[1]);
    pinch={{
      distance:pDist(pts[0],pts[1]),
      view:view(),
      center:svgPoint(mid.x,mid.y)
    }};
    drag=null;
    svg.classList.remove('dragging');
    return;
  }}

  if(pointers.size===1){{
    if(group){{
      // Для touch/pen запоминаем короткое касание как выбор линии.
      tapCandidate={{
        pointerId:e.pointerId,
        group:group,
        startX:e.clientX,
        startY:e.clientY
      }};
      drag=null;
      return;
    }}

    tapCandidate=null;
    drag={{x:e.clientX,y:e.clientY,v:view()}};
    svg.classList.add('dragging');
  }}
}});

svg.addEventListener('pointermove',e=>{{
  if(!pointers.has(e.pointerId)) return;

  const p=pointers.get(e.pointerId);
  p.x=e.clientX;
  p.y=e.clientY;

  if(tapCandidate && tapCandidate.pointerId===e.pointerId){{
    const moved=Math.hypot(
      e.clientX-tapCandidate.startX,
      e.clientY-tapCandidate.startY
    );
    if(moved>10) tapCandidate=null;
  }}

  if(pointers.size===2){{
    const pts=[...pointers.values()];
    const distance=pDist(pts[0],pts[1]);
    if(!pinch || !pinch.distance) return;

    const k=pinch.distance/distance;
    const b=pinch.view;
    const cx=pinch.center[0],cy=pinch.center[1];

    setView([
      cx-(cx-b[0])*k,
      cy-(cy-b[1])*k,
      b[2]*k,
      b[3]*k
    ]);
    return;
  }}

  if(drag && pointers.size===1){{
    const r=svg.getBoundingClientRect();
    const dx=(e.clientX-drag.x)/r.width*drag.v[2];
    const dy=(e.clientY-drag.y)/r.height*drag.v[3];
    setView([drag.v[0]-dx,drag.v[1]-dy,drag.v[2],drag.v[3]]);
  }}
}});

function endPointer(e){{
  // На touch/pen короткое касание линии выбирает ее напрямую.
  if(
    tapCandidate &&
    tapCandidate.pointerId===e.pointerId &&
    pointers.size===1
  ){{
    activateGroup(tapCandidate.group,false);
  }}

  pointers.delete(e.pointerId);
  tapCandidate=null;

  if(pointers.size<2) pinch=null;

  if(pointers.size===0){{
    drag=null;
    svg.classList.remove('dragging');
  }} else if(pointers.size===1){{
    const p=[...pointers.values()][0];
    drag={{x:p.x,y:p.y,v:view()}};
  }}
}}

svg.addEventListener('pointerup',endPointer);
svg.addEventListener('pointercancel',e=>{{
  pointers.delete(e.pointerId);
  tapCandidate=null;
  if(pointers.size<2) pinch=null;
  if(pointers.size===0){{
    drag=null;
    svg.classList.remove('dragging');
  }}
}});
</script>
</body></html>'''
    target.write_text(page,encoding='utf-8')
    return len(metadata)


# --------------------------- PDF GENERATION ---------------------------
MM_TO_PT = 72.0 / 25.4


def _find_pdf_font():
    """Find a local TrueType font with Cyrillic support without bundling font files."""
    candidates = []
    windir = os.environ.get('WINDIR') or os.environ.get('SystemRoot')
    if windir:
        fonts = Path(windir) / 'Fonts'
        candidates += [
            fonts / 'arial.ttf',
            fonts / 'segoeui.ttf',
            fonts / 'calibri.ttf',
        ]
    # Development / Linux fallback. These files are not distributed with the utility.
    candidates += [
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        Path('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise RuntimeError(
        'Не найден TrueType-шрифт с поддержкой кириллицы. '
        'На Windows ожидается Arial (C:\\Windows\\Fonts\\arial.ttf).'
    )


def _pdf_point(x, y, minx, maxy, scale):
    return fitz.Point((x - minx) * scale, (maxy - y) * scale)


def _pdf_color(entity):
    # Technical monochrome output. Layer semantics are carried by PDF OCGs.
    return (0.15, 0.17, 0.19)


def _pdf_draw_entity(page, e, *, minx, maxy, scale, ocg, fontname):
    typ = e.dxftype()
    color = _pdf_color(e)
    width = 0.45

    if typ == 'LINE':
        p1 = _pdf_point(e.dxf.start.x, e.dxf.start.y, minx, maxy, scale)
        p2 = _pdf_point(e.dxf.end.x, e.dxf.end.y, minx, maxy, scale)
        page.draw_line(p1, p2, color=color, width=width, oc=ocg)
        return

    if typ in {'POLYLINE', 'LWPOLYLINE'}:
        if typ == 'POLYLINE':
            pts = [v.dxf.location for v in e.vertices]
            closed = bool(e.is_closed)
        else:
            pts = [type('P', (), {'x': p[0], 'y': p[1]}) for p in e.get_points('xy')]
            closed = bool(e.closed)
        if len(pts) >= 2:
            ppts = [_pdf_point(p.x, p.y, minx, maxy, scale) for p in pts]
            page.draw_polyline(ppts, color=color, width=width, closePath=closed, oc=ocg)
        return

    if typ == 'CIRCLE':
        c = _pdf_point(e.dxf.center.x, e.dxf.center.y, minx, maxy, scale)
        page.draw_circle(c, e.dxf.radius * scale, color=color, width=width, oc=ocg)
        return

    if typ == 'SOLID':
        pts = [e.dxf.vtx0, e.dxf.vtx1, e.dxf.vtx2, e.dxf.vtx3]
        ppts = [_pdf_point(p.x, p.y, minx, maxy, scale) for p in pts]
        page.draw_polyline(ppts, color=color, fill=color, width=0.1, closePath=True, oc=ocg)
        return

    if typ in {'TEXT', 'MTEXT'}:
        val = text_value(e)
        if not val:
            return
        p = e.dxf.insert
        pt = _pdf_point(p.x, p.y, minx, maxy, scale)
        if typ == 'TEXT':
            height = float(e.dxf.height or 2.5)
            rotation = float(e.dxf.rotation or 0.0) % 360
        else:
            height = float(e.dxf.char_height or 2.5)
            rotation = float(e.dxf.rotation or 0.0) % 360 if e.dxf.is_supported('rotation') else 0.0
        fontsize = max(height * scale, 0.5)
        # PyMuPDF insert_text supports the orthogonal rotations used by current 3DE export.
        allowed = (0, 90, 180, 270)
        rotate = min(allowed, key=lambda a: abs(((rotation-a+180)%360)-180))
        page.insert_text(
            pt,
            val,
            fontsize=fontsize,
            fontname=fontname,
            color=color,
            rotate=rotate,
            oc=ocg,
            overlay=True,
        )
        return


def generate_pdf(processed_dxf, target_pdf):
    """
    Generate a vector, searchable PDF from the normalized DXF.
    DXF layers are mapped to PDF Optional Content Groups (PDF layers).
    """
    processed_dxf = Path(processed_dxf)
    target_pdf = Path(target_pdf)
    doc_dxf = ezdxf.readfile(processed_dxf)
    msp = doc_dxf.modelspace()
    ext = bbox.extents(msp)
    if not ext.has_data:
        raise RuntimeError('DXF не содержит отображаемой геометрии.')

    minx, miny = ext.extmin.x, ext.extmin.y
    maxx, maxy = ext.extmax.x, ext.extmax.y
    width = max((maxx - minx) * MM_TO_PT, 10)
    height = max((maxy - miny) * MM_TO_PT, 10)

    pdf = fitz.open()
    page = pdf.new_page(width=width, height=height)

    font_path = _find_pdf_font()
    fontname = 'ArialPDF'
    page.insert_font(fontname=fontname, fontfile=str(font_path))

    entities = list(disassemble.recursive_decompose(msp))
    used_layers = {getattr(e.dxf, 'layer', '0') or '0' for e in entities}

    # Create only layers that actually contain visible entities.
    # Preserve DXF layer-table order, but omit empty service layers such as Defpoints.
    ocgs = {}
    for layer in doc_dxf.layers:
        name = layer.dxf.name
        if name in used_layers:
            ocgs[name] = pdf.add_ocg(name, on=1, intent='View', usage='Artwork')

    def ocg_for(layer_name):
        if layer_name not in ocgs:
            ocgs[layer_name] = pdf.add_ocg(layer_name, on=1, intent='View', usage='Artwork')
        return ocgs[layer_name]

    for e in entities:
        layer = getattr(e.dxf, 'layer', '0') or '0'
        _pdf_draw_entity(
            page, e,
            minx=minx, maxy=maxy, scale=MM_TO_PT,
            ocg=ocg_for(layer), fontname=fontname,
        )

    pdf.set_metadata({
        'title': f'{processed_dxf.stem} - electrical logical scheme',
        'subject': 'Vector PDF generated from 3DEXPERIENCE DXF; PDF layers and searchable text',
        'creator': '3DE Electrical Utility v5',
        'producer': f'PyMuPDF {fitz.VersionBind}',
    })
    target_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.save(target_pdf, garbage=4, deflate=True, clean=True)
    pdf.close()

    # Lightweight verification: reopen, count pages / OCGs / extracted text.
    check = fitz.open(target_pdf)
    if len(check) != 1:
        check.close()
        raise RuntimeError('Ошибка проверки PDF: ожидалась одна страница.')
    layer_count = len(check.get_ocgs())
    text_len = len(check[0].get_text())
    check.close()
    return layer_count, text_len

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Автоматизация DXF электрических схем 3DEXPERIENCE.')
    parser.add_argument('source', type=Path, help='Исходный DXF')
    parser.add_argument('--output-dir', type=Path, default=None, help='Папка результатов')
    args = parser.parse_args()

    source = args.source
    output_dir = args.output_dir or source.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem
    out_dxf = output_dir / f'{stem}_layers_Arial.dxf'
    out_html = output_dir / f'{stem}_interactive.html'
    out_csv = output_dir / f'{stem}_mapping.csv'

    n, a, _ = transform_dxf(source, out_dxf, out_csv)
    h = generate_html(source, out_html)
    print(f'Готово. Электрических линий: {n}')
    print(f'Текстовых объектов переведено на Arial: {a}')
    print(f'Интерактивных линий в HTML: {h}')
    print(f'DXF: {out_dxf}')
    print(f'HTML: {out_html}')
    print(f'CSV: {out_csv}')

if __name__ == '__main__':
    main()
