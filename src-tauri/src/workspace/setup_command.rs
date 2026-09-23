use super::runtime_paths::source_root;
use std::{path::Path, process::Command};

pub(super) fn build<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    runtime: &Path,
    chord_mini: bool,
) -> Result<Command, String> {
    #[cfg(target_os = "macos")]
    {
        let mut command = Command::new("sh");
        command
            .arg(source_root(app)?.join("scripts/setup-macos.sh"))
            .arg(runtime)
            .arg(if chord_mini { "chordmini" } else { "full" });
        Ok(command)
    }
    #[cfg(not(target_os = "macos"))]
    {
        let script = if chord_mini {
            "scripts/setup-chordmini.ps1"
        } else {
            "scripts/setup-analysis.ps1"
        };
        let mut command = Command::new("powershell");
        command
            .args(["-NoProfile", "-ExecutionPolicy", "Bypass", "-File"])
            .arg(source_root(app)?.join(script))
            .arg("-RuntimeRoot")
            .arg(runtime);
        Ok(command)
    }
}
