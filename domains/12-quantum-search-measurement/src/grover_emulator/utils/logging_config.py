"""One logging setup for the CLI and the scripts, in a format a log file can be compared against.

There was no logging in this project before this module — every message was a ``print``. That is
fine for one script and not fine for a sweep: a run's log is an artifact, and two logs of the same
seeded run should differ only in the things that are *supposed* to differ. So the format is fixed
here, once, and the two properties it is fixed for are worth naming.

**Deterministic.** Timestamps are UTC (``time.gmtime``), not local time, so two runs are ordered
correctly regardless of the machine that produced them or the season the log was written in. Fields
are in a fixed order at a fixed width. Nothing depends on the order records happened to arrive in.

**Uncoloured when it is not being read by a terminal.** ANSI colour in a redirected log is not a
cosmetic problem: escape sequences land in the file, ``diff`` between two runs reports every line as
changed, and a regex over a log has to know about them. Colour is therefore opt-in by detection —
a tty, no ``NO_COLOR`` in the environment, a terminal that is not ``dumb`` — and can be forced
either way by the caller. The default is uncoloured everywhere it cannot be seen.

The third property is not about the format: :func:`configure_logging` is idempotent. Calling it
twice replaces the handler it installed instead of adding a second one, because the failure mode of
the naive implementation is every message appearing twice, which reads as a bug in the code that
logged rather than in the code that configured.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import IO

__all__ = [
    "LOG_LEVEL_ENV",
    "LOG_FORMAT",
    "DATE_FORMAT",
    "configure_logging",
    "log_level_from_env",
]

LOG_LEVEL_ENV = "GROVER_EMULATOR_LOG_LEVEL"
"""Environment override, read only when the caller passes no level. A caller that names a level is
explicitly overriding the environment, and having the environment win over the argument is the kind
of precedence that makes a debugging session take longer than the bug is worth."""

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
"""The line format. The level is padded to a fixed width so the message column lines up, which is
what makes a long log skimmable by eye and by ``cut -c``."""

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
"""ISO 8601, to the second, in UTC. Sub-second stamps would make two runs of a fast sweep differ in
a field nobody reads."""

_HANDLER_MARK = "_grover_emulator_handler"
"""Attribute stamped on the handlers this module installs. It is how a second call finds its own
handler among any the embedding application may have added, and leaves those alone."""

_COLOURS: dict[int, str] = {
    logging.DEBUG: "\x1b[36m",  # cyan
    logging.INFO: "\x1b[32m",  # green
    logging.WARNING: "\x1b[33m",  # yellow
    logging.ERROR: "\x1b[31m",  # red
    logging.CRITICAL: "\x1b[1;31m",  # bold red
}

_RESET = "\x1b[0m"


class _LevelColourFormatter(logging.Formatter):
    """The standard formatter, with the whole line wrapped in the level's colour.

    Wrapping the line rather than colouring the level name is deliberate: it is the line that has to
    stand out when scanning a terminal, and it keeps the emitted text free of escapes whenever
    colour is off — the formatter is only ever installed when it is on.
    """

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        colour = _COLOURS.get(record.levelno)
        return f"{colour}{text}{_RESET}" if colour else text


def _resolve_level(level: int | str | None) -> int:
    """Turn ``level`` into a numeric level, or fail loudly naming what was accepted.

    ``None`` is not invalid input: it is the documented default and it means "whatever
    :func:`log_level_from_env` says, else ``INFO``". The environment is consulted through that one
    helper rather than through a second lookup here, so the default and a caller that resolves the
    environment itself cannot disagree about what the environment said.
    """
    if level is None:
        from_env = log_level_from_env()
        if from_env is None:
            return logging.INFO
        level = from_env
    if isinstance(level, str):
        mapping = logging.getLevelNamesMapping()
        if level.upper() not in mapping:
            raise ValueError(
                f"unknown log level {level!r}; use one of {sorted(k for k in mapping if not k.startswith('Level'))}"
            )
        return mapping[level.upper()]
    if isinstance(level, int):
        return level
    raise TypeError(f"level must be an int, a str, or None, got {type(level).__name__}")


def log_level_from_env(environ: dict[str, str] | None = None) -> int | None:
    """The level named by :data:`LOG_LEVEL_ENV`, or None when it is unset or unusable.

    A malformed environment variable is ignored rather than fatal: it is a convenience, and a
    convenience that crashes a run at import time is worse than one that does nothing.
    """
    env = os.environ if environ is None else environ
    raw = env.get(LOG_LEVEL_ENV)
    if not raw:
        return None
    try:
        return _resolve_level(raw)
    except (ValueError, TypeError):
        return None


def _colour_default(stream: IO[str]) -> bool:
    """Colour only when it is being read by a terminal that can show it.

    Both checks matter. ``isatty`` is false for a pipe, a file, and a CI log — which is where
    escapes do the most damage. ``NO_COLOR`` and ``TERM=dumb`` are the conventions a user reaches
    for when their terminal is a tty but their tooling is not, and honouring them costs nothing.
    """
    if not hasattr(stream, "isatty") or not stream.isatty():
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    return True


def configure_logging(
    level: int | str | None = None,
    *,
    color: bool | None = None,
    stream: IO[str] | None = None,
) -> logging.Logger:
    """Install the project's log format on the root logger, and return the package's logger.

    Idempotent: a handler this function installed earlier is removed before a new one is added, so
    calling it from both a CLI entry point and a library import gives one line per record rather
    than two. Handlers installed by anything else are left where they are — a library that reaches
    into a host application's logging setup to remove things it did not add is a library that
    breaks its host.

    Args:
        level: the level to log at, as a number or a name (``"DEBUG"``). ``None`` means "use
            :data:`LOG_LEVEL_ENV` if it is set, else ``INFO``".
        color: force colour on (True) or off (False). ``None`` detects: colour only for a tty with
            no ``NO_COLOR`` and ``TERM`` not ``dumb``.
        stream: where records go. Defaults to ``sys.stderr``, so that a program's real output on
            stdout can be piped somewhere without log lines mixed into it.

    Returns:
        ``logging.getLogger("grover_emulator")``, so a caller can write
        ``log = configure_logging(); log.info(...)`` without repeating the name.
    """
    resolved = _resolve_level(level)
    out = sys.stderr if stream is None else stream
    use_colour = _colour_default(out) if color is None else color

    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, _HANDLER_MARK, False):
            root.removeHandler(handler)
            handler.close()

    formatter: logging.Formatter = (
        _LevelColourFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        if use_colour
        else logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    )
    # UTC for every record, so a log's timestamps do not move when the machine's timezone does.
    formatter.converter = __import__("time").gmtime

    handler = logging.StreamHandler(out)
    handler.setFormatter(formatter)
    setattr(handler, _HANDLER_MARK, True)
    root.addHandler(handler)
    root.setLevel(resolved)

    return logging.getLogger("grover_emulator")
