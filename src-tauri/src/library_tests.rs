use super::*;
use serde_json::json;
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
