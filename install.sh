#!/bin/sh
# hello-dsh installer
#
# 安全约束（有意为之，请勿放宽）：
#   - 只写入 ~/.dsh/skills 或 ~/.agents/skills，不碰任何其他路径
#   - 安装前打印将写入的确切路径
#   - 卸载按本仓库的技能清单逐个比对删除，绝不使用通配符
#   - 不修改 shell profile、git 配置或任何全局设置
#   - 脚本失败不影响技能本身可用——始终可以手动拷贝 skills/ 下的目录

set -eu

REPO_URL="https://github.com/pingfanfan/hello-dsh.git"
TARGET_DEFAULT="$HOME/.dsh/skills"
DRY_RUN=0
UNINSTALL=0
TARGET="$TARGET_DEFAULT"
ASSUME_YES=0

usage() {
  cat <<'EOF'
用法: install.sh [选项]

选项:
  --dry-run        只打印将要执行的操作，不做任何改动
  --uninstall      移除本仓库安装的技能（按清单比对，不使用通配符）
  --agents-dir     安装到 ~/.agents/skills（跨 agent 共享目录）而非 ~/.dsh/skills
  --yes            跳过确认提示
  -h, --help       显示本帮助

不带参数运行时会先展示计划并请求确认。
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --agents-dir) TARGET="$HOME/.agents/skills" ;;
    --yes|-y) ASSUME_YES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

# 定位技能来源目录：优先使用脚本同级的 skills/（已克隆的情况），
# 否则克隆到临时目录。
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CLONE_TMP=""
cleanup() {
  [ -n "$CLONE_TMP" ] && [ -d "$CLONE_TMP" ] && rm -rf "$CLONE_TMP"
  return 0
}
trap cleanup EXIT INT TERM

if [ -d "$SCRIPT_DIR/examples/skills" ]; then
  SRC="$SCRIPT_DIR/examples/skills"
else
  command -v git >/dev/null 2>&1 || { echo "需要 git，未找到。" >&2; exit 1; }
  CLONE_TMP=$(mktemp -d)
  echo "正在获取 hello-dsh ..."
  git clone --depth 1 --quiet "$REPO_URL" "$CLONE_TMP/repo"
  SRC="$CLONE_TMP/repo/examples/skills"
fi

[ -d "$SRC" ] || { echo "找不到技能目录: $SRC" >&2; exit 1; }

# 技能清单 = 源目录下含 SKILL.md 的一级子目录
SKILLS=$(cd "$SRC" && for d in */; do
  [ -f "${d}SKILL.md" ] && printf '%s\n' "${d%/}"
done)

[ -n "$SKILLS" ] || { echo "源目录中没有技能。" >&2; exit 1; }

COUNT=$(printf '%s\n' "$SKILLS" | wc -l | tr -d ' ')

if [ "$UNINSTALL" -eq 1 ]; then
  echo "将从以下位置移除 $COUNT 个技能："
  echo "  $TARGET"
  echo
  printf '%s\n' "$SKILLS" | sed 's/^/  - /'
  echo
  if [ "$DRY_RUN" -eq 1 ]; then echo "[dry-run] 未做任何改动。"; exit 0; fi
  if [ "$ASSUME_YES" -eq 0 ]; then
    printf "确认移除？[y/N] "
    read -r reply </dev/tty || reply=n
    case "$reply" in y|Y|yes|YES) ;; *) echo "已取消。"; exit 0 ;; esac
  fi
  removed=0
  # 逐个按名字删除；不使用通配符，不触碰未在清单中的目录
  printf '%s\n' "$SKILLS" | while IFS= read -r name; do
    [ -n "$name" ] || continue
    dir="$TARGET/$name"
    if [ -d "$dir" ] && [ -f "$dir/SKILL.md" ]; then
      rm -rf "$dir"
      echo "  已移除 $name"
    fi
  done
  echo "完成。未在清单中的技能保持原样。"
  exit 0
fi

echo "hello-dsh — 将安装 $COUNT 个技能"
echo
echo "  来源: $SRC"
echo "  目标: $TARGET"
echo
printf '%s\n' "$SKILLS" | sed 's/^/  - /'
echo
echo "本脚本只写入上述目标目录，不修改 shell 配置或任何全局设置。"
echo

if [ "$DRY_RUN" -eq 1 ]; then echo "[dry-run] 未做任何改动。"; exit 0; fi

if [ "$ASSUME_YES" -eq 0 ]; then
  printf "继续？[y/N] "
  read -r reply </dev/tty || reply=n
  case "$reply" in y|Y|yes|YES) ;; *) echo "已取消。"; exit 0 ;; esac
fi

mkdir -p "$TARGET"
printf '%s\n' "$SKILLS" | while IFS= read -r name; do
  [ -n "$name" ] || continue
  rm -rf "$TARGET/$name"
  cp -R "$SRC/$name" "$TARGET/$name"
  echo "  已安装 $name"
done

echo
echo "完成。DSH 会自动发现这些技能，无需重启。"
echo "移除请运行: install.sh --uninstall"
