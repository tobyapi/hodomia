use std::path::PathBuf;

pub(super) fn pick(kind: &str) -> Result<Option<PathBuf>, String> {
    let dialog = rfd::FileDialog::new();
    match kind {
        "source" => Ok(dialog
            .add_filter("音楽・動画", &["mp3", "mp4", "m4a", "wav", "flac"])
            .pick_file()),
        "project" | "folder" => Ok(dialog.pick_folder()),
        "lyrics" => Ok(dialog.add_filter("歌詞", &["txt"]).pick_file()),
        _ => Err("選択種別が不正です。".into()),
    }
}
