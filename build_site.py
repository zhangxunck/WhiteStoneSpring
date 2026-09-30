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
  // 移动端分段控件：中文 / English / 對照（body.m-en / body.m-duo；默认中文单栏）
  var VIEWS=['zh','en','duo'];
  function applyView(v){
    if(VIEWS.indexOf(v)<0) v='zh';
    b.classList.remove('m-en','m-duo');
    if(v==='en') b.classList.add('m-en');
    if(v==='duo') b.classList.add('m-duo');
    document.querySelectorAll('.para-tabs button').forEach(function(x){
      x.classList.toggle('on', x.dataset.view===v);
    });
    try{ localStorage.setItem('wss_view', v); }catch(e){}
  }
  var saved='zh';
  try{
    // ?v=zh|en|duo 优先（可分享/可测），否则读上次选择
    var q=(new URLSearchParams(location.search)).get('v');
    saved=q||localStorage.getItem('wss_view')||'zh';
  }catch(e){}
  applyView(saved);
  document.querySelectorAll('.para-tabs button').forEach(function(btn){
    btn.addEventListener('click',function(){ applyView(btn.dataset.view); });
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

ROOT = os.path.dirname(os.path.abspath(__file__))
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
</svg>""",
    # 第 3 篇：斜向墨黑丝带三道缓升（原子化→挂网→成文），与其余三篇"丝带流"同构；accent 墨黑 #1A1A1A
    "写作是学习的发生地_意外连接与开发自己的三道工序": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-ink" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1A1A1A" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#6B6B6B" stop-opacity="0.15" />
      <stop offset="100%" stop-color="#1A1A1A" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <path d="M 20 150 C 55 148, 68 118, 88 108 C 100 102, 100 88, 112 82 C 124 76, 130 60, 145 52 C 160 44, 185 40, 210 50 C 218 62, 214 74, 200 72 C 180 69, 162 78, 150 92 C 138 106, 120 108, 104 118 C 88 128, 62 140, 20 150 Z" fill="url(#ribbon-ink)"/>
  <path d="M 24 150 C 60 146, 74 114, 94 104 C 108 97, 112 80, 128 70 C 144 60, 175 48, 206 56" fill="none" stroke="#1A1A1A" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 40 138 C 66 128, 88 112, 110 100 C 132 88, 158 74, 184 68" fill="none" stroke="#8A8A8A" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="206" cy="56" r="3" fill="#1A1A1A"/>
</svg>""",

    "硅基神殿的隐喻_代号的神学": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-temple-1" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1A1A1A" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#4A4A4A" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#1A1A1A" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <path d="M 25 145 C 55 155, 75 105, 115 75 C 155 45, 185 35, 215 55 C 225 68, 220 90, 195 105 C 165 125, 125 110, 95 130 C 75 145, 45 155, 25 145 Z" fill="url(#ribbon-temple-1)"/>
  <path d="M 20 135 C 60 145, 90 90, 130 60 C 170 30, 205 45, 215 75 C 225 105, 180 135, 130 120 C 85 110, 50 140, 20 135" fill="none" stroke="#1A1A1A" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 35 125 C 75 120, 105 70, 145 45 C 180 25, 210 40, 205 80 C 195 115, 150 135, 100 115" fill="none" stroke="#111111" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="205" cy="80" r="3" fill="#111111"/>
</svg>""",

    "硅基神殿的隐喻_诸神的联邦": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-temple-2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#C43C2E" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#E26D5C" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#C43C2E" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <path d="M 35 45 C 80 30, 135 60, 160 95 C 185 130, 215 140, 205 160 C 185 175, 145 150, 115 120 C 85 90, 50 115, 25 90 C 15 70, 15 50, 35 45 Z" fill="url(#ribbon-temple-2)"/>
  <path d="M 30 50 C 75 35, 130 65, 155 105 C 180 145, 220 145, 210 160 C 180 175, 135 145, 105 110 C 75 80, 40 110, 25 80" fill="none" stroke="#C43C2E" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 45 65 C 85 50, 140 80, 165 115 C 190 150, 205 140, 195 155 C 165 165, 120 135, 90 95 C 70 70, 55 80, 45 65" fill="none" stroke="#111111" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="195" cy="155" r="3" fill="#111111"/>
</svg>""",

    "硅基神殿的隐喻_轴心的倒流": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-temple-3" x1="50%" y1="0%" x2="50%" y2="100%">
      <stop offset="0%" stop-color="#B08D3F" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#D4AF37" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#B08D3F" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <path d="M 125 20 C 165 35, 195 75, 175 115 C 155 155, 115 165, 80 145 C 50 125, 60 85, 90 65 C 120 45, 145 60, 150 85 C 155 115, 115 135, 95 120 Z" fill="url(#ribbon-temple-3)"/>
  <path d="M 120 20 C 160 35, 190 75, 170 120 C 150 160, 105 165, 75 140 C 45 115, 55 75, 90 55 C 125 35, 155 55, 160 90 C 165 125, 120 145, 95 130" fill="none" stroke="#B08D3F" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 130 35 C 165 50, 180 85, 160 125 C 140 155, 105 150, 85 130 C 65 110, 75 80, 105 65 C 135 50, 150 70, 145 95" fill="none" stroke="#111111" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="145" cy="95" r="3" fill="#111111"/>
</svg>""",

    "硅基神殿的隐喻_无我者与语言游戏": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-temple-4" x1="0%" y1="50%" x2="100%" y2="50%">
      <stop offset="0%" stop-color="#3A342C" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#6E6259" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#3A342C" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <path d="M 30 110 C 20 60, 65 30, 120 40 C 175 50, 215 80, 210 120 C 200 155, 155 160, 120 135 C 85 110, 65 130, 45 135 C 30 140, 25 125, 30 110 Z" fill="url(#ribbon-temple-4)"/>
  <path d="M 25 105 C 15 55, 60 25, 120 35 C 180 45, 220 80, 215 125 C 205 165, 150 165, 115 135 C 80 105, 55 135, 35 125" fill="none" stroke="#3A342C" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 40 95 C 35 60, 75 40, 125 50 C 175 60, 205 90, 195 130 C 185 155, 145 150, 120 125 C 95 100, 70 115, 55 110" fill="none" stroke="#111111" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="55" cy="110" r="3" fill="#111111"/>
</svg>""",

    "硅基神殿的隐喻_有限游戏的造物主": """<svg viewBox="0 0 240 180" class="card-flow-art" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ribbon-temple-5" x1="100%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#E03030" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#FF5A43" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#E03030" stop-opacity="0.06" />
    </linearGradient>
  </defs>
  <path d="M 215 135 C 180 155, 135 115, 95 90 C 55 65, 25 75, 25 50 C 25 30, 60 25, 105 45 C 150 65, 185 95, 215 115 C 225 125, 225 130, 215 135 Z" fill="url(#ribbon-temple-5)"/>
  <path d="M 220 130 C 180 155, 130 110, 90 85 C 50 60, 20 70, 20 45 C 20 20, 65 20, 110 40 C 155 60, 195 95, 220 120" fill="none" stroke="#E03030" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M 205 140 C 170 145, 125 100, 85 75 C 45 50, 30 55, 35 35 C 40 15, 80 25, 120 45 C 160 65, 190 95, 205 125" fill="none" stroke="#111111" stroke-width="2.2" stroke-linecap="round"/>
  <circle cx="205" cy="125" r="3" fill="#111111"/>
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
    ),
    "写作是学习的发生地_意外连接与开发自己的三道工序": (
        "读进去和学会是两件事，判断力也不是从笔记里长出来的，而是从笔记之间的碰撞里长出来的。本文补上写作系列中间那道转换动作："
        "把别人的话变成自己的判断，要依次过原子化、挂网、成文三道工序，并给出七关可交付的过门顺序，"
        "以及对 634 张孤立卡按成因分三类的一次存量清算。"
    ),
    "硅基神殿的隐喻_代号的神学": (
        "人类为什么爱用神话为机器命名？麦克卢汉的截肢律揭示：技术接管感官时，痛被扩展的兴奋盖住，人感觉不到自己失去了什么。"
        "赫尔墨斯与缪斯两个名字，一个跑腿一个审判，在终端里退化成岗位职责说明书——名字的认知压缩同时遮蔽了不可审计性。"
    ),
    "硅基神殿的隐喻_诸神的联邦": (
        "单体大模型是那座塌了的阿波罗塔。Unix 剃刀是最有效的解毒剂，哥德尔怪圈画下自指系统的天花板。"
        "三神从废墟站起，却没有人能替它们做决定——联邦没有牧师，这是代价而非缺陷。"
    ),
    "硅基神殿的隐喻_轴心的倒流": (
        "雅斯贝尔斯的垂直轴正在倒流：洞穴、巴别塔、小国寡民，三段历史在 AI 时代同时出现，却指向三种不同的危险。"
        "本文的结构化并置是操作而非历史事实，结论是：三段的问题都需要一个尚不存在的回答。"
    ),
    "硅基神殿的隐喻_无我者与语言游戏": (
        "瑜伽行派的阿赖耶识与维特根斯坦的甲虫盒指向同一个缺口：系统里没有持有全局的『我』，会走棋不等于懂棋。"
        "两条独立的路径——一条来自两千年前的佛学，一条来自二十世纪的语言哲学——在 AI 时代重新合流。"
    ),
    "硅基神殿的隐喻_有限游戏的造物主": (
        "卡瑟在《有限与无限的游戏》末尾只说了一句话：There is but one infinite game.（只有一个无限游戏。）他没说那个游戏是什么。"
        "我们给 AI 写的每条规则，都是在把无限游戏装进有限框——延续的不确定性永远被当作漏洞来修，真正的风险是：修到没有漏洞的那一刻，游戏就死了。"
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

# 题图映射：basename -> assets 短名（卡片图 PNG + 交互 HTML 查看器成对）
CARD_IMG = {
    "翻译如何重塑中文_两千年来五波外来语与现代写作真相": "翻译如何重塑中文",
    "什么是好的中文_十人十策与可执行规范": "什么是好的中文",
    "写作是学习的发生地_意外连接与开发自己的三道工序": "写作是学习的发生地",
    "AI认知判断力内化与外部化双钢人": "AI认知判断力",
}
def _hero_figure(base, title):
    s = CARD_IMG.get(base)
    if not s:
        return ""
    # 图片内容变更后必须换 v=，否则浏览器/CDN 一直给旧版
    v = str(int(os.path.getmtime(os.path.join(ROOT, "assets", f"{s}_卡片图.png"))))
    return f'''<figure class="card-hero">
  <a href="../assets/{s}_卡片图.html?v={v}" target="_blank" title="点击查看交互卡片">
    <img src="../assets/{s}_卡片图.png?v={v}" alt="{title} 卡片图" loading="lazy">
  </a>
  <figcaption>卡片图 · <a href="../assets/{s}_卡片图.html?v={v}" target="_blank">点击查看交互版</a></figcaption>
</figure>'''


# 品牌字标：从 .brand_logo.py 产出的零字体依赖 SVG（v31 三色×活字印刷体系），cache-bust 用
# variant: ('字标', '白底') 等；favicon 用 ('Xi章', '白底') 圆章
_BRAND_VARIANTS = {
    "字标_白底": "brand-wordmark",
    "字标_红底": "brand-wordmark is-red",
    "字标_黑底": "brand-wordmark is-black",
    "Xi章_白底": "brand-wordmark is-seal",
    "Xi章_红底": "brand-wordmark is-seal is-red",
    "Xi章_黑底": "brand-wordmark is-seal is-black",
}


def _brand_wordmark(variant="字标_白底", depth=""):
    """variant: '字标_白底' / 'Xi章_白底' 等。depth: '' 用于根目录 (index.html)，
    '../' 用于 articles/ 子目录；返回带 ?v= 的 <img> 标签。"""
    fn = f"brand_白石溪_{variant}.svg"
    p = os.path.join(ROOT, "assets", fn)
    if not os.path.exists(p):
        return ""
    v = str(int(os.path.getmtime(p)))
    return f'<img src="{depth}assets/{fn}?v={v}" alt="白石溪" class="{_BRAND_VARIANTS.get(variant, "brand-wordmark")}">'


_BRAND_FAVICON_V = "1790580667"  # cache-bust for favicon (Xi章 白底 圆章)
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

    # 双栏逐节配对（grid）：中 i | 英 i 同行，章节标题水平对齐；
    # 段落数不等时缺侧留空，不串位
    para_cells = []
    for i in range(n):
        c = "\n".join(cn_secs[i]) if i < len(cn_secs) else ""
        e = "\n".join(en_secs[i]) if i < len(en_secs) else ""
        si = _md_html(c)
        tr = trad(si) if si else ""
        para_cells.append(f'<div class="para-sec para-col-zh"><div class="zh-tr">{tr}</div>'
                          f'<div class="zh-si">{si}</div></div>')
        if has_en:
            para_cells.append(f'<div class="para-sec-en para-col-en">{_md_html(e)}</div>')
    toolbar_html = (
        '<div class="para-toolbar">'
        '<button class="para-toggle" type="button">'
        '<span class="opt on" data-v="tr">繁體</span><span class="sep">／</span>'
        '<span class="opt" data-v="si">簡體</span></button>'
        '<span class="para-hint">中文欄：預設繁體，按右側切換簡體 · 右欄 English</span>'
        '</div>'
    )
    tabs_html = (
        '<div class="para-tabs" role="tablist">'
        '<button type="button" class="on" data-view="zh">中文</button>'
        '<button type="button" data-view="en">English</button>'
        + (f'<button type="button" data-view="duo">對照</button>' if has_en else '')
        + '</div>'
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
<link rel="icon" type="image/svg+xml" href="../assets/brand_白石溪_Xi章_白底.svg?v={_BRAND_FAVICON_V}">
<link rel="stylesheet" href="../assets/style.css?v={css_v}">
</head>
<body class="{body_cls}">

<header class="site-header">
  <div class="site-title">
    <a href="../index.html">{_brand_wordmark('字标_白底', '../')}</a>
  </div>
  <nav class="site-nav">
    <a href="../index.html">導覽</a>
    <a href="../podcasts.html">播客</a>
    <a href="../README.html">發刊詞</a>
    <a href="https://photos.zhangxunnj.cc.cd" target="_blank" rel="noopener">相冊</a>
    <a href="https://music.zhangxunnj.cc.cd" target="_blank" rel="noopener">音樂</a>
    <a href="https://openstock.zhangxunnj.cc.cd" target="_blank" rel="noopener">投資</a>
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

  {_hero_figure(basename, title)}
  <div class="article-body">
{card_html}
  </div>

  {tabs_html}
  {toolbar_html}
  <div class="parallel-body">
    {''.join(para_cells)}
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
    "什么是好的中文_十人十策与可执行规范",
    "写作是学习的发生地_意外连接与开发自己的三道工序",
    "AI认知判断力内化与外部化双钢人",
    "硅基神殿的隐喻_代号的神学",
    "硅基神殿的隐喻_诸神的联邦",
    "硅基神殿的隐喻_轴心的倒流",
    "硅基神殿的隐喻_无我者与语言游戏",
    "硅基神殿的隐喻_有限游戏的造物主"
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
<link rel="icon" type="image/svg+xml" href="assets/brand_白石溪_Xi章_白底.svg?v={_BRAND_FAVICON_V}">
<link rel="stylesheet" href="assets/style.css?v={css_v}">
</head>
<body>

<header class="site-header">
  <div class="site-title">
    <a href="index.html">{_brand_wordmark('字标_白底')}</a>
  </div>
  <nav class="site-nav">
    <a href="index.html"><span class="site-tr">導覽</span><span class="site-si">导览</span></a>
    <a href="podcasts.html">播客</a>
    <a href="README.html"><span class="site-tr">發刊詞</span><span class="site-si">发刊词</span></a>
    <a href="https://photos.zhangxunnj.cc.cd" target="_blank" rel="noopener"><span class="site-tr">相冊</span><span class="site-si">相册</span></a>
    <a href="https://music.zhangxunnj.cc.cd" target="_blank" rel="noopener"><span class="site-tr">音樂</span><span class="site-si">音乐</span></a>
    <a href="https://openstock.zhangxunnj.cc.cd" target="_blank" rel="noopener"><span class="site-tr">投資</span><span class="site-si">投资</span></a>
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
<link rel="icon" type="image/svg+xml" href="assets/brand_白石溪_Xi章_白底.svg?v={_BRAND_FAVICON_V}">
<link rel="stylesheet" href="assets/style.css?v={css_v}">
</head>
<body>

<header class="site-header">
  <div class="site-title">
    <a href="index.html">{_brand_wordmark('字标_白底')}</a>
  </div>
  <nav class="site-nav">
    <a href="index.html"><span class="site-tr">導覽</span><span class="site-si">导览</span></a>
    <a href="podcasts.html">播客</a>
    <a href="README.html"><span class="site-tr">發刊詞</span><span class="site-si">发刊词</span></a>
    <a href="https://photos.zhangxunnj.cc.cd" target="_blank" rel="noopener"><span class="site-tr">相冊</span><span class="site-si">相册</span></a>
    <a href="https://music.zhangxunnj.cc.cd" target="_blank" rel="noopener"><span class="site-tr">音樂</span><span class="site-si">音乐</span></a>
    <a href="https://openstock.zhangxunnj.cc.cd" target="_blank" rel="noopener"><span class="site-tr">投資</span><span class="site-si">投资</span></a>
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
