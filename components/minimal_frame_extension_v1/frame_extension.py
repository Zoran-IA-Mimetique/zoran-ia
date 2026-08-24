from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

PASS = "PASS"
FAIL = "FAIL"
NON_MESURE = "NON_MESURÉ"
K3 = {PASS, FAIL, NON_MESURE}

STATE_IMPOSSIBLE_IN_FRAME = "IMPOSSIBLE_DANS_CADRE"
STATE_EXTENSION_EXISTS = "EXTENSION_COHERENTE_EXISTE"
STATE_GLOBAL_IMPOSSIBLE = "IMPOSSIBLE_GLOBAL"
STATE_NON_MEASURE = "NON_MESURÉ"

VERSION = "ZORAN-MINIMAL-FRAME-EXTENSION-1.0-CANDIDATE"
OBJECT_ID = "ZORAN-BRICK-MIN-FRAME-EXT-V1"
META_ID = "ZORAN-META-FRAME-MOTION-2026-08-24"


class FrameExtensionError(ValueError):
    pass


@dataclass(frozen=True)
class ExtensionCandidate:
    frame_id: str
    parent_frame_id: str
    target_constraint_verdict: str
    preserved_frames: Mapping[str, str]
    peer_frames: Mapping[str, str]
    superior_benefits: Mapping[str, str]
    complexity_cost: int
    causal_evidence_ids: tuple[str, ...]
    falsifier_ids: tuple[str, ...]


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


def _validate_k3(value: str, field: str) -> str:
    if value not in K3:
        raise FrameExtensionError(f"{field}: verdict K3 invalide: {value!r}")
    return value


def _validate_map(values: Mapping[str, str], field: str) -> dict[str, str]:
    if not isinstance(values, Mapping):
        raise FrameExtensionError(f"{field}: mapping requis")
    out: dict[str, str] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not key.strip():
            raise FrameExtensionError(f"{field}: identifiant de cadre invalide")
        out[key] = _validate_k3(value, f"{field}.{key}")
    return dict(sorted(out.items()))


def _validate_ids(values: Sequence[str], field: str, *, required: bool) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise FrameExtensionError(f"{field}: séquence requise")
    normalized = tuple(sorted(set(values)))
    if required and not normalized:
        raise FrameExtensionError(f"{field}: au moins une preuve est requise")
    if any(not isinstance(x, str) or not x.strip() for x in normalized):
        raise FrameExtensionError(f"{field}: identifiant vide ou invalide")
    return normalized


def normalize_candidate(candidate: ExtensionCandidate) -> ExtensionCandidate:
    if not isinstance(candidate.frame_id, str) or not candidate.frame_id.strip():
        raise FrameExtensionError("frame_id requis")
    if not isinstance(candidate.parent_frame_id, str) or not candidate.parent_frame_id.strip():
        raise FrameExtensionError("parent_frame_id requis")
    if candidate.frame_id == candidate.parent_frame_id:
        raise FrameExtensionError("une extension doit différer de son cadre parent")
    if isinstance(candidate.complexity_cost, bool) or not isinstance(candidate.complexity_cost, int):
        raise FrameExtensionError("complexity_cost doit être un entier")
    if candidate.complexity_cost < 0:
        raise FrameExtensionError("complexity_cost doit être >= 0")
    return ExtensionCandidate(
        frame_id=candidate.frame_id.strip(),
        parent_frame_id=candidate.parent_frame_id.strip(),
        target_constraint_verdict=_validate_k3(candidate.target_constraint_verdict, "target_constraint_verdict"),
        preserved_frames=_validate_map(candidate.preserved_frames, "preserved_frames"),
        peer_frames=_validate_map(candidate.peer_frames, "peer_frames"),
        superior_benefits=_validate_map(candidate.superior_benefits, "superior_benefits"),
        complexity_cost=candidate.complexity_cost,
        causal_evidence_ids=_validate_ids(candidate.causal_evidence_ids, "causal_evidence_ids", required=True),
        falsifier_ids=_validate_ids(candidate.falsifier_ids, "falsifier_ids", required=True),
    )


