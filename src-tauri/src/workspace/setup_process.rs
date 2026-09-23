use super::{process_control::hidden, setup_command, Job};
use std::{fs, path::Path};

pub(super) fn spawn<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    runtime: &Path,
    chord_mini: bool,
) -> Result<Job, String> {
    let log_path = runtime.join("setup.log");
    let log = fs::File::create(&log_path).map_err(crate::errors::message)?;
    let child = hidden(&mut setup_command::build(app, runtime, chord_mini)?)
        .env_remove("HF_HUB_OFFLINE")
        .env_remove("TRANSFORMERS_OFFLINE")
        .stdout(log.try_clone().map_err(crate::errors::message)?)
        .stderr(log)
        .spawn()
        .map_err(crate::errors::message)?;
    Ok(Job {
        child,
        root: None,
        log: log_path,
        kind: "setup",
    })
}
