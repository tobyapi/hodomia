import { useEffect, useRef } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { isTauri } from "@tauri-apps/api/core";

/** Keep the window open if saving fails; normal shutdown cancels its worker. */
export function useCloseSave(dirty: boolean, save: () => Promise<void>, onError: (error: string) => void) {
  const current = useRef({ dirty, save, onError });
  current.current = { dirty, save, onError };
  useEffect(() => {
    if (!isTauri()) return;
    let disposed = false, closing = false;
    const pending = getCurrentWindow().onCloseRequested(async event => {
      event.preventDefault();
      if (disposed || closing) return;
      closing = true;
      try {
        if (current.current.dirty) await current.current.save();
        await getCurrentWindow().destroy();
      } catch (error) {
        current.current.onError("終了処理に失敗しました。変更は保持しています: " + String(error));
      } finally { closing = false; }
    });
    pending.catch(error => { if (!disposed) current.current.onError(String(error)); });
    return () => { disposed = true; void pending.then(unlisten => unlisten()).catch(() => {}); };
  }, []);
}
