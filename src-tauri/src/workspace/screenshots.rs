use super::{runtime_paths::runtime_root, screenshot_request};
use std::{fs, time::Duration};
use tauri::Manager;

pub(crate) fn start<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<(), String> {
    let folder = runtime_root(&app)?.join("control/screenshots");
    std::thread::spawn(move || {
        while app.get_webview_window("main").is_some() {
            if let Ok(entries) = fs::read_dir(&folder) {
                for entry in entries.flatten() {
                    let _ = screenshot_request::process(&app, &entry.path());
                }
            }
            std::thread::sleep(Duration::from_millis(250));
        }
    });
    Ok(())
}
