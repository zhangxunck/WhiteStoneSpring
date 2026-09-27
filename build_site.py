import os, sys, glob, re as _re
import markdown
import time

# 簡繁转换（发刊默认繁体；OpenCC 大陆地区规范字形 s2tw）。构建 venv 已装 opencc-python-reimplemented。
try:
    from opencc import OpenCC as _OpenCC
    _CC = _OpenCC('s2tw')
    def trad(text):
        return _CC.convert(text) if text else text
except Exception:
    def trad(text):
        return text

def split_by_h2(mdtext):
    """按 `## ` 切分：返回 (preamble_text, [ [lines] ])，各 section 首行即其 `## ` 标题。"""
    lines = mdtext.split('\n')
    preamble, secs, cur = [], [], None
    for ln in lines:
        if ln.startswith('## '):
            if cur is not None:
                secs.append(cur)
            cur = [ln]
        else:
            if cur is None:
                preamble.append(ln)
            else:
                cur.append(ln)
    if cur is not None:
        secs.append(cur)
    return '\n'.join(preamble), secs

# 简/繁 切换脚本：body 加 .zh-simple 时，各 .zh-tr 隐藏、.zh-si 显示；默认繁体。
TOGGLE_JS = """
(function(){
  var b=document.body;
  document.querySelectorAll('.para-toggle').forEach(function(btn){
    btn.addEventListener('click',function(e){
      e.preventDefault();
      b.classList.toggle('zh-simple');
      document.querySelectorAll('.para-toggle .opt').forEach(function(o){
        o.classList.toggle('on', (o.dataset.v==='si')===b.classList.contains('zh-simple'));
      });
    });
  });
  // 站点级（导览/发刊词）繁/简：点按钮切 body.zh-simple，站名/导航用 site-tr/site-si 成对
  document.querySelectorAll('.lang-toggle').forEach(function(btn){
    btn.addEventListener('click',function(e){
      e.preventDefault();
      var on=b.classList.toggle('zh-simple');
      btn.textContent = on ? '切換簡體' : '切換繁體';
    });
  });
})();
"""

ROOT = "os.path.dirname(os.path.abspath(__file__))"
# style.css 缓存戳：每次 build 刷新（mtime 整秒），保证发刊词/并排版式即时生效
css_v = str(int(os.path.getmtime(os.path.join(ROOT, "assets", "style.css"))))

