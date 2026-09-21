use super::Workspace;
use std::{
    fs,
    path::{Path, PathBuf},
};
use tauri::Manager;

pub(super) fn approved(state: &Workspace, path: &str) -> Result<PathBuf, String> {
    let path = fs::canonicalize(path).map_err(crate::errors::message)?;
    if state
        .approved
        .lock()
        .map_err(crate::errors::message)?
        .contains(&path)
    {
        Ok(path)
    } else {
        Err("ファイル選択からプロジェクトを開いてください。".into())
    }
}

pub(super) fn grant<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    state: &Workspace,
    root: &Path,
) -> Result<(), String> {
    let root = fs::canonicalize(root).map_err(crate::errors::message)?;
    app.asset_protocol_scope()
        .allow_directory(&root, true)
        .map_err(crate::errors::message)?;
    state
        .approved
        .lock()
        .map_err(crate::errors::message)?
        .insert(root);
    Ok(())
}
