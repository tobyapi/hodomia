//! Whether the runtime holds the separation models this build analyzes with.
use serde_json::Value;
use std::path::Path;

/// SETUP_ID in analysis/separation.py. Setups from the htdemucs_ft era must run setup again.
const SETUP_ID: &str = "kim-melband-roformer+bs-roformer-ep17";

pub(super) fn ready(runtime: &Path, manifest: &Value) -> bool {
    manifest["separation"] == SETUP_ID && runtime.join("separation/installation.json").is_file()
}

#[cfg(test)]
#[path = "separation_setup_tests.rs"]
mod tests;
