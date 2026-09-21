use super::runtime_paths::runtime_root;
use serde_json::{json, Value};
use std::fs;

#[tauri::command]
pub fn runtime_status<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<Value, String> {
    let runtime = runtime_root(&app)?;
    let ready = fs::read_to_string(runtime.join("ready.json"))
        .ok()
        .and_then(|text| serde_json::from_str::<Value>(&text).ok());
    let complete = ready
        .as_ref()
        .is_some_and(|v| v["structure"] == "harmonix-all")
        && ready.as_ref().is_some_and(|v| v["vocalEvents"].is_string())
        && runtime
            .join("models/vocal-events/model.safetensors")
            .is_file()
        && runtime.join("venv/Scripts/python.exe").is_file();
    let chord_mini_ready = runtime.join("chordmini/installation.json").is_file()
        && runtime.join("chordmini/venv/Scripts/python.exe").is_file();
    Ok(
        json!({"path": runtime, "ready": complete, "details": ready, "chordMiniReady": chord_mini_ready}),
    )
}
