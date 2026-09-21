use std::io::{Cursor, Write};

pub fn run_if_requested() -> bool {
    let mut args = std::env::args().skip(1);
    if args.next().as_deref() != Some("--capture-parent-window") {
        return false;
    }
    let result = capture(args.next().unwrap_or_default());
    if let Err(error) = result {
        eprintln!("{error}");
        std::process::exit(1);
    }
    true
}

fn capture(id: String) -> Result<(), String> {
    let id: u32 = id.parse().map_err(crate::errors::message)?;
    let parent = parent::verified_pid()?;
    let window = xcap::Window::all()
        .map_err(crate::errors::message)?
        .into_iter()
        .find(|w| w.pid().ok() == Some(parent) && w.id().ok() == Some(id))
        .ok_or("撮影対象のhodomiaウィンドウが見つかりません。")?;
    let image = window.capture_image().map_err(crate::errors::message)?;
    let mut png = Cursor::new(Vec::new());
    image
        .write_to(&mut png, xcap::image::ImageFormat::Png)
        .map_err(crate::errors::message)?;
    std::io::stdout()
        .write_all(png.get_ref())
        .map_err(crate::errors::message)
}

mod parent;
mod process;
