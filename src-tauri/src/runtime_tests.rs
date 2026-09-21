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
