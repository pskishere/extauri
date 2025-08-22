use std::net::SocketAddr;
use std::sync::{Arc, Mutex};

use axum::{
    extract::{Path, Query, State},
    http::{header, StatusCode},
    response::{IntoResponse, Response},
    routing::{delete, get, post},
    Json, Router,
};
use base64::{engine::general_purpose, Engine as _};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tauri::Emitter;
use tower_http::cors::CorsLayer;
use tracing::{error, info};

const EVENT_DRAW: &str = "excalidraw_draw";
const DEFAULT_PORT: u16 = 31337;

#[derive(Clone)]
pub struct AppState {
    app: tauri::AppHandle,
    canvas: Arc<Mutex<CanvasData>>,
}

#[derive(Debug, Deserialize, Serialize, Clone, PartialEq)]
pub struct CanvasData {
    pub elements: Option<Value>,
    #[serde(default, rename = "appState")]
    pub app_state: Option<Value>,
    #[serde(default)]
    pub files: Option<Value>,
    pub updated_at: String,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct DrawPayload {
    #[serde(default)]
    pub elements: Option<Value>,
    #[serde(default, rename = "appState")]
    pub app_state: Option<Value>,
    #[serde(default)]
    pub files: Option<Value>,
}

#[derive(Debug, Deserialize)]
pub struct ExportQuery {
    #[serde(default = "default_format")]
    pub format: String,
    #[serde(default = "default_width")]
    pub width: u32,
    #[serde(default = "default_height")]
    pub height: u32,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct UpdateElementPayload {
    pub element: Value,
}

fn default_format() -> String {
    "svg".to_string()
}

fn default_width() -> u32 {
    800
}

fn default_height() -> u32 {
    600
}

pub async fn start_http_server(app: tauri::AppHandle) -> anyhow::Result<()> {
    let canvas = Arc::new(Mutex::new(CanvasData {
        elements: None,
        app_state: None,
        files: None,
        updated_at: chrono::Utc::now().to_rfc3339(),
    }));
    let state = AppState { app, canvas };

    let router = create_router(state);

    let addr = SocketAddr::from(([127, 0, 0, 1], DEFAULT_PORT));
    let listener = tokio::net::TcpListener::bind(addr).await?;
    let server_addr = listener.local_addr()?;

    info!(
        target: "http_server",
        action = "server_start",
        address = %server_addr,
        port = DEFAULT_PORT,
        "HTTP服务器启动成功"
    );

    axum::serve(listener, router).await?;
    Ok(())
}

pub fn create_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/draw", post(draw_canvas))
        .route("/canvas", get(get_canvas).put(update_canvas))
        .route("/canvas/clear", post(clear_canvas))
        .route("/canvas/export", get(export_canvas))
        .route(
            "/canvas/element/:id",
            delete(remove_element).put(update_element),
        )
        .with_state(state)
        .layer(CorsLayer::permissive())
}

// Health check endpoint
async fn health() -> &'static str {
    "ok"
}

// Draw to canvas and emit event
async fn draw_canvas(
    State(state): State<AppState>,
    Json(payload): Json<DrawPayload>,
) -> impl IntoResponse {
    println!("🎨 收到绘制请求: {:?}", payload);

    // Update canvas data
    {
        let mut canvas = state.canvas.lock().unwrap();
        if let Some(elements) = &payload.elements {
            canvas.elements = Some(elements.clone());
        }
        if let Some(app_state) = &payload.app_state {
            canvas.app_state = Some(app_state.clone());
        }
        if let Some(files) = &payload.files {
            canvas.files = Some(files.clone());
        }
        canvas.updated_at = chrono::Utc::now().to_rfc3339();
    }

    // Emit draw event to frontend
    if let Err(err) = state.app.emit(EVENT_DRAW, &payload) {
        eprintln!("❌ 发送事件失败: {err:?}");
        return (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": "Failed to emit draw event"})),
        );
    }

    println!("✅ 已发送绘制事件到前端");
    (StatusCode::OK, Json(json!({"success": true})))
}

// Get current canvas data
async fn get_canvas(State(state): State<AppState>) -> impl IntoResponse {
    let canvas = state.canvas.lock().unwrap();
    (StatusCode::OK, Json(json!({"canvas": canvas.clone()})))
}

