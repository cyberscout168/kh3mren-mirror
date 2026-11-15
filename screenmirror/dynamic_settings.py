"""Capability-driven settings values and safe scrcpy argument generation."""

from __future__ import annotations

from dataclasses import dataclass
import shlex
import re
from pathlib import Path
from typing import Any

from screenmirror.scrcpy_help import ScrcpyOption


def is_display_only_option_allowed(name: str) -> bool:
    """Return whether an advanced option is compatible with display-only mirroring."""
    option = name.lstrip("-").lower()
    return not (
        "camera" in option
        or option == "video-source"
        or option in {"new-display", "flex-display"}
        or option.startswith(("vd-", "no-vd-"))
    )


def validate_option_value(option: ScrcpyOption, value: Any) -> str:
    """Validate a discovered value option before persisting or emitting it."""
    text = str(value).strip()
    if option.choices and text not in option.choices:
        raise ValueError(f"{option.canonical} must be one of: {', '.join(option.choices)}.")
    if option.canonical == "--port":
        parts = text.split(":")
        if (
            len(parts) not in (1, 2)
            or any(not re.fullmatch(r"\d{1,5}", part) for part in parts)
            or any(not 1 <= int(part) <= 65535 for part in parts)
            or (len(parts) == 2 and int(parts[0]) > int(parts[1]))
        ):
            raise ValueError("--port must be a numeric port or an ascending numeric port range (1-65535).")
    return text


@dataclass
class ScrcpyCommandBuilder:
    executable: Path
    options: list[ScrcpyOption]

    def __post_init__(self) -> None:
        self._by_name = {item.canonical: item for item in self.options}
        for item in self.options:
            self._by_name[item.name] = item
            if item.short_option:
                self._by_name[item.short_option] = item

    def build(self, values: dict[str, Any] | None = None, serial: str = "") -> list[str]:
        values = values or {}
        args = [str(self.executable)]
        if serial.strip():
            serial_option = self._by_name.get("--serial")
            if serial_option is None:
                raise ValueError("This scrcpy executable does not support device serial selection.")
            args.append(f"{serial_option.canonical}={serial.strip()}")
        seen: set[str] = set()
        for key, value in values.items():
            option = self._by_name.get(key) or self._by_name.get(f"--{key}")
            if option is None or not option.supported:
                continue
            if option.canonical in seen:
                raise ValueError(f"Duplicate setting for {option.canonical}.")
            seen.add(option.canonical)
            if option.boolean_flag:
                if bool(value):
                    args.append(option.canonical)
                continue
            if value is None or str(value).strip() == "":
                continue
            text = validate_option_value(option, value)
            args.append(f"{option.canonical}={text}")
        return args

    def preview(self, values: dict[str, Any] | None = None, serial: str = "") -> str:
        return shlex.join(self.build(values, serial))

