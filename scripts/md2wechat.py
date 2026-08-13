#!/usr/bin/env python3
"""把 Markdown 转成可直接粘进微信公众号编辑器的 HTML。

微信编辑器的三个坑，这个脚本都绕开了：

1. 它会剥掉 <style> 标签和 class，只保留内联 style
   → 所有样式写在标签上

2. 粘贴时会吃掉代码块里的 \\n 换行，white-space:pre 也救不回来
   → 每行包一个 <p>，换行变成 DOM 结构而不是空白字符

3. 纯文本 URL 不会自动变成可点链接
   → 裸 URL 自动包 <a>

用法：
    python3 scripts/md2wechat.py drafts/05-公众号-源稿.md
"""
import re
import sys
from pathlib import Path

C = {
    "text": "#2c3e50",
    "muted": "#7a8899",
    "brand": "#2f6fed",
    "link": "#2f6fed",
    "code_bg": "#f2f4f8",
    "code_text": "#3d5a80",
    "block_bg": "#1e2430",
    "block_text": "#c8d3e0",
    "block_line": "#2b3444",
    "border": "#e6eaf0",
    "quote_bg": "#f7f9fc",
    "accent": "#2f6fed",
}

BASE = f"font-size:16px;line-height:1.9;color:{C['text']};word-break:break-word;letter-spacing:.2px;"
MONO = "Menlo,'Courier New',Consolas,monospace"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


LINK_STYLE = f'color:{C["link"]};text-decoration:none;border-bottom:1px solid {C["link"]};'

# 文中常以裸域名形式出现（没有 https://），也要能点
BARE_DOMAINS = r"(?:github\.com|nodejs\.org|platform\.deepseek\.com|deepseek\.com)"


def linkify(t: str) -> str:
    """裸 URL 与裸域名变成可点击链接。已在 <a> 里的不动。"""
    t = re.sub(
        r'(?<!["\'>=])(https?://[^\s<>"）)】*]+)',
        rf'<a href="\1" style="{LINK_STYLE}">\1</a>',
        t,
    )
    # 裸域名：前面不能已经是 // 或 . （避免二次处理）
    t = re.sub(
        rf'(?<![/.\w])({BARE_DOMAINS}(?:/[^\s<>"）)】，。*]*)?)',
        rf'<a href="https://\1" style="{LINK_STYLE}">\1</a>',
        t,
    )
    return t


def inline(s: str, do_link: bool = True) -> str:
    """行内格式：`代码`、**粗体**、[文字](url)、裸 URL。"""
    out = []
    for part in re.split(r"(`[^`]+`)", s):
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(
                f'<code style="background:{C["code_bg"]};color:{C["code_text"]};'
                f"padding:2px 6px;border-radius:3px;font-size:14px;"
                f'font-family:{MONO};">{esc(part[1:-1])}</code>'
            )
        else:
            t = esc(part)
            # Markdown 链接先转，避免 linkify 重复处理
            t = re.sub(
                r"\[([^\]]+)\]\(([^)]+)\)",
                rf'<a href="\2" style="{LINK_STYLE}">\1</a>',
                t,
            )
            t = re.sub(r"\*\*([^*]+)\*\*", r'<strong style="font-weight:600;">\1</strong>', t)
            if do_link:
                t = linkify(t)
            out.append(t)
    return "".join(out)


def code_block(lines: list[str]) -> str:
    """代码块：每行一个 <p>，换行是 DOM 结构，微信剥不掉。"""
    rows = []
    for ln in lines:
        # 前导空格用 &nbsp; 保住缩进
        stripped = ln.lstrip(" ")
        indent = "&nbsp;" * (len(ln) - len(stripped))
        content = indent + esc(stripped) if stripped else "<br>"
        rows.append(
            f'<p style="margin:0;padding:0;font-size:14px;line-height:1.75;'
            f'font-family:{MONO};color:{C["block_text"]};white-space:pre-wrap;">{content}</p>'
        )
    return (
        f'<section style="background:{C["block_bg"]};border-radius:8px;'
        f'padding:18px 20px;margin:22px 0;overflow-x:auto;">'
        + "".join(rows)
        + "</section>"
    )


PLATFORM = "wechat"


