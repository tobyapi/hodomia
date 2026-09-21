use super::{access::grant, paths::registry, Workspace};
use std::fs;
use tauri::Manager;

fn select<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    kind: &str,
) -> Result<Option<String>, String> {
    let Some(path) = super::file_picker::pick(kind)? else {
        return Ok(None);
    };
    let state = app.state::<Workspace>();
    let path = fs::canonicalize(path).map_err(crate::errors::message)?;
    if kind == "project" {
        if !path.join("project.json").is_file() {
            return Err("project.json があるフォルダーを選んでください。".into());
        }
        grant(app, &state, &path)?;
        crate::library::restore(&registry(app)?, &path)?;
    } else {
        state
            .approved
            .lock()
            .map_err(crate::errors::message)?
            .insert(path.clone());
    }
    Ok(Some(path.to_string_lossy().to_string()))
}

#[tauri::command]
pub async fn choose_path<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    kind: String,
) -> Result<Option<String>, String> {
    tauri::async_runtime::spawn_blocking(move || select(&app, &kind))
        .await
        .map_err(crate::errors::message)?
}
