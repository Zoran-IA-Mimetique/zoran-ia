import unittest

from frame_extension import (
    ExtensionCandidate,
    FAIL,
    NON_MESURE,
    PASS,
    STATE_EXTENSION_EXISTS,
    STATE_GLOBAL_IMPOSSIBLE,
    STATE_IMPOSSIBLE_IN_FRAME,
    STATE_NON_MEASURE,
    choose_minimal_extension,
)


def candidate(frame_id, cost, *, target=PASS, preserved=None, peers=None, superior=None, causal=("CAUSE-1",), falsifiers=("FALS-1",)):
    return ExtensionCandidate(
        frame_id=frame_id,
        parent_frame_id="R",
        target_constraint_verdict=target,
        preserved_frames=preserved or {"R": PASS},
        peer_frames=peers or {"PEER": PASS},
        superior_benefits=superior or {"PLANET": PASS},
        complexity_cost=cost,
        causal_evidence_ids=causal,
        falsifier_ids=falsifiers,
    )


class TestFrameExtension(unittest.TestCase):
    def test_selects_minimal_admissible(self):
        out = choose_minimal_extension(
            current_frame_id="R",
            current_constraint_verdict=FAIL,
            candidates=[candidate("C2", 2), candidate("C1", 1)],
            required_preserved_frame_ids=["R"],
            required_peer_frame_ids=["PEER"],
            required_superior_frame_ids=["PLANET"],
        )
        self.assertEqual(out["state"], STATE_EXTENSION_EXISTS)
        self.assertEqual(out["selected_extension"]["frame_id"], "C1")

    def test_regression_blocks(self):
        out = choose_minimal_extension(
            current_frame_id="R",
            current_constraint_verdict=FAIL,
            candidates=[candidate("C1", 1, preserved={"R": FAIL})],
            required_preserved_frame_ids=["R"],
            required_peer_frame_ids=["PEER"],
            required_superior_frame_ids=["PLANET"],
        )
        self.assertEqual(out["state"], STATE_IMPOSSIBLE_IN_FRAME)

    def test_unknown_blocks(self):
        out = choose_minimal_extension(
            current_frame_id="R",
            current_constraint_verdict=FAIL,
            candidates=[candidate("C1", 1, superior={"PLANET": NON_MESURE})],
            required_preserved_frame_ids=["R"],
            required_peer_frame_ids=["PEER"],
            required_superior_frame_ids=["PLANET"],
        )
        self.assertEqual(out["state"], STATE_IMPOSSIBLE_IN_FRAME)
        self.assertEqual(out["candidate_assessments"][0]["status"], NON_MESURE)

    def test_global_impossibility_requires_exhaustion(self):
        out = choose_minimal_extension(
            current_frame_id="R",
            current_constraint_verdict=FAIL,
            candidates=[],
            required_preserved_frame_ids=["R"],
            search_space_exhaustive=True,
            exhaustion_evidence_ids=["EXH-1"],
        )
        self.assertEqual(out["state"], STATE_GLOBAL_IMPOSSIBLE)

    def test_non_measured_current_frame(self):
        out = choose_minimal_extension(
            current_frame_id="R",
            current_constraint_verdict=NON_MESURE,
            candidates=[],
            required_preserved_frame_ids=["R"],
        )
        self.assertEqual(out["state"], STATE_NON_MEASURE)

    def test_hash_is_deterministic(self):
        kwargs = dict(
            current_frame_id="R",
            current_constraint_verdict=FAIL,
            candidates=[candidate("C1", 1)],
            required_preserved_frame_ids=["R"],
            required_peer_frame_ids=["PEER"],
            required_superior_frame_ids=["PLANET"],
        )
        a = choose_minimal_extension(**kwargs)
        b = choose_minimal_extension(**kwargs)
        self.assertEqual(a["semantic_sha256"], b["semantic_sha256"])

    def test_missing_superior_is_non_measured(self):
        out = choose_minimal_extension(
            current_frame_id="R",
            current_constraint_verdict=FAIL,
            candidates=[candidate("C1", 1, superior={"OTHER": PASS})],
            required_preserved_frame_ids=["R"],
            required_peer_frame_ids=["PEER"],
            required_superior_frame_ids=["PLANET"],
        )
        self.assertFalse(out["candidate_assessments"][0]["admissible"])
        self.assertEqual(out["candidate_assessments"][0]["status"], NON_MESURE)


if __name__ == "__main__":
    unittest.main()
