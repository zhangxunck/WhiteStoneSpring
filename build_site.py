import os, sys, glob, re
import markdown

ROOT = "os.path.dirname(os.path.abspath(__file__))"

# 定义 3-C 风格标准 SVG 抽象流动画 (240x180 比例)
ART_SVG_MAP = {
    "翻译如何重塑中文_两千年来五波外来语与现代写作真相": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-red" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#D92318" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#FF5A43" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#D92318" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <!-- 红色水墨流带（宽窄自如变化） -->
  <path d="M 20 135 C 50 145, 80 110, 110 85 C 145 55, 180 40, 210 65 C 220 75, 220 95, 200 110 C 170 130, 130 115, 100 135 C 80 150, 50 155, 20 135 Z" fill="url(#ribbon-red)"/>
  <path d="M 25 140 C 65 145, 95 95, 135 65 C 175 35, 205 55, 215 80 C 220 110, 175 135, 125 125 C 85 115, 55 145, 25 140" fill="none" stroke="#D92318" stroke-width="3" stroke-linecap="round"/>
  <!-- 毕加索式的黑色伴随律动飞线 -->
  <path d="M 30 120 C 70 125, 90 75, 130 50 C 165 30, 195 50, 190 85 C 185 120, 135 140, 85 120" fill="none" stroke="#111111" stroke-width="2.4" stroke-linecap="round"/>
  <circle cx="190" cy="85" r="3.5" fill="#111111"/>
</svg>""",

    "AI认知判断力内化与外部化双钢人": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-blue" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1D3557" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#457B9D" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#1D3557" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <!-- 藏青色 S 形回旋带 -->
  <path d="M 40 140 C 30 80, 70 40, 120 50 C 170 60, 210 90, 200 135 C 190 170, 150 160, 130 130 C 110 95, 80 110, 50 140 Z" fill="url(#ribbon-blue)"/>
  <path d="M 35 90 C 75 50, 135 40, 175 70 C 215 100, 190 150, 140 145 C 90 140, 60 90, 95 65 C 130 40, 180 65, 205 110" fill="none" stroke="#1D3557" stroke-width="3" stroke-linecap="round"/>
  <!-- 黑色伴随律动飞线 -->
  <path d="M 45 130 C 65 70, 110 55, 150 75 C 190 95, 175 140, 130 135 C 95 130, 85 90, 115 70 C 145 50, 185 80, 195 125" fill="none" stroke="#111111" stroke-width="2.4" stroke-linecap="round"/>
  <circle cx="115" cy="70" r="3.5" fill="#111111"/>
</svg>""",

    "什么是好的中文_十人十策与可执行规范": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-green" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1B4D3E" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#2D6A4F" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#1B4D3E" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <!-- 墨绿飞扬带 -->
  <path d="M 30 140 C 60 130, 90 80, 120 45 C 150 15, 180 30, 170 70 C 160 110, 120 145, 160 135 C 195 125, 215 95, 210 115 C 200 150, 140 160, 100 145 Z" fill="url(#ribbon-green)"/>
  <path d="M 35 140 C 80 130, 105 75, 135 40 C 160 10, 185 30, 175 75 C 165 120, 115 145, 165 130 C 200 115, 215 90, 215 110" fill="none" stroke="#1B4D3E" stroke-width="3" stroke-linecap="round"/>
  <!-- 黑色伴随律动飞线 -->
  <path d="M 45 135 C 75 120, 100 70, 125 45 C 150 20, 170 40, 160 80 C 150 120, 110 135, 150 125 C 185 110, 205 95, 205 115" fill="none" stroke="#111111" stroke-width="2.4" stroke-linecap="round"/>
  <circle cx="160" cy="80" r="3.5" fill="#111111"/>
</svg>"""
}

# 1. 完善 style.css
css_extra = """
/* ---- 3-C 系列抽象流动画规范 ---- */
.card-art-box {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #FCFCF9;
  border-bottom: 1px solid var(--rule);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  box-sizing: border-box;
  overflow: hidden;
  transition: background 0.2s ease;
}
.feature-card:hover .card-art-box {
  background: #F9F7F0;
}
.card-flow-art {
  width: 100%;
  height: 100%;
  max-height: 140px;
  overflow: visible;
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.feature-card:hover .card-flow-art {
  transform: scale(1.03);
}

.feature-card {
  border: 1px solid var(--rule);
  background: var(--paper);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative;
  text-decoration: none;
  color: inherit;
}
.feature-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(0,0,0,0.06);
}
.feature-card-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}
"""

css_path = os.path.join(ROOT, "assets/style.css")
current_css = open(css_path, encoding="utf-8").read()
if "/* ---- 3-C 系列抽象流动画规范 ---- */" not in current_css:
    open(css_path, "a", encoding="utf-8").write("\n" + css_extra)

# 2. 编译各文章 HTML
md_files = glob.glob(os.path.join(ROOT, "articles/*.md"))

article_metadata = []

for md_path in md_files:
    raw = open(md_path, encoding="utf-8").read()
    basename = os.path.splitext(os.path.basename(md_path))[0]
    
    # 提取 frontmatter
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
    accent = fm.get("accent", "#E3120B")
    category_label = fm.get("category_label", "特稿")
    subtitle = fm.get("subtitle", "")
    lead = fm.get("lead", "")
    author = fm.get("author", "白石溪特约撰述")
    date = fm.get("date", fm.get("updated", "2026-09-27"))
    
    # Markdown 渲染
    md_parser = markdown.Markdown(extensions=['extra', 'tables', 'fenced_code', 'toc'])
    body_html = md_parser.convert(content)
    
    # 组装文章页面
    page_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 白石溪</title>
<link rel="stylesheet" href="../assets/style.css">
<style>
  :root {{
    --accent: {accent};
  }}
</style>
</head>
<body>

<header class="site-header">
  <div class="site-title"><a href="../index.html">白石溪</a></div>
  <div class="site-tagline">White Stone Spring · 深度思想特稿与现代文风实录</div>
  <nav class="site-nav">
    <a href="../index.html">返回导览</a>
    <a href="../README.html">发刊词</a>
    <a href="https://github.com/zhangxunck/WhiteStoneSpring" target="_blank">代码仓</a>
  </nav>
</header>

<main class="article-container">
  <div class="article-kicker">{category_label}</div>
  <h1 class="article-title">{title}</h1>
  {f'<p class="article-subtitle">{subtitle}</p>' if subtitle else ''}
  
  <div class="article-meta">
    <span>撰文 / {author}</span>
    <span>发布于 {date}</span>
    <span>白石溪 White Stone Spring</span>
  </div>

  {f'<div class="article-lead">{lead}</div>' if lead else ''}

  <div class="article-body">
{body_html}
  </div>

  <footer class="article-footer">
    <p>© 2026 白石溪 White Stone Spring. All rights reserved.</p>
    <p>发表内容遵循署名出处与学术出版规范 · 署名：@zhangxunnj</p>
  </footer>
</main>

</body>
</html>"""
    
    out_path = os.path.join(ROOT, f"articles/{basename}.html")
    open(out_path, "w", encoding="utf-8").write(page_html)
    print("Generated article HTML:", f"{basename}.html")
    
    article_metadata.append({
        "basename": basename,
        "title": title,
        "accent": accent,
        "category_label": category_label,
        "subtitle": subtitle,
        "lead": lead,
        "date": date,
        "author": author,
        "svg_art": ART_SVG_MAP.get(basename, "")
    })

