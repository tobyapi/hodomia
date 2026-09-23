use super::{
    access::grant,
    analysis_support,
    runtime_paths::{python_in_venv, runtime_root},
    worker::call_worker,
    Workspace,
};
use serde_json::{json, Value};
use std::path::Path;
use tauri::Manager;

#[tauri::command]
pub async fn next_ui_request<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || {
        if !analysis_support::AVAILABLE
            || !python_in_venv(&runtime_root(&app)?.join("venv")).exists()
        {
            return Ok(Value::Null);
        }
        let request = call_worker(&app, json!({"operation": "next_ui_request"}))?;
        if let Some(root) = request["root"].as_str() {
            let state = app.state::<Workspace>();
            grant(&app, &state, Path::new(root))?;
        }
        Ok(request)
    })
    .await
    .map_err(crate::errors::message)?
}

#[tauri::command]
pub async fn ack_ui_request<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    request_id: String,
    state: String,
    message: Option<String>,
) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let result = call_worker(&app, json!({"operation": "ack_ui_request", "args": {"requestId": request_id, "state": state, "message": message}}))?;
        super::window_focus::present(&app, &result)?;
        Ok(result)
    }).await.map_err(crate::errors::message)?
}
