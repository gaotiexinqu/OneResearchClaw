#!/usr/bin/env python3
"""
One-Research 模型准备工具

用于下载和准备 One-Research 流水线所需的模型权重。

用法:
    one-report-prepare-models              # 下载所有模型
    one-report-prepare-models --list       # 列出可用模型
    one-report-prepare-models --audio      # 仅下载音频处理模型
    one-report-prepare-models --docling    # 仅下载文档解析模型
    one-report-prepare-models --check       # 检查已下载的模型

模型下载后存放目录: models/<model-name>/
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ============================================================
# 模型配置
# ============================================================

@dataclass
class ModelConfig:
    """模型配置"""
    name: str                          # 模型目录名
    display_name: str                   # 显示名称
    description: str                   # 模型描述
    hf_repo: str                       # HuggingFace 仓库
    download_command: str              # 下载命令
    required_for: list[str] = field(default_factory=list)  # 所属功能组
    optional: bool = False             # 是否为可选模型


MODELS: list[ModelConfig] = [
    ModelConfig(
        name="faster-whisper-large-v2",
        display_name="Faster-Whisper Large v2",
        description="语音识别模型，用于将音频转录为文字",
        hf_repo="Systran/faster-whisper-large-v3",
        download_command="python -c \"from faster_whisper import download_model; download_model('large-v2', output_dir='models/faster-whisper-large-v2')\"",
        required_for=["audio", "meeting"],
    ),
    ModelConfig(
        name="speaker-diarization-community-1",
        display_name="pyannote Speaker Diarization 3.1",
        description="说话人分离模型，用于识别音频中的不同说话人",
        hf_repo="pyannote/speaker-diarization-3.1",
        download_command="huggingface-cli download pyannote/speaker-diarization-3.1 --local-dir models/speaker-diarization-community-1",
        required_for=["audio", "meeting"],
    ),
    ModelConfig(
        name="docling",
        display_name="Docling Models",
        description="文档解析模型，用于从 PDF/DOCX 中提取内容和结构",
        hf_repo="ds4sd/docling-models",
        download_command="docling-tools models download",
        required_for=["document"],
    ),
    ModelConfig(
        name="rapidocr",
        display_name="RapidOCR Models",
        description="OCR 模型，用于文档中的文字识别",
        hf_repo="RapidOM/RapidOCR",
        download_command="huggingface-cli download RapidOM/RapidOCR --local-dir models/rapidocr",
        required_for=["document"],
        optional=True,
    ),
]


# ============================================================
# 工具函数
# ============================================================

def get_repo_root() -> Path:
    """获取项目根目录"""
    # 方式1: 从当前文件向上查找 pyproject.toml
    current = Path(__file__).resolve().parent
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent

    # 方式2: 尝试从环境变量获取
    if "ONEREPO_ROOT" in os.environ:
        return Path(os.environ["ONEREPO_ROOT"])

    # 方式3: 使用当前工作目录
    return Path.cwd()


def get_models_dir(repo_root: Optional[Path] = None) -> Path:
    """获取模型存储目录"""
    if repo_root is None:
        repo_root = get_repo_root()
    return repo_root / "models"


def ensure_models_dir(models_dir: Path) -> None:
    """确保模型目录存在"""
    models_dir.mkdir(parents=True, exist_ok=True)


def is_model_downloaded(model_name: str, models_dir: Path) -> bool:
    """检查模型是否已下载"""
    model_path = models_dir / model_name
    if not model_path.exists():
        return False
    # 检查目录是否非空
    return any(model_path.iterdir())


def get_model_status(model: ModelConfig, models_dir: Path) -> str:
    """获取模型状态"""
    if is_model_downloaded(model.name, models_dir):
        return "✓ 已下载"
    return "○ 未下载"


def format_model_info(model: ModelConfig, models_dir: Path) -> str:
    """格式化模型信息"""
    status = get_model_status(model, models_dir)
    required = ", ".join(model.required_for) if model.required_for else "可选"
    info = textwrap.dedent(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │ {model.display_name:<59} │
    ├─────────────────────────────────────────────────────────────┤
    │ 目录: {model.name:<56} │
    │ 用途: {model.description:<54} │
    │ 需要: {required:<54} │
    │ 状态: {status:<54} │
    │ 仓库: {model.hf_repo:<54} │
    └─────────────────────────────────────────────────────────────┘
    """).strip()
    return info


