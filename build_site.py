import os, sys, glob, re
import markdown

ROOT = "os.path.dirname(os.path.abspath(__file__))"

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

# 1. 编译各文章 HTML
md_files = glob.glob(os.path.join(ROOT, "articles/*.md"))
article_metadata = []

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
    category_label = fm.get("category_label", "特稿")
    subtitle = fm.get("subtitle", "")
    lead = fm.get("lead", "")
    author = fm.get("author", "白石溪特约撰述")
    date = fm.get("date", fm.get("updated", "2026-09-27"))
    
    md_parser = markdown.Markdown(extensions=['extra', 'tables', 'fenced_code', 'toc'])
    body_html = md_parser.convert(content)
    # 移动端优化：表格包入横向滚动容器
    import re as _re
    body_html = _re.sub(r'(<table>.*?</table>)', r'<div class="table-wrap">\1</div>', body_html, flags=_re.S)
    
    page_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 白石溪</title>
<link rel="stylesheet" href="../assets/style.css?v=1790502712">
</head>
<body>

<header class="site-header">
  <div class="site-title"><a href="../index.html">白石溪</a></div>
  <nav class="site-nav">
    <a href="../index.html">导览</a>
    <a href="../README.html">发刊词</a>
    <a href="https://github.com/zhangxunck/WhiteStoneSpring" target="_blank">GitHub</a>
  </nav>
</header>

<main class="article-container">
  <div class="article-kicker">{category_label}</div>
  <h1 class="article-title">{title}</h1>
  {f'<p class="article-subtitle">{subtitle}</p>' if subtitle else ''}
  
  <div class="article-meta">
    <span>{author}</span>
    <span>{date}</span>
  </div>

  {f'<div class="article-lead">{lead}</div>' if lead else ''}

  <div class="article-body">
{body_html}
  </div>

  <footer class="article-footer">
    <p>© 2026 白石溪 White Stone Spring · @zhangxunnj</p>
  </footer>
</main>

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

# 2. 排序与生成 MINIMAL 极简导览主页
order = [
    "翻译如何重塑中文_两千年来五波外来语与现代写作真相",
    "AI认知判断力内化与外部化双钢人",
    "什么是好的中文_十人十策与可执行规范"
]
article_metadata.sort(key=lambda x: order.index(x["basename"]) if x["basename"] in order else 99)

items_html = ""
for a in article_metadata:
    items_html += f"""
    <a class="minimal-article-card" href="articles/{a['basename']}.html">
      <div class="minimal-art-box">
        {a['svg_art']}
      </div>
      <div class="minimal-text-box">
        <div class="minimal-meta-top">
          <span class="minimal-kicker">{a['category_label']}</span>
          <span>·</span>
          <span>{a['date']}</span>
        </div>
        <h2 class="minimal-title">{a['title']}</h2>
        <div class="minimal-abstract">
          {a['abstract']}
        </div>
        <div class="minimal-read-link">
          阅读全文 <span>→</span>
        </div>
      </div>
    </a>
"""

index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>白石溪 · White Stone Spring</title>
<link rel="stylesheet" href="assets/style.css?v=1790502712">
</head>
<body>

<header class="site-header">
  <div class="site-title"><a href="index.html">白石溪</a></div>
  <nav class="site-nav">
    <a href="index.html">导览</a>
    <a href="README.html">发刊词</a>
    <a href="https://github.com/zhangxunck/WhiteStoneSpring" target="_blank">GitHub</a>
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
  <div>© 2026 白石溪 · White Stone Spring</div>
  <div>@zhangxunnj</div>
</footer>

</body>
</html>"""

open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(index_html)
print("Static index.html generated with MINIMAL theme & preserved fluid art.")
