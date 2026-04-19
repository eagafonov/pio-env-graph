from pio_env_graph.models import Graph

ENV_COLOR = "#d4edda"
DEFAULT_COLOR = "#e2e2e2"
PHANTOM_COLOR = "#f8d7da"
PHANTOM_BORDER = "#dc3545"


def _dot_escape(s: str) -> str:
    """Escape a string for use inside DOT double-quoted strings."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _node_label(section) -> str:
    """Build a node label with name and optional attributes."""
    if not section.attrs:
        return _dot_escape(section.name)
    attr_lines = "\\n".join(f"{k}: {_dot_escape(v)}" for k, v in section.attrs.items())
    return f"{_dot_escape(section.name)}\\n{attr_lines}"


def render(graph: Graph, rankdir: str = "RL", show_refs: bool = False) -> str:
    lines: list[str] = []
    lines.append("digraph platformio {")
    lines.append(f"    rankdir={rankdir}")
    lines.append("    node [shape=box]")
    lines.append("")

    # Node definitions with styling
    for section in graph.sections.values():
        color = ENV_COLOR if section.is_env else DEFAULT_COLOR
        label = _node_label(section)
        esc_name = _dot_escape(section.name)
        lines.append(f'    "{esc_name}" [label="{label}", style=filled, fillcolor="{color}"]')

    # Phantom nodes (referenced but not defined)
    for name in sorted(graph.phantoms):
        esc_name = _dot_escape(name)
        lines.append(
            f'    "{esc_name}" [label="{esc_name}\\n(missing)", style="filled,dashed", '
            f'fillcolor="{PHANTOM_COLOR}", color="{PHANTOM_BORDER}", penwidth=2]'
        )

    lines.append("")

    # Edges: child -> parent (extends, solid)
    for section in graph.sections.values():
        for parent in section.extends:
            lines.append(f'    "{_dot_escape(section.name)}" -> "{_dot_escape(parent)}"')

    # Edges: referrer -> referenced (${section.key}, dashed)
    if show_refs:
        for section in graph.sections.values():
            for ref in section.refs:
                if ref not in section.extends:
                    lines.append(
                        f'    "{_dot_escape(section.name)}" -> "{_dot_escape(ref)}" [style=dashed, color="#888888"]'
                    )

    lines.append("}")
    return "\n".join(lines) + "\n"
