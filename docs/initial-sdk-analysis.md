# Initial SDK Inspection and Technical Report

> **Historical snapshot (2026-11-14):** This report records an early workspace inspection before the current Python ScreenMirror application was implemented. Do not use its statements about missing application source or features as the current project status. See the [current README](../README.md) and [documentation index](README.md).

Date: 2026-11-14  
Scope: workspace contents only; no implementation or dependency installation performed.

## Executive conclusion

The workspace does not contain three independent mirroring SDKs. It contains three host-platform distributions of Android SDK Platform-Tools, all reporting `Pkg.Revision=37.0.1`:

| Package label | Actual package | Host format | Evidence |
|---|---|---|---|
| SDK 1 (provisional) | `platform-tools(Windows)` | Windows PE executables and DLLs | `adb.exe`, `AdbWinApi.dll`, `AdbWinUsbApi.dll`; NOTICE identifies `sdk-repo-windows-x86-platform-tools.zip` |
| SDK 2 (provisional) | `platform-tools` | Linux ELF binaries and `lib64/libc++.so` | `adb` begins with ELF signature; NOTICE identifies `sdk-repo-linux-platform-tools.zip` |
| SDK 3 (provisional) | `Mac` | macOS universal Mach-O binary and `lib64/libc++.dylib` | `adb` begins with universal Mach-O signature; NOTICE identifies `sdk-repo-darwin-platform-tools.zip` |

All three contain the same functional family: `adb`, `fastboot`, `sqlite3`, `etc1tool`, `hprof-conv`, filesystem tools, runtime libraries, `source.properties`, and a large third-party `NOTICE.txt`. There are no source files, API headers, SDK libraries, mirroring server, encoder, decoder, streaming protocol implementation, UI, or project documentation in the workspace.

## 1. Independent package analysis

### SDK 1 — Windows Platform-Tools

- Structure: flat host-tool bundle, with `adb.exe`, `fastboot.exe`, `sqlite3.exe`, `etc1tool.exe`, `hprof-conv.exe`, filesystem utilities, two ADB USB DLLs, and `libwinpthread-1.dll`.
- Version: `Pkg.Revision=37.0.1`; the executable reports ADB 1.0.41, version `37.0.1-15733141`.
- Supported OS: Windows host, evidenced by PE `.exe` files and Windows DLLs. The package itself does not establish a Windows minimum version beyond the current executable running on Windows 10 in this inspection.
- Android support: ADB is intended for Android devices, but this bundle contains no compatibility matrix for Android API levels. Device behavior depends on device-side ADB and authorization state.
- Interfaces verified from `adb help`: device listing, USB selection, TCP/IP `connect`/`disconnect`, secure `pair`, shell, push/pull, sync, forward/reverse sockets, install/uninstall, logcat, bugreport, and JDWP-related operations.
- Video/audio: no mirroring protocol, video encoder, video decoder, frame transport, or audio capture API was found. Strings such as `video` and `audio` are not evidence of codec support and must not be treated as such.
- Dependencies: Windows system runtime plus the bundled ADB USB DLLs and pthread runtime. No build metadata is supplied.
- Licensing: NOTICE begins with Apache License 2.0 and includes third-party notices. Redistribution requires preserving applicable license and attribution notices; a complete component-by-component audit is still required.
- Limitations: ADB is a control/transport bridge, not a complete screen capture pipeline. Wireless ADB exposes an attack surface if bound or used on an unsafe network.

### SDK 2 — Linux Platform-Tools

- Structure and tool set match SDK 1, but binaries are Linux ELF and the C++ runtime is `lib64/libc++.so`.
- Version: `Pkg.Revision=37.0.1`.
- Supported OS: Linux host is evidenced by ELF binaries and the Linux package name in NOTICE. Distribution-specific runtime and USB permission requirements are not documented in this bundle.
- ADB interfaces, Android-version uncertainty, video/audio limitations, dependency uncertainty, and security considerations are the same as SDK 1.
- This package cannot be selected by the Windows desktop application at runtime; it is a separate release artifact for Linux deployment.

### SDK 3 — macOS Platform-Tools

- Structure and tool set match SDK 1 and SDK 2, with a macOS universal Mach-O `adb` and `lib64/libc++.dylib`.
- Version: `Pkg.Revision=37.0.1`.
- Supported OS: macOS host is evidenced by the universal Mach-O format and Darwin package name in NOTICE. The bundle does not document minimum macOS versions, signing, notarization, or entitlement requirements.
- ADB interfaces, Android-version uncertainty, video/audio limitations, dependency uncertainty, and security considerations are the same as SDK 1.
- This package is a separate macOS deployment artifact, not an interchangeable library for Windows or Linux.

## 2. Comparison matrix

