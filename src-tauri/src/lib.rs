fn app_builder<R: tauri::Runtime>(builder: tauri::Builder<R>) -> tauri::Builder<R> {
    builder
        .manage(workspace::Workspace::default())
        .invoke_handler(tauri::generate_handler![
            runtime_info::runtime_info,
            workspace::selection::choose_path,
            workspace::operations::workspace_operation,
            workspace::analysis_jobs::start_analysis,
            workspace::job_status::job_status,
            workspace::analysis_jobs::cancel_job,
            workspace::runtime_status::runtime_status,
            workspace::setup::setup_runtime,
            workspace::lyrics::read_lyrics,
            workspace::saved::saved_projects,
            workspace::library_removal::remove_saved_project,
            workspace::ui_requests::next_ui_request,
            workspace::ui_requests::ack_ui_request
        ])
}

pub fn run() {
    app_builder(tauri::Builder::default())
        .setup(|app| {
            workspace::screenshots::start(app.handle().clone())?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to run hodomia");
}

#[cfg(test)]
mod runtime_tests;

mod library;
mod workspace;

mod errors;

#[cfg(windows)]
mod capture_helper;

#[cfg(windows)]
pub use capture_helper::run_if_requested;

mod runtime_info;
