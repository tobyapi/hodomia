use std::path::Path;

#[cfg(windows)]
pub(super) fn save<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    path: &Path,
) -> Result<(u32, u32), String> {
    use tauri::Manager;
    let main = app.get_webview_window("main").ok_or("GUIがありません。")?;
    if main.is_minimized().map_err(crate::errors::message)? {
        return Err("最小化したウィンドウは撮影できません。".into());
    }
    let id = main.hwnd().map_err(crate::errors::message)?.0 as usize as u32;
    save_from_helper(id, path)
}

#[cfg(windows)]
fn save_from_helper(id: u32, path: &Path) -> Result<(u32, u32), String> {
    use std::process::Command;
    let executable = std::env::current_exe().map_err(crate::errors::message)?;
    let output = super::process_control::hidden(
        Command::new(executable)
            .arg("--capture-parent-window")
            .arg(id.to_string()),
    )
    .output()
    .map_err(crate::errors::message)?;
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).into_owned());
    }
    let image = xcap::image::load_from_memory(&output.stdout).map_err(crate::errors::message)?;
    std::fs::write(path, &output.stdout).map_err(crate::errors::message)?;
    Ok((image.width(), image.height()))
}

#[cfg(not(windows))]
pub(super) fn save<R: tauri::Runtime>(
    _app: &tauri::AppHandle<R>,
    _path: &Path,
) -> Result<(u32, u32), String> {
    Err("ウィンドウ撮影はWindows版で利用できます。".into())
}