def render_table(header: list[str], rows: list[list[str]], platform: str) -> str:
    """微信保留 <table>；今日头条会把表格结构整个剥掉，改用卡片式列表。"""
    if platform == "wechat":
        th = "".join(
            f'<th style="padding:11px 13px;text-align:left;font-size:14px;font-weight:600;'
            f'background:{C["quote_bg"]};border-bottom:2px solid {C["border"]};'
            f'color:{C["muted"]};">{inline(c)}</th>'
            for c in header
        )
        tr = "".join(
            "<tr>"
            + "".join(
                f'<td style="padding:11px 13px;font-size:14px;vertical-align:top;'
                f'border-bottom:1px solid {C["border"]};line-height:1.7;">{inline(c)}</td>'
                for c in r
            )
            + "</tr>"
            for r in rows
        )
        return (
            f'<section style="overflow-x:auto;margin:22px 0;">'
            f'<table style="width:100%;border-collapse:collapse;">'
            f"<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></section>"
        )

    # 头条版：每行一张卡片，字段名 + 值上下排列，纯 <p> 结构不会被剥
    cards = []
    for r in rows:
        parts = []
        for idx, cell in enumerate(r):
            label = header[idx] if idx < len(header) else ""
            if idx == 0:
                parts.append(
                    f'<p style="margin:0 0 6px;font-size:15px;font-weight:600;'
                    f'color:{C["text"]};line-height:1.6;">{inline(cell)}</p>'
                )
            else:
                parts.append(
                    f'<p style="margin:0;font-size:14px;color:{C["muted"]};'
                    f'line-height:1.7;">'
                    f'<span style="color:{C["accent"]};">{esc(label)}：</span>'
                    f"{inline(cell)}</p>"
                )
        cards.append(
            f'<section style="margin:0 0 10px;padding:13px 16px;'
            f'background:{C["quote_bg"]};border-left:3px solid {C["accent"]};'
            f'border-radius:0 6px 6px 0;">' + "".join(parts) + "</section>"
        )
    return f'<section style="margin:22px 0;">' + "".join(cards) + "</section>"


