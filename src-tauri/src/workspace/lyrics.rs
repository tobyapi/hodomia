use super::{access::approved, Workspace};
use std::fs;
use tauri::State;

#[tauri::command]
pub fn read_lyrics(path: String, state: State<Workspace>) -> Result<String, String> {
    let path = approved(&state, &path)?;
    if fs::metadata(&path).map_err(crate::errors::message)?.len() > 400_000 {
        return Err("歌詞ファイルは400KB以内にしてください。".into());
    }
    fs::read_to_string(path)
        .map(|s| s.trim_start_matches('\u{feff}').to_string())
        .map_err(crate::errors::message)
}
