# ScreenMirror Installation Guide

[English](INSTALLATION.md) · [ខ្មែរ](INSTALLATION_KM.md) · [Back to README](../README.md)

## Status of downloads

The GitHub repository is private, so cloning the source requires authorization. The project source is available in the repository to authorized users. No downloadable GitHub Release package has been verified.

No downloadable GitHub Release package could be verified. The locally built `dist-easy-run\ScreenMirror` directory is not a published release and should not be treated as one.

## System requirements

| Requirement | Details |
|---|---|
| Desktop OS | Windows x64 only. Windows 10 build 19045 was used for development and package smoke testing. No formal minimum Windows version is declared. |
| Android device | A device with ADB debugging enabled and authorization granted to this PC. No Android-version compatibility matrix is published. |
| USB | A data-capable USB cable; Windows may also need the device manufacturer's USB driver. |
| Wireless | The phone must provide Wireless debugging/pairing. The phone and PC must be able to communicate on a trusted network. |
| Python for source use | Python 3.13.3 was used for the current test/build; the project does not declare a minimum Python version. |
| Bundled runtime | Windows Platform-Tools 37.0.1 and scrcpy 5.0.1 are included. Separate ADB/scrcpy installation is not required for this source/package layout. |
| CPU/RAM/GPU | No minimum has been measured or published. Mirroring performance depends on the device, resolution, network, and graphics drivers. |

## Method A — Prebuilt application

**No release asset has been verified.** See the [Releases page](https://github.com/cyberscout168/kh3mren-mirror/releases) if you have access; use this method only after the maintainer publishes a Windows x64 package.

When an official package is available:

1. Download the Windows x64 release archive from the repository's Releases page.
2. Extract the **whole** `ScreenMirror` folder to a writable location.
3. Keep `ScreenMirror.exe` together with its `_internal` directory and bundled runtime files.
4. Run `ScreenMirror.exe`.
5. If Windows shows an origin/security prompt, verify the download source before allowing it. The current local build is not digitally signed.

Do not copy the local `dist-easy-run` folder as though it were a public release. It is only a development-machine build and has not been validated on a clean Windows installation.

## Method B — Run from source

The following commands match the project layout. You need access authorization to clone the private GitHub repository.

1. Install Git and Python 3.13 (64-bit recommended; 3.13.3 was used for current verification).
2. Clone the repository and enter the project folder:

   ```powershell
   git clone https://github.com/cyberscout168/kh3mren-mirror.git
   Set-Location kh3mren-mirror
   ```

3. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation scripts, call the environment's executable directly instead of changing the machine-wide execution policy:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m screenmirror.main
   ```

4. Install the dependencies listed by the project:

   ```powershell
   python -m pip install -r requirements.txt
   ```

   The manifest pins PySide6 to `>=6.8,<7` and PyInstaller to `>=6.10,<7`.

5. Start ScreenMirror:

   ```powershell
   python -m screenmirror.main
   ```

The application selects `platform-tools(Windows)\adb.exe` and the bundled Windows x64 scrcpy runtime. Do not copy or run the Linux/macOS ADB executables on Windows.

## Build a Windows package

From the project root, run:

```powershell
.\build_windows.ps1
```

The script uses the project's `.venv`, `ScreenMirror.spec`, and bundled runtime directories. It writes the one-folder build to:

```text
dist-easy-run\ScreenMirror\
```

Launch it with:

```powershell
.\dist-easy-run\ScreenMirror\ScreenMirror.exe
```

The build script replaces that output folder and updates the desktop `ScreenMirror` shortcut. Close the packaged application before rebuilding. Distribute the complete `ScreenMirror` folder as an archive; do not distribute the `.exe` by itself.

## First Android connection

Installation alone does not authorize an Android device. Enable Developer options and USB debugging on the device, connect it, then accept the device's debugging authorization prompt. For wireless pairing, use the host/port and one-time pairing code displayed by the phone's Wireless debugging screen. See the [User Guide](USER_GUIDE.md) for the full workflow.

## If startup fails

- Confirm the source tree is complete and dependencies installed in the active `.venv`.
- Run `python -m screenmirror.main` from PowerShell so Python startup errors remain visible.
- For a packaged build, keep `_internal` beside `ScreenMirror.exe` and re-extract the full archive if files are missing.
- Use the in-app Diagnostics page for ADB/scrcpy paths, detected versions, and recent application messages.
- If ADB cannot find a USB device, check the USB cable, debugging authorization, and any required Windows device driver.

## Licensing

The supplied GitHub repository contains an MIT `LICENSE`; third-party ADB and scrcpy distributions have their own notice/license files. Preserve and review applicable notices before redistribution.
