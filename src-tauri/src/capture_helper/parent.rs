use windows::Win32::{
    Foundation::CloseHandle,
    System::Diagnostics::ToolHelp::{
        CreateToolhelp32Snapshot, Process32FirstW, Process32NextW, PROCESSENTRY32W,
        TH32CS_SNAPPROCESS,
    },
};

pub(crate) fn verified_pid() -> Result<u32, String> {
    let pid = parent_pid()?;
    super::process::verify(pid)?;
    Ok(pid)
}

fn parent_pid() -> Result<u32, String> {
    // The snapshot owns a handle, closed after enumeration on every result.
    unsafe {
        let snapshot =
            CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0).map_err(crate::errors::message)?;
        let result = find_parent(snapshot);
        let _ = CloseHandle(snapshot);
        result
    }
}

unsafe fn find_parent(snapshot: windows::Win32::Foundation::HANDLE) -> Result<u32, String> {
    let mut entry = PROCESSENTRY32W {
        dwSize: std::mem::size_of::<PROCESSENTRY32W>() as u32,
        ..Default::default()
    };
    Process32FirstW(snapshot, &mut entry).map_err(crate::errors::message)?;
    loop {
        if entry.th32ProcessID == std::process::id() {
            return Ok(entry.th32ParentProcessID);
        }
        Process32NextW(snapshot, &mut entry).map_err(crate::errors::message)?;
    }
}
