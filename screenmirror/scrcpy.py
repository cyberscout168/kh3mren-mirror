"""Scrcpy discovery, capability caching, command generation, and process lifecycle."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from screenmirror.dynamic_settings import ScrcpyCommandBuilder, is_display_only_option_allowed
from screenmirror.scrcpy_help import ScrcpyHelpParser, ScrcpyOption
from screenmirror.settings import AppSettings


class ScrcpyCapabilityManager:
    def __init__(self, executable: Path | str | None = None, cache_dir: Path | None = None) -> None:
        self.executable = Path(executable).resolve() if executable else None
        self.cache_dir = cache_dir or (Path.home() / ".screenmirror")
        self.version = ""
        self.help_text = ""
        self.options: list[ScrcpyOption] = []
        self.error = ""

    def discover(self, force: bool = False) -> bool:
        if self.executable is None or not self.executable.is_file():
            self.error = "scrcpy executable was not found."
            return False
        try:
            version_result = self._run("--version")
            help_result = self._run("--help")
        except (OSError, subprocess.SubprocessError, TimeoutError) as error:
            self.error = f"Could not run scrcpy: {error}"
            return False
        combined_version = version_result.stdout + version_result.stderr
        combined_help = help_result.stdout + help_result.stderr
        version_match = re.search(r"scrcpy\s+([0-9]+(?:\.[0-9]+)+(?:[-+][\w.]+)?)", combined_version, re.I)
        version = version_match.group(1) if version_match else "unknown"
        fingerprint = self._fingerprint(version, combined_help)
        cached = self._read_cache(fingerprint) if not force else None
        if cached:
            self.version, self.help_text = cached["version"], cached["help_text"]
            self.options = [ScrcpyOption(**item) for item in cached["options"]]
        else:
            self.version, self.help_text = version, combined_help
            self.options = ScrcpyHelpParser().parse(combined_help, version)
            self._write_cache(fingerprint)
        self.error = "" if self.options else "scrcpy help output contained no recognizable options."
        return bool(self.options)

    def _fingerprint(self, version: str, help_text: str) -> str:
        try:
            stat = self.executable.stat()
            executable_identity = f"{self.executable}:{stat.st_size}:{stat.st_mtime_ns}"
        except OSError:
            executable_identity = str(self.executable)
        parser_version = ScrcpyHelpParser.CACHE_VERSION
        cache_input = f"parser:{parser_version}:{executable_identity}:{version}:{help_text}"
        return hashlib.sha256(cache_input.encode()).hexdigest()

    def apply_outputs(self, combined_version: str, combined_help: str, force: bool = False) -> bool:
        version_match = re.search(
            r"scrcpy\s+([0-9]+(?:\.[0-9]+)+(?:[-+][\w.]+)?)",
            combined_version,
            re.I,
        )
        version = version_match.group(1) if version_match else "unknown"
        fingerprint = self._fingerprint(version, combined_help)
        cached = self._read_cache(fingerprint) if not force else None
        if cached:
            self.version, self.help_text = cached["version"], cached["help_text"]
            self.options = [ScrcpyOption(**item) for item in cached["options"]]
        else:
            self.version, self.help_text = version, combined_help
            self.options = ScrcpyHelpParser().parse(combined_help, version)
            self._write_cache(fingerprint)
        self.error = "" if self.options else "scrcpy help output contained no recognizable options."
        return bool(self.options)

    def _run(self, argument: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(self.executable), argument], cwd=str(self.executable.parent), capture_output=True,
                              text=True, timeout=10, check=False)

    def _cache_path(self, fingerprint: str) -> Path:
        return self.cache_dir / f"capabilities-{fingerprint}.json"

    def _read_cache(self, fingerprint: str) -> dict | None:
        try:
            with self._cache_path(fingerprint).open(encoding="utf-8") as stream:
                return json.load(stream)
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _write_cache(self, fingerprint: str) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            payload = {"version": self.version, "help_text": self.help_text,
                       "options": [option.__dict__ for option in self.options]}
            with self._cache_path(fingerprint).open("w", encoding="utf-8") as stream:
                json.dump(payload, stream, indent=2)
        except OSError:
            pass

    def builder(self) -> ScrcpyCommandBuilder:
        if not self.options:
            raise RuntimeError(self.error or "scrcpy capabilities are unavailable.")
        return ScrcpyCommandBuilder(self.executable, self.options)


class ScrcpyCapabilities(ScrcpyCapabilityManager):
    def __init__(self, executable: Path) -> None:
        super().__init__(executable)
        if not self.discover():
            raise RuntimeError(self.error)
        self.video_codecs = self._find_choices("--video-codec") or ("h264",)
        self.record_formats = ("mp4", "mkv", "m4a", "mka", "opus", "aac", "flac", "wav") if self.option("--record") else ()

    @classmethod
    def from_manager(cls, manager: ScrcpyCapabilityManager) -> "ScrcpyCapabilities":
        capabilities = cls.__new__(cls)
        capabilities.executable = manager.executable
        capabilities.cache_dir = manager.cache_dir
        capabilities.version = manager.version
        capabilities.help_text = manager.help_text
        capabilities.options = manager.options
        capabilities.error = manager.error
        capabilities.video_codecs = capabilities._find_choices("--video-codec") or ("h264",)
        capabilities.record_formats = (
            ("mp4", "mkv", "m4a", "mka", "opus", "aac", "flac", "wav")
            if capabilities.option("--record") else ()
        )
        return capabilities

    def option(self, name: str) -> ScrcpyOption | None:
        return next((item for item in self.options if name in {item.canonical, item.long_option, item.short_option}), None)

    def _find_choices(self, name: str) -> tuple[str, ...]:
        item = self.option(name)
        return item.choices if item else ()

    def require(self, option: str) -> None:
        if self.option(option) is None:
            raise RuntimeError(f"The installed scrcpy does not support required option {option}.")

    def build_command(
        self,
        serial: str,
        settings: AppSettings,
        dynamic_values: dict | None = None,
    ) -> list[str]:
        settings.validate()
        if not serial.strip():
            raise ValueError("A device serial is required to start mirroring.")
        if settings.video_codec not in self.video_codecs:
            raise ValueError(f"Video codec {settings.video_codec!r} is not supported by this scrcpy build.")
        # Older callers/tests may construct this compatibility facade without running discovery.
        if not hasattr(self, "options"):
            names = re.findall(r"--[A-Za-z0-9][\w-]*(?:=[^\s]+)?", self.help_text)
            value_names = {"--serial", "--max-size", "--max-fps", "--video-bit-rate", "--video-codec", "--record"}
            self.options = [ScrcpyOption(name=name.split("=", 1)[0].lstrip("-"),
                                         long_option=name.split("=", 1)[0],
                                         argument_name=name.split("=", 1)[1] if "=" in name else ("value" if name.split("=", 1)[0] in value_names else None),
                                         accepts_value="=" in name or name.split("=", 1)[0] in value_names,
                                         boolean_flag="=" not in name and name.split("=", 1)[0] not in value_names)
                            for name in dict.fromkeys(names)]
            self.error = ""
        values = {"--max-size": settings.max_size, "--max-fps": settings.max_fps,
                  "--video-bit-rate": settings.video_bit_rate, "--video-codec": settings.video_codec,
                  "--no-audio": not settings.audio_enabled, "--fullscreen": settings.fullscreen,
                  "--stay-awake": settings.stay_awake, "--turn-screen-off": settings.turn_screen_off}
        if settings.recording_path:
            values["--record"] = settings.recording_path
        if dynamic_values:
            values.update({
                key: value
                for key, value in dynamic_values.items()
                if is_display_only_option_allowed(key)
            })
        return self.builder().build(values, serial)


def find_scrcpy(project_root: Path | None = None) -> Path | None:
    roots = [Path(__file__).resolve().parents[1], Path.cwd()]
    if getattr(sys, "frozen", False):
        roots.insert(0, Path(sys.executable).resolve().parent)
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            roots.insert(0, Path(bundle_root))
    if project_root is not None:
        roots.insert(0, project_root)
    for root in roots:
        for candidate in root.glob("third_party/scrcpy/scrcpy-win64-*/scrcpy.exe"):
            if candidate.is_file():
                return candidate.resolve()
    return None


class ScrcpySession(QObject):
    started = Signal()
    stopped = Signal()
    error_occurred = Signal(str)
    output_received = Signal(str)
    capabilities_ready = Signal()
    shutdown_finished = Signal()

    def __init__(self, executable: Path | None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.executable = executable
        self.capabilities: ScrcpyCapabilities | None = None
        self.process: QProcess | None = None
        self.initialization_error = ""
        self._shutting_down = False
        self._discovery_process: QProcess | None = None
        self._discovery_timer: QTimer | None = None
        self._discovery_stage = ""
        self._discovery_timed_out = False
        self._discovery_stdout = bytearray()
        self._discovery_stderr = bytearray()
        self._discovery_manager: ScrcpyCapabilityManager | None = None
        self._stop_requested = False
        self._termination_requested: set[QProcess] = set()
        self._shutdown_processes: set[QProcess] = set()
        self._shutdown_finished_emitted = False
        self._kill_timers: dict[QProcess, QTimer] = {}
        if executable is not None:
            if not executable.is_file():
                self.initialization_error = "scrcpy executable was not found."
        else:
            self.initialization_error = "scrcpy executable was not found."

    def start_discovery(self, force: bool = False) -> None:
        if self._shutting_down or self.capabilities is not None or self._discovery_process is not None:
            return
        if self.executable is None or not self.executable.is_file():
            self.initialization_error = "scrcpy executable was not found."
            self.error_occurred.emit(self.initialization_error)
            return
        self._discovery_manager = ScrcpyCapabilityManager(self.executable)
        self._discovery_manager.cache_dir = Path.home() / ".screenmirror"
        self._discovery_stage = "version"
        self._start_discovery_process("--version", force)

    def _start_discovery_process(self, argument: str, force: bool) -> None:
        process = QProcess(self)
        self._discovery_process = process
        self._discovery_timed_out = False
        self._discovery_stdout.clear()
        self._discovery_stderr.clear()
        timer = QTimer(self)
        timer.setSingleShot(True)
        self._discovery_timer = timer
        process.setProgram(str(self.executable))
        process.setArguments([argument])
        process.setWorkingDirectory(str(self.executable.parent))
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        process.readyReadStandardOutput.connect(lambda: self._read_discovery_output(process, False))
        process.readyReadStandardError.connect(lambda: self._read_discovery_output(process, True))
        process.errorOccurred.connect(lambda error: self._discovery_error(process, error))
        process.finished.connect(
            lambda code, status: self._discovery_finished(process, code, status, force)
        )
        timer.timeout.connect(lambda: self._discovery_timeout(process))
        timer.start(10_000)
        process.start()

    def _read_discovery_output(self, process: QProcess, stderr: bool) -> None:
        data = bytes(process.readAllStandardError() if stderr else process.readAllStandardOutput())
        (self._discovery_stderr if stderr else self._discovery_stdout).extend(data)

    def _stop_discovery_timer(self) -> None:
        timer = self._discovery_timer
        self._discovery_timer = None
        if timer is not None:
            if timer.isActive():
                timer.stop()
            timer.deleteLater()

    def _finish_discovery(
        self,
        process: QProcess,
        error_message: str | None = None,
    ) -> None:
        if self._discovery_process is not process:
            return
        self._stop_discovery_timer()
        self._discovery_process = None
        self._cancel_force_kill(process)
        process.deleteLater()
        self._termination_requested.discard(process)
        self._shutdown_processes.discard(process)
        if error_message:
            self.initialization_error = error_message
            if not self._shutting_down:
                self.error_occurred.emit(error_message)
        self._maybe_emit_shutdown_finished()

    def _discovery_error(self, process: QProcess, error: QProcess.ProcessError) -> None:
        process_error = process.errorString() or "Unknown process error."
        if error == QProcess.ProcessError.FailedToStart:
            self._finish_discovery(
                process,
                f"Could not start scrcpy {self._discovery_stage} discovery: {process_error}",
            )
        elif not self._shutting_down:
            self.initialization_error = process_error

    def _discovery_timeout(self, process: QProcess) -> None:
        if self._discovery_process is not process:
            return
        self._discovery_timed_out = True
        self._request_termination(process)

    def _discovery_finished(
        self,
        process: QProcess,
        exit_code: int,
        _status: QProcess.ExitStatus,
        force: bool,
    ) -> None:
        if self._discovery_process is not process:
            return
        self._read_discovery_output(process, False)
        self._read_discovery_output(process, True)
        stdout = bytes(self._discovery_stdout).decode(errors="replace")
        stderr = bytes(self._discovery_stderr).decode(errors="replace")
        timed_out = self._discovery_timed_out
        self._finish_discovery(process)
        if self._shutting_down:
            return
        if timed_out:
            message = f"scrcpy {self._discovery_stage} discovery timed out after 10 seconds."
            self.initialization_error = message
            self.error_occurred.emit(message)
            return
        if exit_code != 0:
            self.initialization_error = stderr.strip() or f"scrcpy {self._discovery_stage} discovery failed."
            self.error_occurred.emit(self.initialization_error)
            return
        if self._discovery_stage == "version":
            self._discovery_version_output = stdout + stderr
            self._discovery_stage = "help"
            self._start_discovery_process("--help", force)
            return
        manager = self._discovery_manager
        if manager is None or not manager.apply_outputs(
            getattr(self, "_discovery_version_output", ""), stdout + stderr, force
        ):
            self.initialization_error = manager.error if manager else "scrcpy capability discovery failed."
            if not self._shutting_down:
                self.error_occurred.emit(self.initialization_error)
            return
        self.capabilities = ScrcpyCapabilities.from_manager(manager)
        self.initialization_error = ""
        self.capabilities_ready.emit()

    def start(self, serial: str, settings: AppSettings | None = None, dynamic_values: dict | None = None) -> None:
        if self._shutting_down:
            self.error_occurred.emit("scrcpy is shutting down.")
            return
        if self.capabilities is None:
            self.error_occurred.emit(self.initialization_error or "scrcpy capabilities are unavailable.")
            return
        if self.process is not None:
            self.error_occurred.emit("A scrcpy session is already running.")
            return
        try:
            if dynamic_values is None:
                arguments = self.capabilities.build_command(serial, settings or AppSettings())
            else:
                arguments = self.capabilities.build_command(
                    serial,
                    settings or AppSettings(),
                    dynamic_values,
                )
        except (ValueError, RuntimeError) as error:
            self.error_occurred.emit(str(error))
            return
        process = QProcess(self)
        self.process = process
        process.setProgram(arguments[0])
        process.setArguments(arguments[1:])
        process.setWorkingDirectory(str(self.executable.parent))
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        process.readyReadStandardOutput.connect(lambda: self._read_output(process))
        process.readyReadStandardError.connect(lambda: self._read_output(process))
        process.errorOccurred.connect(lambda error: self._session_error(process, error))
        process.started.connect(self.started.emit)
        process.finished.connect(lambda code, status: self._session_finished(process, code, status))
        process.start()

    def _read_output(self, process: QProcess) -> None:
        output = bytes(process.readAllStandardOutput()).decode(errors="replace") + bytes(process.readAllStandardError()).decode(errors="replace")
        if output.strip():
            self.output_received.emit(output.strip())

    def _session_error(self, process: QProcess, error: QProcess.ProcessError) -> None:
        process_error = process.errorString() or "Unknown process error."
        if error == QProcess.ProcessError.FailedToStart:
            self._finish_session(
                process,
                -1,
                f"Could not start scrcpy: {process_error}",
            )
        elif not self._shutting_down and not self._stop_requested:
            self.error_occurred.emit(process_error)

    def _session_finished(
        self,
        process: QProcess,
        exit_code: int,
        _exit_status: QProcess.ExitStatus,
    ) -> None:
        self._finish_session(process, exit_code)

    def _finish_session(
        self,
        process: QProcess,
        exit_code: int,
        error_message: str | None = None,
    ) -> None:
        if self.process is not process:
            return
        self._read_output(process)
        self.process = None
        self._stop_requested = False
        self._termination_requested.discard(process)
        self._shutdown_processes.discard(process)
        self._cancel_force_kill(process)
        process.deleteLater()
        if not self._shutting_down:
            if error_message:
                self.error_occurred.emit(error_message)
            elif exit_code != 0:
                self.error_occurred.emit(
                    f"scrcpy exited with code {exit_code}; see diagnostics for its output."
                )
            self.stopped.emit()
        self._maybe_emit_shutdown_finished()

    def _request_termination(self, process: QProcess) -> None:
        if process in self._termination_requested:
            return
        self._termination_requested.add(process)
        process.terminate()
        self._schedule_force_kill(process, 1500)

    def _force_kill_if_running(self, process: QProcess) -> None:
        self._cancel_force_kill(process)
        is_active = (
            process in self._shutdown_processes
            or process is self.process
            or process is self._discovery_process
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

    def stop(self) -> None:
        if self.process is None or self._stop_requested:
            return
        self._stop_requested = True
        self._request_termination(self.process)

    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._shutdown_processes = {
            process
            for process in (self._discovery_process, self.process)
            if process is not None
        }
        self._stop_discovery_timer()
        for process in tuple(self._shutdown_processes):
            self._request_termination(process)
        self._maybe_emit_shutdown_finished()