// Update canvas data
async fn update_canvas(
    State(state): State<AppState>,
    Json(payload): Json<DrawPayload>,
) -> impl IntoResponse {
    let payload_json =
        serde_json::to_string(&payload).unwrap_or_else(|_| "无法序列化数据".to_string());
    info!(
        target: "canvas_update",
        action = "update_canvas_start",
        canvas_data = %payload_json,
        "接收到画布更新数据"
    );

    let updated_at = chrono::Utc::now().to_rfc3339();
    {
        let mut canvas = state.canvas.lock().unwrap();
        if let Some(elements) = &payload.elements {
            canvas.elements = Some(elements.clone());
        }
        if let Some(app_state) = &payload.app_state {
            canvas.app_state = Some(app_state.clone());
        }
        if let Some(files) = &payload.files {
            canvas.files = Some(files.clone());
        }
        canvas.updated_at = updated_at.clone();
    }

    // Emit draw event to frontend
    if let Err(err) = state.app.emit(EVENT_DRAW, &payload) {
        error!(
            target: "canvas_update",
            action = "emit_event_failed",
            error = %err,
            "发送更新事件到前端失败"
        );
        return (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": "Failed to emit draw event"})),
        );
    }

    let final_canvas_data = {
        let canvas = state.canvas.lock().unwrap();
        serde_json::to_string(&*canvas).unwrap_or_else(|_| "无法序列化画布数据".to_string())
    };
    info!(
        target: "canvas_update",
        action = "update_canvas_success",
        updated_at = %updated_at,
        final_canvas_data = %final_canvas_data,
        "画布数据已成功更新并发送到前端"
    );
    (StatusCode::OK, Json(json!({"success": true})))
}

// Clear canvas
async fn clear_canvas(State(state): State<AppState>) -> impl IntoResponse {
    info!(
        target: "canvas_clear",
        action = "clear_canvas_start",
        "开始清除画布"
    );

    let clear_payload = DrawPayload {
        elements: Some(json!([])),
        app_state: None,
        files: None,
    };

    let updated_at = chrono::Utc::now().to_rfc3339();
    {
        let mut canvas = state.canvas.lock().unwrap();
        canvas.elements = Some(json!([]));
        canvas.app_state = None;
        canvas.files = None;
        canvas.updated_at = updated_at.clone();
    }

    // Emit clear event to frontend
    if let Err(err) = state.app.emit(EVENT_DRAW, &clear_payload) {
        error!(
            target: "canvas_clear",
            action = "emit_clear_event_failed",
            error = %err,
            "发送清除事件到前端失败"
        );
        return (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": "Failed to emit clear event"})),
        );
    }

    let clear_payload_json =
        serde_json::to_string(&clear_payload).unwrap_or_else(|_| "无法序列化清除数据".to_string());
    let final_canvas_data = {
        let canvas = state.canvas.lock().unwrap();
        serde_json::to_string(&*canvas).unwrap_or_else(|_| "无法序列化画布数据".to_string())
    };
    info!(
        target: "canvas_clear",
        action = "clear_canvas_success",
        updated_at = %updated_at,
        clear_data = %clear_payload_json,
        final_canvas_data = %final_canvas_data,
        "画布已成功清除"
    );
    (StatusCode::OK, Json(json!({"success": true})))
}

