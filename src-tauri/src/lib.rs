// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
mod server;

use tracing::{info, error};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

fn init_logging() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::fmt::layer()
                .json()
                .with_target(true)
                .with_thread_ids(true)
                .with_thread_names(true)
                .with_file(true)
                .with_line_number(true)
        )
        .with(tracing_subscriber::EnvFilter::from_default_env()
            .add_directive("extauri_lib=info".parse().unwrap())
            .add_directive("http_server=info".parse().unwrap())
            .add_directive("canvas_update=info".parse().unwrap())
            .add_directive("canvas_clear=info".parse().unwrap())
            .add_directive("server_startup=info".parse().unwrap()))
        .init();
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 初始化JSON格式日志
    init_logging();
    
    info!("应用程序启动");
    
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                // start HTTP server in background
                if let Err(err) = server::start_http_server(app_handle).await {
                    error!(
                        target: "server_startup",
                        error = %err,
                        "HTTP服务器启动失败"
                    );
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
