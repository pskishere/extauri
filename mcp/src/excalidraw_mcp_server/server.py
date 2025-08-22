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
                "name": "draw_with_brush",
                "description": "Draw with brush tool (create freedraw element)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "points": {
                            "type": "array",
                            "description": "Array of path points for the brush stroke",
                            "items": {
                                "type": "array",
                                "description": "Point coordinates [x, y] or [x, y, pressure]",
                                "minItems": 2,
                                "maxItems": 3,
                                "items": {
                                    "type": "number"
                                }
                            },
                            "minItems": 2
                        },
                        "strokeColor": {
                            "type": "string",
                            "description": "Stroke color (hex format)",
                            "default": "#000000"
                        },
                        "strokeWidth": {
                            "type": "number",
                            "description": "Stroke width",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 2
                        },
                        "opacity": {
                            "type": "number",
                            "description": "Opacity percentage",
                            "minimum": 0,
                            "maximum": 100,
                            "default": 100
                        },
                        "roughness": {
                            "type": "number",
                            "description": "Roughness level",
                            "minimum": 0,
                            "maximum": 2,
                            "default": 1
                        }
                    },
                    "required": ["points"]
                }
            },
            {
                "name": "create_element",
                "description": "Create a new canvas element (supports multiple types)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "elementType": {
                            "type": "string",
                            "enum": ["rectangle", "ellipse", "arrow", "line", "text", "freedraw"],
                            "description": "Type of element to create"
                        },
                        "x": {
                            "type": "number",
                            "description": "X coordinate"
                        },
                        "y": {
                            "type": "number",
                            "description": "Y coordinate"
                        },
                        "width": {
                            "type": "number",
                            "description": "Element width",
                            "minimum": 1
                        },
                        "height": {
                            "type": "number",
                            "description": "Element height",
                            "minimum": 1
                        },
                        "strokeColor": {
                            "type": "string",
                            "description": "Stroke color (hex format)",
                            "default": "#1e1e1e"
                        },
                        "backgroundColor": {
                            "type": "string",
                            "description": "Background color (hex format)",
                            "default": "transparent"
                        },
                        "strokeWidth": {
                            "type": "number",
                            "description": "Stroke width",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 2
                        },
                        "text": {
                            "type": "string",
                            "description": "Text content (for text elements)"
                        },
                        "points": {
                            "type": "array",
                            "description": "Points array (for line/arrow/freedraw elements)",
                            "items": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 2,
                                "maxItems": 3
                            }
                        }
                    },
                    "required": ["elementType", "x", "y"]
                }
            },
            {
                "name": "get_element_by_id",
                "description": "Get specific element by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "element_id": {
                            "type": "string",
                            "description": "Element ID to retrieve",
                            "minLength": 1
                        }
                    },
                    "required": ["element_id"]
                }
            },
            {
                "name": "update_app_state",
                "description": "Update application state (theme, zoom, etc.)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "stateUpdates": {
                            "type": "object",
                            "description": "State fields to update",
                            "properties": {
                                "theme": {
                                    "type": "string",
                                    "enum": ["light", "dark"]
                                },
                                "zoom": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "number", "minimum": 0.1, "maximum": 10}
                                    }
                                },
                                "scrollX": {"type": "number"},
                                "scrollY": {"type": "number"},
                                "viewBackgroundColor": {"type": "string"},
                                "gridModeEnabled": {"type": "boolean"},
                                "zenModeEnabled": {"type": "boolean"}
                            }
                        }
                    },
                    "required": ["stateUpdates"]
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

        # Draw with brush (create freedraw element)
        elif name == "draw_with_brush":
            points = args.get("points")
            stroke_color = args.get("strokeColor", "#1e1e1e")
            stroke_width = args.get("strokeWidth", 2)
            opacity = args.get("opacity", 100)
            roughness = args.get("roughness", 1)

            if not points or len(points) < 2:
                return "❌ Missing or insufficient points for brush stroke (minimum 2 points required)"

            try:
                import time
                import random
                import string

                # Generate Excalidraw-style element ID
                def generate_excalidraw_id():
                    chars = string.ascii_letters + string.digits + '-_'
                    return ''.join(random.choices(chars, k=20))

                # Generate element index
                def generate_index():
                    return f"a{int(time.time() * 1000) % 1000000}"

                element_id = generate_excalidraw_id()

                # Calculate bounds
                min_x = min(point[0] for point in points)
                min_y = min(point[1] for point in points)
                max_x = max(point[0] for point in points)
                max_y = max(point[1] for point in points)
                width = max_x - min_x
                height = max_y - min_y

                # Convert to relative coordinates
                relative_points = [[point[0] - min_x, point[1] - min_y] for point in points]

                # Create complete freedraw element matching Excalidraw structure
                freedraw_element = {
                    "id": element_id,
                    "type": "freedraw",
                    "x": min_x,
                    "y": min_y,
                    "width": width,
                    "height": height,
                    "angle": 0,
                    "strokeColor": stroke_color,
                    "backgroundColor": "transparent",
                    "fillStyle": "solid",
                    "strokeWidth": stroke_width,
                    "strokeStyle": "solid",
                    "roughness": roughness,
                    "opacity": opacity,
                    "groupIds": [],
                    "frameId": None,
                    "index": generate_index(),
                    "roundness": None,
                    "seed": random.randint(1, 2147483647),
                    "version": 1,
                    "versionNonce": random.randint(1, 2147483647),
                    "isDeleted": False,
                    "boundElements": None,
                    "updated": int(time.time() * 1000),
                    "link": None,
                    "locked": False,
                    "points": relative_points,
                    "pressures": [],
                    "simulatePressure": True,
                    "lastCommittedPoint": relative_points[-1] if relative_points else None
                }

                # Get current canvas data
                canvas_response = await self.client.get(f"{BASE_URL}/canvas")
                if canvas_response.status_code != 200:
                    return f"❌ Failed to get current canvas data: HTTP {canvas_response.status_code}"

                canvas_data = canvas_response.json()
                current_canvas = canvas_data.get("canvas", {})
                current_elements = current_canvas.get("elements", [])

                # Ensure current_elements is a list (handle None case)
                if current_elements is None:
                    current_elements = []

                # Add new freedraw element to existing elements
                updated_elements = current_elements + [freedraw_element]

                # Update canvas with new element
                payload = {
                    "elements": updated_elements,
                    "appState": current_canvas.get("appState", {}),
                    "files": current_canvas.get("files", {})
                }

                response = await self.client.put(f"{BASE_URL}/canvas", json=payload)
                if response.status_code == 200:
                    return f"✅ Brush stroke created successfully\nElement ID: {element_id}\nPoints: {len(points)} points\nColor: {stroke_color}\nWidth: {stroke_width}"
                else:
                    return f"❌ Failed to create brush stroke: HTTP {response.status_code}"

            except Exception as e:
                return f"❌ Failed to create brush stroke: {str(e)}"

        # Create element (generic element creation)
        elif name == "create_element":
            element_type = args.get("elementType")
            x = args.get("x")
            y = args.get("y")
            width = args.get("width", 100)
            height = args.get("height", 100)
            stroke_color = args.get("strokeColor", "#1e1e1e")
            background_color = args.get("backgroundColor", "transparent")
            stroke_width = args.get("strokeWidth", 2)
            text_content = args.get("text", "")
            points = args.get("points", [])

            if not element_type or x is None or y is None:
                return "❌ Missing required parameters: elementType, x, y"

            try:
                import time
                import random
                import string

                # Generate Excalidraw-style element ID
                def generate_excalidraw_id():
                    chars = string.ascii_letters + string.digits + '-_'
                    return ''.join(random.choices(chars, k=20))

                def generate_index():
                    return f"a{int(time.time() * 1000) % 1000000}"

                element_id = generate_excalidraw_id()
                current_time = int(time.time() * 1000)

                # Base element structure
                base_element = {
                    "id": element_id,
                    "type": element_type,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "angle": 0,
                    "strokeColor": stroke_color,
                    "backgroundColor": background_color,
                    "fillStyle": "solid",
                    "strokeWidth": stroke_width,
                    "strokeStyle": "solid",
                    "roughness": 1,
                    "opacity": 100,
                    "groupIds": [],
                    "frameId": None,
                    "index": generate_index(),
                    "roundness": None,
                    "seed": random.randint(1, 2147483647),
                    "version": 1,
                    "versionNonce": random.randint(1, 2147483647),
                    "isDeleted": False,
                    "boundElements": None,
                    "updated": current_time,
                    "link": None,
                    "locked": False
                }

                # Add type-specific properties
                if element_type == "text":
                    base_element.update({
                        "text": text_content,
                        "fontSize": 20,
                        "fontFamily": 1,
                        "textAlign": "left",
                        "verticalAlign": "top",
                        "containerId": None,
                        "originalText": text_content,
                        "lineHeight": 1.25
                    })
                elif element_type in ["line", "arrow"]:
                    if not points or len(points) < 2:
                        return f"❌ {element_type} elements require at least 2 points"
                    base_element.update({
                        "points": points,
                        "lastCommittedPoint": points[-1] if points else None
                    })
                    if element_type == "arrow":
                        base_element.update({
                            "startArrowhead": None,
                            "endArrowhead": "arrow"
                        })
                elif element_type == "freedraw":
                    if not points or len(points) < 2:
                        return "❌ Freedraw elements require at least 2 points"
                    # Convert to relative coordinates
                    min_x = min(point[0] for point in points)
                    min_y = min(point[1] for point in points)
                    relative_points = [[point[0] - min_x, point[1] - min_y] for point in points]
                    base_element.update({
                        "x": min_x,
                        "y": min_y,
                        "width": max(point[0] for point in points) - min_x,
                        "height": max(point[1] for point in points) - min_y,
                        "points": relative_points,
                        "pressures": [],
                        "simulatePressure": True,
                        "lastCommittedPoint": relative_points[-1] if relative_points else None
                    })

                # Get current canvas and add element
                canvas_response = await self.client.get(f"{BASE_URL}/canvas")
                if canvas_response.status_code != 200:
                    return f"❌ Failed to get current canvas data: HTTP {canvas_response.status_code}"

                canvas_data = canvas_response.json()
                current_canvas = canvas_data.get("canvas", {})
                current_elements = current_canvas.get("elements", []) or []
                updated_elements = current_elements + [base_element]

                # Update canvas
                payload = {
                    "elements": updated_elements,
                    "appState": current_canvas.get("appState", {}),
                    "files": current_canvas.get("files", {})
                }

                response = await self.client.put(f"{BASE_URL}/canvas", json=payload)
                if response.status_code == 200:
                    return f"✅ {element_type.capitalize()} element created successfully\nElement ID: {element_id}\nPosition: ({x}, {y})\nSize: {width}x{height}"
                else:
                    return f"❌ Failed to create {element_type} element: HTTP {response.status_code}"

            except Exception as e:
                return f"❌ Failed to create {element_type} element: {str(e)}"

        # Get element by ID
        elif name == "get_element_by_id":
            element_id = args.get("element_id")
            if not element_id:
                return "❌ Missing element_id parameter"

            try:
                canvas_response = await self.client.get(f"{BASE_URL}/canvas")
                if canvas_response.status_code != 200:
                    return f"❌ Failed to get canvas data: HTTP {canvas_response.status_code}"

                canvas_data = canvas_response.json()
                elements = canvas_data.get("canvas", {}).get("elements", [])

                # Find element by ID
                target_element = None
                for element in elements:
                    if element.get("id") == element_id:
                        target_element = element
                        break

                if target_element:
                    import json
                    return f"✅ Element found\nID: {element_id}\nType: {target_element.get('type')}\nPosition: ({target_element.get('x')}, {target_element.get('y')})\nSize: {target_element.get('width')}x{target_element.get('height')}\n\nFull element data:\n{json.dumps(target_element, indent=2)}"
                else:
                    return f"❌ Element with ID '{element_id}' not found"

            except Exception as e:
                return f"❌ Failed to get element: {str(e)}"

        # Update app state
        elif name == "update_app_state":
            state_updates = args.get("stateUpdates")
            if not state_updates:
                return "❌ Missing stateUpdates parameter"

            try:
                # Get current canvas data
                canvas_response = await self.client.get(f"{BASE_URL}/canvas")
                if canvas_response.status_code != 200:
                    return f"❌ Failed to get current canvas data: HTTP {canvas_response.status_code}"

                canvas_data = canvas_response.json()
                current_canvas = canvas_data.get("canvas", {})
                current_app_state = current_canvas.get("appState", {})

                # Merge state updates
                updated_app_state = current_app_state.copy() if current_app_state else {}
                updated_app_state.update(state_updates)

                # Update canvas with new app state
                payload = {
                    "elements": current_canvas.get("elements", []),
                    "appState": updated_app_state,
                    "files": current_canvas.get("files", {})
                }

                response = await self.client.put(f"{BASE_URL}/canvas", json=payload)
                if response.status_code == 200:
                    updated_fields = list(state_updates.keys())
                    return f"✅ App state updated successfully\nUpdated fields: {', '.join(updated_fields)}"
                else:
                    return f"❌ Failed to update app state: HTTP {response.status_code}"

            except Exception as e:
                return f"❌ Failed to update app state: {str(e)}"

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