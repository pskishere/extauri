# Excalidraw MCP Server

一个用于 Excalidraw 画布操作的 Model Context Protocol (MCP) 服务器。

## 功能特性

- 🎨 **画布操作**: 支持更新、获取、清除画布内容
- 🔍 **健康检查**: 提供服务器状态检查
- 📤 **导出功能**: 支持 SVG 和 JSON 格式导出
- 🧩 **元素管理**: 支持单个元素的更新和删除
- 🌐 **HTTP 接口**: 完全基于 HTTP API 实现

## 安装

```bash
pip install excalidraw-mcp-server
```

## 使用方法

### 启动服务器

```bash
excalidraw-mcp-server
```

### 配置

默认连接到 `http://127.0.0.1:31337` 的 Excalidraw HTTP 服务器。

### 可用工具

1. **health_check** - 检查服务器状态
2. **get_canvas** - 获取当前画布内容
3. **update_canvas** - 更新画布内容
4. **clear_canvas** - 清除画布
5. **export_canvas** - 导出画布为 SVG 或 JSON
6. **remove_element** - 删除指定元素
7. **update_element** - 更新指定元素

## 开发

### 本地开发

```bash
# 克隆仓库
git clone <repository-url>
cd excalidraw-mcp-server

# 安装依赖
pip install -e .

# 运行服务器
python -m excalidraw_mcp_server.server
```

### 构建包

```bash
pip install build
python -m build
```

## 依赖

- Python >= 3.8
- httpx
- mcp
- requests
- aiohttp
- typing-extensions

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！