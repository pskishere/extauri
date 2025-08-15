#!/usr/bin/env python3
"""
完全按照 HTTP 接口实现的 Excalidraw MCP 服务器
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
import httpx

# Configuration
BASE_URL = "http://127.0.0.1:31337"


class ExcalidrawMCPServer:
    """完全按照 HTTP 接口实现的 MCP 服务器"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.initialized = False

    def get_capabilities(self):
        """获取服务器能力"""
        return {
            "tools": {}
        }

    def get_server_info(self):
        """获取服务器信息"""
        return {
            "name": "excalidraw-http",
            "version": "1.0.0"
        }




    def get_tools(self):
        """获取工具列表 - 对应简化的画布操作接口"""
        return [
            {
                "name": "health_check",
                "description": "检查服务器状态 (GET /health)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },

            {
                "name": "get_canvas",
                "description": "获取当前画布数据 (GET /canvas)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "update_canvas",
                "description": "更新画布数据 (PUT /canvas)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "elements": {
                            "type": "array",
                            "description": "Excalidraw 元素数组，每个元素包含完整的绘图信息",
                            "items": {
                                "type": "object",
                                "description": "Excalidraw 元素对象",
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "元素唯一标识符，如 'element_123456'"
                                    },
                                    "type": {
                                        "type": "string",
                                        "enum": ["rectangle", "ellipse", "diamond", "arrow", "line", "freedraw", "text", "image"],
                                        "description": "元素类型：rectangle(矩形), ellipse(椭圆), diamond(菱形), arrow(箭头), line(直线), freedraw(自由绘制), text(文本), image(图片)"
                                    },
                                    "x": {
                                        "type": "number",
                                        "description": "元素左上角X坐标（像素）"
                                    },
                                    "y": {
                                        "type": "number",
                                        "description": "元素左上角Y坐标（像素）"
                                    },
                                    "width": {
                                        "type": "number",
                                        "description": "元素宽度（像素）"
                                    },
                                    "height": {
                                        "type": "number",
                                        "description": "元素高度（像素）"
                                    },
                                    "angle": {
                                        "type": "number",
                                        "default": 0,
                                        "description": "元素旋转角度（弧度）"
                                    },
                                    "strokeColor": {
                                        "type": "string",
                                        "default": "#000000",
                                        "description": "边框颜色，十六进制格式如 '#FF0000'"
                                    },
                                    "backgroundColor": {
                                        "type": "string",
                                        "default": "transparent",
                                        "description": "填充颜色，十六进制格式如 '#FF0000' 或 'transparent'"
                                    },
                                    "fillStyle": {
                                        "type": "string",
                                        "enum": ["hachure", "cross-hatch", "solid"],
                                        "default": "hachure",
                                        "description": "填充样式：hachure(斜线), cross-hatch(交叉线), solid(实心)"
                                    },
                                    "strokeWidth": {
                                        "type": "number",
                                        "default": 1,
                                        "description": "边框宽度（像素）"
                                    },
                                    "strokeStyle": {
                                        "type": "string",
                                        "enum": ["solid", "dashed", "dotted"],
                                        "default": "solid",
                                        "description": "边框样式：solid(实线), dashed(虚线), dotted(点线)"
                                    },
                                    "roughness": {
                                        "type": "number",
                                        "default": 1,
                                        "minimum": 0,
                                        "maximum": 3,
                                        "description": "粗糙度，0为完全平滑，3为最粗糙"
                                    },
                                    "opacity": {
                                        "type": "number",
                                        "default": 100,
                                        "minimum": 0,
                                        "maximum": 100,
                                        "description": "透明度，0-100"
                                    },
                                    "text": {
                                        "type": "string",
                                        "description": "文本内容（仅text类型元素需要）"
                                    },
                                    "fontSize": {
                                        "type": "number",
                                        "default": 20,
                                        "description": "字体大小（仅text类型元素）"
                                    },
                                    "fontFamily": {
                                        "type": "number",
                                        "default": 1,
                                        "description": "字体族：1(Virgil), 2(Helvetica), 3(Cascadia)"
                                    },
                                    "textAlign": {
                                        "type": "string",
                                        "enum": ["left", "center", "right"],
                                        "default": "left",
                                        "description": "文本对齐方式"
                                    },
                                    "verticalAlign": {
                                        "type": "string",
                                        "enum": ["top", "middle", "bottom"],
                                        "default": "top",
                                        "description": "垂直对齐方式"
                                    },
                                    "points": {
                                        "type": "array",
                                        "description": "路径点数组（用于line, arrow, freedraw类型），格式为[[x1,y1], [x2,y2], ...]",
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "number"
                                            },
                                            "minItems": 2,
                                            "maxItems": 2
                                        }
                                    },
                                    "seed": {
                                        "type": "number",
                                        "description": "随机种子，用于生成一致的手绘效果"
                                    },
                                    "versionNonce": {
                                        "type": "number",
                                        "description": "版本随机数，用于协作同步"
                                    },
                                    "isDeleted": {
                                        "type": "boolean",
                                        "default": false,
                                        "description": "是否已删除"
                                    },
                                    "groupIds": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        },
                                        "default": [],
                                        "description": "所属组ID数组"
                                    },
                                    "frameId": {
                                        "type": ["string", "null"],
                                        "default": null,
                                        "description": "所属框架ID"
                                    },
                                    "roundness": {
                                        "type": ["object", "null"],
                                        "description": "圆角设置，格式为 {type: 'round', value: 数值}"
                                    },
                                    "boundElements": {
                                        "type": ["array", "null"],
                                        "description": "绑定的元素列表"
                                    },
                                    "updated": {
                                        "type": "number",
                                        "description": "最后更新时间戳"
                                    },
                                    "link": {
                                        "type": ["string", "null"],
                                        "description": "关联链接"
                                    },
                                    "locked": {
                                        "type": "boolean",
                                        "default": false,
                                        "description": "是否锁定"
                                    }
                                },
                                "required": ["id", "type", "x", "y", "width", "height"]
                            }
                        },
                        "appState": {
                            "type": "object",
                            "description": "应用状态配置",
                            "properties": {
                                "viewBackgroundColor": {
                                    "type": "string",
                                    "default": "#ffffff",
                                    "description": "画布背景色"
                                },
                                "currentItemStrokeColor": {
                                    "type": "string",
                                    "description": "当前笔触颜色"
                                },
                                "currentItemBackgroundColor": {
                                    "type": "string",
                                    "description": "当前填充颜色"
                                },
                                "currentItemFillStyle": {
                                    "type": "string",
                                    "description": "当前填充样式"
                                },
                                "currentItemStrokeWidth": {
                                    "type": "number",
                                    "description": "当前笔触宽度"
                                },
                                "currentItemRoughness": {
                                    "type": "number",
                                    "description": "当前粗糙度"
                                },
                                "currentItemOpacity": {
                                    "type": "number",
                                    "description": "当前透明度"
                                },
                                "scrollX": {
                                    "type": "number",
                                    "description": "水平滚动位置"
                                },
                                "scrollY": {
                                    "type": "number",
                                    "description": "垂直滚动位置"
                                },
                                "zoom": {
                                    "type": "object",
                                    "description": "缩放设置",
                                    "properties": {
                                        "value": {
                                            "type": "number",
                                            "description": "缩放值"
                                        }
                                    }
                                }
                            }
                        },
                        "files": {
                            "type": "object",
                            "description": "文件附件映射，键为文件ID，值为文件数据"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "clear_canvas",
                "description": "清除画布 (POST /canvas/clear)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "export_canvas",
                "description": "导出画布为toDataURL格式 (GET /canvas/export)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "导出格式: toDataURL",
                            "enum": ["toDataURL"]
                        },
                        "width": {
                            "type": "integer",
                            "description": "导出宽度（像素）",
                            "minimum": 1,
                            "maximum": 4096
                        },
                        "height": {
                            "type": "integer",
                            "description": "导出高度（像素）",
                            "minimum": 1,
                            "maximum": 4096
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "remove_element",
                "description": "移除指定ID的元素",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "element_id": {
                            "type": "string",
                            "description": "要移除的元素ID"
                        }
                    },
                    "required": ["element_id"]
                }
            },
            {
                "name": "update_element",
                "description": "更新指定ID的元素",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "element_id": {
                            "type": "string",
                            "description": "要更新的元素ID"
                        },
                        "element_data": {
                            "type": "object",
                            "description": "新的元素数据，包含要更新的属性",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["rectangle", "ellipse", "diamond", "arrow", "line", "freedraw", "text", "image"],
                                    "description": "元素类型"
                                },
                                "x": {
                                    "type": "number",
                                    "description": "元素左上角X坐标（像素）"
                                },
                                "y": {
                                    "type": "number",
                                    "description": "元素左上角Y坐标（像素）"
                                },
                                "width": {
                                    "type": "number",
                                    "description": "元素宽度（像素）"
                                },
                                "height": {
                                    "type": "number",
                                    "description": "元素高度（像素）"
                                },
                                "angle": {
                                    "type": "number",
                                    "description": "元素旋转角度（弧度）"
                                },
                                "strokeColor": {
                                    "type": "string",
                                    "description": "边框颜色，十六进制格式如 '#FF0000'"
                                },
                                "backgroundColor": {
                                    "type": "string",
                                    "description": "填充颜色，十六进制格式如 '#FF0000' 或 'transparent'"
                                },
                                "fillStyle": {
                                    "type": "string",
                                    "enum": ["hachure", "cross-hatch", "solid"],
                                    "description": "填充样式：hachure(斜线), cross-hatch(交叉线), solid(实心)"
                                },
                                "strokeWidth": {
                                    "type": "number",
                                    "description": "边框宽度（像素）"
                                },
                                "strokeStyle": {
                                    "type": "string",
                                    "enum": ["solid", "dashed", "dotted"],
                                    "description": "边框样式：solid(实线), dashed(虚线), dotted(点线)"
                                },
                                "roughness": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 3,
                                    "description": "粗糙度，0为完全平滑，3为最粗糙"
                                },
                                "opacity": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100,
                                    "description": "透明度，0-100"
                                },
                                "text": {
                                    "type": "string",
                                    "description": "文本内容（仅text类型元素需要）"
                                },
                                "fontSize": {
                                    "type": "number",
                                    "description": "字体大小（仅text类型元素）"
                                },
                                "fontFamily": {
                                    "type": "number",
                                    "description": "字体族：1(Virgil), 2(Helvetica), 3(Cascadia)"
                                },
                                "textAlign": {
                                    "type": "string",
                                    "enum": ["left", "center", "right"],
                                    "description": "文本对齐方式"
                                },
                                "verticalAlign": {
                                    "type": "string",
                                    "enum": ["top", "middle", "bottom"],
                                    "description": "垂直对齐方式"
                                },
                                "points": {
                                    "type": "array",
                                    "description": "路径点数组（用于line, arrow, freedraw类型），格式为[[x1,y1], [x2,y2], ...]",
                                    "items": {
                                        "type": "array",
                                        "items": {
                                            "type": "number"
                                        },
                                        "minItems": 2,
                                        "maxItems": 2
                                    }
                                }
                            }
                        }
                    },
                    "required": ["element_id", "element_data"]
                }
            }
        ]

    async def handle_request(self, request: dict) -> dict:
        """处理请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
            self.initialized = True
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": self.get_capabilities(),
                    "serverInfo": self.get_server_info()
                }
            }

        if not self.initialized:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32002,
                    "message": "Server not initialized"
                }
            }

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": self.get_tools()
                }
            }



        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            try:
                result = await self.call_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"工具执行失败: {str(e)}"
                    }
                }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"未知方法: {method}"
                }
            }

    async def call_tool(self, name: str, args: dict) -> str:
        """执行工具 - 对应简化的画布操作接口"""

        # GET /health
        if name == "health_check":
            try:
                response = await self.client.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    return f"✅ 服务器正常: {response.text}"
                else:
                    return f"❌ 服务器异常: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ 连接失败: {str(e)}"



        # GET /canvas
        elif name == "get_canvas":
            try:
                response = await self.client.get(f"{BASE_URL}/canvas")
                if response.status_code == 200:
                    data = response.json()
                    canvas = data.get("canvas", {})
                    elements_count = len(canvas.get("elements", []) or [])
                    return f"✅ 画布数据\n元素数量: {elements_count}\n更新时间: {canvas.get('updated_at', 'unknown')}"
                else:
                    return f"❌ 获取画布数据失败: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ 获取画布数据失败: {str(e)}"

        # PUT /canvas
        elif name == "update_canvas":
            payload = {
                "elements": args.get("elements"),
                "appState": args.get("appState"),
                "files": args.get("files")
            }
            try:
                response = await self.client.put(f"{BASE_URL}/canvas", json=payload)
                if response.status_code == 200:
                    return "✅ 画布更新成功"
                else:
                    return f"❌ 画布更新失败: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ 画布更新失败: {str(e)}"

        # POST /canvas/clear
        elif name == "clear_canvas":
            try:
                response = await self.client.post(f"{BASE_URL}/canvas/clear")
                if response.status_code == 200:
                    return "✅ 画布清除成功"
                else:
                    return f"❌ 画布清除失败: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ 画布清除失败: {str(e)}"

        # GET /canvas/export
        elif name == "export_canvas":
            format_type = args.get("format", "toDataURL")
            width = args.get("width", 800)
            height = args.get("height", 600)

            # 只支持toDataURL格式
            if format_type != "toDataURL":
                return f"❌ 不支持的格式: {format_type}，仅支持toDataURL格式"

            params = {
                "format": "toDataURL",
                "width": width,
                "height": height
            }

            try:
                response = await self.client.get(f"{BASE_URL}/canvas/export", params=params)
                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")

                    if "application/json" in content_type:
                        # JSON content with toDataURL
                        json_content = response.text
                        try:
                            data = json.loads(json_content)
                            data_url = data.get("dataURL", "")
                            return f"✅ toDataURL导出成功\n尺寸: {width}x{height}\n数据URL长度: {len(data_url)} 字符\n\n数据URL预览:\n{data_url[:100]}{'...' if len(data_url) > 100 else ''}\n\n完整响应:\n{json_content}"
                        except Exception as e:
                            return f"✅ toDataURL导出成功\n内容长度: {len(json_content)} 字符\n\n预览:\n{json_content[:500]}{'...' if len(json_content) > 500 else ''}"
                    else:
                        return f"❌ 意外的内容类型: {content_type}"
                else:
                    return f"❌ 导出失败: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ 导出请求失败: {str(e)}"

        # 移除元素
        elif name == "remove_element":
            element_id = args.get("element_id")
            if not element_id:
                return "❌ 缺少element_id参数"

            try:
                # 调用后端API移除元素
                response = await self.client.delete(f"{BASE_URL}/canvas/element/{element_id}")

                if response.status_code == 404:
                    return f"❌ 未找到ID为 '{element_id}' 的元素"
                elif response.status_code != 200:
                    return f"❌ 移除元素失败: HTTP {response.status_code}"

                result = response.json()
                return f"✅ {result.get('message', '元素移除成功')}"

            except Exception as e:
                return f"❌ 移除元素失败: {str(e)}"

        # 更新元素
        elif name == "update_element":
            element_id = args.get("element_id")
            element_data = args.get("element_data")

            if not element_id:
                return "❌ 缺少element_id参数"
            if not element_data:
                return "❌ 缺少element_data参数"

            try:
                # 调用后端API更新元素
                payload = {"element": element_data}
                response = await self.client.put(f"{BASE_URL}/canvas/element/{element_id}", json=payload)

                if response.status_code == 404:
                    return f"❌ 未找到ID为 '{element_id}' 的元素"
                elif response.status_code != 200:
                    return f"❌ 更新元素失败: HTTP {response.status_code}"

                result = response.json()
                return f"✅ {result.get('message', '元素更新成功')}"

            except Exception as e:
                return f"❌ 更新元素失败: {str(e)}"

        else:
            raise Exception(f"未知工具: {name}")



    async def run(self):
        """运行服务器"""
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break

                try:
                    request = json.loads(line.strip())
                    response = await self.handle_request(request)
                    print(json.dumps(response, ensure_ascii=False), flush=True)
                except json.JSONDecodeError:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"}
                    }
                    print(json.dumps(error_response, ensure_ascii=False), flush=True)
                except Exception as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                    }
                    print(json.dumps(error_response, ensure_ascii=False), flush=True)

        finally:
            await self.client.aclose()


async def main():
    """主入口"""
    server = ExcalidrawMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())