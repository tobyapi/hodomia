use serde_json::Value;
use tauri::Manager;

pub(super) fn present<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    result: &Value,
) -> Result<(), String> {
    if result["state"] == "applied" {
        if let Some(window) = app.get_webview_window("main") {
            window.unminimize().map_err(crate::errors::message)?;
            window.show().map_err(crate::errors::message)?;
            window.set_focus().map_err(crate::errors::message)?;
        }
    }
    Ok(())
}
