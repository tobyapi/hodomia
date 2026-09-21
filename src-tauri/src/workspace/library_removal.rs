use super::{access::approved, paths, Workspace};
use tauri::Manager;

#[tauri::command]
pub async fn remove_saved_project<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    root: String,
) -> Result<(), String> {
    tauri::async_runtime::spawn_blocking(move || {
        let state = app.state::<Workspace>();
        let _guard = state.operation.lock().map_err(crate::errors::message)?;
        let root = approved(&state, &root)?;
        crate::library::hide(&paths::registry(&app)?, &root)
    })
    .await
    .map_err(crate::errors::message)?
}
