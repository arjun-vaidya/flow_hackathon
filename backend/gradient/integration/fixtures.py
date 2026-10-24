"""Synthetic contract harness, only enabled by explicit server configuration."""

import asyncio

from gradient.integration.contracts import (
    Candidate,
    Citation,
    Finding,
    ModuleContext,
    ModuleOutput,
    ModuleSpec,
    Review,
)
from gradient.integration.registry import ModuleRegistry


class FixtureModule:
    def __init__(self, spec: ModuleSpec):
        self.spec = spec

    async def run(self, context: ModuleContext) -> ModuleOutput:
        await asyncio.sleep(0.15)
        common = {"run_id": context.run_id, "module_id": self.spec.name}
        if self.spec.role == "scout":
            return ModuleOutput(
                **common,
                candidates=(
                    Candidate(
                        candidate_id="fixture:replay",
                        project="Replay Fixture",
                        name="Synthetic Builder",
                        category="Agent infrastructure",
                        evidence_ids=("fixture:identity",),
                    ),
                ),
                evidence=(
                    Citation(
                        id="fixture:identity",
                        candidate_id="fixture:replay",
                        url="https://example.com/gradient-fixture",
                        title="Synthetic project and user request",
                        excerpt="Invented: a builder ships replay; a user requests hosting.",
                        source="Integration fixture",
                        kind="Self-reported",
                        limitation="Synthetic excerpt and URL; no real demand established.",
                    ),
                ),
                findings=(
                    Finding(
                        id="fixture:demand",
                        candidate_id="fixture:replay",
                        field="demand",
                        text="A fictional user requests managed replay.",
                        evidence_ids=("fixture:identity",),
                    ),
                    Finding(
                        id="fixture:description",
                        candidate_id="fixture:replay",
                        field="description",
                        text="A synthetic project for testing module integration.",
                        evidence_ids=("fixture:identity",),
                    ),
                ),
            )
        if self.spec.role == "market":
            return ModuleOutput(
                **common,
                findings=(
                    Finding(
                        id="fixture:market",
                        candidate_id="fixture:replay",
                        field="market",
                        text="Synthetic market context; no competitive research was performed.",
                        evidence_ids=("fixture:identity",),
                    ),
                ),
            )
        return ModuleOutput(
            **common,
            reviews=(
                Review(
                    candidate_id="fixture:replay",
                    recommendation="Needs validation",
                    accepted_finding_ids=(
                        "fixture:demand",
                        "fixture:description",
                        "fixture:market",
                    ),
                    unknowns=("This entire run is a synthetic integration fixture.",),
                    questions=("What would independently establish repeated user demand?",),
                ),
            ),
        )


def build_modules() -> ModuleRegistry:
    return ModuleRegistry(
        FixtureModule(ModuleSpec(name="scout", label="Fixture discovery", role="scout")),
        FixtureModule(
            ModuleSpec(name="market", label="Fixture market", role="market", depends_on=("scout",))
        ),
        FixtureModule(
            ModuleSpec(
                name="verifier",
                label="Fixture review",
                role="verifier",
                depends_on=("scout", "market"),
            )
        ),
        demo=True,
    )
