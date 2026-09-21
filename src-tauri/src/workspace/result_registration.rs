use super::{access::grant, paths, Workspace};
use serde_json::Value;
use std::path::Path;

pub(super) fn remember_result<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    state: &Workspace,
    operation: &str,
    result: &Value,
) -> Result<(), String> {
    if operation == "create" {
        grant(
            app,
            state,
            Path::new(result["root"].as_str().ok_or("root missing")?),
        )?;
    }
    if operation == "create" || operation == "snapshot" {
        let root = Path::new(result["root"].as_str().ok_or("root missing")?);
        crate::library::remember(&paths::registry(app)?, root)?;
    }
    Ok(())
}
