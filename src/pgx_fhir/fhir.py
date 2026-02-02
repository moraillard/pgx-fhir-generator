from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

Json = Dict[str, Any]


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_patient(
    *,
    patient_id: str,
    given: Optional[str] = None,
    family: Optional[str] = None,
    birth_date: Optional[str] = None,
    sex: Optional[str] = None,
) -> Json:
    """
    birth_date esperado en formato YYYY-MM-DD
    sex esperado en FHIR Patient.gender:
      female, male, other, unknown
    """
    patient: Json = {
        "resourceType": "Patient",
        "id": patient_id,
    }

    name_parts: Json = {}
    if family:
        name_parts["family"] = family
    if given:
        name_parts["given"] = [given]
    if name_parts:
        patient["name"] = [name_parts]

    if birth_date:
        patient["birthDate"] = birth_date

    if sex:
        patient["gender"] = sex

    return patient


def build_specimen(
    *,
    specimen_id: str,
    patient_ref: str,
    specimen_type_text: str = "specimen",
) -> Json:
    """
    specimen_type_text es texto libre, lo dejamos simple para el bundle mínimo
    """
    return {
        "resourceType": "Specimen",
        "id": specimen_id,
        "subject": {"reference": patient_ref},
        "type": {"text": specimen_type_text},
    }


def build_observation_pgx(
    *,
    obs_id: str,
    patient_ref: str,
    specimen_ref: Optional[str] = None,
    gene: str,
    diplotype: Optional[str] = None,
    phenotype: Optional[str] = None,
    report_time_iso: Optional[str] = None,
    category_text: str = "laboratory",
) -> Json:
    """
    Observation mínimo para PGx
    - gene, diplotype, phenotype quedan como componentes en texto
    - category_text por defecto laboratory
    """
    issued = report_time_iso or _now_iso()

    obs: Json = {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "category": [{"text": category_text}],
        "code": {"text": "Pharmacogenomics result"},
        "subject": {"reference": patient_ref},
        "effectiveDateTime": issued,
        "issued": issued,
        "component": [
            {"code": {"text": "gene"}, "valueString": gene},
        ],
    }

    if specimen_ref:
        obs["specimen"] = {"reference": specimen_ref}

    if diplotype:
        obs["component"].append({"code": {"text": "diplotype"}, "valueString": diplotype})

    if phenotype:
        obs["component"].append({"code": {"text": "phenotype"}, "valueString": phenotype})

    return obs


def build_bundle_collection(
    *,
    resources: Sequence[Json],
    bundle_id: Optional[str] = None,
) -> Json:
    """
    Bundle tipo collection con entries que incluyen fullUrl + resource
    """
    bid = bundle_id or _new_id("bundle")
    entries: List[Json] = []

    for r in resources:
        rtype = r.get("resourceType", "Resource")
        rid = r.get("id") or _new_id(rtype.lower())

        # No mutar el dict original
        r2 = dict(r)
        r2["id"] = rid

        entries.append(
            {
                "fullUrl": f"urn:uuid:{rid}",
                "resource": r2,
            }
        )

    return {
        "resourceType": "Bundle",
        "id": bid,
        "type": "collection",
        "timestamp": _now_iso(),
        "entry": entries,
    }


@dataclass(frozen=True)
class MinimalPgxRecord:
    gene: str
    diplotype: Optional[str] = None
    phenotype: Optional[str] = None


def build_pgx_bundle_minimal(
    *,
    patient_id: Optional[str] = None,
    specimen_id: Optional[str] = None,
    patient_given: Optional[str] = None,
    patient_family: Optional[str] = None,
    birth_date: Optional[str] = None,
    sex: Optional[str] = None,
    specimen_type_text: str = "Blood specimen",
    pgx_results: Sequence[MinimalPgxRecord],
) -> Json:
    """
    Fabrica un bundle mínimo con:
    - Patient
    - Specimen
    - N Observations PGx
    """
    pid = patient_id or _new_id("patient")
    sid = specimen_id or _new_id("specimen")

    patient_ref = f"Patient/{pid}"
    specimen_ref = f"Specimen/{sid}"

    patient = build_patient(
        patient_id=pid,
        given=patient_given,
        family=patient_family,
        birth_date=birth_date,
        sex=sex,
    )

    specimen = build_specimen(
        specimen_id=sid,
        patient_ref=patient_ref,
        specimen_type_text=specimen_type_text,
    )

    observations: List[Json] = []
    for rec in pgx_results:
        oid = _new_id("observation")
        observations.append(
            build_observation_pgx(
                obs_id=oid,
                patient_ref=patient_ref,
                specimen_ref=specimen_ref,
                gene=rec.gene,
                diplotype=rec.diplotype,
                phenotype=rec.phenotype,
            )
        )

    return build_bundle_collection(resources=[patient, specimen, *observations])


def build_bundle_from_pgx_input(pgx_input: "PgXInput") -> Json:
    """
    Convierte PgXInput (tu modelo interno) a un Bundle FHIR mínimo.

    Esta función intenta ser robusta a distintos nombres de campos en tus modelos Pydantic.
    Si no encuentra algo, lo deja como None y genera IDs si faltan.
    """
    from .models import PgXInput  # noqa: F401

    def _get(obj: Any, *names: str) -> Any:
        for n in names:
            if hasattr(obj, n):
                v = getattr(obj, n)
                if v is not None:
                    return v
        return None

    patient_obj = pgx_input.patient
    specimen_obj = pgx_input.specimen

    # IDs: si el modelo no los trae, los inventamos
    patient_id = _get(patient_obj, "id", "patient_id") or _new_id("patient")
    specimen_id = _get(specimen_obj, "id", "specimen_id") or _new_id("specimen")

    # Patient fields (probamos nombres comunes en inglés y español)
    patient_given = _get(patient_obj, "given", "first_name", "firstname", "name", "nombres", "nombre")
    patient_family = _get(patient_obj, "family", "last_name", "lastname", "surname", "apellidos", "apellido")
    birth_date = _get(patient_obj, "birth_date", "birthdate", "date_of_birth", "dob", "fecha_nacimiento")
    sex = _get(patient_obj, "sex", "gender", "sexo", "genero")

    # Specimen fields
    specimen_type_text = _get(specimen_obj, "type_text", "specimen_type", "type", "tipo") or "Blood specimen"

    # Results mapping
    results: List[MinimalPgxRecord] = []
    for r in pgx_input.results:
        gene = _get(r, "gene", "gen")
        diplotype = _get(r, "diplotype", "diplotipo")
        phenotype = _get(r, "phenotype", "fenotipo")

        if gene is None:
            raise ValueError("Result record missing gene (tried: gene/gen).")

        results.append(
            MinimalPgxRecord(
                gene=str(gene),
                diplotype=str(diplotype) if diplotype is not None else None,
                phenotype=str(phenotype) if phenotype is not None else None,
            )
        )

    return build_pgx_bundle_minimal(
        patient_id=str(patient_id),
        specimen_id=str(specimen_id),
        patient_given=str(patient_given) if patient_given is not None else None,
        patient_family=str(patient_family) if patient_family is not None else None,
        birth_date=str(birth_date) if birth_date is not None else None,
        sex=str(sex) if sex is not None else None,
        specimen_type_text=str(specimen_type_text),
        pgx_results=results,
    )

