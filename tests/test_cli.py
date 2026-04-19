import textwrap
from pathlib import Path
from unittest.mock import patch

from pio_env_graph.cli import main


def write_ini(tmp_path: Path, content: str) -> Path:
    ini = tmp_path / "platformio.ini"
    ini.write_text(textwrap.dedent(content))
    return ini


INI_CONTENT = """\
    [arduino]
    framework = arduino

    [esp8266]
    extends = arduino
    platform = espressif8266

    [env:hello]
    extends = esp8266
"""


def test_cli_explicit_path_stdout(tmp_path, capsys):
    path = write_ini(tmp_path, INI_CONTENT)
    with patch("sys.argv", ["pio-env-graph", str(path)]):
        main()
    captured = capsys.readouterr()
    assert "digraph platformio" in captured.out
    assert '"esp8266" -> "arduino"' in captured.out
    assert '"env:hello" -> "esp8266"' in captured.out


def test_cli_auto_discover(tmp_path, capsys, monkeypatch):
    write_ini(tmp_path, INI_CONTENT)
    monkeypatch.chdir(tmp_path)
    with patch("sys.argv", ["pio-env-graph"]):
        main()
    captured = capsys.readouterr()
    assert "digraph platformio" in captured.out


def test_cli_output_file(tmp_path):
    path = write_ini(tmp_path, INI_CONTENT)
    out_file = tmp_path / "graph.dot"
    with patch("sys.argv", ["pio-env-graph", str(path), "-o", str(out_file)]):
        main()
    content = out_file.read_text()
    assert "digraph platformio" in content
    assert '"esp8266" -> "arduino"' in content


def test_cli_missing_file(tmp_path, capsys):
    with patch("sys.argv", ["pio-env-graph", str(tmp_path / "nonexistent.ini")]):
        try:
            main()
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code != 0
    captured = capsys.readouterr()
    assert "not found" in captured.err.lower() or "no such file" in captured.err.lower()


def test_cli_direction_flag(tmp_path, capsys):
    path = write_ini(tmp_path, INI_CONTENT)
    with patch("sys.argv", ["pio-env-graph", str(path), "-d", "BT"]):
        main()
    captured = capsys.readouterr()
    assert "rankdir=BT" in captured.out


def test_cli_default_direction_lr(tmp_path, capsys):
    path = write_ini(tmp_path, INI_CONTENT)
    with patch("sys.argv", ["pio-env-graph", str(path)]):
        main()
    captured = capsys.readouterr()
    assert "rankdir=RL" in captured.out


def test_cli_auto_discover_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with patch("sys.argv", ["pio-env-graph"]):
        try:
            main()
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code != 0
