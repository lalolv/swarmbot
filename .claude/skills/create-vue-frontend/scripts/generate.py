"""create-vue-frontend 模板生成器。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


IDENTIFIER_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9 _-]*$")
PORT_RE = re.compile(r"^\d{2,5}$")


TEMPLATE_ORDER = [
    "package.json.tpl",
    "vite.config.ts.tpl",
    "tsconfig.json.tpl",
    "tsconfig.node.json.tpl",
    "index.html.tpl",
    "src/main.ts.tpl",
    "src/app.css.tpl",
    "src/lib/utils.ts.tpl",
    "src/themes/index.ts.tpl",
    "src/themes/neobrutalism.css.tpl",
    "src/themes/ai-native.css.tpl",
    "src/stores/theme.ts.tpl",
    "src/composables/useTheme.ts.tpl",
    "src/api/client.ts.tpl",
    "src/stores/observability.ts.tpl",
    "src/components/ui/button/Button.vue.tpl",
    "src/components/ui/button/index.ts.tpl",
    "src/components/ui/badge/Badge.vue.tpl",
    "src/components/ui/badge/index.ts.tpl",
    "src/components/ui/dialog/Dialog.vue.tpl",
    "src/components/ui/dialog/DialogHeader.vue.tpl",
    "src/components/ui/dialog/DialogFooter.vue.tpl",
    "src/components/ui/dialog/index.ts.tpl",
    "src/components/ui/input/Input.vue.tpl",
    "src/components/ui/input/index.ts.tpl",
    "src/components/ui/alert/Alert.vue.tpl",
    "src/components/ui/alert/index.ts.tpl",
    "src/components/ui/card/Card.vue.tpl",
    "src/components/ui/card/index.ts.tpl",
    "src/components/ui/dropdown/DropdownPopover.vue.tpl",
    "src/components/ui/dropdown/index.ts.tpl",
    "src/components/ThemeSwitcher.vue.tpl",
    "src/components/Header.vue.tpl",
    "src/components/InfiniteCanvas.vue.tpl",
    "src/components/RobotCard.vue.tpl",
    "src/components/RobotAvatar.vue.tpl",
    "src/App.vue.tpl",
]


def validate_args(args: argparse.Namespace) -> None:
    if not IDENTIFIER_RE.fullmatch(args.app_name):
        raise ValueError(f"app_name 含非法字符: {args.app_name!r}")
    if not args.app_subtitle.strip():
        raise ValueError("app_subtitle 不能为空")
    if not PORT_RE.fullmatch(args.api_port):
        raise ValueError(f"api_port 非法端口号: {args.api_port!r}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9\-]*", args.package_name):
        raise ValueError(f"package_name 非法（npm 规范）: {args.package_name!r}")


def resolve_target_dir(target_dir: str, workspace_root: Path) -> Path:
    candidate = Path(target_dir)
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    candidate = candidate.resolve()
    if candidate == Path("/"):
        raise ValueError("target_dir 不能是根目录")
    if workspace_root not in candidate.parents and candidate != workspace_root:
        raise ValueError(f"target_dir 越界工作区: {candidate}")
    return candidate


def render(content: str, replacements: dict[str, str]) -> str:
    result = content
    for key, value in replacements.items():
        result = result.replace("{" + key + "}", value)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 Vue 3 前端脚手架")
    parser.add_argument("--app-name", default="My App")
    parser.add_argument("--app-subtitle", default="Task Orchestration System")
    parser.add_argument("--api-port", default="8000")
    parser.add_argument("--target-dir", default="frontend")
    parser.add_argument("--package-name", default="my-app-frontend")
    args = parser.parse_args()

    try:
        validate_args(args)
    except ValueError as exc:
        print(f"[ERROR] 参数校验失败: {exc}")
        return 2

    workspace_root = Path.cwd().resolve()
    templates_root = (Path(__file__).resolve().parent.parent / "templates").resolve()
    target_dir_abs = resolve_target_dir(args.target_dir, workspace_root)

    replacements = {
        "app_name": args.app_name,
        "app_subtitle": args.app_subtitle,
        "api_base_port": args.api_port,
        "package_name": args.package_name,
    }

    generated: list[Path] = []

    for rel_tpl in TEMPLATE_ORDER:
        template_path = templates_root / rel_tpl
        if not template_path.exists():
            print(f"[ERROR] 模板不存在: {template_path}")
            return 3

        # 去掉 .tpl 后缀，得到目标相对路径
        target_rel = Path(rel_tpl[:-4])
        target_path = target_dir_abs / target_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)

        content = template_path.read_text(encoding="utf-8")
        rendered = render(content, replacements)
        target_path.write_text(rendered, encoding="utf-8")
        generated.append(target_path)

    print(f"[OK] 已生成 {len(generated)} 个文件 → {target_dir_abs}")
    for path in generated:
        print(f"  {path.relative_to(workspace_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
