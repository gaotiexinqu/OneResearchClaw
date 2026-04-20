#!/usr/bin/env python3
"""
One-Research 系统依赖检查工具

检查并提示用户安装所需系统依赖（ffmpeg, espeak-ng 等）。

用法:
    one-report-install-system-deps          # 检查并显示状态
    one-report-install-system-deps --check  # 仅检查，不安装
    one-report-install-system-deps --install  # 自动安装（需要 sudo）
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ============================================================
# 系统依赖配置
# ============================================================

@dataclass
class SystemDep:
    """系统依赖配置"""
    name: str                        # 包管理器中的名称
    display_name: str                # 显示名称
    command: str                     # 检测命令
    apt_package: str                 # APT 包名
    brew_package: str                # Homebrew 包名
    description: str                # 用途描述
    required_for: list[str]         # 所属功能组


SYSTEM_DEPS: list[SystemDep] = [
    SystemDep(
        name="ffmpeg",
        display_name="FFmpeg",
        command="ffmpeg",
        apt_package="ffmpeg",
        brew_package="ffmpeg",
        description="音视频处理（格式转换、提取音频流）",
        required_for=["audio", "meeting"],
    ),
    SystemDep(
        name="espeak-ng",
        display_name="eSpeak NG",
        command="espeak-ng",
        apt_package="espeak-ng",
        brew_package="espeak-ng",
        description="语音合成（用于 TTS 音频导出）",
        required_for=["export"],
    ),
    SystemDep(
        name="node",
        display_name="Node.js",
        command="node",
        apt_package="nodejs",
        brew_package="node",
        description="JavaScript 运行时（用于 PPTX 导出）",
        required_for=["export"],
    ),
    SystemDep(
        name="npm",
        display_name="npm",
        command="npm",
        apt_package="npm",
        brew_package="npm",
        description="Node.js 包管理器（用于安装 pptxgenjs）",
        required_for=["export"],
    ),
]


# ============================================================
# 工具函数
# ============================================================

def get_os_type() -> str:
    """获取操作系统类型"""
    system = platform.system().lower()
    if system == "linux":
        # 检查是否是 WSL
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    return "wsl"
        except Exception:
            pass
        return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    return "unknown"


def check_command(command: str) -> bool:
    """检查命令是否可用"""
    return shutil.which(command) is not None


def check_package_installed(package_name: str) -> bool:
    """检查 APT 包是否已安装"""
    try:
        result = subprocess.run(
            ["dpkg", "-s", package_name],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_install_command(dep: SystemDep, os_type: str) -> tuple[str, bool]:
    """获取安装命令"""
    if os_type in ("linux", "wsl"):
        return f"sudo apt-get install -y {dep.apt_package}", True
    elif os_type == "macos":
        return f"brew install {dep.brew_package}", True
    else:
        return "", False


def install_package(package_name: str, os_type: str) -> bool:
    """安装包"""
    if os_type in ("linux", "wsl"):
        try:
            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", package_name],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False
    elif os_type == "macos":
        try:
            result = subprocess.run(
                ["brew", "install", package_name],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False
    return False


# ============================================================
# 检查和报告
# ============================================================

@dataclass
class DepStatus:
    """依赖状态"""
    dep: SystemDep
    installed: bool
    install_command: str
    can_install: bool


def check_all_deps() -> list[DepStatus]:
    """检查所有系统依赖"""
    os_type = get_os_type()
    statuses = []

    for dep in SYSTEM_DEPS:
        installed = check_command(dep.command)
        install_cmd, can_install = get_install_command(dep, os_type)

        statuses.append(DepStatus(
            dep=dep,
            installed=installed,
            install_command=install_cmd,
            can_install=can_install,
        ))

    return statuses


def print_status_report(statuses: list[DepStatus]) -> None:
    """打印状态报告"""
    os_type = get_os_type()
    print(f"\n📋 One-Research 系统依赖检查 ({os_type.upper()})\n")
    print("-" * 70)

    for status in statuses:
        icon = "✅" if status.installed else "❌"
        print(f"  {icon} {status.dep.display_name}")
        print(f"      命令: {status.dep.command}")
        print(f"      用途: {status.dep.description}")

        if status.installed:
            print(f"      状态: 已安装")
        else:
            print(f"      状态: 未安装")
            if status.can_install:
                print(f"      安装: {status.install_command}")
            else:
                print(f"      安装: 不支持自动安装，请手动安装")

    print("-" * 70)

    all_installed = all(s.installed for s in statuses)
    if all_installed:
        print("\n✅ 所有系统依赖已就绪！")
    else:
        missing = [s.dep.display_name for s in statuses if not s.installed]
        print(f"\n⚠️  缺少系统依赖: {', '.join(missing)}")
        print("   请运行 'one-report-install-system-deps --install' 进行安装")
        print("   或手动安装上述依赖")


def install_missing_deps() -> bool:
    """安装缺失的系统依赖"""
    os_type = get_os_type()

    if os_type not in ("linux", "wsl", "macos"):
        print("⚠️  不支持的操作系统，无法自动安装")
        return False

    if os_type in ("linux", "wsl"):
        # 更新包列表
        print("📦 更新 APT 包列表...")
        result = subprocess.run(
            ["sudo", "apt-get", "update"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"⚠️  APT 更新失败: {result.stderr}")
            return False

    statuses = check_all_deps()
    missing = [s for s in statuses if not s.installed]

    if not missing:
        print("✅ 所有系统依赖已就绪，无需安装")
        return True

    print(f"\n📥 开始安装 {len(missing)} 个缺失的系统依赖...")

    success_count = 0
    for status in missing:
        print(f"\n📦 安装 {status.dep.display_name}...")
        print(f"   命令: {status.install_command}")

        if install_package(status.dep.apt_package, os_type):
            print(f"   ✅ {status.dep.display_name} 安装完成")
            success_count += 1
        else:
            print(f"   ❌ {status.dep.display_name} 安装失败")
            print(f"   请手动运行: {status.install_command}")

    print("\n" + "=" * 70)
    print(f"安装结果: {success_count}/{len(missing)}")

    if success_count == len(missing):
        print("\n🎉 所有系统依赖安装完成！")
        return True
    else:
        print("\n⚠️  部分依赖安装失败，请手动安装")
        return False


# ============================================================
# 主函数
# ============================================================

def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="One-Research 系统依赖检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            示例:
              %(prog)s                    # 检查并显示状态
              %(prog)s --check            # 仅检查，不安装
              %(prog)s --install          # 自动安装缺失依赖

            注意:
              自动安装需要 sudo 权限（Linux）或 Homebrew（macOS）
        """),
    )

    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="仅检查状态，不执行安装",
    )

    parser.add_argument(
        "--install", "-i",
        action="store_true",
        help="自动安装缺失的系统依赖",
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，仅返回退出码",
    )

    return parser.parse_args()


def main() -> int:
    """主函数"""
    args = parse_args()

    if args.install:
        if install_missing_deps():
            return 0
        else:
            return 1
    else:
        statuses = check_all_deps()
        if not args.quiet:
            print_status_report(statuses)

        all_installed = all(s.installed for s in statuses)
        return 0 if all_installed else 1


if __name__ == "__main__":
    raise SystemExit(main())