# 3-C 纯流动抽象艺术 SVG
ART_SVG_MAP = {
    "翻译如何重塑中文_两千年来五波外来语与现代写作真相": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-red" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#D92318" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#FF5A43" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#D92318" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <path d="M 20 135 C 50 145, 80 110, 110 85 C 145 55, 180 40, 210 65 C 220 75, 220 95, 200 110 C 170 130, 130 115, 100 135 C 80 150, 50 155, 20 135 Z" fill="url(#ribbon-red)"/>
  <path d="M 25 140 C 65 145, 95 95, 135 65 C 175 35, 205 55, 215 80 C 220 110, 175 135, 125 125 C 85 115, 55 145, 25 140" fill="none" stroke="#D92318" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 30 120 C 70 125, 90 75, 130 50 C 165 30, 195 50, 190 85 C 185 120, 135 140, 85 120" fill="none" stroke="#111111" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="190" cy="85" r="3" fill="#111111"/>
</svg>""",

    "AI认知判断力内化与外部化双钢人": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-blue" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1D3557" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#457B9D" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#1D3557" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <path d="M 40 140 C 30 80, 70 40, 120 50 C 170 60, 210 90, 200 135 C 190 170, 150 160, 130 130 C 110 95, 80 110, 50 140 Z" fill="url(#ribbon-blue)"/>
  <path d="M 35 90 C 75 50, 135 40, 175 70 C 215 100, 190 150, 140 145 C 90 140, 60 90, 95 65 C 130 40, 180 65, 205 110" fill="none" stroke="#1D3557" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 45 130 C 65 70, 110 55, 150 75 C 190 95, 175 140, 130 135 C 95 130, 85 90, 115 70 C 145 50, 185 80, 195 125" fill="none" stroke="#111111" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="115" cy="70" r="3" fill="#111111"/>
</svg>""",

    "什么是好的中文_十人十策与可执行规范": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-green" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1B4D3E" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#2D6A4F" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#1B4D3E" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <path d="M 30 140 C 60 130, 90 80, 120 45 C 150 15, 180 30, 170 70 C 160 110, 120 145, 160 135 C 195 125, 215 95, 210 115 C 200 150, 140 160, 100 145 Z" fill="url(#ribbon-green)"/>
  <path d="M 35 140 C 80 130, 105 75, 135 40 C 160 10, 185 30, 175 75 C 165 120, 115 145, 165 130 C 200 115, 215 90, 215 110" fill="none" stroke="#1B4D3E" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 45 135 C 75 120, 100 70, 125 45 C 150 20, 170 40, 160 80 C 150 120, 110 135, 150 125 C 185 110, 205 95, 205 115" fill="none" stroke="#111111" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="160" cy="80" r="3" fill="#111111"/>
</svg>"""
}

# 特稿精炼摘要
CURATED_ABSTRACTS = {
    "翻译如何重塑中文_两千年来五波外来语与现代写作真相": (
        "两千年来，东汉佛经、明末利玛窦、晚清和制汉语、新文化运动欧化与当代官方政论，五次外来语浪潮深刻重构了中文的语法结构。"
        "本篇基于 3.2MB 真实语料库切片分析，穿透被动句滥用与空心动词迷障，揭示母语在吸收外来滋养与守卫自身气韵节律之间的历史账本。"
    ),
    "AI认知判断力内化与外部化双钢人": (
        "大语言模型让生成内容的边际成本趋近于零，却让判断力的稀缺性指数级上升。当思考被过度外包，写作者面临记忆工作台悬空的生理退化风险。"
        "本文构建认知内化与外部化的双钢人模型：既论证为何必须将敏锐的审美标尺焊进大脑，又阐明如何建立可验证的外部文件体系守住知识资产。"
    ),
    "什么是好的中文_十人十策与可执行规范": (
        "好中文不是玄学，而是一套可拆解、可训练的工程规范。本文系统梳理从资中筠、王鼎钧、朱自清到乔治·奥威尔等十位语言大家的实践路径，"
        "提炼出对仗配重、动词复活、句序精简等四层证据链，并给出一套可在文稿交付前逐项打勾验证的「七关自检法则」，让好文字有迹可循。"
    )
}

# 1. 编译各文章 HTML（正文：默认繁体 中文栏 ｜ 英文栏 并排；按钮切简体）
md_files = [f for f in glob.glob(os.path.join(ROOT, "articles/*.md")) if not f.endswith(".en.md")]
article_metadata = []

def _md_html(mdtext):
    p = markdown.Markdown(extensions=['extra', 'tables', 'fenced_code', 'toc'])
    h = p.convert(mdtext)
    h = _re.sub(r'(<table>.*?</table>)', r'<div class="table-wrap">\1</div>', h, flags=_re.S)
    return h

for md_path in md_files:
    raw = open(md_path, encoding="utf-8").read()
    basename = os.path.splitext(os.path.basename(md_path))[0]
    
    fm = {}
    content = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            content = parts[2]
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip('"').strip("'")
    
    title = fm.get("title", basename)
    category_label = fm.get("category_label", fm.get("accent_name", "特稿"))
    subtitle = fm.get("subtitle", "")
    lead = fm.get("lead", "")
    author = fm.get("author", "白石溪特约撰述")
    date = fm.get("date", fm.get("updated", "2026-09-27"))
    
    # 英文正文（可选；缺则单栏并加 body.no-en）
    en_path = md_path[:-3] + ".en.md"
    en_content = ""
    if os.path.exists(en_path):
        en_raw = open(en_path, encoding="utf-8").read()
        en_content = en_raw.split("---", 2)[2] if en_raw.startswith("---") else en_raw
    has_en = bool(en_content.strip())
    
    # 中文按 ## 切段；每段给 简体(原文) 与 繁体(s2tw) 双份；英文按 ## 切段
    cn_pream, cn_secs = split_by_h2(content)
    en_pream, en_secs = split_by_h2(en_content) if has_en else ("", [])
    n = max(len(cn_secs), len(en_secs))

    # 题图/导语（preamble）只渲染一次、全宽置于双栏之上
    card_html = _md_html(cn_pream)

    para_body_zh, para_body_en = "", ""
    for i in range(n):
        c = "\n".join(cn_secs[i]) if i < len(cn_secs) else ""
        e = "\n".join(en_secs[i]) if i < len(en_secs) else ""
        si = _md_html(c)
        tr = trad(si) if si else ""
        para_body_zh += (f'<div class="para-sec"><div class="zh-tr">{tr}</div>'
                          f'<div class="zh-si">{si}</div></div>')
        if has_en:
            para_body_en += f'<div class="para-sec-en">{_md_html(e)}</div>'

    zh_col_body = para_body_zh
    en_col_body = f'<div class="para-col-en">{para_body_en}</div>' if has_en else ""
    toolbar_html = (
        '<div class="para-toolbar">'
        '<button class="para-toggle" type="button">'
        '<span class="opt on" data-v="tr">繁體</span><span class="sep">／</span>'
        '<span class="opt" data-v="si">簡體</span></button>'
        '<span class="para-hint">中文欄：預設繁體，按右側切換簡體 · 右欄 English</span>'
        '</div>'
    )
    body_cls = "has-parallel" if has_en else ""
    
    page_html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noimageindex">
<meta name="copyright" content="zhangxunnj (白石溪 White Stone Spring), 2026, 保留所有权利">
<title>{trad(title)} · 白石溪</title>
<link rel="stylesheet" href="../assets/style.css?v={css_v}">
</head>
<body class="{body_cls}">

<header class="site-header">
  <div class="site-title"><a href="../index.html">白石溪</a></div>
  <nav class="site-nav">
    <a href="../index.html">導覽</a>
    <a href="../podcasts.html">播客</a>
    <a href="../README.html">發刊詞</a>
    <a href="https://github.com/zhangxunck/WhiteStoneSpring" target="_blank">GitHub</a>
  </nav>
</header>

<main class="article-container">
  <div class="article-kicker">{trad(category_label)}</div>
  <h1 class="article-title">{trad(title)}</h1>
  {f'<p class="article-subtitle">{trad(subtitle)}</p>' if subtitle else ''}
  <div class="article-meta">
    <span>{trad(author)}</span>
    <span>{date}</span>
  </div>

  <div class="article-body">
{card_html}
  </div>

  {toolbar_html}
  <div class="parallel-body">
    <div class="para-col-zh">{para_body_zh}</div>
    {en_col_body}
  </div>

  <footer class="article-footer">
    <p>© 2026 白石溪 White Stone Spring · @zhangxunnj</p>
  </footer>
</main>

<script>{TOGGLE_JS}</script>
</body>
</html>"""
    
    out_path = os.path.join(ROOT, f"articles/{basename}.html")
    open(out_path, "w", encoding="utf-8").write(page_html)
    print("Generated article HTML:", f"{basename}.html")
    
    abstract = CURATED_ABSTRACTS.get(basename, lead)
    
    article_metadata.append({
        "basename": basename,
        "title": title,
        "category_label": category_label,
        "subtitle": subtitle,
        "lead": lead,
        "abstract": abstract,
        "date": date,
        "author": author,
        "svg_art": ART_SVG_MAP.get(basename, "")
    })

# 2. 排序与生成 MINIMAL 极简导览主页（默认繁体）
order = [
    "翻译如何重塑中文_两千年来五波外来语与现代写作真相",
    "AI认知判断力内化与外部化双钢人",
    "什么是好的中文_十人十策与可执行规范"
]
article_metadata.sort(key=lambda x: order.index(x["basename"]) if x["basename"] in order else 99)

items_html = ""
for a in article_metadata:
    t_title = trad(a['title'])
    t_abs = trad(a['abstract'])
    t_cat = trad(a['category_label'])
    items_html += f"""
    <a class="minimal-article-card" href="articles/{a['basename']}.html">
      <div class="minimal-art-box">
        {a['svg_art']}
      </div>
      <div class="minimal-text-box">
        <div class="minimal-meta-top">
          <span class="minimal-kicker">{t_cat}</span>
          <span>·</span>
          <span>{a['date']}</span>
        </div>
        <h2 class="minimal-title">{t_title}</h2>
        <div class="minimal-abstract">
          {t_abs}
        </div>
        <div class="minimal-read-link">
          全文閱讀 <span>→</span>
        </div>
      </div>
    </a>
"""

index_html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>白石溪 · White Stone Spring</title>
<link rel="stylesheet" href="assets/style.css?v={css_v}">
</head>
<body>

<header class="site-header">
  <div class="site-title"><a href="index.html">白石溪</a></div>
  <nav class="site-nav">
    <a href="index.html"><span class="site-tr">導覽</span><span class="site-si">导览</span></a>
    <a href="podcasts.html">播客</a>
    <a href="README.html"><span class="site-tr">發刊詞</span><span class="site-si">发刊词</span></a>
    <a href="https://github.com/zhangxunck/WhiteStoneSpring" target="_blank">GitHub</a>
    <button class="lang-toggle" type="button">切換簡體</button>
  </nav>
</header>

<main class="home-container">
  <div class="home-intro">
    <div class="home-motto">“It's all made up, but you get to make it up.”</div>
  </div>

  <section class="minimal-articles-list">
{items_html}
  </section>
</main>

<footer class="site-footer">
  <div>© 2026 zhangxunnj · 白石溪 White Stone Spring · 保留所有權利</div>
  <div>@zhangxunnj</div>
</footer>

<script>{TOGGLE_JS}</script>
</body>
</html>"""

open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(index_html)

# 3. 编译 README.md -> README.html（发刊词页，导航锚点；默认繁体）
readme_md = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
readme_parser = markdown.Markdown(extensions=['extra', 'tables', 'fenced_code', 'toc'])
readme_html = readme_parser.convert(readme_md)
readme_html = _re.sub(r'(<table>.*?</table>)', r'<div class="table-wrap">\1</div>', readme_html, flags=_re.S)
readme_html_tr = trad(readme_html)  # 默认繁体
readme_page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noimageindex">
<meta name="copyright" content="zhangxunnj (白石溪 White Stone Spring), 2026, 保留所有权利">
<title>發刊詞 · 白石溪</title>
<link rel="stylesheet" href="assets/style.css?v={css_v}">
</head>
<body>

<header class="site-header">
  <div class="site-title"><a href="index.html">白石溪</a></div>
  <nav class="site-nav">
    <a href="index.html"><span class="site-tr">導覽</span><span class="site-si">导览</span></a>
    <a href="podcasts.html">播客</a>
    <a href="README.html"><span class="site-tr">發刊詞</span><span class="site-si">发刊词</span></a>
    <a href="https://github.com/zhangxunck/WhiteStoneSpring" target="_blank">GitHub</a>
    <button class="lang-toggle" type="button">切換簡體</button>
  </nav>
</header>

<main class="article-container">
  <h1 class="article-title"><span class="site-tr">發刊詞</span><span class="site-si">发刊词</span></h1>
  <div class="article-body">
{readme_html_tr}
  </div>
  <footer class="article-footer">
    <p>© 2026 白石溪 White Stone Spring · @zhangxunnj</p>
  </footer>
</main>

<script>{TOGGLE_JS}</script>
</body>
</html>"""
open(os.path.join(ROOT, "README.html"), "w", encoding="utf-8").write(readme_page)
print("Generated README.html (发刊词, 默认繁体)")

# 4. 生成 sitemap.xml（供收录与版权锚点，主入口 = blog 域）
BASE = "https://blog.zhangxunnj.cc.cd/"
urls = ['<url><loc>' + BASE + '</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>',
        '<url><loc>' + BASE + 'podcasts.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>',
        '<url><loc>' + BASE + 'README.html</loc><changefreq>monthly</changefreq></url>']
for a in article_metadata:
    urls.append('<url><loc>' + BASE + 'articles/' + a["basename"] + '.html</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>')
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + '\n</urlset>'
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(sitemap)

print("Static index.html generated with MINIMAL theme & preserved fluid art.")
