from hashlib import sha256

from gradient.integration.contracts import (
    Candidate,
    Citation,
    Finding,
    ModuleOutput,
    ModuleSpec,
    OpportunityEvidence,
    OpportunityView,
    Review,
)


class ResultAggregator:
    """Join module outputs by stable IDs; structural checks do not replace Peter's Verifier."""

    def __init__(self, run_id: str, demo: bool = False):
        self.run_id = run_id
        self.demo = demo
        self.outputs: dict[str, ModuleOutput] = {}
        self.specs: dict[str, ModuleSpec] = {}

    def accept(self, spec: ModuleSpec, output: ModuleOutput) -> None:
        if output.run_id != self.run_id or output.module_id != spec.name:
            raise ValueError("Module output belongs to a different run or module")
        if spec.name in self.outputs:
            if self.outputs[spec.name] == output:
                return  # Idempotent replay; revisions require a new run.
            raise ValueError("Conflicting second output from a completed module")
        self.outputs[spec.name] = output
        self.specs[spec.name] = spec

    def build(self) -> tuple[tuple[OpportunityView, ...], tuple[str, ...]]:
        evidence: dict[str, Citation] = {}
        candidates: dict[str, Candidate] = {}
        findings: dict[str, Finding] = {}
        reviews: dict[str, list[Review]] = {}
        origins: dict[str, set[str]] = {}
        warnings: list[str] = []
        invalid_evidence: set[str] = set()
        invalid_findings: set[str] = set()
        conflicting_candidates: set[str] = set()
        ordered = sorted(self.outputs)
        for name in ordered:
            output = self.outputs[name]
            warnings.extend(f"{name}: {warning}" for warning in output.warnings)
            for item in output.evidence:
                previous = evidence.get(item.id)
                if previous and previous != item:
                    invalid_evidence.add(item.id)
                    warnings.append(f"Conflicting evidence ID {item.id}; excluded.")
                else:
                    evidence[item.id] = item
        for key in invalid_evidence:
            evidence.pop(key, None)

        def cited(ids: tuple[str, ...], candidate_id: str) -> bool:
            return bool(ids) and all(
                key in evidence and evidence[key].candidate_id == candidate_id for key in ids
            )

        for name in ordered:
            output = self.outputs[name]
            for candidate in output.candidates:
                if self.specs[name].role != "scout":
                    warnings.append(f"{name}: only Scout may establish candidate identity.")
                    continue
                if not cited(candidate.evidence_ids, candidate.candidate_id):
                    warnings.append(f"Unresolved identity citations for {candidate.candidate_id}.")
                    continue
                previous = candidates.get(candidate.candidate_id)
                if previous and previous.model_dump(
                    exclude={"evidence_ids"}
                ) != candidate.model_dump(exclude={"evidence_ids"}):
                    conflicting_candidates.add(candidate.candidate_id)
                else:
                    candidates[candidate.candidate_id] = candidate
                origins.setdefault(candidate.candidate_id, set()).add(name)
            for finding in output.findings:
                if finding.field != "uncertainty" and not cited(
                    finding.evidence_ids, finding.candidate_id
                ):
                    warnings.append(f"Unresolved citations for finding {finding.id}; excluded.")
                    continue
                if finding.evidence_ids and not cited(finding.evidence_ids, finding.candidate_id):
                    warnings.append(f"Cross-candidate or unresolved citations for {finding.id}.")
                    continue
                previous = findings.get(finding.id)
                if previous and previous != finding:
                    invalid_findings.add(finding.id)
                    warnings.append(f"Conflicting finding ID {finding.id}; excluded.")
                else:
                    findings[finding.id] = finding
                    origins.setdefault(finding.candidate_id, set()).add(name)
        for key in invalid_findings:
            findings.pop(key, None)

        for name in ordered:
            for review in self.outputs[name].reviews:
                if self.specs[name].role != "verifier":
                    warnings.append(f"{name}: recommendations require a Verifier output.")
                    continue
                ids = (*review.accepted_finding_ids, *review.rejected_finding_ids)
                if not all(
                    key in findings and findings[key].candidate_id == review.candidate_id
                    for key in ids
                ) or set(review.accepted_finding_ids) & set(review.rejected_finding_ids):
                    warnings.append(
                        f"Invalid review references for {review.candidate_id}; ignored."
                    )
                    continue
                reviews.setdefault(review.candidate_id, []).append(review)
                origins.setdefault(review.candidate_id, set()).add(name)

        opportunities = []
        for key, candidate in sorted(candidates.items()):
            if key in conflicting_candidates:
                warnings.append(f"Conflicting candidate identity for {key}; candidate withheld.")
                continue
            candidate_reviews = reviews.get(key, [])
            accepted = set().union(*(set(r.accepted_finding_ids) for r in candidate_reviews))
            rejected = set().union(*(set(r.rejected_finding_ids) for r in candidate_reviews))
            conflicted = (
                bool(accepted & rejected) or len({r.recommendation for r in candidate_reviews}) > 1
            )
            accepted -= rejected
            usable = [
                f for f in findings.values() if f.candidate_id == key and f.id not in rejected
            ]
            if candidate_reviews:
                usable = [f for f in usable if f.id in accepted or f.field == "uncertainty"]
            unknowns = [text for review in candidate_reviews for text in review.unknowns]
            if not candidate_reviews:
                unknowns.append("Evidence review is pending; research findings are provisional.")
            if conflicted:
                unknowns.append("Verifier outputs disagree; a human review is required.")

            def field_value(
                field: str,
                default: str,
                usable: list[Finding] = usable,
                unknowns: list[str] = unknowns,
            ) -> str:
                values = sorted({f.text for f in usable if f.field == field})
                if len(values) > 1:
                    unknowns.append(
                        f"Research modules supplied differing {field} findings: "
                        + " | ".join(values)
                    )
                    return "Conflicting findings; see open questions."
                return values[0] if values else default

            description = field_value(
                "description", "Project description has not been established."
            )
            demand = field_value("demand", "Customer demand has not been established.")
            trigger = field_value("trigger", "No recent trigger has been established.")
            thesis = field_value("thesis", "Thesis fit is awaiting research.")
            market = field_value("market", "Market research has not been supplied.")
            unknowns.extend(f.text for f in usable if f.field == "uncertainty")
            recommendation = "Needs validation"
            if candidate_reviews and not conflicted:
                recommendation = candidate_reviews[0].recommendation
                demand_claims = [f for f in usable if f.field == "demand" and f.id in accepted]
                if (
                    recommendation == "Worth a conversation"
                    and len({f.text for f in demand_claims}) != 1
                ):
                    recommendation = "Needs validation"
                    unknowns.append("A positive recommendation requires a reviewed demand finding.")
            unique_evidence: dict[str, Citation] = {}
            for citation in evidence.values():
                if citation.candidate_id == key:
                    # Exact URL (including comment fragments) identifies a source item.
                    existing = unique_evidence.get(str(citation.url))
                    if existing and existing.excerpt != citation.excerpt:
                        unknowns.append("Different excerpts were supplied for the same source URL.")
                    else:
                        unique_evidence[str(citation.url)] = citation
            display_name = candidate.name or "Builder identity unknown"
            opportunities.append(
                OpportunityView(
                    id=f"{self.run_id}:{sha256(key.encode()).hexdigest()[:20]}",
                    runId=self.run_id,
                    candidateId=key,
                    name=display_name,
                    initials="".join(part[0] for part in display_name.split()[:2]).upper(),
                    project=candidate.project,
                    handle=candidate.handle or "Unknown",
                    category=candidate.category,
                    recommendation=recommendation,
                    description=description,
                    demand=demand,
                    trigger=trigger,
                    thesis=thesis,
                    market=market,
                    uncertainty=" ".join(dict.fromkeys(unknowns))
                    or "Company formation, revenue and fundraising remain unknown.",
                    evidence=tuple(
                        OpportunityEvidence(
                            id=e.id,
                            title=e.title,
                            quote=e.excerpt,
                            kind=e.kind,
                            author=e.author or "Unknown",
                            source=e.source,
                            date=e.date or "Date unknown",
                            sourceUrl=e.url,
                            isDemo=self.demo,
                            interpretation=" ".join(
                                f.text for f in usable if e.id in f.evidence_ids
                            )
                            or "Source supplied by the research module; interpretation is pending.",
                            limitation=e.limitation,
                        )
                        for e in unique_evidence.values()
                    ),
                    questions=tuple(
                        dict.fromkeys(q for r in candidate_reviews for q in r.questions)
                    )
                    or (
                        "Which user problem repeats, and what direct evidence supports it?",
                        "Is the builder interested in forming a company?",
                    ),
                    isDemo=self.demo,
                    reviewStatus="conflicted"
                    if conflicted
                    else "reviewed"
                    if candidate_reviews
                    else "pending",
                    modules=tuple(sorted(origins.get(key, set()))),
                )
            )
        priority = {"Worth a conversation": 0, "Needs validation": 1, "Watch": 2}
        opportunities.sort(key=lambda item: (priority[item.recommendation], item.project, item.id))
        return tuple(opportunities), tuple(dict.fromkeys(warnings))
