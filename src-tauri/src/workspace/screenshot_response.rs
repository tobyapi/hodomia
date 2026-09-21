use super::window_capture;
use serde_json::{json, Value};
use std::{
    fs,
    path::Path,
    time::{SystemTime, UNIX_EPOCH},
};

pub(super) fn respond<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    path: &Path,
    id: &str,
) -> Result<(), String> {
    let request: Value = serde_json::from_slice(&fs::read(path).map_err(crate::errors::message)?)
        .map_err(crate::errors::message)?;
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(crate::errors::message)?
        .as_secs_f64();
    if request["expiresAt"].as_f64().unwrap_or(0.0) <= now {
        return Ok(());
    }
    let png = path.with_file_name(format!("{id}.png"));
    let response = match window_capture::save(app, &png) {
        Ok((width, height)) => json!({"ok": true, "width": width, "height": height}),
        Err(message) => json!({"ok": false, "message": message}),
    };
    let temporary = path.with_file_name(format!("{id}.response.tmp"));
    fs::write(&temporary, response.to_string()).map_err(crate::errors::message)?;
    fs::rename(
        temporary,
        path.with_file_name(format!("{id}.response.json")),
    )
    .map_err(crate::errors::message)
}
