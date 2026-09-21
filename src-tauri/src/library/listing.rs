use super::{
    roots::{default_roots, registered_roots},
    summary::project,
};
use serde_json::Value;
use std::{collections::HashSet, fs, path::Path};

pub(super) fn list(parent: &Path, registry: &Path) -> Result<Vec<Value>, String> {
    let mut roots = default_roots(parent)?;
    registered_roots(registry, &mut roots)?;
    let mut seen = HashSet::new();
    let mut projects = Vec::new();
    for root in roots {
        let Ok(root) = fs::canonicalize(root) else {
            continue;
        };
        if !seen.insert(root.clone())
            || registry
                .join("hidden")
                .join(super::entry_name(&root))
                .exists()
        {
            continue;
        }
        if let Some(value) = project(root) {
            projects.push(value);
        }
    }
    projects.sort_by(|a, b| {
        b["createdAt"]
            .as_str()
            .cmp(&a["createdAt"].as_str())
            .then_with(|| a["root"].as_str().cmp(&b["root"].as_str()))
    });
    Ok(projects)
}
