use super::{
    analysis_support,
    process_control::hidden,
    runtime_paths::{runtime_root, source_root},
};
use serde_json::Value;
use std::{
    io::Write,
    process::{Command, Stdio},
};

pub(super) fn worker<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> Result<Command, String> {
    let runtime = runtime_root(app)?;
    let mut command = Command::new(analysis_support::analysis_python(&runtime)?);
    hidden(&mut command)
        .arg(source_root(app)?.join("analysis/cli.py"))
        .arg("--runtime")
        .arg(runtime)
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8")
        .env("HF_HUB_OFFLINE", "1")
        .env("TRANSFORMERS_OFFLINE", "1")
        .env("HF_HUB_DISABLE_TELEMETRY", "1")
        .stdin(Stdio::piped());
    Ok(command)
}

pub(super) fn call_worker<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    request: Value,
) -> Result<Value, String> {
    let mut child = worker(app)?
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(crate::errors::message)?;
    child
        .stdin
        .take()
        .ok_or("stdin unavailable")?
        .write_all(request.to_string().as_bytes())
        .map_err(crate::errors::message)?;
    let output = child.wait_with_output().map_err(crate::errors::message)?;
    super::worker_response::decode(output)
}
