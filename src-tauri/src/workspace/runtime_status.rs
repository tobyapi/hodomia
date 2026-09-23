use super::{
    analysis_support,
    runtime_paths::{python_in_venv, runtime_root},
};
use serde_json::{json, Value};
use std::{fs, path::Path};

fn analysis_ready(runtime: &Path, ready: Option<&Value>) -> bool {
    analysis_support::AVAILABLE
        && ready.is_some_and(|v| v["structure"] == "harmonix-all")
        && ready.is_some_and(|v| v["vocalEvents"].is_string())
        && runtime
            .join("models/vocal-events/model.safetensors")
            .is_file()
        && python_in_venv(&runtime.join("venv")).is_file()
}

fn chord_mini_ready(runtime: &Path) -> bool {
    analysis_support::AVAILABLE
        && runtime.join("chordmini/installation.json").is_file()
        && python_in_venv(&runtime.join("chordmini/venv")).is_file()
}

#[tauri::command]
pub fn runtime_status<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<Value, String> {
    let runtime = runtime_root(&app)?;
    let ready = fs::read_to_string(runtime.join("ready.json"))
        .ok()
        .and_then(|text| serde_json::from_str::<Value>(&text).ok());
    let complete = analysis_ready(&runtime, ready.as_ref());
    let chord_mini_ready = chord_mini_ready(&runtime);
    Ok(
        json!({"path": runtime, "ready": complete, "details": ready, "chordMiniReady": chord_mini_ready,
               "analysisSupported": analysis_support::AVAILABLE}),
    )
}
