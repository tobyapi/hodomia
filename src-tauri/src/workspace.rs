use serde_json::{json, Value};
use std::{
    collections::HashSet,
    fs,
    io::Write,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
};
use tauri::{Manager, State};

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
            let _ = stop_job(job);
        }
    }
}

fn stop_job(job: &mut Job) -> Result<(), String> {
    if job.child.try_wait().map_err(|e| e.to_string())?.is_some() {
        return Ok(());
    }
    if let Some(root) = &job.root {
        fs::write(root.join("cancel.flag"), b"cancel").map_err(|e| e.to_string())?;
    }
    #[cfg(windows)]
    hidden(Command::new("taskkill").args(["/PID", &job.child.id().to_string(), "/T", "/F"]))
        .output()
        .map_err(|e| e.to_string())?;
    #[cfg(not(windows))]
    job.child.kill().map_err(|e| e.to_string())?;
    job.child.wait().map_err(|e| e.to_string())?;
    Ok(())
}

fn hidden(command: &mut Command) -> &mut Command {
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
    command
}

fn source_root<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> Result<PathBuf, String> {
    let development = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf();
    if cfg!(debug_assertions) {
        Ok(development)
    } else {
        let resources = app.path().resource_dir().map_err(|e| e.to_string())?;
        if resources.join("analysis/cli.py").exists() {
            Ok(resources)
        } else {
            Ok(development)
        }
    }
}

fn runtime_root<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> Result<PathBuf, String> {
    if let Some(path) = std::env::var_os("MUSIC_SWEEPER_RUNTIME") {
        return Ok(PathBuf::from(path));
    }
    // This initial release targets the user's development PC. Installed copies
    // use their own writable application-data directory when this cache is absent.
    let local = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join(".runtime");
    if local.exists() {
        return Ok(local);
    }
    Ok(app
        .path()
        .app_data_dir()
        .map_err(|e| e.to_string())?
        .join("runtime"))
}

fn approved(state: &Workspace, path: &str) -> Result<PathBuf, String> {
    let path = fs::canonicalize(path).map_err(|e| e.to_string())?;
    if state
        .approved
        .lock()
        .map_err(|e| e.to_string())?
        .contains(&path)
    {
        Ok(path)
    } else {
        Err("ファイル選択からプロジェクトを開いてください。".into())
    }
}

fn grant<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    state: &Workspace,
    root: &Path,
) -> Result<(), String> {
    let root = fs::canonicalize(root).map_err(|e| e.to_string())?;
    app.asset_protocol_scope()
        .allow_directory(&root, true)
        .map_err(|e| e.to_string())?;
    state
        .approved
        .lock()
        .map_err(|e| e.to_string())?
        .insert(root);
    Ok(())
}

fn worker<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> Result<Command, String> {
    let runtime = runtime_root(app)?;
    let python = runtime.join("venv/Scripts/python.exe");
    if !python.exists() {
        return Err("解析環境が未準備です。「初回セットアップ」を実行してください。".into());
    }
    let mut command = Command::new(python);
    hidden(&mut command)
        .arg(source_root(app)?.join("analysis/cli.py"))
        .arg("--runtime")
        .arg(runtime)
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8")
        .env("HF_HUB_OFFLINE", "1")
        .env("TRANSFORMERS_OFFLINE", "1")
        .env("HF_HUB_DISABLE_TELEMETRY", "1")
        .stdin(Stdio::piped());
    Ok(command)
}

fn call_worker<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    request: Value,
) -> Result<Value, String> {
    let mut child = worker(app)?
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;
    child
        .stdin
        .take()
        .ok_or("stdin unavailable")?
        .write_all(request.to_string().as_bytes())
        .map_err(|e| e.to_string())?;
    let output = child.wait_with_output().map_err(|e| e.to_string())?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let response: Value = stdout
        .lines()
        .rev()
        .find_map(|line| serde_json::from_str(line).ok())
        .ok_or_else(|| {
            format!(
                "解析プロセスから応答がありません: {}",
                String::from_utf8_lossy(&output.stderr)
            )
        })?;
    if output.status.success() && response["ok"] == true {
        Ok(response["value"].clone())
    } else {
        Err(response["error"]
            .as_str()
            .unwrap_or("解析に失敗しました")
            .to_string())
    }
}

