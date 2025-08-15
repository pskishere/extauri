#!/bin/bash

# Excalidraw MCP Server 发布脚本

echo "🚀 开始发布 Excalidraw MCP Server..."

# 检查是否已构建
if [ ! -d "dist" ]; then
    echo "❌ 未找到 dist 目录，请先运行构建命令:"
    echo "   python3 -m build"
    exit 1
fi

# 检查构建文件
if [ ! -f "dist/excalidraw_mcp_server-1.0.2.tar.gz" ] || [ ! -f "dist/excalidraw_mcp_server-1.0.2-py3-none-any.whl" ]; then
    echo "❌ 构建文件不完整，请重新构建:"
    echo "   python3 -m build"
    exit 1
fi

echo "✅ 构建文件检查完成"

# 检查包内容
echo "📦 检查包内容..."
python3 -m twine check dist/*

if [ $? -ne 0 ]; then
    echo "❌ 包检查失败，请修复问题后重试"
    exit 1
fi

echo "✅ 包检查通过"

# 询问发布目标
echo ""
echo "请选择发布目标:"
echo "1) TestPyPI (测试环境)"
echo "2) PyPI (正式环境)"
read -p "请输入选择 (1 或 2): " choice

case $choice in
    1)
        echo "🧪 发布到 TestPyPI..."
        python3 -m twine upload --repository testpypi dist/*
        if [ $? -eq 0 ]; then
            echo "✅ 成功发布到 TestPyPI!"
            echo "📋 安装测试命令:"
            echo "   pip install --index-url https://test.pypi.org/simple/ excalidraw-mcp-server"
        fi
        ;;
    2)
        echo "🌍 发布到 PyPI..."
        read -p "⚠️  确认发布到正式 PyPI? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            python3 -m twine upload dist/*
            if [ $? -eq 0 ]; then
                echo "✅ 成功发布到 PyPI!"
                echo "📋 安装命令:"
                echo "   pip install excalidraw-mcp-server"
            fi
        else
            echo "❌ 取消发布"
        fi
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "🎉 发布流程完成!"