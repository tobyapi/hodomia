#[derive(serde::Serialize)]
struct RuntimeInfo {
    name: &'static str,
    version: &'static str,
    runtime: &'static str,
}

#[tauri::command]
fn runtime_info() -> RuntimeInfo {
    RuntimeInfo {
        name: "Music Sweeper",
        version: env!("CARGO_PKG_VERSION"),
        runtime: "Tauri",
    }
}

fn app_builder<R: tauri::Runtime>(builder: tauri::Builder<R>) -> tauri::Builder<R> {
    builder
        .manage(workspace::Workspace::default())
        .invoke_handler(tauri::generate_handler![
            runtime_info,
            workspace::choose_path,
            workspace::workspace_operation,
            workspace::start_analysis,
            workspace::job_status,
            workspace::cancel_job,
            workspace::runtime_status,
            workspace::setup_runtime,
            workspace::read_lyrics,
            workspace::saved_projects,
            workspace::remove_saved_project
        ])
}

pub fn run() {
    app_builder(tauri::Builder::default())
        .run(tauri::generate_context!())
        .expect("failed to run Music Sweeper");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn runtime_info_has_the_frontend_contract() {
        let app = app_builder(tauri::test::mock_builder())
            .build(tauri::test::mock_context(tauri::test::noop_assets()))
            .unwrap();
        let window = tauri::WebviewWindowBuilder::new(&app, "main", Default::default())
            .build()
            .unwrap();
        let response = tauri::test::get_ipc_response(
            &window,
            tauri::webview::InvokeRequest {
                cmd: "runtime_info".into(),
                callback: tauri::ipc::CallbackFn(0),
                error: tauri::ipc::CallbackFn(1),
                url: "http://tauri.localhost".parse().unwrap(),
                body: tauri::ipc::InvokeBody::default(),
                headers: Default::default(),
                invoke_key: tauri::test::INVOKE_KEY.to_string(),
            },
        )
        .unwrap();
        let value = response.deserialize::<serde_json::Value>().unwrap();
        assert_eq!(value["name"], "Music Sweeper");
        assert_eq!(value["version"], env!("CARGO_PKG_VERSION"));
        assert_eq!(value["runtime"], "Tauri");
    }
}
mod library;
mod workspace;