// Export canvas as SVG or other formats
async fn export_canvas(
    State(state): State<AppState>,
    Query(params): Query<ExportQuery>,
) -> impl IntoResponse {
    println!(
        "📤 导出画布: format={}, width={}, height={}",
        params.format, params.width, params.height
    );

    let canvas = state.canvas.lock().unwrap();
    let default_elements = json!([]);
    let elements = canvas.elements.as_ref().unwrap_or(&default_elements);

    match params.format.as_str() {
        "svg" => {
            let svg_content = generate_svg(elements, params.width, params.height);
            Response::builder()
                .status(StatusCode::OK)
                .header(header::CONTENT_TYPE, "image/svg+xml")
                .header(
                    header::CONTENT_DISPOSITION,
                    "inline; filename=\"canvas.svg\"",
                )
                .body(svg_content)
                .unwrap()
        }
        "json" => {
            let export_data = json!({
                "elements": elements,
                "appState": canvas.app_state,
                "files": canvas.files,
                "exported_at": chrono::Utc::now().to_rfc3339(),
                "format": "excalidraw"
            });
            Response::builder()
                .status(StatusCode::OK)
                .header(header::CONTENT_TYPE, "application/json")
                .header(
                    header::CONTENT_DISPOSITION,
                    "attachment; filename=\"canvas.excalidraw\"",
                )
                .body(export_data.to_string())
                .unwrap()
        }
        "toDataURL" => {
            // Generate SVG first, then convert to base64 data URL
            let svg_content = generate_svg(elements, params.width, params.height);
            let base64_svg = general_purpose::STANDARD.encode(svg_content.as_bytes());
            let data_url = format!("data:image/svg+xml;base64,{}", base64_svg);

            let response_data = json!({
                "dataURL": data_url,
                "width": params.width,
                "height": params.height,
                "format": "svg",
                "exported_at": chrono::Utc::now().to_rfc3339()
            });

            Response::builder()
                .status(StatusCode::OK)
                .header(header::CONTENT_TYPE, "application/json")
                .body(response_data.to_string())
                .unwrap()
        }
        "png" | "jpeg" | "webp" => {
            // For now, return a placeholder response for raster formats
            // In a real implementation, you would use a library like resvg or headless browser
            let placeholder = format!(
                "{{\"error\": \"Format '{}' not yet implemented. Use 'svg' or 'json' instead.\"}}",
                params.format
            );
            Response::builder()
                .status(StatusCode::NOT_IMPLEMENTED)
                .header(header::CONTENT_TYPE, "application/json")
                .body(placeholder)
                .unwrap()
        }
        _ => {
            let error = json!({"error": format!("Unsupported format: {}. Supported formats: svg, json, toDataURL, png, jpeg, webp", params.format)});
            Response::builder()
                .status(StatusCode::BAD_REQUEST)
                .header(header::CONTENT_TYPE, "application/json")
                .body(error.to_string())
                .unwrap()
        }
    }
}

fn generate_svg(elements: &Value, width: u32, height: u32) -> String {
    let mut svg_elements = Vec::new();

    if let Some(elements_array) = elements.as_array() {
        for element in elements_array {
            if let Some(svg_element) = convert_element_to_svg(element) {
                svg_elements.push(svg_element);
            }
        }
    }

    format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<svg width="{}" height="{}" viewBox="0 0 {} {}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="white"/>
  {}
</svg>"#,
        width,
        height,
        width,
        height,
        svg_elements.join("\n  ")
    )
}

fn convert_element_to_svg(element: &Value) -> Option<String> {
    let element_type = element.get("type")?.as_str()?;
    let x = element.get("x")?.as_f64().unwrap_or(0.0);
    let y = element.get("y")?.as_f64().unwrap_or(0.0);
    let width = element.get("width")?.as_f64().unwrap_or(0.0);
    let height = element.get("height")?.as_f64().unwrap_or(0.0);
    let stroke_color = element.get("strokeColor")?.as_str().unwrap_or("#000000");
    let background_color = element
        .get("backgroundColor")?
        .as_str()
        .unwrap_or("transparent");
    let stroke_width = element.get("strokeWidth")?.as_f64().unwrap_or(1.0);

    match element_type {
        "rectangle" => Some(format!(
            r#"<rect x="{}" y="{}" width="{}" height="{}" fill="{}" stroke="{}" stroke-width="{}"/>"#,
            x, y, width, height, background_color, stroke_color, stroke_width
        )),
        "ellipse" => {
            let cx = x + width / 2.0;
            let cy = y + height / 2.0;
            let rx = width / 2.0;
            let ry = height / 2.0;
            Some(format!(
                r#"<ellipse cx="{}" cy="{}" rx="{}" ry="{}" fill="{}" stroke="{}" stroke-width="{}"/>"#,
                cx, cy, rx, ry, background_color, stroke_color, stroke_width
            ))
        }
        "arrow" | "line" => {
            let x2 = x + width;
            let y2 = y + height;
            Some(format!(
                r#"<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="{}"/>"#,
                x, y, x2, y2, stroke_color, stroke_width
            ))
        }
        "text" => {
            let text_content = element
                .get("text")
                .and_then(|v| v.as_str())
                .unwrap_or("[text]");
            let font_size = element
                .get("fontSize")
                .and_then(|v| v.as_f64())
                .unwrap_or(16.0);
            let text_align = element
                .get("textAlign")
                .and_then(|v| v.as_str())
                .unwrap_or("left");
            let font_family = element
                .get("fontFamily")
                .and_then(|v| v.as_i64())
                .unwrap_or(1);

            let font_family_name = match font_family {
                1 => "Virgil",
                2 => "Helvetica",
                3 => "Cascadia",
                _ => "Virgil",
            };

            let anchor = match text_align {
                "center" => "middle",
                "right" => "end",
                _ => "start",
            };

            Some(format!(
                r#"<text x="{}" y="{}" font-size="{}" font-family="{}" text-anchor="{}" fill="{}" dominant-baseline="hanging">{}</text>"#,
                x,
                y,
                font_size,
                font_family_name,
                anchor,
                stroke_color,
                text_content
                    .replace('&', "&amp;")
                    .replace('<', "&lt;")
                    .replace('>', "&gt;")
                    .replace('"', "&quot;")
                    .replace('\'', "&#39;")
            ))
        }
        _ => {
            // For unsupported elements, create a placeholder rectangle
            Some(format!(
                r#"<rect x="{}" y="{}" width="{}" height="{}" fill="none" stroke="{}" stroke-width="{}" stroke-dasharray="5,5"/>"#,
                x, y, width, height, stroke_color, stroke_width
            ))
        }
    }
}

