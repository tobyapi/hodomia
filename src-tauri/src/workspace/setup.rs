use super::{process::assert_idle, runtime_paths::runtime_root, worker::call_worker, Workspace};
use serde_json::json;
use std::fs;
use tauri::State;

#[tauri::command]
pub fn setup_runtime<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<Workspace>,
    chord_mini: Option<bool>,
) -> Result<(), String> {
    let mut job = state.job.lock().map_err(crate::errors::message)?;
    assert_idle(&mut job)?;
    let runtime = runtime_root(&app)?;
    fs::create_dir_all(&runtime).map_err(crate::errors::message)?;
    if runtime.join("venv/Scripts/python.exe").exists()
        && call_worker(&app, json!({"operation": "latest_job"}))?["running"] == true
    {
        return Err("解析中です。完了または中止後にセットアップしてください。".into());
    }
    *job = Some(super::setup_process::spawn(
        &app,
        &runtime,
        chord_mini.unwrap_or(false),
    )?);
    Ok(())
}
