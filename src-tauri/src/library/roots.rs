use std::{
    collections::HashSet,
    fs,
    path::{Path, PathBuf},
};

pub(super) fn default_roots(parent: &Path) -> Result<HashSet<PathBuf>, String> {
    let mut roots = HashSet::new();
    if parent.exists() {
        for entry in fs::read_dir(parent).map_err(crate::errors::message)? {
            let path = entry.map_err(crate::errors::message)?.path();
            if path.is_dir() {
                roots.insert(path);
            }
        }
    }
    Ok(roots)
}
pub(super) fn registered_roots(
    registry: &Path,
    roots: &mut HashSet<PathBuf>,
) -> Result<(), String> {
    if !registry.exists() {
        return Ok(());
    }
    for entry in fs::read_dir(registry).map_err(crate::errors::message)? {
        let entry = entry.map_err(crate::errors::message)?;
        let root = fs::read_to_string(entry.path())
            .ok()
            .and_then(|text| serde_json::from_str::<String>(&text).ok());
        if let Some(root) = root {
            roots.insert(PathBuf::from(root));
        }
    }
    Ok(())
}
