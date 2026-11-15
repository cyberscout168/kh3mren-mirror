<p align="center">
  <img src="assets/screenmirror.png" width="96" alt="ScreenMirror application icon">
</p>

<h1 align="center">ScreenMirror</h1>

<p align="center"><strong>Manage Android devices and mirror their screens to Windows with ADB and scrcpy.</strong></p>
<p align="center"><a href="README.md">English</a> · <a href="README_KM.md">ខ្មែរ</a></p>
<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%20x64-0078D4" alt="Windows x64">
  <img src="https://img.shields.io/badge/license-MIT-2ea44f" alt="MIT License">
  <img src="https://img.shields.io/badge/UI-English%20%7C%20Khmer-5849be" alt="English and Khmer UI">
</p>

ScreenMirror is an MIT-licensed **Windows screen mirroring** project for **Android to Windows** device management. This **Python Screen Mirroring Application** and **PySide6 Desktop Application** uses ADB for discovery and connections, then launches the bundled Windows x64 scrcpy process for native screen display, input, and optional recording. Its English/Khmer UI makes the project useful as Khmer screen mirroring software as well as an international Android screen mirroring tool. The GitHub repository is currently private, so the MIT-licensed source is not publicly accessible yet.

> **Repository access:** This GitHub repository is private; cloning the source requires authorization. No downloadable GitHub Release package has been verified. See the installation guide for source and package instructions.

## What it can do

- Discover authorized USB and wireless Android devices through bundled Windows Platform-Tools.
- Start and stop the ADB server, pair/connect/disconnect wireless devices, and inspect device state.
- Start scrcpy mirroring in a separate native window; ScreenMirror does not decode or render video frames itself.
- Configure resolution, frame rate, bitrate, a codec supported by the bundled scrcpy, audio forwarding, fullscreen, stay-awake, and screen-off options.
- Capture a PNG screenshot from a selected device.
- Configure scrcpy recording for mirror sessions (MP4/MKV options are presented by the UI).
- Choose English or Khmer UI; the selection is saved between launches.
- Inspect current service details and bounded in-app diagnostics.

### Implemented does not mean hardware-verified

The Python unit suite currently has **49 passing tests**. A Windows package was also built and launched on the development machine. These checks do **not** verify Android compatibility: no physical Android device was used to test discovery, pairing, mirroring, input, audio, screenshots, or recording.

## Platform and requirements

- **Supported desktop target:** Windows x64. Windows 10 (build 19045) was used for development and package smoke testing. The project does not declare a formal minimum Windows version.
- **Android:** a device with ADB debugging enabled and authorization granted to this computer. The project does not publish an Android-version compatibility matrix.
- **Wireless ADB:** the phone and PC must be able to reach each other over a trusted network; the phone must expose Wireless debugging/pairing for the chosen workflow.
- **Python:** Python 3.13.3 was used for the latest local tests/build. A minimum supported Python version is not declared.
- **Bundled tools:** Windows Platform-Tools 37.0.1 and scrcpy 5.0.1 are included in the source/package. The application does not require the user to separately install ADB or scrcpy.
- **Hardware baseline:** no specific CPU, RAM, or GPU minimum has been measured or published.

The macOS and Linux ADB folders are retained in the workspace; they do not mean the desktop UI, scrcpy runtime, or packaging is supported on those systems.

## Get ScreenMirror

### Prebuilt application

