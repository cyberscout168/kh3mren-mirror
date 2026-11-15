"""Safe, host-aware ADB integration for ScreenMirror."""

from __future__ import annotations

import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QProcess, QTimer, Signal


@dataclass(frozen=True, slots=True)
class AdbDevice:
    serial: str
    state: str
    model: str = ""
    product: str = ""
    transport_id: str = ""


def host_package_name() -> str:
    system = platform.system()
    if system == "Windows":
        return "platform-tools(Windows)"
    if system == "Darwin":
        return "Mac"
    if system == "Linux":
        return "platform-tools"
    raise RuntimeError(f"Unsupported host operating system: {system}")


def adb_executable_name() -> str:
    return "adb.exe" if platform.system() == "Windows" else "adb"


def find_adb(project_root: Path | None = None) -> Path | None:
    """Find only the ADB distribution matching the current host OS."""

    package = host_package_name()
    executable = adb_executable_name()
    roots = [Path(__file__).resolve().parents[1], Path.cwd()]
    if getattr(sys, "frozen", False):
        roots.insert(0, Path(sys.executable).resolve().parent)
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            roots.insert(0, Path(bundle_root))
    if project_root is not None:
        roots.insert(0, project_root)
    for root in roots:
        candidate = root / package / executable
        if candidate.is_file():
            return candidate.resolve()
    return None


def parse_devices(output: str) -> list[AdbDevice]:
    devices: list[AdbDevice] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices"):
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        metadata = {}
        for field in fields[2:]:
            key, separator, value = field.partition(":")
            if separator:
                metadata[key] = value
        devices.append(
            AdbDevice(
                serial=fields[0],
                state=fields[1],
                model=metadata.get("model", ""),
                product=metadata.get("product", ""),
                transport_id=metadata.get("transport_id", ""),
            )
        )
    return devices


