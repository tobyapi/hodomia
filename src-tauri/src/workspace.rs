use std::{collections::HashSet, path::PathBuf, process::Child, sync::Mutex};

#[derive(Default)]
pub struct Workspace {
    approved: Mutex<HashSet<PathBuf>>,
    job: Mutex<Option<Job>>,
    operation: Mutex<()>,
}

struct Job {
    child: Child,
    root: Option<PathBuf>,
    log: PathBuf,
    kind: &'static str,
}

impl Drop for Workspace {
    fn drop(&mut self) {
        if let Ok(Some(job)) = self.job.get_mut() {
            let _ = process::stop_job(job);
        }
    }
}

mod access;
pub(crate) mod analysis_jobs;
pub(crate) mod job_status;
pub(crate) mod lyrics;
pub(crate) mod operations;
mod paths;
mod process;
pub(crate) mod runtime_status;
pub(crate) mod saved;
pub(crate) mod selection;
pub(crate) mod setup;
pub(crate) mod ui_requests;
mod worker;

mod worker_response;

mod operation_args;

mod setup_process;

mod file_picker;
pub(crate) mod library_removal;
mod process_control;
mod result_registration;
mod runtime_paths;
mod screenshot_request;
mod screenshot_response;
pub(crate) mod screenshots;
mod window_capture;
mod window_focus;
