# ScreenMirror User Guide

[English](USER_GUIDE.md) · [ខ្មែរ](USER_GUIDE_KM.md) · [Back to README](../README.md)

This guide describes controls present in the current Windows application. Android hardware behavior has not been validated; device authorization and supported scrcpy options can vary by phone and Android version.

## 1. Start the application

- From source, run `python -m screenmirror.main` inside the project's virtual environment.
- From a complete Windows package, run `ScreenMirror.exe` from its extracted `ScreenMirror` folder.
- ScreenMirror checks the host-matched ADB executable and discovers bundled scrcpy capabilities during startup. The Devices page provides ADB server controls and refresh actions.
- To switch languages, open **Settings** and choose **English** or **ខ្មែរ**. The choice is saved for the next launch.

## 2. Connect by USB

1. On Android, enable Developer options and USB debugging. The names and navigation differ by manufacturer.
2. Connect the phone with a data-capable USB cable.
3. Unlock the phone and accept its USB debugging authorization prompt for this computer. Do not authorize an untrusted computer.
4. Open **Devices** and use **Refresh** if the phone is not listed. The device must be in the ready/`device` state before mirroring or screenshots.
5. Select the device card. The dashboard and Mirroring page show the current selection and state.

On Windows, some devices require an OEM USB driver. ScreenMirror includes ADB tools but does not install phone-specific drivers.

## 3. Connect with Wireless ADB

Use this only on a trusted network.

1. On the phone, enable **Wireless debugging** and open its pairing-code workflow.
2. In **Devices → Wireless ADB**, enter the pairing endpoint (`host:port`) shown by the phone and the current pairing code.
3. Choose **Pair device**. The code field is masked and cleared before the request is submitted.
4. After pairing succeeds, replace the target with the connection endpoint (`host:port`) shown by the phone and choose **Connect**. Pairing and connection endpoints may use different ports.
5. Refresh the device list and select the connected device.
6. To disconnect, select the wireless device and choose **Disconnect selected**.

The pairing code is redacted from captured ADB output, but it is passed to ADB as a process argument and may be observable to local process-inspection tools while the command runs. Avoid shared or untrusted computers and networks.

## 4. Start and stop mirroring

1. Select an authorized device in **Devices**.
2. Open **Mirroring** and choose **Start mirroring**.
3. scrcpy opens a separate native window. Use that window for the mirrored display and scrcpy's supported input controls. ScreenMirror's UI does not render the video stream itself.
4. To stop, choose **Stop session** in ScreenMirror or close the scrcpy window.

Only one scrcpy session is supported at a time. If Start is unavailable, confirm that a ready device is selected, ADB is not busy, and a session is not already active.

## 5. Configure the mirror profile

Open **Edit profile** from Mirroring or Settings. The standard profile includes:

- maximum resolution (default 720p);
- maximum frame rate (default 30 FPS);
- video bitrate (default 4M);
- a video codec supported by the bundled scrcpy (default H.264);
- audio forwarding (enabled by default);
- fullscreen, keep-device-awake, and screen-off options;
- an optional recording destination.

Save changes before starting the next session. Advanced settings are populated from the bundled scrcpy's own `--help` output; only discovered options are offered. Unsupported options from another scrcpy release may not appear.

## 6. Capture a screenshot

1. Select an authorized, ready device.
2. Open **Screenshots** and choose **Save screenshot…**.
3. Select a destination in the Windows save dialog.
4. ScreenMirror captures a PNG using ADB and lists the latest captures for the current application session. The list is temporary; the app does not scan existing files or maintain a screenshot library.

The native Windows file dialog may use the Windows display language.

## 7. Configure recording

In the mirror profile, enter or browse to an `.mp4` or `.mkv` destination. When a destination is configured, it is passed to scrcpy for new mirror sessions. Recording starts with the session and ends when that scrcpy session stops; ScreenMirror does not provide a live recording toggle or encode video itself.

Clear the recording destination in the profile if you do not want it applied to subsequent sessions. Recording support and output depend on the device and bundled scrcpy; no Android hardware recording test has been completed.

## 8. Diagnostics and safe shutdown

- Open **Diagnostics** to see the selected ADB executable, ADB version, scrcpy capability status, selected device, and a bounded list of recent messages.
- For a normal exit, close the ScreenMirror window. The application coordinates asynchronous ADB and scrcpy shutdown before it exits.
- Do not delete or move files from a packaged app's `_internal` folder while the app is running.

For common connection and startup problems, see the [FAQ](FAQ.md).
