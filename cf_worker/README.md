# 白石溪 CF 网关 Worker

Cloudflare Worker `baishixi-gateway`（账号 6f4d87ec…，路由 `blog.zhangxunnj.cc.cd/*` → GitHub Pages）。

## 职能
1. **路径重写**：`/` → `https://zhangxunck.github.io/WhiteStoneSpring/`（CF 代理层暴露纯净自定义域名）
2. **防盗链**：`/assets/` 下全部资源（含 HTML 卡片图/SVG/PNG/CSS）带外部 Referer 时，非白名单域名返回 403
3. 白名单：`zhangxunnj.cc.cd`、`zhangxunck.github.io`、google/bing/baidu

## 部署
```bash
# wrangler（需 CF 账号 6f4d87ec 的登录态）
wrangler deploy cf_worker/baishixi-gateway.js
# 或面板：Workers → baishixi-gateway → 粘贴 worker.js
```

## 路由
`blog.zhangxunnj.cc.cd/*` 已在 zone 1d07575e… 绑定本 Worker；DNS CNAME `blog.zhangxunnj.cc.cd → zhangxunck.github.io`（proxied）为冗余记录。
