from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

Sex = Literal["female", "male", "unknown"]


class Patient(BaseModel):
    patient_id: str = Field(..., min_length=1)
    given_name: str = Field(..., min_length=1)
    family_name: str = Field(..., min_length=1)
    birth_date: date
    sex: Sex = "unknown"


class Specimen(BaseModel):
    specimen_id: str = Field(..., min_length=1)
    patient_id: str = Field(..., min_length=1)
    specimen_type: Literal["blood", "saliva", "tumor", "other"] = "blood"
    collected_on: date


class PgXGeneResult(BaseModel):
    gene: str = Field(..., min_length=2)
    diplotype: str = Field(..., min_length=1)
    phenotype: str = Field(..., min_length=1)
    activity_score: Optional[float] = None



class PgXInput(BaseModel):
    patient: Patient
    specimen: Specimen
    results: list[PgXGeneResult]
    ruleset_version: str = "0.1"
