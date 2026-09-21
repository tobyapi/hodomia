use std::process::Command;

pub(super) fn hidden(command: &mut Command) -> &mut Command {
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
    command
}
pub(super) fn terminate(child: &mut std::process::Child) -> Result<(), String> {
    #[cfg(windows)]
    hidden(Command::new("taskkill").args(["/PID", &child.id().to_string(), "/T", "/F"]))
        .output()
        .map_err(crate::errors::message)?;
    #[cfg(not(windows))]
    child.kill().map_err(crate::errors::message)?;
    Ok(())
}