#[tauri::command]
pub async fn choose_path<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    kind: String,
) -> Result<Option<String>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let dialog = rfd::FileDialog::new();
        let path = match kind.as_str() {
            "source" => dialog
                .add_filter("音楽・動画", &["mp3", "mp4", "m4a", "wav", "flac"])
                .pick_file(),
            "project" | "folder" => dialog.pick_folder(),
            "lyrics" => dialog.add_filter("歌詞", &["txt"]).pick_file(),
            _ => return Err("選択種別が不正です。".into()),
        };
        if let Some(path) = path {
            let state = app.state::<Workspace>();
            let path = fs::canonicalize(path).map_err(|e| e.to_string())?;
            if kind == "project" {
                if !path.join("project.json").is_file() {
                    return Err("project.json があるフォルダーを選んでください。".into());
                }
                grant(&app, &state, &path)?;
                crate::library::restore(
                    &app.path()
                        .app_data_dir()
                        .map_err(|e| e.to_string())?
                        .join("library"),
                    &path,
                )?;
            } else {
                state
                    .approved
                    .lock()
                    .map_err(|e| e.to_string())?
                    .insert(path.clone());
            }
            Ok(Some(path.to_string_lossy().to_string()))
        } else {
            Ok(None)
        }
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub async fn workspace_operation<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    operation: String,
    mut args: Value,
) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let state = app.state::<Workspace>();
        let _guard = state.operation.lock().map_err(|e| e.to_string())?;
        let mut deletion_job = if operation == "delete_analysis" {
            Some(state.job.lock().map_err(|e| e.to_string())?)
        } else {
            None
        };
        if let Some(job) = deletion_job.as_mut() {
            assert_idle(job)?;
        }
        match operation.as_str() {
            "create" => {
                approved(&state, args["source"].as_str().ok_or("source missing")?)?;
                let parent = app
                    .path()
                    .document_dir()
                    .map_err(|e| e.to_string())?
                    .join("Music Sweeper")
                    .join("Projects");
                fs::create_dir_all(&parent).map_err(|e| e.to_string())?;
                args["parent"] = json!(parent);
            }
            "snapshot" | "save" | "export" | "delete_analysis" => {
                approved(&state, args["root"].as_str().ok_or("root missing")?)?;
            }
            _ => return Err("操作が不正です。".into()),
        }
        let result = call_worker(&app, json!({"operation": operation, "args": args}))?;
        if operation == "create" {
            grant(
                &app,
                &state,
                Path::new(result["root"].as_str().ok_or("root missing")?),
            )?;
        }
        if operation == "create" || operation == "snapshot" {
            let root = Path::new(result["root"].as_str().ok_or("root missing")?);
            crate::library::remember(
                &app.path()
                    .app_data_dir()
                    .map_err(|e| e.to_string())?
                    .join("library"),
                root,
            )?;
        }
        Ok(result)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub async fn saved_projects<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
) -> Result<Vec<Value>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let state = app.state::<Workspace>();
        let _guard = state.operation.lock().map_err(|e| e.to_string())?;
        let parent = app
            .path()
            .document_dir()
            .map_err(|e| e.to_string())?
            .join("Music Sweeper/Projects");
        let registry = app
            .path()
            .app_data_dir()
            .map_err(|e| e.to_string())?
            .join("library");
        let projects = crate::library::list(&parent, &registry)?;
        for project in &projects {
            grant(
                &app,
                &state,
                Path::new(project["root"].as_str().ok_or("root missing")?),
            )?;
        }
        Ok(projects)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub async fn remove_saved_project<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    root: String,
) -> Result<(), String> {
    tauri::async_runtime::spawn_blocking(move || {
        let state = app.state::<Workspace>();
        let _guard = state.operation.lock().map_err(|e| e.to_string())?;
        let root = approved(&state, &root)?;
        crate::library::hide(
            &app.path()
                .app_data_dir()
                .map_err(|e| e.to_string())?
                .join("library"),
            &root,
        )
    })
    .await
    .map_err(|e| e.to_string())?
}

fn assert_idle(job: &mut Option<Job>) -> Result<(), String> {
    if let Some(active) = job {
        if active
            .child
            .try_wait()
            .map_err(|e| e.to_string())?
            .is_none()
        {
            return Err("実行中の処理が終わるまでお待ちください。".into());
        }
    }
    Ok(())
}

#[tauri::command]
pub fn start_analysis<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    root: String,
    options: Value,
    state: State<Workspace>,
) -> Result<Value, String> {
    let root = approved(&state, &root)?;
    let mut job = state.job.lock().map_err(|e| e.to_string())?;
    assert_idle(&mut job)?;
    let started = call_worker(
        &app,
        json!({"operation": "start_job", "args": {"root": root, "options": options}}),
    )?;
    *job = None;
    Ok(started)
}

#[tauri::command]
pub fn runtime_status<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<Value, String> {
    let runtime = runtime_root(&app)?;
    let ready = fs::read_to_string(runtime.join("ready.json"))
        .ok()
        .and_then(|text| serde_json::from_str::<Value>(&text).ok());
    let complete = ready
        .as_ref()
        .is_some_and(|v| v["structure"] == "harmonix-all")
        && ready.as_ref().is_some_and(|v| v["vocalEvents"].is_string())
        && runtime
            .join("models/vocal-events/model.safetensors")
            .is_file()
        && runtime.join("venv/Scripts/python.exe").is_file();
    let chord_mini_ready = runtime.join("chordmini/installation.json").is_file()
        && runtime.join("chordmini/venv/Scripts/python.exe").is_file();
    Ok(
        json!({"path": runtime, "ready": complete, "details": ready, "chordMiniReady": chord_mini_ready}),
    )
}

