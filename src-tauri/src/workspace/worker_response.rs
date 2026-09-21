use serde_json::Value;
use std::process::Output;

pub(super) fn decode(output: Output) -> Result<Value, String> {
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
