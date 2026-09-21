use std::path::{Path, PathBuf};
use tauri::Manager;

pub(super) fn source_root<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> Result<PathBuf, String> {
    let development = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf();
    if cfg!(debug_assertions) {
        Ok(development)
    } else {
        let resources = app.path().resource_dir().map_err(crate::errors::message)?;
        if resources.join("analysis/cli.py").exists() {
            Ok(resources)
        } else {
            Ok(development)
        }
    }
}
pub(super) fn runtime_root<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
) -> Result<PathBuf, String> {
    if let Some(path) = std::env::var_os("HODOMIA_RUNTIME") {
        return Ok(PathBuf::from(path));
    }
    // This initial release targets the user's development PC. Installed copies
    // use their own writable application-data directory when this cache is absent.
    let local = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join(".runtime");
    if local.exists() {
        return Ok(local);
    }
    Ok(app
        .path()
        .app_data_dir()
        .map_err(crate::errors::message)?
        .join("runtime"))
}
