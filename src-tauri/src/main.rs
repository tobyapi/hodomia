#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    #[cfg(windows)]
    if music_sweeper_lib::run_if_requested() {
        return;
    }
    music_sweeper_lib::run();
}
