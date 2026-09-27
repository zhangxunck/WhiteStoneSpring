import os, sys, glob, re
import markdown

ROOT = "os.path.dirname(os.path.abspath(__file__))"

# 1. 读 style.css 获取基础样式
css = open(os.path.join(ROOT, "assets/style.css"), encoding="utf-8").read()

# 2. 增强 CSS: 保证代码块、Markdown 表格、列表、引用绝对优雅对齐
extra_css = """
/* ---- Markdown 表格增强 ---- */
.story-inner table {
  width: 100%;
  border-collapse: collapse;
  margin: 28px 0;
  font-size: 14.5px;
  background: var(--panel);
  border: 1px solid var(--rule);
}
.story-inner th, .story-inner td {
  padding: 10px 14px;
  border: 1px solid var(--rule);
  text-align: left;
  line-height: 1.6;
}
.story-inner thead th {
  background: var(--accent);
  color: #ffffff;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.story-inner tbody tr:nth-child(even) {
  background: rgba(0, 0, 0, 0.02);
}
.story-inner td:first-child {
  font-weight: 600;
}

/* ---- 引用块增强 ---- */
.story-inner blockquote {
  margin: 28px 0;
  padding: 16px 24px;
  border-left: 4px solid var(--accent);
  background: rgba(0, 0, 0, 0.02);
  color: var(--ink);
  font-size: 17px;
  line-height: 1.8;
  font-style: normal;
}
.story-inner blockquote p {
  margin: 0;
}

/* ---- 列表增强 ---- */
.story-inner ul, .story-inner ol {
  padding-left: 28px;
  margin: 18px 0;
}
.story-inner li {
  margin-bottom: 8px;
  line-height: 1.85;
}

/* ---- 代码块 ---- */
.story-inner pre {
  background: #14161a;
  color: #e6e6e6;
  padding: 18px 20px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13.5px;
  line-height: 1.6;
  font-family: "SF Mono", Menlo, Consolas, monospace;
}

/* ---- 内嵌交互视图 ---- */
.card-preview-frame {
  margin: 32px 0 24px 0;
}
"""
full_css = css + "\n" + extra_css
open(os.path.join(ROOT, "assets/style.css"), "w", encoding="utf-8").write(full_css)
print("CSS updated with robust table & typography styling.")

# 3. 解析 Frontmatter 函数
def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_raw = parts[1]
    body = parts[2]
    meta = {}
    for line in fm_raw.strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            # 剥离行内注释
            if "#" in v:
                v = v.split("#")[0].strip()
            meta[k] = v
    return meta, body

# 4. 生成每一篇文章的原生 HTML
md_files = glob.glob(os.path.join(ROOT, "articles", "*.md"))
articles_meta = []

for mf in md_files:
    raw = open(mf, encoding="utf-8").read()
    meta, body = parse_frontmatter(raw)
    
    accent = meta.get("accent", "#E3120B")
    accent_name = meta.get("accent_name", "深度特稿")
    kicker = meta.get("kicker", "Special Report")
    title = meta.get("title", "未命名文章")
    standfirst = meta.get("standfirst", "")
    date = meta.get("created", "2026-09-27")
    
    # 渲染 Markdown 为 HTML (启用 tables, fenced_code, attr_list 等扩展)
    html_body = markdown.markdown(body, extensions=['extra', 'tables', 'fenced_code', 'nl2br'])
    
    # 套入高保真 Article 模板
    doc_html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} · 白石溪</title>
  <meta name="description" content="{standfirst}">
  <link rel="stylesheet" href="../assets/style.css">
  <style>
    :root {{
      --accent: {accent};
      --accent-dim: {accent}18;
    }}
  </style>
</head>
<body data-layout="article">
  <main class="container">
    <article class="feature-story">
      <div class="story-masthead" style="background:{accent};">
        <a class="mast-title" href="../index.html" style="color:#ffffff;text-decoration:none;">白石溪</a>
        <span class="mast-sub">White Stone Spring</span>
      </div>
      <div class="story-inner">
        <div class="kicker" style="color:{accent};">{kicker}</div>
        <h1 class="story-title">{title}</h1>
        <p class="standfirst">{standfirst}</p>
        <hr class="accent-rule" style="background:{accent};">
        <div class="byline">
          <span class="byline-tag" style="border-color:{accent};color:{accent};">{accent_name}</span>
          <span class="byline-date">{date}</span>
        </div>
        
        {html_body}
        
        <div class="story-foot">
          <span>白石溪 · 持续调查与实测</span>
          <a class="back" href="../index.html" style="color:{accent};">← 返回首页</a>
        </div>
      </div>
    </article>
  </main>
</body>
</html>
"""
    out_html_path = mf[:-3] + ".html"
    open(out_html_path, "w", encoding="utf-8").write(doc_html)
    print("Generated article HTML:", os.path.basename(out_html_path))
    
    articles_meta.append({
        "title": title,
        "url": "articles/" + os.path.basename(out_html_path),
        "accent": accent,
        "accent_name": accent_name,
        "kicker": kicker,
        "standfirst": standfirst,
        "date": date
    })

# 5. 生成纯静态 Index 首页
cards_html = ""
for a in sorted(articles_meta, key=lambda x: x["date"], reverse=True):
    cards_html += f"""
    <a class="feature-card" href="{a['url']}" style="--accent:{a['accent']};">
      <div class="card-top" style="background:{a['accent']};"></div>
      <div class="card-body">
        <div class="card-kicker" style="color:{a['accent']};">{a['kicker']}</div>
        <h2 class="card-title">{a['title']}</h2>
        <p class="card-stand">{a['standfirst']}</p>
        <div class="card-foot">
          <span class="card-tag" style="color:{a['accent']};border-color:{a['accent']};">{a['accent_name']}</span>
          <span class="card-date">{a['date']}</span>
        </div>
      </div>
    </a>
"""

home_html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>首页 · 白石溪 White Stone Spring</title>
  <meta name="description" content="关于中文写作与思想的持续调查">
  <link rel="stylesheet" href="assets/style.css">
  <style>
    :root {{ --accent:#E3120B; }}
  </style>
</head>
<body data-layout="home">
  <div class="site-masthead" style="background:#E3120B;">
    <a class="site-name" href="index.html" style="color:#ffffff;text-decoration:none;">白石溪 · White Stone Spring</a>
    <span class="site-sub">Language · Writing · Ideas</span>
  </div>
  
  <main class="container">
    <section class="home-intro">
      <div class="kicker">白石溪 · White Stone Spring</div>
      <h1 class="home-title">一条持续调查「语言、写作与思想」的溪。</h1>
      <p class="home-dek" style="font-style:italic;color:#7a7a7a;margin-bottom:12px;">“It's all made up, but you get to make it up.”</p>
      <p class="home-dek">石头是白的，水是真的，不长高东西，也不装。这里的每一篇长文都建立在<b>可复算的数据与一手文献</b>上——不留空泛修辞，用实测语料与证据说话。</p>
    </section>

    <section class="issue-strip">
      <div class="issue-label">溪里有什么 · 按主题分色</div>
      <div class="issue-meta">{len(articles_meta)} 篇深度特稿 · 持续更新</div>
    </section>

    <div class="feature-grid">
      {cards_html}
    </div>
  </main>

  <footer class="site-foot">
    <span>白石溪 White Stone Spring</span>
    <span>持续调查 · 实测数据底座 · @zhangxunnj</span>
  </footer>
</body>
</html>
"""
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(home_html)
print("Static index.html generated with all 3 articles.")
