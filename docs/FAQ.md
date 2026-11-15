# ScreenMirror FAQ and Troubleshooting

[English](FAQ.md) · [ខ្មែរ](FAQ_KM.md) · [Back to README](../README.md)

## Why is my Android device not listed?

1. Connect the device with a data-capable USB cable or complete Wireless ADB pairing and connection.
2. Enable USB debugging and accept the authorization prompt on the unlocked phone.
3. Open **Devices** and choose **Refresh**. If the ADB server is stopped, choose **Start ADB server**.
4. On Windows, check whether the device needs its OEM USB driver.
5. A device marked `unauthorized` is not ready for mirroring; approve the prompt on the phone and refresh.

## ADB shows `unauthorized`. What should I do?

Unlock the phone and accept the USB debugging authorization prompt for this computer. If the prompt is not visible, reconnect the cable and refresh. Only authorize computers you trust. ScreenMirror does not bypass Android's authorization.

## Why did wireless pairing fail?

- Use the current pairing `host:port` and one-time code displayed by the phone's Wireless debugging pairing screen.
- Pair first, then replace the target with the phone's connection `host:port` and choose **Connect**. These endpoints can use different ports.
- Confirm that the PC and phone can reach each other on a trusted network and that no network isolation blocks the connection.
- Pairing codes expire and should not be reused. The app masks and clears the code, but ADB receives it as a process argument.

## Why will mirroring not start?

- Select a device in the ready/`device` state.
- Wait for scrcpy capability discovery to finish and ensure no session is already running.
- Check the **Diagnostics** page for the detected scrcpy version and recent errors.
- In the mirror profile, choose a codec supported by the bundled scrcpy. Advanced controls only include options discovered from that executable.
- The project has not been hardware-validated across Android models or versions; a failure may be device- or OS-specific.

## Why does the scrcpy window open separately?

That is the current design. scrcpy owns native video decoding, rendering, and its supported input controls. ScreenMirror manages ADB, settings, and process lifecycle; it does not embed the video surface.

## Where did my screenshot go?

The destination is selected in the Windows save dialog. ScreenMirror captures a PNG and lists up to 12 recent captures during the current app session. It does not scan folders or keep a persistent screenshot library.

## How do audio and recording work?

Audio forwarding is enabled by default when supported by the device and scrcpy. Recording is configured with an output path in the mirror profile; the path is passed to scrcpy and applies when a new mirror session starts. Recording stops with that session. There is no live recording toggle in ScreenMirror, and hardware behavior has not been tested.

## What if ScreenMirror closes or ADB/scrcpy stops unexpectedly?

While the UI is open, check **Diagnostics** for process output and current versions. Reopen the app and retry only after confirming the device state. The current UI does not provide a persistent crash-report viewer; capture any visible error text when reporting a problem.

## How do I stop mirroring and close the app safely?

Choose **Stop session** or close the scrcpy window. To exit the application, close ScreenMirror normally; it coordinates ADB and scrcpy process shutdown. Avoid force-ending the process unless it is unresponsive.

## Is there a public prebuilt Windows download?

A downloadable GitHub Release could not be verified. The supplied repository was private during this documentation review, and its local `dist-easy-run` folder is not a published release. Check the repository's [Releases page](https://github.com/cyberscout168/kh3mren-mirror/releases) if you have access.

## Does ScreenMirror support macOS or Linux?

No. The current desktop UI, bundled scrcpy runtime, and packaging target Windows x64. macOS/Linux ADB files remain in the workspace but do not constitute supported desktop releases.

## How can I report a question or issue?

Contact the maintainer at [sankhemren117@gmail.com](mailto:sankhemren117@gmail.com). Include the Windows version, ScreenMirror/ADB/scrcpy versions, device state, and relevant Diagnostics messages. Do not send pairing codes, passwords, or other secrets.
