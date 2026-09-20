import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { clearMocks } from "@tauri-apps/api/mocks";
import { afterEach, vi } from "vitest";

afterEach(() => { cleanup(); clearMocks(); vi.unstubAllGlobals(); });
