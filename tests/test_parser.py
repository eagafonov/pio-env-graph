import textwrap
from pathlib import Path

from pio_env_graph.parser import parse


def write_ini(tmp_path: Path, content: str) -> Path:
    ini = tmp_path / "platformio.ini"
    ini.write_text(textwrap.dedent(content))
    return ini


def test_parse_single_section_no_extends(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [env]
        monitor_speed = 115200
    """,
    )
    graph = parse(path)
    assert "env" in graph.sections
    assert graph.sections["env"].extends == []


def test_parse_single_extends(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [arduino]
        framework = arduino

        [esp8266]
        extends = arduino
        platform = espressif8266
    """,
    )
    graph = parse(path)
    assert graph.sections["esp8266"].extends == ["arduino"]


def test_parse_multiple_extends(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [hw:wemos-d1-mini]
        board = d1_mini

        [env:hello-world]
        build_src_filter = +<hello-world/**>

        [env:hello-world-d1-mini]
        extends = hw:wemos-d1-mini, env:hello-world
    """,
    )
    graph = parse(path)
    section = graph.sections["env:hello-world-d1-mini"]
    assert section.extends == ["hw:wemos-d1-mini", "env:hello-world"]


def test_parse_is_env_flag(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [env]
        monitor_speed = 115200

        [env:gpio]
        extends = env
    """,
    )
    graph = parse(path)
    assert graph.sections["env"].is_env is False
    assert graph.sections["env:gpio"].is_env is True


def test_parse_missing_extends_target_warns(tmp_path, capsys):
    path = write_ini(
        tmp_path,
        """\
        [env:hello-world-esp32]
        extends = esp32, env:hello-world
    """,
    )
    graph = parse(path)
    assert graph.sections["env:hello-world-esp32"].extends == [
        "esp32",
        "env:hello-world",
    ]
    assert graph.phantoms == {"esp32", "env:hello-world"}
    captured = capsys.readouterr()
    assert "esp32" in captured.err
    assert "env:hello-world" in captured.err


def test_parse_ignores_default_section(tmp_path):
    """configparser has a DEFAULT section - we should skip it."""
    path = write_ini(
        tmp_path,
        """\
        [env]
        monitor_speed = 115200
    """,
    )
    graph = parse(path)
    assert "DEFAULT" not in graph.sections


def test_parse_ignores_platformio_section(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [platformio]
        src_dir = src

        [env]
        monitor_speed = 115200
    """,
    )
    graph = parse(path)
    assert "platformio" not in graph.sections
    assert "env" in graph.sections


def test_parse_extra_configs(tmp_path):
    main_ini = tmp_path / "platformio.ini"
    main_ini.write_text(textwrap.dedent("""\
        [platformio]
        extra_configs = extra.ini

        [arduino]
        framework = arduino
    """))
    extra_ini = tmp_path / "extra.ini"
    extra_ini.write_text(textwrap.dedent("""\
        [esp8266]
        extends = arduino
        platform = espressif8266
    """))
    graph = parse(main_ini)
    assert "arduino" in graph.sections
    assert "esp8266" in graph.sections
    assert graph.sections["esp8266"].extends == ["arduino"]


def test_parse_extra_configs_multiple(tmp_path):
    main_ini = tmp_path / "platformio.ini"
    main_ini.write_text(textwrap.dedent("""\
        [platformio]
        extra_configs = extra1.ini
                        extra2.ini

        [base]
        framework = arduino
    """))
    (tmp_path / "extra1.ini").write_text(textwrap.dedent("""\
        [esp8266]
        extends = base
    """))
    (tmp_path / "extra2.ini").write_text(textwrap.dedent("""\
        [env:hello]
        extends = esp8266
    """))
    graph = parse(main_ini)
    assert "base" in graph.sections
    assert "esp8266" in graph.sections
    assert "env:hello" in graph.sections
    assert graph.sections["env:hello"].extends == ["esp8266"]


def test_parse_extra_configs_missing_file_warns(tmp_path, capsys):
    main_ini = tmp_path / "platformio.ini"
    main_ini.write_text(textwrap.dedent("""\
        [platformio]
        extra_configs = nonexistent.ini

        [env]
        monitor_speed = 115200
    """))
    graph = parse(main_ini)
    assert "env" in graph.sections
    captured = capsys.readouterr()
    assert "nonexistent.ini" in captured.err


def test_parse_attrs(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [esp8266]
        platform = espressif8266
        framework = arduino
        board = d1_mini
        build_flags = -DFOO
    """,
    )
    graph = parse(path)
    s = graph.sections["esp8266"]
    assert s.attrs == {
        "platform": "espressif8266",
        "framework": "arduino",
        "board": "d1_mini",
    }


def test_parse_attrs_empty_when_missing(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [env]
        monitor_speed = 115200
    """,
    )
    graph = parse(path)
    assert graph.sections["env"].attrs == {}


def test_parse_refs(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [env]
        build_src_filter = -<**>

        [esp_defaults]
        build_flags = -DFOO

        [env:hello]
        build_src_filter =
            ${env.build_src_filter}
            +<hello/**>
        build_flags = ${esp_defaults.build_flags}
    """,
    )
    graph = parse(path)
    assert sorted(graph.sections["env:hello"].refs) == ["env", "esp_defaults"]


def test_parse_refs_skip_self_reference(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [env]
        base_flags = -DBASE
        build_flags = ${env.base_flags} -DEXTRA
    """,
    )
    graph = parse(path)
    assert graph.sections["env"].refs == []


def test_parse_refs_empty_when_no_refs(tmp_path):
    path = write_ini(
        tmp_path,
        """\
        [env]
        monitor_speed = 115200
    """,
    )
    graph = parse(path)
    assert graph.sections["env"].refs == []


def test_parse_extra_configs_glob(tmp_path):
    main_ini = tmp_path / "platformio.ini"
    main_ini.write_text(textwrap.dedent("""\
        [platformio]
        extra_configs = extras/*.ini

        [base]
        framework = arduino
    """))
    extras_dir = tmp_path / "extras"
    extras_dir.mkdir()
    (extras_dir / "esp8266.ini").write_text(textwrap.dedent("""\
        [esp8266]
        extends = base
    """))
    (extras_dir / "esp32.ini").write_text(textwrap.dedent("""\
        [esp32]
        extends = base
    """))
    graph = parse(main_ini)
    assert "base" in graph.sections
    assert "esp8266" in graph.sections
    assert "esp32" in graph.sections


def test_parse_extra_configs_glob_no_match_warns(tmp_path, capsys):
    main_ini = tmp_path / "platformio.ini"
    main_ini.write_text(textwrap.dedent("""\
        [platformio]
        extra_configs = boards/*.ini

        [env]
        monitor_speed = 115200
    """))
    graph = parse(main_ini)
    assert "env" in graph.sections
    captured = capsys.readouterr()
    assert "boards/*.ini" in captured.err
    assert "matched no files" in captured.err
