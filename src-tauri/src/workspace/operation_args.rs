use super::{access::approved, paths, Workspace};
use serde_json::{json, Value};
use std::fs;

pub(super) fn prepare<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    state: &Workspace,
    operation: &str,
    args: &mut Value,
) -> Result<(), String> {
    match operation {
        "create" => {
            approved(state, args["source"].as_str().ok_or("source missing")?)?;
            let parent = paths::projects(app)?;
            fs::create_dir_all(&parent).map_err(crate::errors::message)?;
            args["parent"] = json!(parent);
        }
        "snapshot" | "save" | "export" | "delete_analysis" => {
            approved(state, args["root"].as_str().ok_or("root missing")?)?;
        }
        _ => return Err("操作が不正です。".into()),
    }
    Ok(())
}
