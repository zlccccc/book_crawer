#!/usr/bin/env python3
"""运行所有测试"""

import sys
import subprocess


def main():
    """运行所有测试文件"""
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
