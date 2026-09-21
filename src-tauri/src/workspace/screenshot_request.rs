use super::screenshot_response;
use std::{fs, path::Path};

fn request_id(path: &Path) -> Option<&str> {
    let name = path.file_name()?.to_str()?.strip_suffix(".request.json")?;
    (name.len() == 32
        && name
            .bytes()
            .all(|c| c.is_ascii_hexdigit() && !c.is_ascii_uppercase()))
    .then_some(name)
}

pub(super) fn process<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    path: &Path,
) -> Result<(), String> {
    let Some(id) = request_id(path) else {
        return Ok(());
    };
    let working = path.with_file_name(format!("{id}.working.json"));
    fs::rename(path, &working).map_err(crate::errors::message)?;
    let result = screenshot_response::respond(app, &working, id);
    let _ = fs::remove_file(working);
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_only_generated_request_names() {
        assert!(request_id(Path::new("0123456789abcdef0123456789abcdef.request.json")).is_some());
        for name in [
            "foo.request.json",
            "0123456789abcdef0123456789abcdef.png",
            "../x.json",
        ] {
            assert!(request_id(Path::new(name)).is_none());
        }
    }
}
