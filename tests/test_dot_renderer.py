from pio_env_graph.models import Graph, Section
from pio_env_graph.renderers.dot import render, _dot_escape


def make_graph(*sections: Section) -> Graph:
    return Graph(sections={s.name: s for s in sections})


def test_render_empty_graph():
    graph = make_graph()
    dot = render(graph)
    assert "digraph platformio" in dot
    assert "rankdir=RL" in dot


def test_render_rankdir_override():
    graph = make_graph()
    dot = render(graph, rankdir="BT")
    assert "rankdir=BT" in dot


def test_render_single_node():
    graph = make_graph(Section(name="env", extends=[]))
    dot = render(graph)
    assert '"env"' in dot


def test_render_extends_edge():
    graph = make_graph(
        Section(name="arduino", extends=[]),
        Section(name="esp8266", extends=["arduino"]),
    )
    dot = render(graph)
    assert '"esp8266" -> "arduino"' in dot


def test_render_multiple_extends_edges():
    graph = make_graph(
        Section(name="hw:wemos-d1-mini", extends=[]),
        Section(name="env:hello-world", extends=[]),
        Section(
            name="env:hello-world-d1-mini",
            extends=["hw:wemos-d1-mini", "env:hello-world"],
        ),
    )
    dot = render(graph)
    assert '"env:hello-world-d1-mini" -> "hw:wemos-d1-mini"' in dot
    assert '"env:hello-world-d1-mini" -> "env:hello-world"' in dot


def test_render_env_node_green_fill():
    graph = make_graph(Section(name="env:gpio", extends=[]))
    dot = render(graph)
    assert '"env:gpio"' in dot
    assert "#d4edda" in dot


def test_render_non_env_node_gray_fill():
    graph = make_graph(Section(name="esp32", extends=[]))
    dot = render(graph)
    assert '"esp32"' in dot
    assert "#e2e2e2" in dot


def test_render_is_valid_dot_syntax():
    """The output should start with digraph and end with closing brace."""
    graph = make_graph(
        Section(name="arduino", extends=[]),
        Section(name="esp8266", extends=["arduino"]),
    )
    dot = render(graph)
    lines = dot.strip().splitlines()
    assert lines[0].strip().startswith("digraph")
    assert lines[-1].strip() == "}"


def test_render_node_with_attrs():
    graph = make_graph(
        Section(
            name="esp8266",
            extends=[],
            attrs={"platform": "espressif8266", "framework": "arduino"},
        ),
    )
    dot = render(graph)
    assert "platform: espressif8266" in dot
    assert "framework: arduino" in dot


def test_render_node_without_attrs():
    graph = make_graph(
        Section(name="env", extends=[]),
    )
    dot = render(graph)
    assert 'label="env"' in dot


def test_render_ref_edge_dashed():
    graph = make_graph(
        Section(name="env", extends=[]),
        Section(name="env:hello", extends=[], refs=["env"]),
    )
    dot = render(graph, show_refs=True)
    assert '"env:hello" -> "env" [style=dashed' in dot


def test_render_ref_edge_hidden_by_default():
    graph = make_graph(
        Section(name="env", extends=[]),
        Section(name="env:hello", extends=[], refs=["env"]),
    )
    dot = render(graph)
    assert "dashed" not in dot


def test_render_phantom_node():
    graph = Graph(
        sections={"env:hello": Section(name="env:hello", extends=["missing"])},
        phantoms={"missing"},
    )
    dot = render(graph)
    assert "(missing)" in dot
    assert "#f8d7da" in dot
    assert "#dc3545" in dot


def test_render_no_phantom_when_all_defined():
    graph = make_graph(
        Section(name="base", extends=[]),
        Section(name="env:hello", extends=["base"]),
    )
    dot = render(graph)
    assert "(missing)" not in dot


def test_render_extends_suppresses_ref_edge():
    """If a section both extends and refs the same target, only solid edge."""
    graph = make_graph(
        Section(name="env", extends=[]),
        Section(name="env:hello", extends=["env"], refs=["env"]),
    )
    dot = render(graph, show_refs=True)
    assert '"env:hello" -> "env"' in dot
    assert "dashed" not in dot


def test_dot_escape_quotes():
    assert _dot_escape('say "hello"') == 'say \\"hello\\"'


def test_dot_escape_backslash():
    assert _dot_escape("back\\slash") == "back\\\\slash"


def test_dot_escape_newline():
    assert _dot_escape("line1\nline2") == "line1\\nline2"


def test_render_node_name_with_quote():
    graph = make_graph(Section(name='sec"tion', extends=[]))
    dot = render(graph)
    assert 'sec\\"tion' in dot


def test_render_attr_value_with_quote():
    graph = make_graph(
        Section(name="esp", extends=[], attrs={"platform": 'val"ue'}),
    )
    dot = render(graph)
    assert 'val\\"ue' in dot
    # escaped quotes should not break DOT structure
    lines = dot.strip().splitlines()
    assert lines[0].strip().startswith("digraph")
    assert lines[-1].strip() == "}"
