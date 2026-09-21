use super::{
    access::approved,
    process::{assert_idle, stop_job},
    worker::call_worker,
    Workspace,
};
use serde_json::{json, Value};
use tauri::State;

#[tauri::command]
pub fn start_analysis<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    root: String,
    options: Value,
    state: State<Workspace>,
) -> Result<Value, String> {
    let root = approved(&state, &root)?;
    let mut job = state.job.lock().map_err(crate::errors::message)?;
    assert_idle(&mut job)?;
    let started = call_worker(
        &app,
        json!({"operation": "start_job", "args": {"root": root, "options": options}}),
    )?;
    *job = None;
    Ok(started)
}

#[tauri::command]
pub fn cancel_job<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<Workspace>,
    job_id: Option<String>,
) -> Result<(), String> {
    let mut job = state.job.lock().map_err(crate::errors::message)?;
    if let Some(job) = job.as_mut() {
        stop_job(job)?;
    } else if let Some(job_id) = job_id {
        call_worker(
            &app,
            json!({"operation": "cancel_job", "args": {"jobId": job_id}}),
        )?;
    }
    Ok(())
}