No downloadable GitHub Release package could be verified from the accessible repository state. The repository is private, and the local `dist-easy-run` build is not a published release. Check the [Releases page](https://github.com/cyberscout168/kh3mren-mirror/releases) only if you have repository access and the maintainer has published an asset.

When a Windows x64 package is published, download and extract the **complete ScreenMirror folder** and run `ScreenMirror.exe` from that folder. Do not move the executable by itself: the one-folder build depends on its `_internal` directory and bundled tools. The executable is not digitally signed in the current local build, so Windows may display a security warning; only run a package obtained from a source you trust.

### Run from source

These commands have been checked against the project layout. You need access to the private GitHub repository to clone the source.

```powershell
git clone https://github.com/cyberscout168/kh3mren-mirror.git
Set-Location kh3mren-mirror

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m screenmirror.main
```

`requirements.txt` installs PySide6 and PyInstaller. For a build from source, run this from PowerShell:

```powershell
.\build_windows.ps1
.\dist-easy-run\ScreenMirror\ScreenMirror.exe
```

The build script replaces the output folder `dist-easy-run\ScreenMirror` and updates the `ScreenMirror` desktop shortcut. Close a running packaged app before rebuilding.

See the [documentation index](docs/README.md), [installation guide](docs/INSTALLATION.md), [user guide](docs/USER_GUIDE.md), and [FAQ](docs/FAQ.md).

## Screenshots and demonstration

No ScreenMirror UI screenshots or demonstration videos are currently included. The repository contains the application icon and bundled scrcpy assets, but those are not screenshots of ScreenMirror. Once captured from the real application, recommended images are:

1. The Windows dashboard and authorized device list.
2. Wireless pairing and connection controls (with the pairing code hidden).
3. Mirror profile and advanced settings.
4. Screenshot and recording destination workflows.

Place genuine, current captures under `docs/images/` and add descriptive alt text. Do not use mockups or third-party scrcpy images as if they were ScreenMirror screenshots.

## Project architecture

| Component | Responsibility |
|---|---|
| `screenmirror/ui/main_window.py` | PySide6 pages, controls, dialogs, language selection, and status display |
| `screenmirror/adb.py` | Host-matched ADB discovery and asynchronous process operations |
| `screenmirror/scrcpy.py` | scrcpy capability discovery, command construction, and session lifecycle |
| `screenmirror/settings.py` | Mirror, dynamic-option, and UI-language persistence |
| `screenmirror/i18n.py` | English/Khmer strings, dynamic messages, and font selection |
| `platform-tools(Windows)/` | Bundled Windows ADB and related Android platform tools |
| `third_party/scrcpy/` | Bundled Windows x64 scrcpy 5.0.1 runtime |
| `tests/` | Unit tests, including process lifecycle and localization tests |
| `src/` | Preserved legacy C++/Qt sources; not the current Python app entry point |

ADB and scrcpy run as separate processes. Screenshot capture uses asynchronous ADB output. Video rendering and device input are handled by scrcpy's native window, not by an in-app Python video pipeline.

## Verification and limitations

- **Automated:** `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` — 49 passed on the development workspace.
- **Package:** `.\build_windows.ps1` completed and the local packaged window launched on Windows.
- **Not verified:** Android hardware behavior, clean-machine installation, signed distribution, and macOS/Linux desktop support.
- Recording begins when a mirror session starts if a destination is configured; it is not an in-app live recording toggle.
- Native Windows file dialogs and raw operating-system/process error details may appear in the Windows display language or English.
- Wireless pairing codes are masked and cleared by the UI and redacted from ADB output, but are passed as process arguments and may be observable to local process-inspection tools.

See the [English installation guide](docs/INSTALLATION.md), [English user guide](docs/USER_GUIDE.md), and [English FAQ](docs/FAQ.md). Khmer versions are linked at the top of each document.

## License

The supplied GitHub repository contains an [MIT License](https://github.com/cyberscout168/kh3mren-mirror/blob/main/LICENSE). Preserve its notice when redistributing. Third-party components also have their own license/notice files; review those before redistribution.

## Contact

For questions, technical discussions, feedback, or collaboration opportunities, contact the project maintainer at [**sankhemren117@gmail.com**](mailto:sankhemren117@gmail.com).

## Suggested GitHub repository topics

`screen-mirroring` · `android` · `windows` · `python` · `pyside6` · `adb` · `scrcpy` · `open-source` · `desktop-application` · `khmer`

These are recommendations for repository settings; documentation changes do not change GitHub topics or repository visibility.
