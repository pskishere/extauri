# Excalidraw MCP Server

一个基于 Model Context Protocol (MCP) 的 Excalidraw 画布操作服务器，允许 AI 模型直接与 Excalidraw 画布进行交互。

## 功能特性

- 🎨 **画布操作**: 获取、更新、清空画布内容，完全兼容 Excalidraw 格式
- 🖌️ **增强画笔绘制**: 创建精确的自由绘制元素，完整的 Excalidraw 数据结构
- 📤 **导出功能**: 支持 SVG、PNG、JSON、Data URL 等多种格式导出
- 🔧 **多元素管理**: 创建、删除、更新、查询画布元素（文本、矩形、椭圆、箭头、线条、自由绘制）
- 🔄 **实时同步**: 与 Excalidraw 前端实时数据同步
- 🌐 **HTTP API**: 完整的 RESTful API 接口
- 🎯 **元素查询**: 通过 ID 查找和检索特定元素
- 📐 **坐标系统**: 正确处理绝对和相对坐标系统
- ⚙️ **应用状态管理**: 全面控制 Excalidraw 应用状态和 UI 设置
- 🔗 **数据结构兼容**: 与真实 Excalidraw 数据结构完全兼容

## 安装

### 从源码安装

```bash
cd mcp
pip install -e .
```

### 使用 pip 安装

```bash
pip install excalidraw-mcp-server
```

## MCP 客户端配置

在你的 MCP 客户端配置文件中添加以下配置：

```json
{
  "mcpServers": {
    "excalidraw": {
      "command": "python3",
      "args": [
        "-m",
        "excalidraw_mcp_server"
      ],
      "env": {
        "EXCALIDRAW_SERVER_URL": "http://localhost:31337"
      }
    }
  }
}
```

### 配置说明

- **command**: 使用 `python3` 执行 Python 模块
- **args**: 指定运行 `excalidraw_mcp_server` 模块
- **env.EXCALIDRAW_SERVER_URL**: Excalidraw 后端服务器地址（默认: `http://localhost:31337`）

## 使用方法

### 1. 启动 Excalidraw 应用

首先启动 Tauri 应用（包含 Excalidraw 前端和后端服务器）：

```bash
# 在项目根目录
npm run tauri dev
```

### 2. 启动 MCP 服务器

MCP 服务器会自动连接到运行在 `localhost:31337` 的 Excalidraw 后端。

### 3. 可用工具

#### 基础操作
- `health_check` - 检查服务器状态
- `get_canvas` - 获取当前画布数据
- `update_canvas` - 更新画布内容（支持完整的 Excalidraw 数据结构）
- `clear_canvas` - 清空画布
- `update_app_state` - 更新应用状态和 UI 设置

#### 绘制工具
- `draw_with_brush` - 使用画笔工具绘制（增强版，生成完整的 Excalidraw 元素）
  ```json
  {
    "points": [[423, 223], [422, 224], [418, 226]],
    "strokeColor": "#1e1e1e",
    "strokeWidth": 2,
    "opacity": 100,
    "roughness": 1
  }
  ```

#### 元素管理
- `create_element` - 创建新元素（支持文本、矩形、椭圆、箭头、线条、自由绘制）
- `get_element_by_id` - 通过 ID 获取特定元素
- `remove_element` - 删除指定元素
- `update_element` - 更新指定元素

#### 导出功能
- `export_canvas` - 导出画布
  ```json
  {
    "format": "toDataURL",
    "width": 1024,
    "height": 768
  }
  ```

## API 端点

MCP 服务器通过以下 HTTP API 与 Excalidraw 后端通信：

- `GET /health` - 健康检查
- `GET /canvas` - 获取画布数据
- `PUT /canvas` - 更新画布数据
- `POST /canvas/clear` - 清空画布
- `GET /canvas/export` - 导出画布
- `DELETE /canvas/element/:id` - 删除元素
- `PUT /canvas/element/:id` - 更新元素

## 数据结构兼容性

本 MCP 服务器完全兼容真实的 Excalidraw 数据结构。以下是一个真实的 freedraw 元素示例：

```json
{
  "elements": [{
    "id": "or-p-XGqJ5rg6RcTvkdHa",
    "type": "freedraw",
    "x": 423,
    "y": 223,
    "width": 189,
    "height": 134,
    "angle": 0,
    "strokeColor": "#1e1e1e",
    "backgroundColor": "transparent",
    "fillStyle": "solid",
    "strokeWidth": 2,
    "strokeStyle": "solid",
    "roughness": 1,
    "opacity": 100,
    "groupIds": [],
    "frameId": null,
    "index": "a0",
    "roundness": null,
    "seed": 1392042132,
    "version": 40,
    "versionNonce": 784354964,
    "isDeleted": false,
    "boundElements": null,
    "updated": 1755841866070,
    "link": null,
    "locked": false,
    "points": [[0,0], [-1,1], [-5,3], ...],
    "pressures": [],
    "simulatePressure": true,
    "lastCommittedPoint": [41,-23]
  }],
  "appState": {
    "theme": "light",
    "zoom": {"value": 1},
    "viewBackgroundColor": "#ffffff",
    "gridModeEnabled": false,
    "currentItemStrokeColor": "#1e1e1e",
    "currentItemStrokeWidth": 2,
    ...
  },
  "files": {},
  "timestamp": "2025-08-22T05:51:06.875Z"
}
```

### 关键特性

- **完整元素支持**: 支持所有 Excalidraw 元素类型和属性
- **坐标系统**: 正确处理绝对坐标和相对坐标
- **ID 生成**: 生成符合 Excalidraw 标准的元素 ID
- **版本控制**: 支持元素版本和版本随机数
- **应用状态**: 完整的应用状态管理和同步

## 测试

### 运行测试脚本

```bash
# 测试画笔功能
python test_brush.py

# 测试 MCP 工具定义
python test_mcp_brush.py

# 增强功能测试
python test_enhanced_features.py

# 数据结构兼容性演示
python demo_user_data_structure.py
```

### 手动测试

```bash
# 检查服务器状态
curl http://localhost:31337/health

# 获取画布数据
curl http://localhost:31337/canvas

# 清空画布
curl -X POST http://localhost:31337/canvas/clear
```

## 开发

### 项目结构

```
mcp/
├── src/
│   └── excalidraw_mcp_server/
│       ├── __init__.py
│       └── server.py          # 主要 MCP 服务器实现
├── pyproject.toml             # 项目配置
├── requirements.txt           # 依赖列表
└── README.md                  # 本文档
```

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

### 依赖

- `httpx` - HTTP 客户端库
- `typing-extensions` - 类型注解扩展

## 故障排除

### 常见问题

1. **连接失败**: 确保 Excalidraw 后端服务器正在运行（端口 31337）
2. **权限错误**: 检查 Python 环境和模块安装
3. **端口冲突**: 修改 `EXCALIDRAW_SERVER_URL` 环境变量

### 调试

启用详细日志：

```bash
EXCALIDRAW_DEBUG=1 python -m excalidraw_mcp_server
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！