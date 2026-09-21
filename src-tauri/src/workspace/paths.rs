use std::path::PathBuf;
use tauri::Manager;

pub(super) fn registry<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> Result<PathBuf, String> {
    Ok(app
        .path()
        .app_data_dir()
        .map_err(crate::errors::message)?
        .join("library"))
}

pub(super) fn projects<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> Result<PathBuf, String> {
    Ok(app
        .path()
        .document_dir()
        .map_err(crate::errors::message)?
        .join("Music Sweeper/Projects"))
}
