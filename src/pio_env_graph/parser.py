import configparser
import re
import sys
from pathlib import Path

from pio_env_graph.models import Graph, Section

_REF_PATTERN = re.compile(r"\$\{([^.}]+)\.[^}]+\}")


def _resolve_extra_configs(config: configparser.ConfigParser, base_dir: Path) -> list[Path]:
    """Extract extra_configs from [platformio] section and resolve paths.

    Supports glob patterns (e.g. ``boards/*.ini``) as PlatformIO does.
    """
    raw = config.get("platformio", "extra_configs", fallback="")
    paths: list[Path] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        matched = sorted(base_dir.glob(line))
        if matched:
            paths.extend(matched)
        else:
            print(
                f"Warning: extra_configs entry '{line}' matched no files",
                file=sys.stderr,
            )
    return paths


DISPLAY_ATTRS = ("platform", "framework", "board")


def parse(path: Path) -> Graph:
    base_dir = path.parent
    config = configparser.ConfigParser(interpolation=None)
    files_to_read = [path]
    files_to_read.extend(
        _resolve_extra_configs(
            _read_config(path),
            base_dir,
        )
    )

    # Read all files into one config
    config.read(files_to_read, encoding="utf-8")

    sections: dict[str, Section] = {}
    for name in config.sections():
        if name == "platformio":
            continue
        extends_raw = config.get(name, "extends", fallback="")
        extends = [e.strip() for e in extends_raw.split(",") if e.strip()]
        attrs = {}
        for key in DISPLAY_ATTRS:
            val = config.get(name, key, fallback="")
            if val:
                attrs[key] = val
        # Extract ${section.key} references
        refs: set[str] = set()
        for key in config.options(name):
            val = config.get(name, key, fallback="")
            for match in _REF_PATTERN.finditer(val):
                ref_section = match.group(1)
                if ref_section != name:  # skip self-references
                    refs.add(ref_section)
        sections[name] = Section(name=name, extends=extends, refs=sorted(refs), attrs=attrs)

    # Collect phantom extends targets
    all_names = set(sections.keys())
    phantoms: set[str] = set()
    for section in sections.values():
        for parent in section.extends:
            if parent not in all_names:
                phantoms.add(parent)
                print(
                    f"Warning: section [{section.name}] extends '{parent}' which is not defined in the file",
                    file=sys.stderr,
                )

    return Graph(sections=sections, phantoms=phantoms)


def _read_config(path: Path) -> configparser.ConfigParser:
    config = configparser.ConfigParser(interpolation=None)
    config.read(path, encoding="utf-8")
    return config
