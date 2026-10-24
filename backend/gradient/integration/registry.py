import importlib
import os

from gradient.integration.contracts import ModuleContext, ModuleOutput, ModuleSpec, ResearchModule


class UnavailableModule:
    def __init__(self, name: str, label: str, role: str, depends_on: tuple[str, ...]):
        self._spec = ModuleSpec.model_validate(
            {
                "name": name,
                "label": label,
                "role": role,
                "depends_on": depends_on,
                "available": False,
            }
        )

    @property
    def spec(self) -> ModuleSpec:
        return self._spec

    async def run(self, context: ModuleContext) -> ModuleOutput:
        raise RuntimeError("Research module is not registered")


class ModuleRegistry:
    def __init__(self, *modules: ResearchModule, demo: bool = False):
        if not 1 <= len(modules) <= 8:
            raise ValueError("Register between one and eight research modules")
        self.demo = demo
        self.modules: dict[str, ResearchModule] = {}
        for module in modules:
            if module.spec.name in self.modules:
                raise ValueError(f"Duplicate module: {module.spec.name}")
            self.modules[module.spec.name] = module
        visited: set[str] = set()

        def visit(name: str, path: set[str]) -> None:
            if name in path:
                raise ValueError("Research module dependencies contain a cycle")
            if name not in self.modules:
                raise ValueError(f"Missing module dependency: {name}")
            if name in visited:
                return
            for dependency in self.modules[name].spec.depends_on:
                visit(dependency, path | {name})
            visited.add(name)

        for name in self.modules:
            visit(name, set())


def load_modules() -> ModuleRegistry:
    # Server-controlled import path, never accepted from an HTTP request.
    factory_path = os.getenv("GRADIENT_MODULE_FACTORY")
    if factory_path:
        module_path, factory_name = factory_path.split(":", 1)
        registry = getattr(importlib.import_module(module_path), factory_name)()
        if not isinstance(registry, ModuleRegistry):
            raise TypeError("Module factory must return ModuleRegistry")
        return registry
    return ModuleRegistry(
        UnavailableModule("scout", "Builder discovery", "scout", ()),
        UnavailableModule("market", "Market research", "market", ("scout",)),
        UnavailableModule("verifier", "Evidence review", "verifier", ("scout", "market")),
    )