// Remove element by ID
async fn remove_element(
    State(state): State<AppState>,
    Path(element_id): Path<String>,
) -> impl IntoResponse {
    println!("🗑️ 移除元素: {}", element_id);

    let mut updated_elements = Vec::new();
    let mut element_found = false;

    {
        let canvas = state.canvas.lock().unwrap();
        if let Some(elements) = &canvas.elements {
            if let Some(elements_array) = elements.as_array() {
                for element in elements_array {
                    if let Some(id) = element.get("id").and_then(|v| v.as_str()) {
                        if id != element_id {
                            updated_elements.push(element.clone());
                        } else {
                            element_found = true;
                        }
                    } else {
                        updated_elements.push(element.clone());
                    }
                }
            }
        }
    }

    if !element_found {
        return (
            StatusCode::NOT_FOUND,
            Json(json!({"error": format!("Element with ID '{}' not found", element_id)})),
        );
    }

    let draw_payload = DrawPayload {
        elements: Some(json!(updated_elements)),
        app_state: None,
        files: None,
    };

    // Update canvas data
    {
        let mut canvas = state.canvas.lock().unwrap();
        canvas.elements = Some(json!(updated_elements));
        canvas.updated_at = chrono::Utc::now().to_rfc3339();
    }

    // Emit update event to frontend
    if let Err(err) = state.app.emit(EVENT_DRAW, &draw_payload) {
        eprintln!("❌ 发送移除事件失败: {err:?}");
        return (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": "Failed to emit remove event"})),
        );
    }

    println!("✅ 元素已移除: {}", element_id);
    (
        StatusCode::OK,
        Json(json!({"success": true, "message": format!("Element '{}' removed", element_id)})),
    )
}

// Update element by ID
async fn update_element(
    State(state): State<AppState>,
    Path(element_id): Path<String>,
    Json(payload): Json<UpdateElementPayload>,
) -> impl IntoResponse {
    println!("🔄 更新元素: {} -> {:?}", element_id, payload.element);

    let mut updated_elements = Vec::new();
    let mut element_found = false;

    {
        let canvas = state.canvas.lock().unwrap();
        if let Some(elements) = &canvas.elements {
            if let Some(elements_array) = elements.as_array() {
                for element in elements_array {
                    if let Some(id) = element.get("id").and_then(|v| v.as_str()) {
                        if id == element_id {
                            updated_elements.push(payload.element.clone());
                            element_found = true;
                        } else {
                            updated_elements.push(element.clone());
                        }
                    } else {
                        updated_elements.push(element.clone());
                    }
                }
            }
        }
    }

    if !element_found {
        return (
            StatusCode::NOT_FOUND,
            Json(json!({"error": format!("Element with ID '{}' not found", element_id)})),
        );
    }

    let draw_payload = DrawPayload {
        elements: Some(json!(updated_elements)),
        app_state: None,
        files: None,
    };

    // Update canvas data
    {
        let mut canvas = state.canvas.lock().unwrap();
        canvas.elements = Some(json!(updated_elements));
        canvas.updated_at = chrono::Utc::now().to_rfc3339();
    }

    // Emit update event to frontend
    if let Err(err) = state.app.emit(EVENT_DRAW, &draw_payload) {
        eprintln!("❌ 发送更新事件失败: {err:?}");
        return (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": "Failed to emit update event"})),
        );
    }

    println!("✅ 元素已更新: {}", element_id);
    (
        StatusCode::OK,
        Json(json!({"success": true, "message": format!("Element '{}' updated", element_id)})),
    )
}
