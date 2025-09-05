#!/usr/bin/env bash
set -euo pipefail

# =========== 可配置默认值 ===========
MAIN_BRANCH="main"
FEATURE_BRANCH_DEFAULT=""    # 留空=自动检测当前分支
UPSTREAM_REMOTE="upstream"
ORIGIN_REMOTE="origin"
MODE="rebase"                # 可选：rebase / merge
# ==================================

usage() {
  cat <<'EOF'
用法:
  ./git-sync-wip.sh [--branch <feature-branch>] [--merge|--rebase]

说明:
  - 在有未提交改动时自动执行：
      1) git stash（临时保存改动）
      2) 同步上游：main ← upstream/main
      3) 同步功能分支：feature ← main（默认 rebase，可选 merge）
      4) git stash pop（恢复改动）
  - 默认基于 rebase（历史更直），可用 --merge 切换。

示例:
  ./git-sync-wip.sh                         # 自动检测当前分支为 feature 分支，rebase
  ./git-sync-wip.sh --branch feat/synology-chat
  ./git-sync-wip.sh --merge                 # 用 merge 而不是 rebase
EOF
}

# -------- 参数解析 --------
FEATURE_BRANCH="${FEATURE_BRANCH_DEFAULT}"
while (( "$#" )); do
  case "${1:-}" in
    --branch) shift; FEATURE_BRANCH="${1:-}"; shift || true ;;
    --merge)  MODE="merge"; shift ;;
    --rebase) MODE="rebase"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数: $1"; usage; exit 1 ;;
  esac
done

# -------- 前置检查 --------
need() { command -v "$1" >/dev/null 2>&1 || { echo "❌ 缺少命令：$1"; exit 1; }; }
need git

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ 当前目录不是 git 仓库"; exit 1
fi

# 自动检测当前分支为 feature 分支
if [[ -z "$FEATURE_BRANCH" ]]; then
  FEATURE_BRANCH="$(git branch --show-current)"
fi
if [[ -z "$FEATURE_BRANCH" || "$FEATURE_BRANCH" == "$MAIN_BRANCH" ]]; then
  echo "❌ 当前分支是 ${MAIN_BRANCH} 或未检测到，请用 --branch 指定你的功能分支。"
  exit 1
fi

echo "🔧 MAIN=${MAIN_BRANCH}  FEATURE=${FEATURE_BRANCH}  MODE=${MODE}"

# 检查远程
ORIGIN_URL=$(git remote get-url "${ORIGIN_REMOTE}" 2>/dev/null || true)
UPSTREAM_URL=$(git remote get-url "${UPSTREAM_REMOTE}" 2>/dev/null || true)
[[ -z "${ORIGIN_URL}" ]]   && { echo "❌ 未配置远程 ${ORIGIN_REMOTE}"; exit 1; }
[[ -z "${UPSTREAM_URL}" ]] && { echo "❌ 未配置远程 ${UPSTREAM_REMOTE}"; exit 1; }
echo "✅ origin   = ${ORIGIN_URL}"
echo "✅ upstream = ${UPSTREAM_URL}"

# -------- stash 未提交改动 --------
STASHED=0
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "💾 检测到未提交改动 → git stash"
  git stash push -u -m "sync-wip-$(date +%s)" >/dev/null
  STASHED=1
else
  echo "ℹ️ 工作区干净，无需 stash"
fi

# -------- 同步 upstream/main 到本地 main 并推回 origin --------
set +e
git fetch "${UPSTREAM_REMOTE}" --prune
git fetch "${ORIGIN_REMOTE}"   --prune
set -e

echo "🔁 切到 ${MAIN_BRANCH}"
git checkout "${MAIN_BRANCH}" >/dev/null 2>&1 || git checkout -b "${MAIN_BRANCH}"

echo "⬇️ 更新 ${MAIN_BRANCH} ← ${UPSTREAM_REMOTE}/${MAIN_BRANCH}"
if [[ "${MODE}" == "rebase" ]]; then
  git rebase "${UPSTREAM_REMOTE}/${MAIN_BRANCH}"
else
  git merge --no-edit "${UPSTREAM_REMOTE}/${MAIN_BRANCH}" || true
fi

echo "⬆️ 推送 ${MAIN_BRANCH} → ${ORIGIN_REMOTE}"
git push "${ORIGIN_REMOTE}" "${MAIN_BRANCH}"

# -------- 同步功能分支到最新 main --------
echo "🔁 切到功能分支 ${FEATURE_BRANCH}"
git checkout "${FEATURE_BRANCH}"

echo "🔄 ${FEATURE_BRANCH} ← ${MAIN_BRANCH}（${MODE}）"
if [[ "${MODE}" == "rebase" ]]; then
  git rebase "${MAIN_BRANCH}"
else
  git merge --no-edit "${MAIN_BRANCH}" || true
fi

echo "⬆️ 推送 ${FEATURE_BRANCH} → ${ORIGIN_REMOTE}"
git push -u "${ORIGIN_REMOTE}" "${FEATURE_BRANCH}"

# -------- 恢复 stash --------
if [[ "${STASHED}" -eq 1 ]]; then
  echo "🧺 恢复未提交改动：git stash pop（如有冲突请按提示解决）"
  set +e
  git stash pop
  RC=$?
  set -e
  if [[ $RC -ne 0 ]]; then
    echo "⚠️ stash pop 发生冲突。请按文件提示解决后执行："
    if [[ "${MODE}" == "rebase" ]]; then
      echo "   git add <已解决文件> && git rebase --continue"
    else
      echo "   git add <已解决文件> && git commit"
    fi
  fi
else
  echo "ℹ️ 无需恢复 stash"
fi

echo "✅ 同步完成：${MAIN_BRANCH} 与 ${FEATURE_BRANCH} 已更新，未提交改动已恢复"