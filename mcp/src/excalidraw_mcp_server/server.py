#!/usr/bin/env python3
"""
Excalidraw MCP Server implemented entirely according to HTTP interface
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
import httpx

# Configuration
BASE_URL = "http://127.0.0.1:31337"


class ExcalidrawMCPServer:
    """MCP Server implemented entirely according to HTTP interface"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.initialized = False

    def get_capabilities(self):
        """Get server capabilities"""
        return {
            "tools": {}
        }

    def get_server_info(self):
        """Get server information"""
        return {
            "name": "excalidraw-http",
            "version": "1.0.0"
        }




    def get_tools(self):
        """Get tool list - corresponding to simplified canvas operation interface"""
        return [
            {
                "name": "health_check",
                "description": "Check server status (GET /health)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },

            {
                "name": "get_canvas",
                "description": "Get current canvas data (GET /canvas)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "update_canvas",
                "description": "Update canvas data (PUT /canvas)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "elements": {
                            "type": "array",
                            "description": "Array of Excalidraw drawing elements",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "Unique element identifier"},
                                    "type": {"type": "string", "description": "Element type (rectangle, ellipse, arrow, line, text, etc.)"},
                                    "x": {"type": "number", "description": "X coordinate"},
                                    "y": {"type": "number", "description": "Y coordinate"},
                                    "width": {"type": "number", "description": "Element width"},
                                    "height": {"type": "number", "description": "Element height"},
                                    "strokeColor": {"type": "string", "description": "Stroke color"},
                                    "backgroundColor": {"type": "string", "description": "Background color"},
                                    "strokeWidth": {"type": "number", "description": "Stroke width"},
                                    "roughness": {"type": "number", "description": "Roughness level (0-2)"},
                                    "opacity": {"type": "number", "description": "Opacity (0-100)"}
                                },
                                "required": ["id", "type", "x", "y"]
                            },
                            "default": []
                        },
                        "appState": {
                            "type": "object",
                            "description": "Application state including viewport and UI settings",
                            "properties": {
                                "viewBackgroundColor": {"type": "string", "description": "Canvas background color"},
                                "gridSize": {"type": "number", "description": "Grid size"},
                                "scrollX": {"type": "number", "description": "Horizontal scroll position"},
                                "scrollY": {"type": "number", "description": "Vertical scroll position"},
                                "zoom": {"type": "object", "description": "Zoom configuration"}
                            },
                            "default": {}
                        },
                        "files": {
                            "type": "object",
                            "description": "File attachments (images, etc.) keyed by file ID",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "mimeType": {"type": "string", "description": "MIME type of the file"},
                                    "id": {"type": "string", "description": "File identifier"},
                                    "dataURL": {"type": "string", "description": "Base64 encoded file data"}
                                }
                            },
                            "default": {}
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "clear_canvas",
                "description": "Clear canvas (POST /canvas/clear)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "export_canvas",
                "description": "Export canvas as toDataURL format (GET /canvas/export)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "Export format: toDataURL",
                            "enum": ["toDataURL"],
                            "default": "toDataURL"
                        },
                        "width": {
                            "type": "integer",
                            "description": "Export width in pixels",
                            "minimum": 1,
                            "maximum": 4096,
                            "default": 1024
                        },
                        "height": {
                            "type": "integer",
                            "description": "Export height in pixels",
                            "minimum": 1,
                            "maximum": 4096,
                            "default": 768
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "remove_element",
                "description": "Remove element by specified ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "element_id": {
                            "type": "string",
                            "description": "Unique identifier of the element to remove",
                            "pattern": "^[a-zA-Z0-9_-]+$",
                            "minLength": 1,
                            "maxLength": 100
                        }
                    },
                    "required": ["element_id"]
                }
            },
            {
                "name": "update_element",
                "description": "Update element by specified ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "element_id": {
                            "type": "string",
                            "description": "Unique identifier of the element to update",
                            "pattern": "^[a-zA-Z0-9_-]+$",
                            "minLength": 1,
                            "maxLength": 100
                        },
                        "element_data": {
                            "type": "object",
                            "description": "Updated element properties",
                            "properties": {
                                "type": {"type": "string", "description": "Element type (rectangle, ellipse, arrow, line, text, etc.)"},
                                "x": {"type": "number", "description": "X coordinate"},
                                "y": {"type": "number", "description": "Y coordinate"},
                                "width": {"type": "number", "description": "Element width"},
                                "height": {"type": "number", "description": "Element height"},
                                "strokeColor": {"type": "string", "description": "Stroke color"},
                                "backgroundColor": {"type": "string", "description": "Background color"},
                                "strokeWidth": {"type": "number", "description": "Stroke width", "minimum": 0},
                                "roughness": {"type": "number", "description": "Roughness level", "minimum": 0, "maximum": 2},
                                "opacity": {"type": "number", "description": "Opacity percentage", "minimum": 0, "maximum": 100}
                            },
                            "additionalProperties": True
                        }
                    },
                    "required": ["element_id", "element_data"]
                }
            }
        ]

    async def handle_request(self, request: dict) -> dict:
        """Handle request"""
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
                        "message": f"Tool execution failed: {str(e)}"
                    }
                }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                }
            }

    async def call_tool(self, name: str, args: dict) -> str:
        """Execute tool - corresponding to simplified canvas operation interface"""

        # GET /health
        if name == "health_check":
            try:
                response = await self.client.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    return f"✅ Server is healthy: {response.text}"
                else:
                    return f"❌ Server error: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ Connection failed: {str(e)}"



        # GET /canvas
        elif name == "get_canvas":
            try:
                response = await self.client.get(f"{BASE_URL}/canvas")
                if response.status_code == 200:
                    data = response.json()
                    canvas = data.get("canvas", {})
                    elements_count = len(canvas.get("elements", []) or [])
                    return f"✅ Canvas data\nElements count: {elements_count}\nUpdated at: {canvas.get('updated_at', 'unknown')}"
                else:
                    return f"❌ Failed to get canvas data: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ Failed to get canvas data: {str(e)}"

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
                    return "✅ Canvas updated successfully"
                else:
                    return f"❌ Failed to update canvas: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ Failed to update canvas: {str(e)}"

        # POST /canvas/clear
        elif name == "clear_canvas":
            try:
                response = await self.client.post(f"{BASE_URL}/canvas/clear")
                if response.status_code == 200:
                    return "✅ Canvas cleared successfully"
                else:
                    return f"❌ Failed to clear canvas: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ Failed to clear canvas: {str(e)}"

        # GET /canvas/export
        elif name == "export_canvas":
            format_type = args.get("format", "toDataURL")
            width = args.get("width", 800)
            height = args.get("height", 600)

            # Only support toDataURL format
            if format_type != "toDataURL":
                return f"❌ Unsupported format: {format_type}, only toDataURL format is supported"

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
                            return f"✅ toDataURL export successful\nSize: {width}x{height}\nData URL length: {len(data_url)} characters\n\nData URL preview:\n{data_url[:100]}{'...' if len(data_url) > 100 else ''}\n\nFull response:\n{json_content}"
                        except Exception as e:
                            return f"✅ toDataURL export successful\nContent length: {len(json_content)} characters\n\nPreview:\n{json_content[:500]}{'...' if len(json_content) > 500 else ''}"
                    else:
                        return f"❌ Unexpected content type: {content_type}"
                else:
                    return f"❌ Export failed: HTTP {response.status_code}"
            except Exception as e:
                return f"❌ Export request failed: {str(e)}"

        # Remove element
        elif name == "remove_element":
            element_id = args.get("element_id")
            if not element_id:
                return "❌ Missing element_id parameter"

            try:
                # Call backend API to remove element
                response = await self.client.delete(f"{BASE_URL}/canvas/element/{element_id}")

                if response.status_code == 404:
                    return f"❌ Element with ID '{element_id}' not found"
                elif response.status_code != 200:
                    return f"❌ Failed to remove element: HTTP {response.status_code}"

                result = response.json()
                return f"✅ {result.get('message', 'Element removed successfully')}"

            except Exception as e:
                return f"❌ Failed to remove element: {str(e)}"

        # Update element
        elif name == "update_element":
            element_id = args.get("element_id")
            element_data = args.get("element_data")

            if not element_id:
                return "❌ Missing element_id parameter"
            if not element_data:
                return "❌ Missing element_data parameter"

            try:
                # Call backend API to update element
                payload = {"element": element_data}
                response = await self.client.put(f"{BASE_URL}/canvas/element/{element_id}", json=payload)

                if response.status_code == 404:
                    return f"❌ Element with ID '{element_id}' not found"
                elif response.status_code != 200:
                    return f"❌ Failed to update element: HTTP {response.status_code}"

                result = response.json()
                return f"✅ {result.get('message', 'Element updated successfully')}"

            except Exception as e:
                return f"❌ Failed to update element: {str(e)}"

        else:
            raise Exception(f"Unknown tool: {name}")



    async def run(self):
        """Run server"""
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break

                request_id = None
                try:
                    request = json.loads(line.strip())
                    request_id = request.get("id")
                    response = await self.handle_request(request)
                    print(json.dumps(response, ensure_ascii=False), flush=True)
                except json.JSONDecodeError:
                    # Try to extract id from malformed JSON if possible
                    try:
                        import re
                        id_match = re.search(r'"id"\s*:\s*(\d+|"[^"]*")', line)
                        if id_match:
                            id_str = id_match.group(1)
                            request_id = int(id_str) if id_str.isdigit() else id_str.strip('"')
                    except:
                        pass
                    
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32700, "message": "Parse error"}
                    }
                    print(json.dumps(error_response, ensure_ascii=False), flush=True)
                except Exception as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                    }
                    print(json.dumps(error_response, ensure_ascii=False), flush=True)

        finally:
            await self.client.aclose()


async def main():
    """Main entry point"""
    server = ExcalidrawMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())