class AdbManager(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)
    version_detected = Signal(str)
    devices_changed = Signal(list)
    busy_changed = Signal(bool)
    screenshot_busy_changed = Signal(bool)
    shutdown_finished = Signal()

    def __init__(self, project_root: Path | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.adb_path = find_adb(project_root)
        self.devices: list[AdbDevice] = []
        self._process: QProcess | None = None
        self._process_callback: Callable[[str, str, int], None] | None = None
        self._process_timer: QTimer | None = None
        self._refresh_pending = False
        self._screenshot_process: QProcess | None = None
        self._screenshot_timer: QTimer | None = None
        self._screenshot_serial = ""
        self._screenshot_destination: Path | None = None
        self._screenshot_stdout = bytearray()
        self._screenshot_stderr = bytearray()
        self._screenshot_process_error = ""
        self._screenshot_callback: Callable[[bool, str], None] | None = None
        self._shutting_down = False
        self._shutdown_processes: set[QProcess] = set()
        self._shutdown_finished_emitted = False
        self._kill_timers: dict[QProcess, QTimer] = {}

    @staticmethod
    def _command_timeout_ms(arguments: list[str]) -> int:
        operation = arguments[0] if arguments else ""
        if operation == "version":
            return 10_000
        if operation == "devices":
            return 15_000
        if operation in {"kill-server", "disconnect"}:
            return 15_000
        if operation in {"start-server", "connect", "pair"}:
            return 30_000
        return 30_000

    def run(self, arguments: list[str], callback: Callable[[str, str, int], None]) -> None:
        if self._shutting_down:
            self.error_occurred.emit("ADB is shutting down.")
            return
        if self.adb_path is None:
            self.error_occurred.emit("Host-matched ADB executable was not found.")
            return
        if self._process is not None:
            self.error_occurred.emit("ADB is busy; wait for the current operation to finish.")
            return

        process = QProcess(self)
        self._process = process
        self._process_callback = callback
        timeout_ms = self._command_timeout_ms(arguments)
        completed = False
        timed_out = False
        process.setProgram(str(self.adb_path))
        process.setArguments(arguments)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)

        timer = QTimer(self)
        timer.setSingleShot(True)
        self._process_timer = timer

        def finish(
            exit_code: int,
            stdout: str,
            stderr: str,
            invoke_callback: bool = True,
        ) -> None:
            nonlocal completed
            if completed:
                return
            completed = True
            was_current = self._process is process
            if timer.isActive():
                timer.stop()
            timer.deleteLater()
            if self._process_timer is timer:
                self._process_timer = None
            if was_current:
                self._process = None
                self._process_callback = None
                self.busy_changed.emit(False)
            self._cancel_force_kill(process)
            process.deleteLater()
            pending_refresh = self._refresh_pending
            self._refresh_pending = False
            if invoke_callback and was_current and not self._shutting_down:
                callback(stdout, stderr, exit_code)
            self._shutdown_processes.discard(process)
            self._maybe_emit_shutdown_finished()
            if pending_refresh and not self._shutting_down and self._process is None:
                self.refresh_devices()

        def finished(exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
            stdout = bytes(process.readAllStandardOutput()).decode(errors="replace")
            stderr = bytes(process.readAllStandardError()).decode(errors="replace")
            if timed_out:
                stderr = f"ADB command '{arguments[0] if arguments else 'unknown'}' timed out after {timeout_ms // 1000} seconds."
            finish(exit_code, stdout, stderr)

        def error_occurred(error: QProcess.ProcessError) -> None:
            process_error = process.errorString() or "Unknown process error."
            if error == QProcess.ProcessError.FailedToStart:
                if not self._shutting_down:
                    self.error_occurred.emit(f"Could not start ADB command: {process_error}")
                finish(-1, "", process_error, invoke_callback=False)
            elif not self._shutting_down and not timed_out:
                self.error_occurred.emit(f"ADB process error: {process_error}")

        def timeout() -> None:
            nonlocal timed_out
            if completed or self._process is not process:
                return
            timed_out = True
            process.terminate()
            self._schedule_force_kill(process, 1000)

        process.errorOccurred.connect(error_occurred)
        process.finished.connect(finished)
        timer.timeout.connect(timeout)
        self.busy_changed.emit(True)
        timer.start(timeout_ms)
        process.start()

    def _force_kill_if_running(self, process: QProcess) -> None:
        self._cancel_force_kill(process)
        is_active = (
            process is self._process
            or process is self._screenshot_process
            or process in self._shutdown_processes
        )
        if is_active and process.state() != QProcess.ProcessState.NotRunning:
            process.kill()

    def _schedule_force_kill(self, process: QProcess, delay_ms: int) -> None:
        self._cancel_force_kill(process)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._force_kill_if_running(process))
        self._kill_timers[process] = timer
        timer.start(delay_ms)

    def _cancel_force_kill(self, process: QProcess) -> None:
        timer = self._kill_timers.pop(process, None)
        if timer is not None:
            if timer.isActive():
                timer.stop()
            timer.deleteLater()

    def _maybe_emit_shutdown_finished(self) -> None:
        if (
            self._shutting_down
            and not self._shutdown_processes
            and not self._shutdown_finished_emitted
        ):
            self._shutdown_finished_emitted = True
            self.shutdown_finished.emit()

    def check_version(self) -> None:
        self.run(["version"], self._version_finished)

    def _version_finished(self, stdout: str, stderr: str, code: int) -> None:
        if code != 0:
            self.error_occurred.emit(f"ADB version check failed: {stderr.strip()}")
            return
        self.version_detected.emit(stdout.strip())
        self.status_changed.emit("ADB version verified.")

    def start_server(self) -> None:
        self.run(["start-server"], self._server_finished)

    def _server_finished(self, _stdout: str, stderr: str, code: int) -> None:
        if code != 0:
            self.error_occurred.emit(f"Could not start ADB server: {stderr.strip()}")
            return
        self.status_changed.emit("ADB server started.")
        self.refresh_devices()

    def stop_server(self) -> None:
        self.run(["kill-server"], self._stop_server_finished)

    def _stop_server_finished(self, _stdout: str, stderr: str, code: int) -> None:
        if code != 0:
            self.error_occurred.emit(f"Could not stop ADB server: {stderr.strip()}")
            return
        self.devices = []
        self.devices_changed.emit(self.devices)
        self.status_changed.emit("ADB server stopped.")

    def refresh_devices(self) -> None:
        if self._shutting_down:
            return
        if self._process is not None:
            self._refresh_pending = True
            return
        self.run(["devices", "-l"], self._devices_finished)

    def _devices_finished(self, stdout: str, stderr: str, code: int) -> None:
        if code != 0:
            self.error_occurred.emit(f"Could not list devices: {stderr.strip()}")
            return
        self.devices = parse_devices(stdout)
        self.devices_changed.emit(self.devices)
        self.status_changed.emit(f"Detected {len(self.devices)} device(s).")

    def connect_wireless(self, host_port: str) -> None:
        target = host_port.strip()
        if not target:
            self.error_occurred.emit("Wireless connection requires host:port.")
            return
        self.run(["connect", target], lambda out, err, code: self._connection_finished(target, out, err, code))

    def _connection_finished(self, target: str, stdout: str, stderr: str, code: int) -> None:
        if code != 0:
            self.error_occurred.emit(f"Could not connect to {target}: {stderr.strip()}")
            return
        self.status_changed.emit(stdout.strip() or f"Connected to {target}.")
        self.refresh_devices()

    def pair_wireless(self, host_port: str, pairing_code: str) -> None:
        target, code_text = host_port.strip(), pairing_code.strip()
        if not target or not code_text:
            self.error_occurred.emit("Wireless pairing requires host:port and a pairing code.")
            return

        def finished(stdout: str, stderr: str, exit_code: int) -> None:
            redacted_stdout = stdout.replace(code_text, "[redacted]")
            redacted_stderr = stderr.replace(code_text, "[redacted]")
            self._pair_finished(target, redacted_stdout, redacted_stderr, exit_code)

        self.run(["pair", target, code_text], finished)

    def _pair_finished(self, target: str, stdout: str, stderr: str, code: int) -> None:
        if code != 0:
            self.error_occurred.emit(f"Could not pair with {target}: {stderr.strip()}")
            return
        self.status_changed.emit(stdout.strip() or f"Paired with {target}.")

    def disconnect_device(self, serial: str) -> None:
        target = serial.strip()
        if not target:
            self.error_occurred.emit("Disconnect requires a device serial.")
            return
        self.run(["disconnect", target], lambda out, err, code: self._connection_finished(target, out, err, code))

    def screenshot(
        self,
        serial: str,
        destination: Path,
        callback: Callable[[bool, str], None] | None = None,
    ) -> bool:
        """Capture one PNG asynchronously without blocking the Qt event loop."""
        if self._shutting_down:
            self.error_occurred.emit("ADB is shutting down.")
            return False
        if self.adb_path is None:
            message = "Host-matched ADB executable was not found."
            self.error_occurred.emit(message)
            if callback:
                callback(False, message)
            return False
        target = serial.strip()
        if not target:
            message = "Screenshot requires a device serial."
            self.error_occurred.emit(message)
            if callback:
                callback(False, message)
            return False
        if self._screenshot_process is not None:
            message = "A screenshot is already in progress."
            self.error_occurred.emit(message)
            if callback:
                callback(False, message)
            return False

        process = QProcess(self)
        self._screenshot_process = process
        self._screenshot_serial = target
        self._screenshot_destination = destination
        self._screenshot_stdout.clear()
        self._screenshot_stderr.clear()
        self._screenshot_process_error = ""
        self._screenshot_callback = callback
        completed = False
        timed_out = False

        timer = QTimer(self)
        timer.setSingleShot(True)
        self._screenshot_timer = timer

        def finish(success: bool, message: str) -> None:
            nonlocal completed
            if completed:
                return
            completed = True
            active_callback = self._screenshot_callback
            self._screenshot_callback = None
            self._screenshot_process = None
            self._screenshot_serial = ""
            self._screenshot_destination = None
            if timer.isActive():
                timer.stop()
            timer.deleteLater()
            if self._screenshot_timer is timer:
                self._screenshot_timer = None
            self.screenshot_busy_changed.emit(False)
            self._cancel_force_kill(process)
            process.deleteLater()
            self._shutdown_processes.discard(process)
            self._maybe_emit_shutdown_finished()
            if not self._shutting_down:
                if not success:
                    self.error_occurred.emit(message)
                if active_callback:
                    active_callback(success, message)

        def finished(exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
            stdout = bytes(self._screenshot_stdout) + bytes(process.readAllStandardOutput())
            stderr = bytes(self._screenshot_stderr) + bytes(process.readAllStandardError())
            if timed_out:
                finish(False, "Screenshot timed out after 60 seconds.")
                return
            if exit_code != 0:
                finish(
                    False,
                    stderr.decode(errors="replace").strip()
                    or self._screenshot_process_error
                    or "Screenshot failed",
                )
                return
            if not stdout.startswith(b"\x89PNG\r\n\x1a\n"):
                finish(False, "ADB returned invalid PNG screenshot data.")
                return
            try:
                destination.write_bytes(stdout)
            except OSError as error:
                finish(False, f"Could not save screenshot: {error}")
                return
            finish(True, str(destination))

        def read_stdout() -> None:
            self._screenshot_stdout.extend(bytes(process.readAllStandardOutput()))

        def read_stderr() -> None:
            self._screenshot_stderr.extend(bytes(process.readAllStandardError()))

        def process_error(error: QProcess.ProcessError) -> None:
            if completed:
                return
            message = process.errorString() or "Screenshot process failed."
            if error == QProcess.ProcessError.FailedToStart:
                finish(False, f"Could not start screenshot process: {message}")
            elif not self._shutting_down:
                self._screenshot_process_error = message

        def timeout() -> None:
            nonlocal timed_out
            if completed or self._screenshot_process is not process:
                return
            timed_out = True
            process.terminate()
            self._schedule_force_kill(process, 1000)

        process.setProgram(str(self.adb_path))
        process.setArguments(["-s", target, "exec-out", "screencap", "-p"])
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        process.readyReadStandardOutput.connect(read_stdout)
        process.readyReadStandardError.connect(read_stderr)
        process.errorOccurred.connect(process_error)
        process.finished.connect(finished)
        timer.timeout.connect(timeout)
        self.screenshot_busy_changed.emit(True)
        timer.start(60_000)
        process.start()
        return True

    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._refresh_pending = False
        self._shutdown_processes = {
            process
            for process in (self._process, self._screenshot_process)
            if process is not None
        }
        for timer in (self._process_timer, self._screenshot_timer):
            if timer is not None and timer.isActive():
                timer.stop()
        for process in tuple(self._shutdown_processes):
            process.terminate()
            self._schedule_force_kill(process, 1500)
        self._maybe_emit_shutdown_finished()