| Evaluation | SDK 1: Windows | SDK 2: Linux | SDK 3: macOS |
|---|---|---|---|
| Architecture | ADB host executable plus USB/runtime DLLs | ADB host executable plus ELF runtime | Universal macOS ADB plus Darwin runtime |
| OS support | Windows host | Linux host | macOS host |
| Android support | ADB protocol; exact API range not stated | ADB protocol; exact API range not stated | ADB protocol; exact API range not stated |
| ADB integration | Strong; executable verified | Strong by package identity; execution not available on Windows | Strong by package identity; execution not available on Windows |
| USB | Yes, through Windows ADB USB components | Yes, subject to Linux USB permissions | Yes, subject to macOS/device authorization |
| Wireless | `connect`, `pair`, `disconnect` verified in help | Same release family; verify on native host | Same release family; verify on native host |
| Video streaming | None supplied | None supplied | None supplied |
| Encoding/decoding | None supplied | None supplied | None supplied |
| Performance | ADB transport performance only; no mirror benchmark | ADB transport performance only; no mirror benchmark | ADB transport performance only; no mirror benchmark |
| Stability | Release binary, but no project-specific SLA or tests | Same | Same |
| Documentation | `source.properties` and NOTICE only | `source.properties` and NOTICE only | `source.properties` and NOTICE only |
| Licensing | Apache 2.0 plus bundled third-party notices; audit required | Same | Same |
| Integration difficulty | Low for process-based ADB manager; no video engine | Low on Linux; separate artifact | Low on macOS; separate artifact |

## 3. Feasibility and recommendations

### What these packages can provide

Use one host-matched Platform-Tools package as the ADB subsystem for:

- device discovery and state tracking;
- USB and TCP/IP ADB sessions;
- secure wireless pairing where supported by the device;
- shell commands and socket forwarding/reverse forwarding;
- file transfer, diagnostics, logcat, and installation workflows.

### What is missing

The workspace has no implementation for Android screen capture, MediaCodec configuration, H.264/H.265 transport, desktop decoding, input injection policy, recording, screenshots, rendering, or UI. The requested application therefore cannot be built from these packages alone.

### Best SDK decisions

- Core ADB/device-management engine: all three are equivalent functionally; select the package matching the host OS and pin the verified revision.
- Video streaming: none of the three. A separate mirroring implementation is required, such as a verified scrcpy-compatible design or an in-house Android capture/MediaCodec agent plus desktop decoder.
- SDKs that should not be used: none should be rejected for their intended host platform; however, do not combine the Windows, Linux, and macOS binaries in one runtime or treat any as a video SDK.
- Combining SDKs: technically reasonable only as platform-specific distribution assets. Combining multiple copies in one process adds no capability. Combining Platform-Tools with an independently licensed capture/codec stack is reasonable after protocol, security, and license review.

## 4. Proposed architecture after approval

Keep ADB process isolation behind an `AdbManager` interface. Add separate modules for `DeviceManager`, `ConnectionManager`, Android capture/encoder agent, transport framing, desktop decoder/rendering, input, recording, screenshots, UI, and diagnostics. The ADB layer should not own video assumptions.

Recommended initial technology direction:

- C++ or Rust for the capture/transport/decoder boundary where latency and predictable buffering matter.
- Qt for a mature cross-platform desktop UI and native rendering integration; evaluate Tauri only if a web UI is strategically important. Avoid Electron for the first performance-critical prototype unless its runtime cost is measured acceptable.
- Android `MediaProjection`/`MediaCodec` must be verified against the target Android versions before committing to exact capture behavior.
- Use hardware decode when available, with a software fallback. H.264 should be the baseline interoperability codec; H.265 is an optional capability requiring device, decoder, and licensing review.
- Use bounded queues, timestamps, frame-drop policy, and explicit latency metrics. Never claim zero latency.

## 5. Roadmap and prototype gates

1. Complete SDK/license and target-device validation.
2. Freeze the cross-platform ADB abstraction and package selection.
3. Build an ADB connection prototype: discovery, authorization, USB, TCP/IP, pairing, reconnect, and multi-device tests.
4. Add one Android capture/encoder path and one desktop decoder/render path for USB.
5. Add wireless transport, then input control.
6. Add measurement-driven buffering and hardware acceleration.
7. Add recording, screenshots, advanced controls, and UI refinement.
8. Run compatibility, soak, security, packaging, and release-license tests.

Phases are intentionally gated: video work should not begin until the ADB/device lifecycle is observable and reliable.

## 6. Performance and benchmark plan

Measure, per device and transport, capture timestamp → encode completion → send → receive → decode → present. Record median, p95, and p99 latency; FPS delivered; dropped frames; bitrate; encode/decode time; CPU/GPU utilization; memory; reconnect time; and thermal/long-run behavior.

Benchmark matrix: USB 2/3 where available, 2.4/5 GHz Wi-Fi, 30/60/90/120 FPS requests, several resolutions and bitrates, hardware/software codec paths, one and multiple devices, and Android versions/devices representative of the target market. Use test patterns with timestamps or a high-speed camera for end-to-end validation; do not infer display latency from ADB command timing.

## 7. Risks and open questions

- The supplied artifacts do not identify the intended Android device range or provide an Android-side capture agent.
- Wireless ADB pairing and TCP exposure require explicit trust, network, and firewall controls.
- H.264/H.265 patent and distribution obligations need legal review independent of the ADB Apache notices.
- macOS signing/notarization, Linux packaging/udev rules, and Windows driver/runtime packaging are not covered by these bundles.
- The current workspace contains no test devices, source project, build system, or native-host documentation.

Before implementation, please confirm whether additional SDK archives or source trees were intended to be uploaded. In particular, the project still needs the mirroring/capture SDK or Android agent, if one exists, plus the target desktop OSes and minimum Android versions.

## 8. Approval gate

No code or dependency installation has been performed. Implementation should begin only after confirming that these three Platform-Tools packages are the intended ADB dependencies and approving a separate choice for the Android capture/video stack.
