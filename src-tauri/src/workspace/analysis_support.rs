pub(super) const AVAILABLE: bool =
    cfg!(windows) || cfg!(all(target_os = "macos", target_arch = "aarch64"));

pub(super) fn require() -> Result<(), String> {
    if AVAILABLE {
        Ok(())
    } else {
        Err("この環境では音源解析を利用できません。Windows x64 または Apple Silicon 搭載 Mac をご利用ください。".into())
    }
}

pub(super) fn analysis_python(runtime: &std::path::Path) -> Result<std::path::PathBuf, String> {
    require()?;
    let python = super::runtime_paths::python_in_venv(&runtime.join("venv"));
    if !python.exists() {
        return Err("解析環境が未準備です。「初回セットアップ」を実行してください。".into());
    }
    Ok(python)
}
