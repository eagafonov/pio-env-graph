from dataclasses import dataclass, field


@dataclass
class Section:
    name: str
    extends: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)

    @property
    def is_env(self) -> bool:
        return self.name.startswith("env:")


@dataclass
class Graph:
    sections: dict[str, Section] = field(default_factory=dict)
    phantoms: set[str] = field(default_factory=set)
