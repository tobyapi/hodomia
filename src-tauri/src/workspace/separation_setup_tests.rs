use super::*;
use serde_json::json;
use std::fs;

#[test]
fn only_the_current_separation_setup_is_ready() {
    let runtime =
        std::env::temp_dir().join(format!("hodomia-separation-setup-{}", std::process::id()));
    let installation = runtime.join("separation/installation.json");
    fs::create_dir_all(installation.parent().unwrap()).unwrap();
    fs::write(&installation, "{}").unwrap();
    assert!(ready(&runtime, &json!({"separation": SETUP_ID})));
    assert!(!ready(&runtime, &json!({"separation": "htdemucs_ft"})));
    assert!(!ready(&runtime, &json!({})));
    fs::remove_file(&installation).unwrap();
    assert!(!ready(&runtime, &json!({"separation": SETUP_ID})));
    fs::remove_dir_all(&runtime).unwrap();
}
