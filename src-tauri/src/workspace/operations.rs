use super::{operation_args, process::assert_idle, worker::call_worker, Workspace};
use serde_json::{json, Value};
use tauri::Manager;

fn execute<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    operation: &str,
    mut args: Value,
) -> Result<Value, String> {
    let state = app.state::<Workspace>();
    let _guard = state.operation.lock().map_err(crate::errors::message)?;
    let mut deletion_job = if operation == "delete_analysis" {
        Some(state.job.lock().map_err(crate::errors::message)?)
    } else {
        None
    };
    if let Some(job) = deletion_job.as_mut() {
        assert_idle(job)?;
    }
    operation_args::prepare(app, &state, operation, &mut args)?;
    let result = call_worker(app, json!({"operation": operation, "args": args}))?;
    super::result_registration::remember_result(app, &state, operation, &result)?;
    Ok(result)
}

#[tauri::command]
pub async fn workspace_operation<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    operation: String,
    args: Value,
) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || execute(&app, &operation, args))
        .await
        .map_err(crate::errors::message)?
}