#[tauri::command]
pub fn setup_runtime<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<Workspace>,
    chord_mini: Option<bool>,
) -> Result<(), String> {
    let mut job = state.job.lock().map_err(|e| e.to_string())?;
    assert_idle(&mut job)?;
    let runtime = runtime_root(&app)?;
    fs::create_dir_all(&runtime).map_err(|e| e.to_string())?;
    if runtime.join("venv/Scripts/python.exe").exists()
        && call_worker(&app, json!({"operation": "latest_job"}))?["running"] == true
    {
        return Err("解析中です。完了または中止後にセットアップしてください。".into());
    }
    let log_path = runtime.join("setup.log");
    let log = fs::File::create(&log_path).map_err(|e| e.to_string())?;
    let script = if chord_mini.unwrap_or(false) {
        "scripts/setup-chordmini.ps1"
    } else {
        "scripts/setup-analysis.ps1"
    };
    let child = hidden(
        Command::new("powershell")
            .args(["-NoProfile", "-ExecutionPolicy", "Bypass", "-File"])
            .arg(source_root(&app)?.join(script))
            .arg("-RuntimeRoot")
            .arg(&runtime),
    )
    .env_remove("HF_HUB_OFFLINE")
    .env_remove("TRANSFORMERS_OFFLINE")
    .stdout(log.try_clone().map_err(|e| e.to_string())?)
    .stderr(log)
    .spawn()
    .map_err(|e| e.to_string())?;
    *job = Some(Job {
        child,
        root: None,
        log: log_path,
        kind: "setup",
    });
    Ok(())
}

#[tauri::command]
pub fn job_status<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<Workspace>,
) -> Result<Value, String> {
    let mut job = state.job.lock().map_err(|e| e.to_string())?;
    if let Some(active) = job.as_mut() {
        let exit = active.child.try_wait().map_err(|e| e.to_string())?;
        let text = fs::read_to_string(&active.log).unwrap_or_default();
        let tail: String = text
            .chars()
            .rev()
            .take(3000)
            .collect::<String>()
            .chars()
            .rev()
            .collect();
        let result = Ok(
            json!({"running": exit.is_none(), "success": exit.map(|s| s.success()), "kind": active.kind, "log": tail}),
        );
        if exit.is_some() {
            *job = None;
        }
        result
    } else {
        if !runtime_root(&app)?.join("venv/Scripts/python.exe").exists() {
            return Ok(json!({"running": false, "kind": null, "log": ""}));
        }
        call_worker(&app, json!({"operation": "latest_job"}))
    }
}

#[tauri::command]
pub fn cancel_job<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<Workspace>,
    job_id: Option<String>,
) -> Result<(), String> {
    let mut job = state.job.lock().map_err(|e| e.to_string())?;
    if let Some(job) = job.as_mut() {
        stop_job(job)?;
    } else if let Some(job_id) = job_id {
        call_worker(
            &app,
            json!({"operation": "cancel_job", "args": {"jobId": job_id}}),
        )?;
    }
    Ok(())
}

#[tauri::command]
pub async fn next_ui_request<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || {
        if !runtime_root(&app)?.join("venv/Scripts/python.exe").exists() {
            return Ok(Value::Null);
        }
        let request = call_worker(&app, json!({"operation": "next_ui_request"}))?;
        if let Some(root) = request["root"].as_str() {
            let state = app.state::<Workspace>();
            grant(&app, &state, Path::new(root))?;
        }
        Ok(request)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub async fn ack_ui_request<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    request_id: String,
    state: String,
    message: Option<String>,
) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let result = call_worker(&app, json!({"operation": "ack_ui_request", "args": {"requestId": request_id, "state": state, "message": message}}))?;
        if result["state"] == "applied" {
            if let Some(window) = app.get_webview_window("main") {
                window.unminimize().map_err(|e| e.to_string())?;
                window.show().map_err(|e| e.to_string())?;
                window.set_focus().map_err(|e| e.to_string())?;
            }
        }
        Ok(result)
    }).await.map_err(|e| e.to_string())?
}

#[tauri::command]
pub fn read_lyrics(path: String, state: State<Workspace>) -> Result<String, String> {
    let path = approved(&state, &path)?;
    if fs::metadata(&path).map_err(|e| e.to_string())?.len() > 400_000 {
        return Err("歌詞ファイルは400KB以内にしてください。".into());
    }
    fs::read_to_string(path)
        .map(|s| s.trim_start_matches('\u{feff}').to_string())
        .map_err(|e| e.to_string())
}