def assess_candidate(candidate: ExtensionCandidate, *, required_preserved_frame_ids: Iterable[str], required_peer_frame_ids: Iterable[str] = (), required_superior_frame_ids: Iterable[str] = ()) -> dict:
    c = normalize_candidate(candidate)
    preserved_required = tuple(sorted(set(required_preserved_frame_ids)))
    peer_required = tuple(sorted(set(required_peer_frame_ids)))
    superior_required = tuple(sorted(set(required_superior_frame_ids)))

    missing_preserved = [x for x in preserved_required if x not in c.preserved_frames]
    missing_peers = [x for x in peer_required if x not in c.peer_frames]
    missing_superior = [x for x in superior_required if x not in c.superior_benefits]
    unknown: list[str] = []
    regressions: list[str] = []

    for group, values, required in (
        ("preserved", c.preserved_frames, preserved_required),
        ("peer", c.peer_frames, peer_required),
        ("superior", c.superior_benefits, superior_required),
    ):
        for frame_id in required:
            if frame_id not in values:
                continue
            verdict = values[frame_id]
            if verdict == NON_MESURE:
                unknown.append(f"{group}:{frame_id}")
            elif verdict == FAIL:
                regressions.append(f"{group}:{frame_id}")

    target_unknown = c.target_constraint_verdict == NON_MESURE
    target_fail = c.target_constraint_verdict == FAIL
    admissible = (
        not missing_preserved and not missing_peers and not missing_superior and
        not unknown and not regressions and not target_unknown and not target_fail and
        all(c.preserved_frames[x] == PASS for x in preserved_required) and
        all(c.peer_frames[x] == PASS for x in peer_required) and
        all(c.superior_benefits[x] == PASS for x in superior_required)
    )
    status = PASS if admissible else (FAIL if regressions or target_fail else NON_MESURE)
    return {
        "frame_id": c.frame_id,
        "parent_frame_id": c.parent_frame_id,
        "status": status,
        "admissible": admissible,
        "complexity_cost": c.complexity_cost,
        "missing_preserved": missing_preserved,
        "missing_peers": missing_peers,
        "missing_superior": missing_superior,
        "unknown": sorted(unknown),
        "regressions": sorted(regressions),
        "target_constraint_verdict": c.target_constraint_verdict,
        "causal_evidence_ids": list(c.causal_evidence_ids),
        "falsifier_ids": list(c.falsifier_ids),
    }


def choose_minimal_extension(*, current_frame_id: str, current_constraint_verdict: str, candidates: Sequence[ExtensionCandidate], required_preserved_frame_ids: Iterable[str], required_peer_frame_ids: Iterable[str] = (), required_superior_frame_ids: Iterable[str] = (), search_space_exhaustive: bool = False, exhaustion_evidence_ids: Sequence[str] = ()) -> dict:
    if not isinstance(current_frame_id, str) or not current_frame_id.strip():
        raise FrameExtensionError("current_frame_id requis")
    current_constraint_verdict = _validate_k3(current_constraint_verdict, "current_constraint_verdict")
    exhaustion_ids = _validate_ids(exhaustion_evidence_ids, "exhaustion_evidence_ids", required=bool(search_space_exhaustive))

    assessed = [
        assess_candidate(c, required_preserved_frame_ids=required_preserved_frame_ids, required_peer_frame_ids=required_peer_frame_ids, required_superior_frame_ids=required_superior_frame_ids)
        for c in candidates
    ]
    assessed = sorted(assessed, key=lambda item: (not item["admissible"], item["complexity_cost"], item["frame_id"]))
    admissible = [item for item in assessed if item["admissible"]]

    if current_constraint_verdict == PASS:
        state, selected = PASS, None
    elif current_constraint_verdict == NON_MESURE:
        state, selected = STATE_NON_MEASURE, None
    elif admissible:
        state, selected = STATE_EXTENSION_EXISTS, admissible[0]
    elif search_space_exhaustive:
        state, selected = STATE_GLOBAL_IMPOSSIBLE, None
    else:
        state, selected = STATE_IMPOSSIBLE_IN_FRAME, None

    semantic = {
        "_type": "minimal_frame_extension_certificate",
        "object_id": OBJECT_ID,
        "meta_id": META_ID,
        "version": VERSION,
        "current_frame_id": current_frame_id.strip(),
        "current_constraint_verdict": current_constraint_verdict,
        "state": state,
        "selected_extension": selected,
        "candidate_assessments": assessed,
        "search_space_exhaustive": bool(search_space_exhaustive),
        "exhaustion_evidence_ids": list(exhaustion_ids),
        "policy": {
            "fail_closed": True,
            "unknown_blocks_promotion": True,
            "regression_blocks_promotion": True,
            "minimality_order": ["complexity_cost", "frame_id"],
            "global_impossibility_requires_exhaustion_proof": True,
        },
    }
    semantic["semantic_sha256"] = _digest(semantic)
    return semantic
