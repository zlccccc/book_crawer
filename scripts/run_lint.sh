#!/bin/bash
# 代码检查脚本

set -e

echo "========================================="
echo "运行代码检查"
echo "========================================="

# 1. 运行 ruff 代码风格检查
echo ""
echo "1. Ruff 代码风格检查..."
ruff check src/ tests/ || true

# 2. 运行 ruff 自动修复
echo ""
echo "2. Ruff 自动修复..."
ruff check --fix src/ tests/ || true

# 3. 运行 mypy 类型检查
echo ""
echo "3. Mypy 类型检查..."
mypy src/ || true

# 4. 运行测试
echo ""
echo "4. 运行测试..."
python run_tests.py

echo ""
echo "========================================="
echo "代码检查完成"
echo "========================================="
