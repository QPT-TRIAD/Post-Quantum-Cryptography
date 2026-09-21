"""``configure_logging`` called the way its own signature says it can be called.

The level is typed ``int | str | None`` and the last of those is the default, so
``configure_logging()`` is the call the signature recommends. What is asserted here is the rule
behind that default — the argument beats the environment, the environment beats ``INFO``, and an
unusable environment variable is ignored rather than fatal — together with the property that lets a
caller stop writing the resolution out by hand: the default and an explicit environment lookup never
disagree about what the environment said. Invalid input still fails loudly, which is the half of the
behaviour that already worked and is pinned here so the fix cannot be read as permission to accept
anything.
"""

from __future__ import annotations

import io
import logging

import pytest

from grover_emulator.utils.logging_config import (
    LOG_LEVEL_ENV,
    configure_logging,
    log_level_from_env,
)


@pytest.fixture(autouse=True)
def root_logger_restored():
    """The root logger is process-global and these tests reconfigure it; put it back afterwards.

    Handlers the configuration installed are removed and closed, and any handler that was there
    beforehand is put back — pytest's own capture handlers among them, so that a later test still
    sees captured output.
    """
    root = logging.getLogger()
    before = list(root.handlers)
    level = root.level
    yield
    for handler in list(root.handlers):
        if handler not in before:
            root.removeHandler(handler)
            handler.close()
    for handler in before:
        if handler not in root.handlers:
            root.addHandler(handler)
    root.setLevel(level)


@pytest.fixture(autouse=True)
def level_env_unset(monkeypatch):
    """A level set in the developer's own environment must not decide what these tests measure."""
    monkeypatch.delenv(LOG_LEVEL_ENV, raising=False)


# -----------------------------------------------------------------------------------------------
# the default, which is the argument the signature recommends
# -----------------------------------------------------------------------------------------------


def test_the_no_argument_call_installs_a_working_logger():
    """The call with no level at all returns the package logger, and records go through it."""
    stream = io.StringIO()
    log = configure_logging(stream=stream)
    assert log.name == "grover_emulator"
    log.info("the default level is usable")
    assert "the default level is usable" in stream.getvalue()


def test_the_default_level_is_info_when_the_environment_names_none():
    configure_logging()
    assert logging.getLogger().level == logging.INFO


def test_the_default_level_is_the_environment_when_it_names_one(monkeypatch):
    monkeypatch.setenv(LOG_LEVEL_ENV, "DEBUG")
    configure_logging()
    assert logging.getLogger().level == logging.DEBUG


def test_a_malformed_environment_variable_is_ignored_rather_than_fatal(monkeypatch):
    """A convenience that crashes a run at import time is worse than one that does nothing."""
    monkeypatch.setenv(LOG_LEVEL_ENV, "verbose-ish")
    assert log_level_from_env() is None
    configure_logging()
    assert logging.getLogger().level == logging.INFO


# -----------------------------------------------------------------------------------------------
# the argument, which is unchanged
# -----------------------------------------------------------------------------------------------


def test_an_explicit_level_name_is_used_as_named(monkeypatch):
    """The argument wins over the environment, which is the precedence the module documents."""
    monkeypatch.setenv(LOG_LEVEL_ENV, "DEBUG")
    configure_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING


def test_an_explicit_level_number_is_used_as_named(monkeypatch):
    monkeypatch.setenv(LOG_LEVEL_ENV, "DEBUG")
    configure_logging(logging.ERROR)
    assert logging.getLogger().level == logging.ERROR


@pytest.mark.parametrize("env", [None, "DEBUG", "warning", "verbose-ish"])
def test_the_default_agrees_with_resolving_the_environment_yourself(env, monkeypatch):
    """``configure_logging()`` and ``configure_logging(log_level_from_env() or "INFO")`` agree.

    The second form is what a caller has to write if the default is not usable, and the two have to
    resolve to the same level in every state the variable can be in — unset, usable, lower-case,
    malformed — or the shorthand is not a shorthand for it. The same case is covered by the CLI's
    own tests, where the shorthand is what the run actually calls.
    """
    if env is None:
        monkeypatch.delenv(LOG_LEVEL_ENV, raising=False)
    else:
        monkeypatch.setenv(LOG_LEVEL_ENV, env)

    configure_logging(log_level_from_env() or "INFO")
    written_out = logging.getLogger().level
    configure_logging()
    assert logging.getLogger().level == written_out
    assert written_out == (log_level_from_env() or logging.INFO)


def test_calling_it_twice_replaces_its_own_handler():
    """Idempotent: a record appears once, however many times the setup ran."""
    stream = io.StringIO()
    configure_logging(stream=stream)
    configure_logging(stream=stream)
    logging.getLogger("grover_emulator").info("once")
    assert stream.getvalue().count("once") == 1


# -----------------------------------------------------------------------------------------------
# what is still refused
# -----------------------------------------------------------------------------------------------


def test_a_level_that_is_not_a_level_still_raises():
    """A float is not a level and a name that is not one is not either; both fail where they are read."""
    with pytest.raises(TypeError, match="int, a str, or None"):
        configure_logging(1.5)
    with pytest.raises(TypeError, match="int, a str, or None"):
        configure_logging(object())
    with pytest.raises(ValueError, match="unknown log level"):
        configure_logging("LOUD")
    with pytest.raises(ValueError, match="unknown log level"):
        configure_logging("")
