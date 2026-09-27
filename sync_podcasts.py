import os, sys, json, re, urllib.request, time
from datetime import datetime

ROOT = "os.path.dirname(os.path.abspath(__file__))"
ENV_FILE = os.path.expanduser("~/.hermes/.env")
TOK_FILE = os.path.expanduser("~/.hermes/state/pocketcast_token.txt")

CATEGORIES = {
    "投资 · 商业": ["起朱楼宴宾客", "面基", "知行小酒馆", "不可思议Bookish", "請聽，哈佛管理學！"],
    "认知 · 科技": ["The a16z Show", "管理派", "Infinite Loops"],
    "人文 · 阅读": ["史蒂夫说", "907编辑部", "电影巨辩"],
    "思想 · 历史": ["不明白播客", "剧谈社"]
}

def get_token():
    if os.path.exists(TOK_FILE):
        tok = open(TOK_FILE).read().strip()
        if tok:
            return tok
    # Fallback to .env
    creds = {}
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().replace("export ", "").split("=", 1)
                creds[k] = v.strip("'\"")
    email, pw = creds.get("POCKETCASTS_EMAIL"), creds.get("POCKETCASTS_PASSWORD")
    if email and pw:
        req = urllib.request.Request(
            "https://api.pocketcasts.com/user/login",
            data=json.dumps({"email": email, "password": pw, "scope": "webplayer"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            tok = data.get("token") or (data.get("userToken") or {}).get("token")
            if tok:
                os.makedirs(os.path.dirname(TOK_FILE), exist_ok=True)
                open(TOK_FILE, "w").write(tok)
                return tok
    raise RuntimeError("无法获取 Pocket Casts Token")

def fetch_starred():
    tok = get_token()
    req = urllib.request.Request(
        "https://api.pocketcasts.com/user/starred",
        data=json.dumps({"v": 1}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    eps = [e for e in data.get("episodes", []) if not e.get("isDeleted")]
    return eps

def get_category(pod_title):
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in pod_title.lower():
                return cat
    return "特选 · 杂谈"

def format_duration(sec):
    if not sec: return ""
    m = sec // 60
    h = m // 60
    rem_m = m % 60
    return f"{h}小时{rem_m}分" if h > 0 else f"{m}分钟"

def build_podcasts_page(eps):
    # 分类归档
    categorized = {}
    for e in eps:
        pod = e.get("podcastTitle", "未知播客").strip()
        cat = get_category(pod)
        categorized.setdefault(cat, []).append(e)

    # 排序
    for cat in categorized:
        categorized[cat].sort(key=lambda x: x.get("published", ""), reverse=True)

    cards_html = ""
    for cat in ["投资 · 商业", "认知 · 科技", "人文 · 阅读", "思想 · 历史", "特选 · 杂谈"]:
        items = categorized.get(cat, [])
        if not items: continue
        
        cards_html += f"""
        <div class="podcast-section">
          <h2 class="podcast-sec-title">{cat} <span class="podcast-count">({len(items)})</span></h2>
          <div class="podcast-list">
        """
        for item in items:
            title = item.get("title", "").strip()
            pod = item.get("podcastTitle", "").strip()
            pub = (item.get("published") or "")[:10]
            dur = format_duration(item.get("duration", 0))
            audio_url = item.get("url", "")
            
            # 清理标题冗余
            clean_title = re.sub(r'^(Vol\.\s*\d+|EP\.\s*\d+|E\d+[\.、\s]|#\d+[-\d]*\s*)', '', title, flags=re.I).strip()
            
            cards_html += f"""
            <article class="podcast-card">
              <div class="podcast-card-meta">
                <span class="podcast-name">{pod}</span>
                <span class="podcast-dot">·</span>
                <span class="podcast-date">{pub}</span>
                {f'<span class="podcast-dot">·</span><span class="podcast-dur">{dur}</span>' if dur else ''}
              </div>
              <h3 class="podcast-title">{clean_title if clean_title else title}</h3>
              <div class="podcast-actions">
                {f'<a href="{audio_url}" target="_blank" rel="noopener" class="podcast-listen-btn">音频直链 ↗</a>' if audio_url else ''}
              </div>
            </article>
            """
        cards_html += """
          </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noimageindex">
<title>加星播客 · 白石溪</title>
<link rel="stylesheet" href="assets/style.css?v=1790502712">
<style>
  .podcasts-container {{
    max-width: 860px;
    margin: 0 auto;
    padding: 3rem 1.5rem;
  }}
  .podcast-intro {{
    margin-bottom: 3.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border, #eee);
  }}
  .podcast-header-title {{
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.8rem;
  }}
  .podcast-header-desc {{
    color: #666;
    font-size: 1rem;
    line-height: 1.6;
  }}
  .podcast-section {{
    margin-bottom: 3rem;
  }}
  .podcast-sec-title {{
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 1.2rem;
    padding-left: 0.6rem;
    border-left: 3px solid #111;
  }}
  .podcast-count {{
    font-size: 0.9rem;
    color: #888;
    font-weight: 400;
  }}
  .podcast-list {{
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }}
  .podcast-card {{
    background: #fff;
    border: 1px solid #eaeaea;
    border-radius: 6px;
    padding: 1.2rem 1.4rem;
    transition: all 0.2s ease;
  }}
  .podcast-card:hover {{
    border-color: #bbb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  }}
  .podcast-card-meta {{
    font-size: 0.85rem;
    color: #777;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    flex-wrap: wrap;
  }}
  .podcast-name {{
    font-weight: 600;
    color: #333;
  }}
  .podcast-title {{
    font-size: 1.1rem;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 0.8rem;
    color: #111;
  }}
  .podcast-actions {{
    display: flex;
    gap: 0.8rem;
  }}
  .podcast-listen-btn {{
    font-size: 0.82rem;
    color: #444;
    text-decoration: none;
    border: 1px solid #ddd;
    padding: 0.25rem 0.65rem;
    border-radius: 4px;
    transition: all 0.15s ease;
  }}
  .podcast-listen-btn:hover {{
    background: #f7f7f7;
    border-color: #999;
    color: #000;
  }}
</style>
</head>
<body>

<header class="site-header">
  <div class="site-title"><a href="index.html">白石溪</a></div>
  <nav class="site-nav">
    <a href="index.html">导览</a>
    <a href="podcasts.html">播客</a>
    <a href="README.html">发刊词</a>
    <a href="https://github.com/zhangxunck/WhiteStoneSpring" target="_blank">GitHub</a>
  </nav>
</header>

<main class="podcasts-container">
  <div class="podcast-intro">
    <h1 class="podcast-header-title">加星单集 · Podcast Inquiries</h1>
    <p class="podcast-header-desc">
      从数百期收听实践中筛选出的高信息密度对谈与思想切片。涵盖商业投资认知框架、人文阅读抵抗、科技演进与历史谱系。
      数据与 Pocket Casts 个人加星库双向保真同步。
    </p>
  </div>

  {cards_html}
</main>

<footer class="site-footer">
  <div>© 2026 zhangxunnj · 白石溪 White Stone Spring · 保留所有权利</div>
  <div>@zhangxunnj</div>
</footer>

</body>
</html>
"""
    out_file = os.path.join(ROOT, "podcasts.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ 成功生成 {out_file}，收录 {len(eps)} 期单集")

if __name__ == "__main__":
    eps = fetch_starred()
    build_podcasts_page(eps)
