"""Tests for the command line: errors must never show a traceback."""
from pathlib import Path

import pytest

from pacman_game import cli
from pacman_game.renderer import RendererError


def run_main(monkeypatch: pytest.MonkeyPatch, *arguments: str) -> int:
    """Call main() as if the program had been started with arguments."""
    monkeypatch.setattr("sys.argv", ["pac-man.py", *arguments])
    return cli.main()


def write_config(tmp_path: Path) -> str:
    """Write a small valid config file and return its path."""
    path = tmp_path / "config.json"
    scores = tmp_path / "scores.json"
    path.write_text('# comment\n{"highscore_filename": "%s"}' % scores,
                    encoding="utf-8")
    return str(path)


@pytest.mark.parametrize("arguments", [(), ("a.json", "b.json")])
def test_wrong_number_of_arguments(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        arguments: tuple[str, ...]) -> None:
    """Exactly one argument is required."""
    assert run_main(monkeypatch, *arguments) == 1
    assert "Usage" in capsys.readouterr().err


def test_missing_config_file(monkeypatch: pytest.MonkeyPatch,
                             capsys: pytest.CaptureFixture[str]) -> None:
    """A missing file gives a clear message and no traceback."""
    assert run_main(monkeypatch, "nothing_here.json") == 1
    error = capsys.readouterr().err
    assert "not found" in error and "Traceback" not in error


def test_broken_config_file(monkeypatch: pytest.MonkeyPatch,
                            capsys: pytest.CaptureFixture[str],
                            tmp_path: Path) -> None:
    """Invalid JSON is reported with its line."""
    path = tmp_path / "broken.json"
    path.write_text("{ \"lives\": ", encoding="utf-8")
    assert run_main(monkeypatch, str(path)) == 1
    error = capsys.readouterr().err
    assert "Invalid JSON" in error and "Traceback" not in error


def test_window_cannot_be_opened(monkeypatch: pytest.MonkeyPatch,
                                 capsys: pytest.CaptureFixture[str],
                                 tmp_path: Path) -> None:
    """A missing display is reported cleanly."""
    def no_window(*args: object) -> None:
        raise RendererError("Cannot open the game window: no display")

    monkeypatch.setattr(cli, "Renderer", no_window)
    assert run_main(monkeypatch, write_config(tmp_path)) == 1
    assert "no display" in capsys.readouterr().err


def test_normal_run_closes_the_window(monkeypatch: pytest.MonkeyPatch,
                                      tmp_path: Path) -> None:
    """When the app ends, the exit code is 0 and the window is closed."""
    calls: list[str] = []
    monkeypatch.setattr(cli.App, "run", lambda self: calls.append("run"))
    original_close = cli.Renderer.close

    def close(self: cli.Renderer) -> None:
        calls.append("close")
        original_close(self)

    monkeypatch.setattr(cli.Renderer, "close", close)
    assert run_main(monkeypatch, write_config(tmp_path)) == 0
    assert calls == ["run", "close"]


def test_unexpected_error_has_no_traceback(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        tmp_path: Path) -> None:
    """Even a bug shows one line; PACMAN_DEBUG shows the full error."""
    def explode(self: cli.App) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli.App, "run", explode)
    config = write_config(tmp_path)
    monkeypatch.delenv("PACMAN_DEBUG", raising=False)
    assert run_main(monkeypatch, config) == 1
    assert "Unexpected error: boom" in capsys.readouterr().err
    monkeypatch.setenv("PACMAN_DEBUG", "1")
    with pytest.raises(RuntimeError):
        run_main(monkeypatch, config)


def test_ctrl_c_is_silent(monkeypatch: pytest.MonkeyPatch,
                          tmp_path: Path) -> None:
    """Ctrl+C ends the game quietly."""
    def interrupt(self: cli.App) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli.App, "run", interrupt)
    assert run_main(monkeypatch, write_config(tmp_path)) == 0
