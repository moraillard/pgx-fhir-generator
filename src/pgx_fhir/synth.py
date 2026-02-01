from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

from .models import Patient, Specimen, PgXGeneResult, PgXInput


def make_synthetic_input(seed: int = 7) -> PgXInput:
    rng = random.Random(seed)

    patient = Patient(
        patient_id=f"P{rng.randint(1000, 9999)}",
        given_name=rng.choice(["Maria", "Sofia", "Valentina", "Camila", "Daniela"]),
        family_name=rng.choice(["Perez", "Gonzalez", "Rojas", "Soto", "Torres"]),
        birth_date=date(1991, 10, 9),
        sex="female",
    )

    specimen = Specimen(
        specimen_id=f"S{rng.randint(1000, 9999)}",
        patient_id=patient.patient_id,
        specimen_type=rng.choice(["blood", "saliva"]),
        collected_on=date.today(),
    )

    results = [
        PgXGeneResult(gene="CYP2C19", diplotype="*1/*2", phenotype="intermediate metabolizer"),
        PgXGeneResult(gene="CYP2D6", diplotype="*1/*4", phenotype="intermediate metabolizer", activity_score=1.0),
        PgXGeneResult(gene="SLCO1B1", diplotype="*1/*5", phenotype="decreased function"),
    ]

    return PgXInput(patient=patient, specimen=specimen, results=results, ruleset_version="0.1")


def write_input_json(out_path: str | Path, seed: int = 7) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = make_synthetic_input(seed=seed).model_dump(mode="json")
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_path
