use serde_json::{json, Value};
use std::{
    collections::HashSet,
    fs,
    path::{Path, PathBuf},
};

pub fn list(parent: &Path, registry: &Path) -> Result<Vec<Value>, String> {
    let mut roots = HashSet::new();
    if parent.exists() {
        for entry in fs::read_dir(parent).map_err(|e| e.to_string())? {
            let entry = entry.map_err(|e| e.to_string())?;
            if entry.path().is_dir() {
                roots.insert(entry.path());
            }
        }
    }
    if registry.exists() {
        for entry in fs::read_dir(registry).map_err(|e| e.to_string())? {
            let entry = entry.map_err(|e| e.to_string())?;
            if let Ok(text) = fs::read_to_string(entry.path()) {
                if let Ok(root) = serde_json::from_str::<String>(&text) {
                    roots.insert(PathBuf::from(root));
                }
            }
        }
    }
    let mut seen = HashSet::new();
    let mut projects = Vec::new();
    for root in roots {
        let Ok(root) = fs::canonicalize(root) else {
            continue;
        };
        if !seen.insert(root.clone()) || registry.join("hidden").join(entry_name(&root)).exists() {
            continue;
        }
        let Ok(text) = fs::read_to_string(root.join("project.json")) else {
            continue;
        };
        let Ok(value) = serde_json::from_str::<Value>(&text) else {
            continue;
        };
        if value["kind"] != "music-sweeper" || value["schemaVersion"] != 1 {
            continue;
        }
        if value["name"].as_str().is_none() || value["duration"].as_f64().is_none() {
            continue;
        }
        projects.push(json!({"root": root, "name": value["name"], "duration": value["duration"],
            "createdAt": value["createdAt"], "hasAnalysis": value["currentRun"].as_str().is_some()}));
    }
    projects.sort_by(|a, b| {
        b["createdAt"]
            .as_str()
            .cmp(&a["createdAt"].as_str())
            .then_with(|| a["root"].as_str().cmp(&b["root"].as_str()))
    });
    Ok(projects)
}

pub fn remember(registry: &Path, root: &Path) -> Result<(), String> {
    let root = fs::canonicalize(root).map_err(|e| e.to_string())?;
    fs::create_dir_all(registry).map_err(|e| e.to_string())?;
    fs::write(
        registry.join(entry_name(&root)),
        serde_json::to_vec(&root).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
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
    let root = fs::canonicalize(root).map_err(|e| e.to_string())?;
    let marker = registry.join("hidden").join(entry_name(&root));
    if marker.exists() {
        fs::remove_file(marker).map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn library_survives_restart_and_deduplicates_default_projects() {
        let temp = std::env::temp_dir().join(format!(
            "music-library-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let parent = temp.join("projects");
        let registry = temp.join("registry");
        let project = parent.join("song");
        let external = temp.join("external");
        fs::create_dir_all(&project).unwrap();
        fs::create_dir_all(&external).unwrap();
        let manifest = json!({"kind":"music-sweeper", "schemaVersion":1, "name":"保存済み", "duration":60, "createdAt":"2026-09-21", "currentRun":"run-1"});
        fs::write(project.join("project.json"), manifest.to_string()).unwrap();
        fs::write(external.join("project.json"), manifest.to_string()).unwrap();
        remember(&registry, &project).unwrap();
        remember(&registry, &external).unwrap();
        fs::write(registry.join("broken.json"), "invalid").unwrap();
        let rows = list(&parent, &registry).unwrap();
        assert_eq!(rows.len(), 2);
        assert!(rows.iter().all(|row| row["hasAnalysis"] == true));
        hide(&registry, &project).unwrap();
        remember(&registry, &project).unwrap();
        assert_eq!(list(&parent, &registry).unwrap().len(), 1);
        assert!(project.join("project.json").is_file());
        restore(&registry, &project).unwrap();
        assert_eq!(list(&parent, &registry).unwrap().len(), 2);
        fs::remove_file(external.join("project.json")).unwrap();
        assert_eq!(list(&parent, &registry).unwrap().len(), 1);
        fs::remove_dir_all(temp).unwrap();
    }
}
