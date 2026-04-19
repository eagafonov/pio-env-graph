from pathlib import Path

from pio_env_graph.parser import parse
from pio_env_graph.renderers.dot import render

FIXTURE = Path(__file__).parent / "fixtures" / "platformio.ini"


def test_parse_real_ini():
    graph = parse(FIXTURE)
    # Verify key sections exist
    assert "env" in graph.sections
    assert "arduino" in graph.sections
    assert "esp8266" in graph.sections
    assert "esp32" in graph.sections
    assert "env:gpio" in graph.sections
    assert "hw:wemos-d1-mini" in graph.sections


def test_parse_real_ini_extends():
    graph = parse(FIXTURE)
    assert "arduino" in graph.sections["esp8266"].extends
    assert "esp32" in graph.sections["esp32s3"].extends
    assert "hw:default" in graph.sections["env:gpio"].extends


def test_parse_real_ini_multi_extends():
    graph = parse(FIXTURE)
    section = graph.sections["env:hello-world-d1-mini"]
    assert "hw:wemos-d1-mini" in section.extends
    assert "env:hello-world" in section.extends


def test_render_real_ini_produces_valid_dot():
    graph = parse(FIXTURE)
    dot = render(graph)
    lines = dot.strip().splitlines()
    assert lines[0].strip().startswith("digraph")
    assert lines[-1].strip() == "}"
    # Spot-check some edges
    assert '"esp8266" -> "arduino"' in dot
    assert '"env:gpio" -> "hw:default"' in dot


def test_render_real_ini_env_styling():
    graph = parse(FIXTURE)
    dot = render(graph)
    # env: sections should have green
    assert '"env:gpio"' in dot
    assert "#d4edda" in dot
    # non-env sections should have gray
    assert '"esp32"' in dot
    assert "#e2e2e2" in dot


def test_parse_real_ini_attrs():
    graph = parse(FIXTURE)
    assert graph.sections["esp8266"].attrs["platform"] == "espressif8266"
    assert graph.sections["arduino"].attrs["framework"] == "arduino"
    assert graph.sections["hw:wemos-d1-mini"].attrs["board"] == "d1_mini"