# 3. 排序与生成带有 3-C 纯流动抽象艺术卡片的 index.html
order = [
    "翻译如何重塑中文_两千年来五波外来语与现代写作真相",
    "AI认知判断力内化与外部化双钢人",
    "什么是好的中文_十人十策与可执行规范"
]
article_metadata.sort(key=lambda x: order.index(x["basename"]) if x["basename"] in order else 99)

cards_html = ""
for a in article_metadata:
    cards_html += f"""
    <a class="feature-card" href="articles/{a['basename']}.html" style="--accent: {a['accent']};">
      <div class="card-art-box">
        {a['svg_art']}
      </div>
      <div class="feature-card-content">
        <div class="feature-card-kicker">{a['category_label']}</div>
        <h2 class="feature-card-title">{a['title']}</h2>
        <p class="feature-card-lead">{a['lead'][:125] + '...' if len(a['lead']) > 125 else a['lead']}</p>
        <div class="feature-card-meta">
          <span>{a['date']}</span>
          <span style="color: var(--accent); font-weight: 600;">阅读全文 →</span>
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
<link rel="stylesheet" href="assets/style.css">
</head>
<body>

<header class="site-header">
  <div class="site-title"><a href="index.html">白石溪</a></div>
  <div class="site-tagline">White Stone Spring · 深度思想特稿与现代文风实录</div>
  <nav class="site-nav">
    <a href="index.html">导览</a>
    <a href="README.html">发刊词</a>
    <a href="https://github.com/zhangxunck/WhiteStoneSpring" target="_blank">GitHub</a>
  </nav>
</header>

<main class="home-container">
  <section class="home-intro">
    <div class="home-motto">“It's all made up, but you get to make it up.”</div>
    <div class="home-bio-zh">
      <strong>白石溪</strong>是一处致力于深度沉淀、思想探究与规范写作的中文发表平台。记录跨越千年的母语演变真相、AI 时代的人本认知范式，以及回归朴素力量的写作实践。
    </div>
    <div class="home-bio-en">
      <strong>White Stone Spring</strong> is an independent journal dedicated to in-depth essays, cognitive inquiry, and standard Chinese writing—tracing two millennia of linguistic evolution, cognitive paradigms in the era of artificial intelligence, and disciplined prose.
    </div>
  </section>

  <section class="features-grid">
{cards_html}
  </section>
</main>

<footer class="site-footer">
  <p>© 2026 白石溪 White Stone Spring. Published by @zhangxunnj.</p>
  <p>凡有所作，皆归清虚 · It's all made up, but you get to make it up.</p>
</footer>

</body>
</html>"""

open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(index_html)
print("Static index.html generated with 3-C Flowing Calligraphic Ribbons.")
