#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    #[cfg(windows)]
    if hodomia_lib::run_if_requested() {
        return;
    }
    hodomia_lib::run();
}
