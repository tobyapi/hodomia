use serde_json::{json, Value};
use std::{fs, path::PathBuf};

pub(super) fn project(root: PathBuf) -> Option<Value> {
    let text = fs::read_to_string(root.join("project.json")).ok()?;
    let value: Value = serde_json::from_str(&text).ok()?;
    if value["kind"] != "hodomia" || value["schemaVersion"] != 1 {
        return None;
    }
    value["name"].as_str()?;
    value["duration"].as_f64()?;
    Some(
        json!({"root": root, "name": value["name"], "duration": value["duration"],
        "createdAt": value["createdAt"], "hasAnalysis": value["currentRun"].as_str().is_some()}),
    )
}
