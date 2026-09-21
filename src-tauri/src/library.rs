use serde_json::Value;
use std::{fs, path::Path};

mod listing;

pub fn list(parent: &Path, registry: &Path) -> Result<Vec<Value>, String> {
    listing::list(parent, registry)
}

pub fn remember(registry: &Path, root: &Path) -> Result<(), String> {
    let root = fs::canonicalize(root).map_err(crate::errors::message)?;
    fs::create_dir_all(registry).map_err(crate::errors::message)?;
    fs::write(
        registry.join(entry_name(&root)),
        serde_json::to_vec(&root).map_err(crate::errors::message)?,
    )
    .map_err(crate::errors::message)
}

fn entry_name(root: &Path) -> String {
    use std::hash::{DefaultHasher, Hash, Hasher};
    let mut hash = DefaultHasher::new();
    root.hash(&mut hash);
    format!("{:016x}.json", hash.finish())
}

pub fn hide(registry: &Path, root: &Path) -> Result<(), String> {
    remember(&registry.join("hidden"), root)
}

pub fn restore(registry: &Path, root: &Path) -> Result<(), String> {
    let root = fs::canonicalize(root).map_err(crate::errors::message)?;
    let marker = registry.join("hidden").join(entry_name(&root));
    if marker.exists() {
        fs::remove_file(marker).map_err(crate::errors::message)?;
    }
    Ok(())
}

#[cfg(test)]
#[path = "library_tests.rs"]
mod tests;

mod roots;
mod summary;
