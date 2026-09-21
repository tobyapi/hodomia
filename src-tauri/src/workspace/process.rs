use super::process_control::terminate;
use super::Job;
use std::fs;

pub(super) fn stop_job(job: &mut Job) -> Result<(), String> {
    if job
        .child
        .try_wait()
        .map_err(crate::errors::message)?
        .is_some()
    {
        return Ok(());
    }
    if let Some(root) = &job.root {
        fs::write(root.join("cancel.flag"), b"cancel").map_err(crate::errors::message)?;
    }
    terminate(&mut job.child)?;
    job.child.wait().map_err(crate::errors::message)?;
    Ok(())
}

pub(super) fn assert_idle(job: &mut Option<Job>) -> Result<(), String> {
    if let Some(active) = job {
        if active
            .child
            .try_wait()
            .map_err(crate::errors::message)?
            .is_none()
        {
            return Err("実行中の処理が終わるまでお待ちください。".into());
        }
    }
    Ok(())
}
