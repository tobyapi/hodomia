use windows::Win32::{
    Foundation::CloseHandle,
    System::Threading::{
        OpenProcess, QueryFullProcessImageNameW, PROCESS_NAME_WIN32,
        PROCESS_QUERY_LIMITED_INFORMATION,
    },
};

pub(super) fn verify(pid: u32) -> Result<(), String> {
    let executable = executable_path(pid)?;
    let own = std::env::current_exe().map_err(crate::errors::message)?;
    if std::path::Path::new(&executable) != own {
        return Err("撮影ヘルパーはMusic Sweeperからだけ起動できます。".into());
    }
    Ok(())
}

fn executable_path(pid: u32) -> Result<String, String> {
    unsafe {
        let process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, pid)
            .map_err(crate::errors::message)?;
        let mut buffer = vec![0u16; 32768];
        let mut size = buffer.len() as u32;
        let result = QueryFullProcessImageNameW(
            process,
            PROCESS_NAME_WIN32,
            windows::core::PWSTR(buffer.as_mut_ptr()),
            &mut size,
        );
        let _ = CloseHandle(process);
        result.map_err(crate::errors::message)?;
        String::from_utf16(&buffer[..size as usize]).map_err(crate::errors::message)
    }
}
