from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping, Sequence

PASS = "PASS"
FAIL = "FAIL"
NON_MESURE = "NON_MESURÉ"
K3 = {PASS, FAIL, NON_MESURE}

OBJECT_ID = "ZORAN-BRICK-FRAME-SEARCH-STITCH-V1"
META_ID = "ZORAN-META-FRAME-MOTION-SEARCH-2026-08-24"
VERSION = "1.0-candidate"


class FrameSearchStitchError(ValueError):
    pass


@dataclass(frozen=True)
class FrameObservation:
    frame_id: str
    parent_frame_id: str
    source_id: str
    source_sha256: str
    relieves_constraints: tuple[str, ...]
    relation_evidence_ids: tuple[str, ...]
    complexity_cost: int


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


def _valid_id(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FrameSearchStitchError(f"{name} requis")
    return value.strip()


def _valid_sha(value: str) -> str:
    value = _valid_id(value, "source_sha256").lower()
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise FrameSearchStitchError("source_sha256 invalide")
    return value


def detect_blocking_boundary(
    frame_verdicts: Mapping[str, str],
    *,
    saturation_order: Sequence[str] = (),
    saturation_evidence_ids: Sequence[str] = (),
) -> dict:
    if not isinstance(frame_verdicts, Mapping) or not frame_verdicts:
        raise FrameSearchStitchError("frame_verdicts non vide requis")
    normalized: dict[str, str] = {}
    for frame_id, verdict in frame_verdicts.items():
        frame_id = _valid_id(frame_id, "frame_id")
        if verdict not in K3:
            raise FrameSearchStitchError(f"verdict K3 invalide pour {frame_id}")
        normalized[frame_id] = verdict

    failures = sorted(frame_id for frame_id, verdict in normalized.items() if verdict == FAIL)
    unknowns = sorted(frame_id for frame_id, verdict in normalized.items() if verdict == NON_MESURE)
    order = tuple(saturation_order)
    evidence = tuple(sorted(set(saturation_evidence_ids)))
    if any(not isinstance(item, str) or not item.strip() for item in order + evidence):
        raise FrameSearchStitchError("preuve/ordre de saturation invalide")

    ambiguity = None
    if len(failures) == 1:
        status, blocker = FAIL, failures[0]
    elif len(failures) > 1:
        ordered_failures = [frame_id for frame_id in order if frame_id in failures]
        if evidence and ordered_failures and set(failures).issubset(set(order)):
            status, blocker = FAIL, ordered_failures[0]
        else:
            status, blocker = NON_MESURE, None
            ambiguity = "MULTIPLE_FAIL_NO_SATURATION_PROOF"
    elif unknowns:
        status, blocker = NON_MESURE, unknowns[0]
    else:
        status, blocker = PASS, None

    payload = {
        "object_id": OBJECT_ID,
        "meta_id": META_ID,
        "version": VERSION,
        "status": status,
        "blocking_frame_id": blocker,
        "all_failures": failures,
        "all_unknowns": unknowns,
        "saturation_order": list(order),
        "saturation_evidence_ids": list(evidence),
        "ambiguity": ambiguity,
        "frame_verdicts": dict(sorted(normalized.items())),
        "selection_policy": "SINGLE_FAIL_OR_PROVEN_SATURATION_ORDER_FAIL_CLOSED",
    }
    return {**payload, "boundary_sha256": _digest(payload)}


def discover_candidate_frames(boundary: Mapping[str, object], observations: Sequence[FrameObservation]) -> dict:
    blocker = boundary.get("blocking_frame_id")
    status = boundary.get("status")
    if status == PASS:
        candidates = []
    elif status == NON_MESURE:
        candidates = []
    elif status == FAIL:
        _valid_id(blocker, "blocking_frame_id")
        candidates = []
        for observation in observations:
            frame_id = _valid_id(observation.frame_id, "frame_id")
            parent_frame_id = _valid_id(observation.parent_frame_id, "parent_frame_id")
            source_id = _valid_id(observation.source_id, "source_id")
            source_sha256 = _valid_sha(observation.source_sha256)
            if frame_id == parent_frame_id:
                raise FrameSearchStitchError("extension identique au parent interdite")
            if isinstance(observation.complexity_cost, bool) or not isinstance(observation.complexity_cost, int) or observation.complexity_cost < 0:
                raise FrameSearchStitchError("complexity_cost invalide")
            relieves = tuple(sorted(set(observation.relieves_constraints)))
            relation_evidence_ids = tuple(sorted(set(observation.relation_evidence_ids)))
            if any(not isinstance(item, str) or not item.strip() for item in relieves):
                raise FrameSearchStitchError("relieves_constraints invalide")
            if not relation_evidence_ids or any(not isinstance(item, str) or not item.strip() for item in relation_evidence_ids):
                raise FrameSearchStitchError("relation_evidence_ids requis")
            if blocker in relieves:
                candidates.append({
                    "frame_id": frame_id,
                    "parent_frame_id": parent_frame_id,
                    "source_id": source_id,
                    "source_sha256": source_sha256,
                    "relieves_constraints": list(relieves),
                    "relation_evidence_ids": list(relation_evidence_ids),
                    "complexity_cost": observation.complexity_cost,
                    "discovery_authority": False,
                })
        candidates.sort(key=lambda item: (item["complexity_cost"], item["frame_id"], item["source_sha256"]))
    else:
        raise FrameSearchStitchError("boundary.status invalide")

    semantic = {
        "object_id": OBJECT_ID,
        "meta_id": META_ID,
        "version": VERSION,
        "boundary_sha256": boundary.get("boundary_sha256"),
        "blocking_frame_id": blocker,
        "candidate_frames": candidates,
        "semantic_engine_authority": False,
        "decision_authority": "K3_DETERMINISTIC_CHAIN",
    }
    return {**semantic, "discovery_sha256": _digest(semantic)}


def build_extension_candidates(discovery: Mapping[str, object], deterministic_evaluations: Mapping[str, Mapping[str, object]]) -> dict:
    out = []
    for candidate in discovery.get("candidate_frames", []):
        frame_id = candidate["frame_id"]
        evaluation = deterministic_evaluations.get(frame_id)
        if evaluation is None:
            continue
        required = {
            "target_constraint_verdict",
            "preserved_frames",
            "peer_frames",
            "superior_benefits",
            "causal_evidence_ids",
            "falsifier_ids",
        }
        if not required.issubset(evaluation):
            continue
        verdicts = [evaluation["target_constraint_verdict"]]
        for field in ("preserved_frames", "peer_frames", "superior_benefits"):
            values = evaluation[field]
            if not isinstance(values, Mapping):
                raise FrameSearchStitchError(f"{field} mapping requis")
            verdicts.extend(values.values())
        if any(verdict not in K3 for verdict in verdicts):
            raise FrameSearchStitchError("évaluation déterministe contient un verdict K3 invalide")
        causal_evidence_ids = tuple(sorted(set(evaluation["causal_evidence_ids"])))
        falsifier_ids = tuple(sorted(set(evaluation["falsifier_ids"])))
        if not causal_evidence_ids or not falsifier_ids:
            continue
        out.append({
            "frame_id": frame_id,
            "parent_frame_id": candidate["parent_frame_id"],
            "target_constraint_verdict": evaluation["target_constraint_verdict"],
            "preserved_frames": dict(sorted(evaluation["preserved_frames"].items())),
            "peer_frames": dict(sorted(evaluation["peer_frames"].items())),
            "superior_benefits": dict(sorted(evaluation["superior_benefits"].items())),
            "complexity_cost": candidate["complexity_cost"],
            "causal_evidence_ids": list(causal_evidence_ids),
            "falsifier_ids": list(falsifier_ids),
            "source_id": candidate["source_id"],
            "source_sha256": candidate["source_sha256"],
        })
    out.sort(key=lambda item: (item["complexity_cost"], item["frame_id"], item["source_sha256"]))
    semantic = {
        "object_id": OBJECT_ID,
        "meta_id": META_ID,
        "version": VERSION,
        "candidate_evaluations": out,
        "discovery_authority": False,
        "decision_authority": "K3_DETERMINISTIC_CHAIN",
    }
    return {**semantic, "evaluation_stitch_sha256": _digest(semantic)}
