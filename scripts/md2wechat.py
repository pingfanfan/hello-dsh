#!/usr/bin/env python3
"""把 Markdown 转成可直接粘进微信公众号编辑器的 HTML。

公众号编辑器会剥掉 <style> 标签和 class，只保留内联 style，
所以每个元素的样式都得写在标签上。

用法：
    python3 scripts/md2wechat.py drafts/05-公众号-源稿.md
    # 输出 drafts/05-公众号.html
"""
import re
import sys
from pathlib import Path

# 公众号里实测可用的配色（浅色底，微信不支持深色模式切换）
C = {
    "text": "#2c3e50",
    "muted": "#6b7c93",
    "brand": "#2563eb",
    "code_bg": "#f6f8fa",
    "code_text": "#476582",
    "block_bg": "#f8f9fb",
    "border": "#e3e8ef",
    "quote_bg": "#f7f9fc",
    "quote_bar": "#2563eb",
}

BASE = f"font-size:16px;line-height:1.85;color:{C['text']};word-break:break-word;"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s: str) -> str:
    """处理行内格式：`代码`、**粗体**、[链接](url)。"""
    out = []
    i = 0
    # 先切出行内代码，避免其中的 * 被误认成粗体
    for part in re.split(r"(`[^`]+`)", s):
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            code = esc(part[1:-1])
            out.append(
                f'<code style="background:{C["code_bg"]};color:{C["code_text"]};'
                f'padding:2px 6px;border-radius:3px;font-size:14px;'
                f'font-family:Menlo,Consolas,monospace;">{code}</code>'
            )
        else:
            t = esc(part)
            t = re.sub(
                r"\[([^\]]+)\]\(([^)]+)\)",
                rf'<a href="\2" style="color:{C["brand"]};text-decoration:none;">\1</a>',
                t,
            )
            t = re.sub(r"\*\*([^*]+)\*\*", r'<strong style="font-weight:600;">\1</strong>', t)
            out.append(t)
    return "".join(out)


def convert(md: str, img_base: str) -> str:
    lines = md.split("\n")
    html, i = [], 0
    n = len(lines)

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
            code = esc("\n".join(buf))
            html.append(
                f'<pre style="background:{C["block_bg"]};border:1px solid {C["border"]};'
                f'border-radius:6px;padding:16px;overflow-x:auto;margin:20px 0;'
                f'font-size:14px;line-height:1.7;font-family:Menlo,Consolas,monospace;'
                f'color:{C["code_text"]};white-space:pre;">{code}</pre>'
            )
            continue

        # 表格
        if line.startswith("|") and i + 1 < n and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1]):
            header = [c.strip() for c in line.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            th = "".join(
                f'<th style="padding:10px 12px;text-align:left;font-size:14px;font-weight:600;'
                f'border-bottom:2px solid {C["border"]};color:{C["muted"]};">{inline(c)}</th>'
                for c in header
            )
            tr = "".join(
                "<tr>"
                + "".join(
                    f'<td style="padding:10px 12px;font-size:14px;vertical-align:top;'
                    f'border-bottom:1px solid {C["border"]};">{inline(c)}</td>'
                    for c in r
                )
                + "</tr>"
                for r in rows
            )
            html.append(
                f'<section style="overflow-x:auto;margin:20px 0;">'
                f'<table style="width:100%;border-collapse:collapse;">'
                f"<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></section>"
            )
            continue

        # 图片
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line)
        if m:
            alt, src = m.group(1), m.group(2)
            if not src.startswith("http"):
                src = img_base + src.split("/")[-1]
            cap = (
                f'<figcaption style="text-align:center;font-size:13px;color:{C["muted"]};'
                f'margin-top:8px;">{esc(alt)}</figcaption>'
                if alt
                else ""
            )
            html.append(
                f'<figure style="margin:24px 0;"><img src="{src}" alt="{esc(alt)}" '
                f'style="width:100%;border-radius:6px;border:1px solid {C["border"]};display:block;">'
                f"{cap}</figure>"
            )
            i += 1
            continue

        # 引用
        if line.startswith("> "):
            buf = []
            while i < n and lines[i].startswith("> "):
                buf.append(lines[i][2:])
                i += 1
            body = inline(" ".join(buf))
            html.append(
                f'<blockquote style="margin:20px 0;padding:14px 18px;'
                f'background:{C["quote_bg"]};border-left:4px solid {C["quote_bar"]};'
                f'border-radius:0 6px 6px 0;color:{C["muted"]};font-size:15px;'
                f'line-height:1.8;">{body}</blockquote>'
            )
            continue

        # 标题
        if line.startswith("### "):
            html.append(
                f'<h3 style="font-size:17px;font-weight:600;margin:28px 0 12px;'
                f'color:{C["text"]};">{inline(line[4:])}</h3>'
            )
            i += 1
            continue
        if line.startswith("## "):
            html.append(
                f'<h2 style="font-size:19px;font-weight:700;margin:36px 0 16px;'
                f'padding-left:12px;border-left:4px solid {C["brand"]};'
                f'color:{C["text"]};line-height:1.4;">{inline(line[3:])}</h2>'
            )
            i += 1
            continue
        if line.startswith("# "):
            html.append(
                f'<h1 style="font-size:22px;font-weight:700;margin:0 0 24px;'
                f'color:{C["text"]};line-height:1.5;">{inline(line[2:])}</h1>'
            )
            i += 1
            continue

        # 分隔线
        if line.strip() in ("---", "***"):
            html.append(
                f'<hr style="border:none;border-top:1px solid {C["border"]};margin:32px 0;">'
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
                f'<li style="margin-bottom:8px;line-height:1.8;">{inline(x)}</li>' for x in items
            )
            html.append(
                f'<ul style="margin:16px 0;padding-left:22px;font-size:16px;'
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
                f'<li style="margin-bottom:8px;line-height:1.8;">{inline(x)}</li>' for x in items
            )
            html.append(
                f'<ol style="margin:16px 0;padding-left:22px;font-size:16px;'
                f'color:{C["text"]};">{li}</ol>'
            )
            continue

        # 空行
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
            html.append(
                f'<p style="margin:16px 0;{BASE}">{inline(" ".join(buf))}</p>'
            )

    return "\n".join(html)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src = Path(sys.argv[1])
    md = src.read_text(encoding="utf-8")

    # 去掉给自己看的元信息块：标题后连续的引用行 + 分隔线
    lines = md.split("\n")
    keep, skipping = [], True
    for idx, ln in enumerate(lines):
        if idx == 0:
            keep.append(ln)
            continue
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
<body style="margin:0;background:#eef1f5;padding:24px 12px;">
<div style="max-width:677px;margin:0 auto;background:#fff;padding:28px 24px;border-radius:8px;">
<section style="{BASE}font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB',sans-serif;">
{body}
</section>
</div>
</body>"""

    dst = src.parent / (src.stem.replace("-源稿", "") + ".html")
    dst.write_text(out, encoding="utf-8")
    print(f"已生成 {dst}")
    print(f"  代码块 {body.count('<pre')} 个")
    print(f"  引用 {body.count('<blockquote')} 处")
    print(f"  表格 {body.count('<table')} 个")
    print(f"  图片 {body.count('<figure')} 张")
    print(f"  行内代码 {body.count('<code')} 处")


if __name__ == "__main__":
    main()
