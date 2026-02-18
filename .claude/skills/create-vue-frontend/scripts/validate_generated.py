"""生成后校验脚本。

用途：
1. 检查必要文件是否存在
2. 检查占位符残留（{app_name} 等未替换）
3. 检查 Vue 文件是否包含 <template> 标签
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"\{(app_name|app_subtitle|api_base_port|package_name)\}")

REQUIRED_FILES = [
    "package.json",
    "vite.config.ts",
    "index.html",
    "src/main.ts",
    "src/App.vue",
    "src/app.css",
    "src/lib/utils.ts",
    "src/themes/index.ts",
    "src/themes/neobrutalism.css",
    "src/themes/dark.css",
    "src/stores/theme.ts",
    "src/stores/observability.ts",
    "src/composables/useTheme.ts",
    "src/api/client.ts",
    "src/components/Header.vue",
    "src/components/InfiniteCanvas.vue",
    "src/components/RobotCard.vue",
    "src/components/RobotAvatar.vue",
    "src/components/ThemeSwitcher.vue",
    "src/components/ui/button/Button.vue",
    "src/components/ui/badge/Badge.vue",
    "src/components/ui/dialog/Dialog.vue",
    "src/components/ui/input/Input.vue",
    "src/components/ui/alert/Alert.vue",
    "src/components/ui/card/Card.vue",
]


def validate_required_files(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"缺少文件: {rel}")
    return errors


def validate_placeholders(file: Path) -> list[str]:
    errors: list[str] = []
    text = file.read_text(encoding="utf-8")
    matches = PLACEHOLDER_RE.findall(text)
    if matches:
        unique = sorted(set(matches))
        errors.append(f"占位符未替换: {file.name} → {unique}")
    return errors


def validate_vue_template(file: Path) -> list[str]:
    errors: list[str] = []
    text = file.read_text(encoding="utf-8")
    if "<template>" not in text and "<template " not in text:
        errors.append(f"缺少 <template> 标签: {file.name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验生成的 Vue 前端代码")
    parser.add_argument("--root", required=True, help="生成代码根目录")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] 无效目录: {root}")
        return 2

    all_errors: list[str] = []

    # 1. 必要文件检查
    all_errors.extend(validate_required_files(root))

    # 2. 遍历所有文件检查占位符和 Vue 结构
    for file in sorted(root.rglob("*")):
        if not file.is_file():
            continue
        if file.suffix in (".ts", ".js", ".vue", ".css", ".html", ".json"):
            all_errors.extend(validate_placeholders(file))
        if file.suffix == ".vue":
            all_errors.extend(validate_vue_template(file))

    if all_errors:
        print(f"[ERROR] 校验失败（{len(all_errors)} 项）:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    vue_count = len(list(root.rglob("*.vue")))
    ts_count = len(list(root.rglob("*.ts")))
    css_count = len(list(root.rglob("*.css")))
    print(f"[OK] 校验通过 — Vue:{vue_count} TS:{ts_count} CSS:{css_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