# ============================================================
# 下载器
# ============================================================

def check_huggingface_cli() -> bool:
    """检查 huggingface-cli 是否可用"""
    try:
        subprocess.run(
            ["huggingface-cli", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_huggingface_hub() -> bool:
    """检查 huggingface_hub 是否可用"""
    try:
        import huggingface_hub  # noqa: F401
        return True
    except ImportError:
        return False


def download_with_huggingface_cli(repo_id: str, local_dir: str, token: Optional[str] = None) -> bool:
    """使用 huggingface-cli 下载模型"""
    cmd = ["huggingface-cli", "download", repo_id]
    if token:
        cmd.extend(["--token", token])
    cmd.extend(["--local-dir", local_dir])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"      下载失败: {e.stderr}", file=sys.stderr)
        return False


def download_with_huggingface_hub(repo_id: str, local_dir: str, token: Optional[str] = None) -> bool:
    """使用 huggingface_hub Python 包下载模型"""
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            token=token,
            resume_download=True,
        )
        return True
    except Exception as e:
        print(f"      下载失败: {e}", file=sys.stderr)
        return False


def download_model(model: ModelConfig, models_dir: Path, token: Optional[str] = None) -> bool:
    """下载单个模型"""
    model_path = models_dir / model.name
    print(f"\n📥 正在下载: {model.display_name}")
    print(f"   目标目录: {model_path}")
    print(f"   HuggingFace: {model.hf_repo}")

    # 确保目录存在
    model_path.mkdir(parents=True, exist_ok=True)

    # 根据模型类型选择下载方式
    if "docling" in model.name:
        # Docling 使用专门的工具
        print("   使用 docling-tools 下载...")
        try:
            result = subprocess.run(
                ["docling-tools", "models", "download"],
                capture_output=True,
                text=True,
                cwd=models_dir,
            )
            if result.returncode == 0:
                print(f"   ✅ {model.display_name} 下载完成")
                return True
            else:
                print(f"   ⚠️  下载命令执行失败: {result.stderr}", file=sys.stderr)
                return False
        except FileNotFoundError:
            print("   ⚠️  docling-tools 未安装，请先安装: pip install docling", file=sys.stderr)
            return False
    elif "faster-whisper" in model.name:
        # Faster-Whisper 使用 Python API
        print("   使用 faster-whisper 下载...")
        try:
            from faster_whisper import download_model
            download_model("large-v2", output_dir=str(model_path))
            print(f"   ✅ {model.display_name} 下载完成")
            return True
        except Exception as e:
            print(f"   ⚠️  下载失败: {e}", file=sys.stderr)
            return False
    else:
        # 其他模型使用 huggingface-cli 或 huggingface_hub
        print("   使用 HuggingFace 下载...")

        if check_huggingface_cli():
            return download_with_huggingface_cli(model.hf_repo, str(model_path), token)
        elif check_huggingface_hub():
            return download_with_huggingface_hub(model.hf_repo, str(model_path), token)
        else:
            print("   ⚠️  未找到 huggingface-cli 或 huggingface_hub", file=sys.stderr)
            print("   请安装: pip install huggingface_hub", file=sys.stderr)
            return False


def download_all_models(models_dir: Path, token: Optional[str] = None) -> dict[str, bool]:
    """下载所有模型"""
    results = {}
    for model in MODELS:
        results[model.name] = download_model(model, models_dir, token)
    return results


def download_models_by_group(groups: list[str], models_dir: Path, token: Optional[str] = None) -> dict[str, bool]:
    """按功能组下载模型"""
    results = {}
    for model in MODELS:
        if any(g in model.required_for for g in groups):
            results[model.name] = download_model(model, models_dir, token)
    return results


def download_specific_models(model_names: list[str], models_dir: Path, token: Optional[str] = None) -> dict[str, bool]:
    """下载指定的模型"""
    results = {}
    name_to_model = {m.name: m for m in MODELS}

    for name in model_names:
        if name in name_to_model:
            results[name] = download_model(name_to_model[name], models_dir, token)
        else:
            print(f"⚠️  未知模型: {name}")
            results[name] = False
    return results


# ============================================================
# 检查和报告
# ============================================================

