from __future__ import annotations

from pgx_fhir.fhir import build_pgx_bundle_minimal, MinimalPgxRecord


def _resources_by_type(bundle: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for e in bundle.get("entry", []):
        r = e.get("resource", {})
        rtype = r.get("resourceType")
        if not rtype:
            continue
        out.setdefault(rtype, []).append(r)
    return out


def test_build_pgx_bundle_minimal_references_and_structure() -> None:
    bundle = build_pgx_bundle_minimal(
        patient_id="P1",
        specimen_id="S1",
        birth_date="1991-10-09",
        sex="female",
        specimen_type_text="blood",
        pgx_results=[
            MinimalPgxRecord(gene="CYP2C19", diplotype="*1/*2", phenotype="intermediate metabolizer"),
            MinimalPgxRecord(gene="CYP2D6", diplotype="*1/*4", phenotype="intermediate metabolizer"),
        ],
    )

    # Bundle shape
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert "entry" in bundle and isinstance(bundle["entry"], list)
    assert len(bundle["entry"]) >= 2

    by_type = _resources_by_type(bundle)

    # Must include Patient + Specimen
    assert "Patient" in by_type and len(by_type["Patient"]) == 1
    assert "Specimen" in by_type and len(by_type["Specimen"]) == 1
    assert "Observation" in by_type and len(by_type["Observation"]) == 2

    patient = by_type["Patient"][0]
    specimen = by_type["Specimen"][0]

    # IDs are the ones we set
    assert patient["id"] == "P1"
    assert specimen["id"] == "S1"

    # Specimen must reference Patient
    assert specimen["subject"]["reference"] == "Patient/P1"

    # Each Observation must reference Patient + Specimen and include gene component
    for obs in by_type["Observation"]:
        assert obs["resourceType"] == "Observation"
        assert obs["status"] == "final"
        assert obs["subject"]["reference"] == "Patient/P1"
        assert obs["specimen"]["reference"] == "Specimen/S1"

        comps = obs.get("component", [])
        assert isinstance(comps, list) and len(comps) >= 1

        # gene component must exist and be non-empty
        gene_values = [
            c.get("valueString")
            for c in comps
            if c.get("code", {}).get("text") == "gene"
        ]
        assert len(gene_values) == 1
        assert isinstance(gene_values[0], str) and gene_values[0].strip()
