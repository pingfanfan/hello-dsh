#!/usr/bin/env python3
"""把 Markdown 转成适合 X（Twitter）长文的纯文本。

X 的长文编辑器不接受粘贴的 HTML 或 Markdown 语法，只能用纯文本 +
它自己的加粗按钮。所以这里的策略是：

- 标题用符号分隔，视觉上形成层次
- 代码块用全角方框包起来，在无等宽字体的环境里也能看出边界
- 表格拍平成「A → B」的行
- 图片位置留占位标记，方便手动插图
- 链接保留完整 URL（X 会自动识别）

用法：
    python3 scripts/md2twitter.py drafts/05-公众号-源稿.md
"""
import re
import sys
from pathlib import Path

RULE = "━━━━━━━━━━━━━━"


def strip_inline(s: str) -> str:
    """去掉 Markdown 行内标记，保留可读文本。"""
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1（\2）", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    return s


def convert(md: str) -> str:
    lines = md.split("\n")
    out, i, n = [], 0, len(lines)
    img_no = 0

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
            out.append("┌" + "─" * 30)
            for b in buf:
                out.append("│ " + b if b.strip() else "│")
            out.append("└" + "─" * 30)
            out.append("")
            continue

        # 表格 → 拍平成箭头行
        if line.startswith("|") and i + 1 < n and re.match(r"^\|[\s\-:|]+\|$", lines[i + 1]):
            header = [c.strip() for c in line.strip("|").split("|")]
            i += 2
            while i < n and lines[i].startswith("|"):
                cells = [strip_inline(c.strip()) for c in lines[i].strip("|").split("|")]
                if len(cells) >= 2:
                    out.append(f"▸ {cells[0]}")
                    for k in range(1, len(cells)):
                        label = header[k] if k < len(header) else ""
                        out.append(f"   {strip_inline(label)}：{cells[k]}")
                    out.append("")
                i += 1
            continue

        # 图片 → 占位
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line)
        if m:
            img_no += 1
            alt = m.group(1)
            fname = m.group(2).split("/")[-1]
            out.append(f"【插图 {img_no}：{fname}{' — ' + alt if alt else ''}】")
            out.append("")
            i += 1
            continue

        # 引用
        if line.startswith("> "):
            buf = []
            while i < n and lines[i].startswith("> "):
                buf.append(strip_inline(lines[i][2:]))
                i += 1
            out.append("「" + " ".join(buf) + "」")
            out.append("")
            continue

        # 标题
        if line.startswith("### "):
            out.append("")
            out.append("◆ " + strip_inline(line[4:]))
            out.append("")
            i += 1
            continue
        if line.startswith("## "):
            out.append("")
            out.append(RULE)
            out.append(strip_inline(line[3:]))
            out.append(RULE)
            out.append("")
            i += 1
            continue
        if line.startswith("# "):
            out.append(strip_inline(line[2:]))
            out.append("")
            i += 1
            continue

        if line.strip() in ("---", "***"):
            out.append("")
            out.append("· · ·")
            out.append("")
            i += 1
            continue

        # 列表
        if re.match(r"^[-*] ", line):
            while i < n and re.match(r"^[-*] ", lines[i]):
                out.append("· " + strip_inline(lines[i][2:]))
                i += 1
            out.append("")
            continue

        if re.match(r"^\d+\. ", line):
            k = 1
            while i < n and re.match(r"^\d+\. ", lines[i]):
                out.append(f"{k}. " + strip_inline(re.sub(r'^\d+\. ', '', lines[i])))
                k += 1
                i += 1
            out.append("")
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
            out.append(strip_inline(" ".join(buf)))
            out.append("")

    # 压掉连续空行
    txt = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", txt).strip() + "\n"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src = Path(sys.argv[1])
    md = src.read_text(encoding="utf-8")

    lines = md.split("\n")
    keep, skipping = [lines[0]], True
    for ln in lines[1:]:
        if skipping and (ln.startswith(">") or not ln.strip() or ln.strip() == "---"):
            continue
        skipping = False
        keep.append(ln)
    md = keep[0] + "\n\n" + "\n".join(keep[1:])

    body = convert(md)
    dst = src.parent / (src.stem.replace("-源稿", "") + "-X长文.txt")
    dst.write_text(body, encoding="utf-8")

    print(f"已生成 {dst}")
    print(f"  字数 {len(body)}")
    print(f"  插图位 {body.count('【插图')} 处（需手动上传）")
    print()
    print("用法：全选复制，粘进 X 的 Article 编辑器。")
    print("     标题行可以用编辑器的加粗按钮再强调一次。")


if __name__ == "__main__":
    main()
