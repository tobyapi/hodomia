use super::{access::grant, paths, Workspace};
use serde_json::Value;
use std::path::Path;
use tauri::Manager;

fn list<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> Result<Vec<Value>, String> {
    let state = app.state::<Workspace>();
    let _guard = state.operation.lock().map_err(crate::errors::message)?;
    let projects = crate::library::list(&paths::projects(app)?, &paths::registry(app)?)?;
    for project in &projects {
        grant(
            app,
            &state,
            Path::new(project["root"].as_str().ok_or("root missing")?),
        )?;
    }
    Ok(projects)
}

#[tauri::command]
pub async fn saved_projects<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
) -> Result<Vec<Value>, String> {
    tauri::async_runtime::spawn_blocking(move || list(&app))
        .await
        .map_err(crate::errors::message)?
}