def check_models(models_dir: Path) -> None:
    """检查已下载的模型状态"""
    print("\n📋 模型状态检查\n")

    all_downloaded = True
    for model in MODELS:
        status = get_model_status(model, models_dir)
        is_downloaded = "已下载" in status

        if not is_downloaded:
            all_downloaded = False

        status_icon = "✅" if is_downloaded else "⭕"
        print(f"  {status_icon} {model.display_name}")
        print(f"      目录: {model.name}")
        print(f"      用途: {model.description}")

        if not is_downloaded:
            print(f"      ⚠️  需要运行下载: one-report-prepare-models --{model.required_for[0] if model.required_for else 'all'}")
        print()

    if all_downloaded:
        print("✅ 所有模型已准备就绪！")
    else:
        print("⚠️  部分模型未下载，流水线可能无法正常工作。")
        print("   运行 'one-report-prepare-models --all' 下载所有模型。")


def list_models(models_dir: Path) -> None:
    """列出所有可用模型"""
    print("\n📦 One-Research 可用模型\n")

    for model in MODELS:
        print(format_model_info(model, models_dir))
        print()


# ============================================================
# 主函数
# ============================================================

def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="One-Research 模型准备工具 - 下载和管理模型权重",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            示例:
              %(prog)s --all                    # 下载所有模型
              %(prog)s --list                  # 列出可用模型
              %(prog)s --check                 # 检查已下载的模型
              %(prog)s --audio                 # 仅下载音频处理模型
              %(prog)s --document              # 仅下载文档解析模型
              %(prog)s faster-whisper-large-v2 # 下载指定模型

            环境变量:
              HF_TOKEN     HuggingFace 访问令牌（用于私有模型）
              ONEREPO_ROOT One-Research 项目根目录
        """),
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有可用模型及其状态",
    )

    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="检查已下载模型的状态",
    )

    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="下载所有模型",
    )

    parser.add_argument(
        "--audio",
        action="store_true",
        help="下载音频处理模型（Whisper + 说话人分离）",
    )

    parser.add_argument(
        "--document", "-d",
        action="store_true",
        help="下载文档解析模型（Docling）",
    )

    parser.add_argument(
        "--models-dir",
        type=Path,
        default=None,
        help=f"模型存储目录（默认: <项目根目录>/models）",
    )

    parser.add_argument(
        "models",
        nargs="*",
        metavar="MODEL_NAME",
        help="指定要下载的模型名称",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出",
    )

    return parser.parse_args()


def main() -> int:
    """主函数"""
    args = parse_args()
    repo_root = get_repo_root()
    models_dir = args.models_dir or get_models_dir(repo_root)

    # 确保模型目录存在
    ensure_models_dir(models_dir)

    print(f"📂 项目根目录: {repo_root}")
    print(f"📂 模型目录: {models_dir}")

    # 列出模型
    if args.list:
        list_models(models_dir)
        return 0

    # 检查模型状态
    if args.check:
        check_models(models_dir)
        return 0

    # 获取 HuggingFace token
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")

    # 收集要下载的模型
    download_all = args.all
    download_groups: list[str] = []
    download_specific: list[str] = []

    if args.audio:
        download_groups.append("audio")
        download_groups.append("meeting")
        download_all = True  # 音频组需要多个模型

    if args.document:
        download_groups.append("document")

    if args.models:
        download_specific = args.models

    if not (download_all or download_groups or download_specific):
        print("\n⚠️  未指定要下载的内容")
        print("   使用 --all 下载所有模型，或使用 --list 查看可用模型")
        print("   更多信息: one-report-prepare-models --help")
        return 1

    # 执行下载
    print("\n" + "=" * 60)
    print("开始下载模型")
    print("=" * 60)

    if download_specific:
        results = download_specific_models(download_specific, models_dir, token)
    elif download_groups:
        results = download_models_by_group(download_groups, models_dir, token)
    else:
        results = download_all_models(models_dir, token)

    # 汇总结果
    print("\n" + "=" * 60)
    print("下载结果汇总")
    print("=" * 60)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for name, success in results.items():
        model = next((m for m in MODELS if m.name == name), None)
        display_name = model.display_name if model else name
        icon = "✅" if success else "❌"
        print(f"  {icon} {display_name}")

    print(f"\n成功: {success_count}/{total_count}")

    if success_count == total_count:
        print("\n🎉 所有模型下载完成！")
        return 0
    else:
        print("\n⚠️  部分模型下载失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
