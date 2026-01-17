#!/usr/bin/env python3
"""运行所有测试"""

import sys
import subprocess
import os


def main():
    """运行所有测试文件"""
    # 获取项目根目录（scripts的父目录）
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)

    print("=" * 60)
    print("运行单元测试...")
    print("=" * 60)
    result1 = subprocess.run([sys.executable, "tests/test_crawler.py"]).returncode

    print("\n" + "=" * 60)
    print("运行集成测试...")
    print("=" * 60)
    result2 = subprocess.run([sys.executable, "tests/test_integration.py"]).returncode

    if result1 == 0 and result2 == 0:
        print("\n" + "=" * 60)
        print("所有测试通过!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("有测试失败!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
