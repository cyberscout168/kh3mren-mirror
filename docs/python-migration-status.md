# ScreenMirror Python Migration Status

> **Historical snapshot (2026-11-14):** This report predates later lifecycle fixes and Khmer localization. Treat its implementation, test, and package status as historical; see the [current README](../README.md) and [documentation index](README.md) for the latest verified information.

Date: 2026-11-14

## Supported desktop platform

The currently supported Python desktop app and packaged release target Windows only. The bundled scrcpy runtime and PyInstaller build are Windows-specific. Host-aware ADB selection and the retained Linux/macOS Platform-Tools are not a claim of supported Linux/macOS application or mirroring releases.

## Preserved

- Original C++/Qt sources under `src/` remain unchanged as a reference implementation.
- Existing SDK analysis and milestone documentation remain in `docs/`.
- Host-specific Platform-Tools bundles remain unchanged.

## Implemented

- Python 3.13.3 virtual environment under `.venv`.
- PySide6 Widgets application structure under `screenmirror/`.
- Host-aware ADB selection code for Windows, macOS, and Linux; only the Windows desktop app/package is currently supported.
- Safe argument-based ADB process execution.
- ADB version check and server lifecycle.
- USB device discovery and state parsing.
- Wireless ADB connect, pair, and disconnect operations.
- Device table with serial, state, model, and transport ID.
- Diagnostics log panel.
- Real screenshot capture through `adb exec-out screencap -p`.
- scrcpy 5.0.1 official Windows x64 runtime integration.
- Start/stop mirroring controls for an authorized selected device.
- Capability-aware scrcpy command construction using the bundled executable's `--help` output.
- Persistent Qt settings for resolution, FPS, bitrate, available video codec, audio, fullscreen, stay-awake, screen-off, and recording destination.
- Optional per-session recording via scrcpy's verified recording options.
- Unit tests for command arguments, whitespace-safe serial/path handling, codec rejection, and invalid settings.
- Standard-library parser test.
- scrcpy settings/command-builder tests.
- PyInstaller one-folder Windows build including Windows Platform-Tools and scrcpy runtime files.

## Dependency state

- Python: 3.13.3.
- PySide6: 6.12.0.
- PyInstaller: 6.22.3.
- No Qt Online Installer or Qt account was used for the Python migration.

## Verification

The results below are historical results recorded on 2026-11-14; they were not re-run as part of the later lifecycle-fix task.

- Python syntax compilation: passed.
- ADB parser test: passed (`1` test).
- PySide6 GUI offscreen smoke test: passed.
- PyInstaller build: passed.
- Packaged GUI offscreen smoke test: passed.
- Packaged scrcpy executable version check: passed (`5.0.1`).
- ADB executable detection: passed; Windows Platform-Tools 37.0.1 was found.
- Physical Android hardware: not verified; no device was connected.

## Not implemented

- Physical-device end-to-end scrcpy mirroring, input, audio, and recording: not verified; no device was connected.
- Keyboard/mouse control UI and protocol.
- Audio streaming.
- Screen recording.
- Multiple concurrent mirroring sessions.
- Hardware-accelerated video rendering.
- In-app video rendering; the current design uses scrcpy's own native window and its built-in input path.

scrcpy is now the selected and bundled mirroring engine. Hardware verification remains pending.

## Package output

The pre-existing build under `dist/ScreenMirror/` was preserved. The updated candidate was freshly packaged to `build/release-candidate/ScreenMirror/ScreenMirror.exe`; it includes Windows Platform-Tools 37.0.1 and scrcpy 5.0.1 (including the supplied `LICENSE.txt` and server). The candidate launched and remained running in a four-second offscreen process smoke test. ADB and scrcpy version checks passed from the packaged directory. It has not been tested against a connected Android device or on another Windows machine.

Packaging command:

```powershell
.\.venv\Scripts\pyinstaller.exe --noconfirm --distpath build\release-candidate --workpath build\pyinstaller-work ScreenMirror.spec
```
