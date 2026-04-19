from pio_env_graph.models import Section, Graph


def test_section_is_env_true_for_env_prefix():
    s = Section(name="env:gpio", extends=["hw:default"])
    assert s.is_env is True


def test_section_is_env_false_for_plain_section():
    s = Section(name="esp32", extends=["arduino"])
    assert s.is_env is False


def test_section_is_env_false_for_env_base():
    s = Section(name="env", extends=[])
    assert s.is_env is False


def test_graph_holds_sections():
    s1 = Section(name="arduino", extends=[])
    s2 = Section(name="esp32", extends=["arduino"])
    g = Graph(sections={"arduino": s1, "esp32": s2})
    assert g.sections["esp32"].extends == ["arduino"]