def convert(md: str, img_base: str) -> str:
    lines = md.split("\n")
    html, i, n = [], 0, len(lines)

    while i < n:
        line = lines[i]

        # 代码块
        if line.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            html.append(code_block(buf))
            continue

        # 表格
        if line.startswith("|") and i + 1 < n and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1]):
            header = [c.strip() for c in line.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            html.append(render_table(header, rows, PLATFORM))
            continue

        # 图片
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line)
        if m:
            alt, src = m.group(1), m.group(2)
            if not src.startswith("http"):
                src = img_base + src.split("/")[-1]
            cap = (
                f'<p style="text-align:center;font-size:13px;color:{C["muted"]};'
                f'margin:10px 0 0;">{esc(alt)}</p>'
                if alt
                else ""
            )
            html.append(
                f'<section style="margin:26px 0;"><img src="{src}" alt="{esc(alt)}" '
                f'style="width:100%;border-radius:8px;border:1px solid {C["border"]};'
                f'display:block;">{cap}</section>'
            )
            i += 1
            continue

        # 引用
        if line.startswith("> "):
            buf = []
            while i < n and lines[i].startswith("> "):
                buf.append(lines[i][2:])
                i += 1
            html.append(
                f'<section style="margin:22px 0;padding:15px 18px;'
                f'background:{C["quote_bg"]};border-left:3px solid {C["accent"]};'
                f'border-radius:0 6px 6px 0;">'
                f'<p style="margin:0;color:{C["muted"]};font-size:15px;'
                f'line-height:1.85;">{inline(" ".join(buf))}</p></section>'
            )
            continue

        # 标题
        if line.startswith("### "):
            html.append(
                f'<h3 style="font-size:17px;font-weight:600;margin:30px 0 14px;'
                f'color:{C["text"]};line-height:1.5;">{inline(line[4:], False)}</h3>'
            )
            i += 1
            continue

        if line.startswith("## "):
            txt = inline(line[3:], False)
            html.append(
                f'<section style="margin:38px 0 18px;">'
                f'<span style="display:inline-block;background:{C["accent"]};color:#fff;'
                f"font-size:17px;font-weight:600;padding:7px 16px;border-radius:6px;"
                f'line-height:1.5;">{txt}</span></section>'
            )
            i += 1
            continue

        if line.startswith("# "):
            html.append(
                f'<h1 style="font-size:21px;font-weight:700;margin:0 0 8px;'
                f'color:{C["text"]};line-height:1.55;text-align:center;">'
                f'{inline(line[2:], False)}</h1>'
                f'<section style="text-align:center;margin:0 0 28px;">'
                f'<span style="display:inline-block;width:44px;height:3px;'
                f'background:{C["accent"]};border-radius:2px;"></span></section>'
            )
            i += 1
            continue

        # 分隔线
        if line.strip() in ("---", "***"):
            html.append(
                f'<section style="text-align:center;margin:34px 0;">'
                f'<span style="color:{C["border"]};font-size:14px;letter-spacing:6px;">'
                f"● ● ●</span></section>"
            )
            i += 1
            continue

        # 无序列表
        if re.match(r"^[-*] ", line):
            items = []
            while i < n and re.match(r"^[-*] ", lines[i]):
                items.append(lines[i][2:])
                i += 1
            li = "".join(
                f'<li style="margin-bottom:9px;line-height:1.85;">{inline(x)}</li>'
                for x in items
            )
            html.append(
                f'<ul style="margin:18px 0;padding-left:24px;font-size:16px;'
                f'color:{C["text"]};">{li}</ul>'
            )
            continue

        # 有序列表
        if re.match(r"^\d+\. ", line):
            items = []
            while i < n and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            li = "".join(
                f'<li style="margin-bottom:9px;line-height:1.85;">{inline(x)}</li>'
                for x in items
            )
            html.append(
                f'<ol style="margin:18px 0;padding-left:24px;font-size:16px;'
                f'color:{C["text"]};">{li}</ol>'
            )
            continue

        if not line.strip():
            i += 1
            continue

        # 普通段落
        buf = []
        while i < n and lines[i].strip() and not re.match(
            r"^(#{1,3} |[-*] |\d+\. |> |```|\||!\[|---$)", lines[i]
        ):
            buf.append(lines[i])
            i += 1
        if buf:
            html.append(f'<p style="margin:18px 0;{BASE}">{inline(" ".join(buf))}</p>')

    return "\n".join(html)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    global PLATFORM
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    PLATFORM = "toutiao" if "--toutiao" in sys.argv else "wechat"

    src = Path(args[0])
    md = src.read_text(encoding="utf-8")

    # 剥掉标题后的元信息块（引用行 + 分隔线）
    lines = md.split("\n")
    keep, skipping = [lines[0]], True
    for ln in lines[1:]:
        if skipping and (ln.startswith(">") or not ln.strip() or ln.strip() == "---"):
            continue
        skipping = False
        keep.append(ln)
    md = keep[0] + "\n\n" + "\n".join(keep[1:])

    img_base = "https://raw.githubusercontent.com/pingfanfan/hello-dsh/main/assets/"
    body = convert(md, img_base)

    out = f"""<!doctype html>
<meta charset="utf-8">
<title>公众号排版稿 — 全选复制后粘进编辑器</title>
<body style="margin:0;background:#eceff3;padding:26px 12px;">
<div style="max-width:677px;margin:0 auto;background:#fff;padding:32px 26px;border-radius:10px;">
<section style="{BASE}font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB',sans-serif;">
{body}
</section>
</div>
</body>"""

    suffix = "-头条" if PLATFORM == "toutiao" else ""
    dst = src.parent / (src.stem.replace("-源稿", "") + suffix + ".html")
    dst.write_text(out, encoding="utf-8")

    plat = "今日头条" if PLATFORM == "toutiao" else "微信公众号"
    print(f"已生成 {dst}  [{plat}]")
    print(f"  代码块 {body.count('background:' + C['block_bg'])} 个（每行独立 <p>，微信不会吃掉换行）")
    print(f"  可点击链接 {body.count('<a href')} 个")
    if PLATFORM == "wechat":
        print(f"  表格 {body.count('<table')} 个（<table> 标签）")
    else:
        print(f"  表格 0 个（已改为卡片式列表，头条不会剥掉）")
    print(f"  图片 {body.count('<img')} 张")
    print(f"  行内代码 {body.count('<code')} 处")


if __name__ == "__main__":
    main()
