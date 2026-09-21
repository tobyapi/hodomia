#[derive(serde::Serialize)]
pub(crate) struct RuntimeInfo {
    name: &'static str,
    version: &'static str,
    runtime: &'static str,
}

#[tauri::command]
pub(crate) fn runtime_info() -> RuntimeInfo {
    RuntimeInfo {
        name: "hodomia",
        version: env!("CARGO_PKG_VERSION"),
        runtime: "Tauri",
    }
}
