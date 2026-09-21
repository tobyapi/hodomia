use super::{runtime_paths::runtime_root, worker::call_worker, Workspace};
use serde_json::{json, Value};
use std::fs;
use tauri::State;

#[tauri::command]
pub fn job_status<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<Workspace>,
) -> Result<Value, String> {
    let mut job = state.job.lock().map_err(crate::errors::message)?;
    if let Some(active) = job.as_mut() {
        let exit = active.child.try_wait().map_err(crate::errors::message)?;
        let text = fs::read_to_string(&active.log).unwrap_or_default();
        let tail: String = text
            .chars()
            .rev()
            .take(3000)
            .collect::<String>()
            .chars()
            .rev()
            .collect();
        let result = Ok(
            json!({"running": exit.is_none(), "success": exit.map(|s| s.success()), "kind": active.kind, "log": tail}),
        );
        if exit.is_some() {
            *job = None;
        }
        result
    } else {
        if !runtime_root(&app)?.join("venv/Scripts/python.exe").exists() {
            return Ok(json!({"running": false, "kind": null, "log": ""}));
        }
        call_worker(&app, json!({"operation": "latest_job"}))
    }
}
