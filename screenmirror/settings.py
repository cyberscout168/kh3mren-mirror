"""Persistent, validated scrcpy and application settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSettings
from screenmirror.dynamic_settings import is_display_only_option_allowed, validate_option_value
from screenmirror.i18n import SUPPORTED_LANGUAGES
from screenmirror.scrcpy_help import ScrcpyOption


# Advanced values are intentionally empty by default. The standard mirror
# profile is represented by AppSettings; scrcpy supplies its own defaults for
# audio source/codec, hardware decoding, and input methods.
DEFAULT_DYNAMIC_VALUES: dict[str, object] = {}


@dataclass
class UiSettings:
    language: str = "en"

    @classmethod
    def load(cls) -> "UiSettings":
        store = QSettings("ScreenMirror", "ScreenMirror")
        language = str(store.value("ui/language", "en"))
        return cls(language if language in SUPPORTED_LANGUAGES else "en")

    def save(self) -> None:
        if self.language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported interface language: {self.language}")
        store = QSettings("ScreenMirror", "ScreenMirror")
        store.setValue("ui/language", self.language)
        store.sync()


@dataclass
class AppSettings:
    max_size: int = 720
    max_fps: int = 30
    video_bit_rate: str = "4M"
    video_codec: str = "h264"
    audio_enabled: bool = True
    fullscreen: bool = False
    stay_awake: bool = True
    turn_screen_off: bool = False
    recording_path: str = ""

    @classmethod
    def load(cls) -> "AppSettings":
        store = QSettings("ScreenMirror", "ScreenMirror")
        defaults = cls()
        return cls(
            max_size=store.value("mirror/max_size", defaults.max_size, type=int),
            max_fps=store.value("mirror/max_fps", defaults.max_fps, type=int),
            video_bit_rate=str(store.value("mirror/video_bit_rate", defaults.video_bit_rate)),
            video_codec=str(store.value("mirror/video_codec", defaults.video_codec)),
            audio_enabled=store.value("mirror/audio_enabled", defaults.audio_enabled, type=bool),
            fullscreen=store.value("mirror/fullscreen", defaults.fullscreen, type=bool),
            stay_awake=store.value("mirror/stay_awake", defaults.stay_awake, type=bool),
            turn_screen_off=store.value("mirror/turn_screen_off", defaults.turn_screen_off, type=bool),
            recording_path=str(store.value("mirror/recording_path", defaults.recording_path)),
        )

    def save(self) -> None:
        store = QSettings("ScreenMirror", "ScreenMirror")
        for name, value in vars(self).items():
            store.setValue(f"mirror/{name}", value)
        store.sync()

    def validate(self) -> None:
        if not 240 <= self.max_size <= 8192:
            raise ValueError("Maximum size must be between 240 and 8192 pixels.")
        if not 1 <= self.max_fps <= 240:
            raise ValueError("Maximum FPS must be between 1 and 240.")
        rate = self.video_bit_rate.strip().upper()
        digits = rate[:-1] if rate.endswith(("K", "M")) else rate
        if not digits.isdigit() or int(digits) <= 0:
            raise ValueError("Bitrate must be a positive number, optionally ending in K or M (for example 8M).")
        if self.video_codec not in {"h264", "h265", "av1", "vp8", "vp9"}:
            raise ValueError("Unsupported video codec value.")
        if self.recording_path and not Path(self.recording_path).suffix:
            raise ValueError("Recording destination must include a file extension, such as .mp4.")


class DynamicSettings:
    """Persistent values keyed by discovered option name, separate from capabilities."""

    def __init__(
        self,
        values: dict[str, object] | None = None,
        persisted_keys: set[str] | None = None,
    ) -> None:
        self.values = dict(values or {})
        self._persisted_keys = set(persisted_keys if persisted_keys is not None else self.values)

    @classmethod
    def load(
        cls,
        supported: set[str],
        choices: dict[str, tuple[str, ...]] | None = None,
        options: dict[str, ScrcpyOption] | None = None,
    ) -> "DynamicSettings":
        store = QSettings("ScreenMirror", "ScreenMirror")
        store.beginGroup("dynamic")
        values = {}
        persisted_keys = set()
        for key in store.childKeys():
            if not is_display_only_option_allowed(key):
                persisted_keys.add(key)
                continue
            if key not in supported:
                continue
            persisted_keys.add(key)
            value = store.value(key)
            allowed = (choices or {}).get(key, ())
            if allowed and str(value) not in allowed:
                continue
            option = (options or {}).get(key)
            if option is not None and not option.boolean_flag:
                try:
                    value = validate_option_value(option, value)
                except ValueError:
                    continue
            values[key] = value
        store.endGroup()
        return cls(values, persisted_keys=persisted_keys)

    @property
    def needs_cleanup(self) -> bool:
        """Whether a persisted value was rejected or is incompatible with display mirroring."""
        return bool(self._persisted_keys - self.values.keys())

    def save(self) -> None:
        store = QSettings("ScreenMirror", "ScreenMirror")
        store.beginGroup("dynamic")
        for key in self._persisted_keys - self.values.keys():
            store.remove(key)
        for key, value in self.values.items():
            store.setValue(key, value)
        store.endGroup()
        store.sync()
        self._persisted_keys = set(self.values)

    def reset(self) -> None:
        self.values.clear()

    @classmethod
    def defaults_for(cls, supported: set[str]) -> "DynamicSettings":
        return cls({key: value for key, value in DEFAULT_DYNAMIC_VALUES.items() if key in supported})
