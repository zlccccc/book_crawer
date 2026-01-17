#!/usr/bin/env python3
"""代码检查脚本 - Python版本"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*50}")
    print(f"{description}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    """主函数"""
    # 切换到项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)

    print("=" * 50)
    print("运行代码检查")
    print("=" * 50)

    results = []

    # 1. Ruff 代码风格检查
    results.append(run_command(
        "ruff check src/ tests/",
        "1. Ruff 代码风格检查"
    ))

    # 2. Ruff 自动修复
    results.append(run_command(
        "ruff check --fix src/ tests/",
        "2. Ruff 自动修复"
    ))

    # 3. Mypy 类型检查
    results.append(run_command(
        "mypy src/",
        "3. Mypy 类型检查"
    ))

    # 4. 运行测试
    results.append(run_command(
        "python scripts/run_tests.py",
        "4. 运行测试"
    ))

    print("\n" + "=" * 50)
    print("代码检查完成")
    print("=" * 50)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
