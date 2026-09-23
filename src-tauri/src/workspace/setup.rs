use super::{
    analysis_support,
    process::assert_idle,
    runtime_paths::{python_in_venv, runtime_root},
    worker::call_worker,
    Workspace,
};
use serde_json::json;
use std::fs;
use tauri::State;

#[tauri::command]
pub fn setup_runtime<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<Workspace>,
    chord_mini: Option<bool>,
) -> Result<(), String> {
    analysis_support::require()?;
    let mut job = state.job.lock().map_err(crate::errors::message)?;
    assert_idle(&mut job)?;
    let runtime = runtime_root(&app)?;
    fs::create_dir_all(&runtime).map_err(crate::errors::message)?;
    if python_in_venv(&runtime.join("venv")).exists()
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
