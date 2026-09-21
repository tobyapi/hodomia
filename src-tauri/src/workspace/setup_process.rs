use super::{process_control::hidden, runtime_paths::source_root, Job};
use std::{fs, path::Path, process::Command};

pub(super) fn spawn<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    runtime: &Path,
    chord_mini: bool,
) -> Result<Job, String> {
    let log_path = runtime.join("setup.log");
    let log = fs::File::create(&log_path).map_err(crate::errors::message)?;
    let script = if chord_mini {
        "scripts/setup-chordmini.ps1"
    } else {
        "scripts/setup-analysis.ps1"
    };
    let child = hidden(
        Command::new("powershell")
            .args(["-NoProfile", "-ExecutionPolicy", "Bypass", "-File"])
            .arg(source_root(app)?.join(script))
            .arg("-RuntimeRoot")
            .arg(runtime),
    )
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
