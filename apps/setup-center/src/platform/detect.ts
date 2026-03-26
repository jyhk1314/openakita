// Runtime platform detection constants.
// Extracted to a separate file to avoid circular dependencies.

export const IS_TAURI =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export const IS_CAPACITOR =
  typeof window !== "undefined" &&
  "Capacitor" in window &&
  !IS_TAURI;

export const IS_WEB = !IS_TAURI && !IS_CAPACITOR;

/** 桌面 WebView 在 Windows 上运行时 UA 含 Windows（研发中心终端仅支持此组合）。 */
export const IS_WINDOWS =
  typeof navigator !== "undefined" && /Windows/i.test(navigator.userAgent);
