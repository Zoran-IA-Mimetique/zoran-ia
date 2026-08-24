import unittest
from frame_search_stitch import *

SHA_A = "a" * 64
SHA_B = "b" * 64


class TestFrameSearchStitch(unittest.TestCase):
    def test_multiple_fail_without_saturation_proof_is_non_mesure(self):
        boundary = detect_blocking_boundary({"Z": FAIL, "A": FAIL})
        self.assertIsNone(boundary["blocking_frame_id"])
        self.assertEqual(boundary["status"], NON_MESURE)
        self.assertEqual(boundary["ambiguity"], "MULTIPLE_FAIL_NO_SATURATION_PROOF")

    def test_multiple_fail_with_saturation_proof_selects_first(self):
        boundary = detect_blocking_boundary(
            {"Z": FAIL, "A": FAIL},
            saturation_order=("Z", "A"),
            saturation_evidence_ids=("SAT-1",),
        )
        self.assertEqual(boundary["blocking_frame_id"], "Z")
        self.assertEqual(boundary["status"], FAIL)

    def test_pass_has_no_boundary(self):
        boundary = detect_blocking_boundary({"A": PASS})
        self.assertIsNone(boundary["blocking_frame_id"])

    def test_discovery_matches_blocker_only(self):
        boundary = detect_blocking_boundary({"REAL::SQRT_NEGATIVE": FAIL})
        observations = [
            FrameObservation("COMPLEX_NUMBERS", "REAL_NUMBERS", "SRC-C", SHA_A, ("REAL::SQRT_NEGATIVE",), ("REL-1",), 1),
            FrameObservation("UNRELATED", "REAL_NUMBERS", "SRC-U", SHA_B, ("OTHER",), ("REL-2",), 0),
        ]
        discovery = discover_candidate_frames(boundary, observations)
        self.assertEqual([item["frame_id"] for item in discovery["candidate_frames"]], ["COMPLEX_NUMBERS"])

    def test_discovery_has_no_authority(self):
        boundary = detect_blocking_boundary({"A": FAIL})
        discovery = discover_candidate_frames(boundary, [FrameObservation("B", "A", "SRC", SHA_A, ("A",), ("REL-1",), 1)])
        self.assertFalse(discovery["semantic_engine_authority"])

    def test_non_mesure_does_not_invent_extension(self):
        boundary = detect_blocking_boundary({"A": NON_MESURE})
        discovery = discover_candidate_frames(boundary, [FrameObservation("B", "A", "SRC", SHA_A, ("A",), ("REL-1",), 1)])
        self.assertEqual(discovery["candidate_frames"], [])

    def test_invalid_source_hash_rejected(self):
        boundary = detect_blocking_boundary({"A": FAIL})
        with self.assertRaises(FrameSearchStitchError):
            discover_candidate_frames(boundary, [FrameObservation("B", "A", "SRC", "bad", ("A",), ("REL-1",), 1)])

    def test_evaluation_required(self):
        boundary = detect_blocking_boundary({"A": FAIL})
        discovery = discover_candidate_frames(boundary, [FrameObservation("B", "A", "SRC", SHA_A, ("A",), ("REL-1",), 1)])
        evaluated = build_extension_candidates(discovery, {})
        self.assertEqual(evaluated["candidate_evaluations"], [])

    def test_sqrt_minus_one_chain(self):
        boundary = detect_blocking_boundary({"REAL::SQRT_NEGATIVE": FAIL})
        discovery = discover_candidate_frames(boundary, [
            FrameObservation("MATH::COMPLEX", "MATH::REAL", "SRC-MATH-C", SHA_A, ("REAL::SQRT_NEGATIVE",), ("REL-1",), 1)
        ])
        evaluations = {
            "MATH::COMPLEX": {
                "target_constraint_verdict": PASS,
                "preserved_frames": {"MATH::REAL_EMBEDDING": PASS},
                "peer_frames": {"MATH::ARITHMETIC": PASS},
                "superior_benefits": {"MATH::SOLVABILITY": PASS},
                "causal_evidence_ids": ["EVID-I2-EQ-MINUS1"],
                "falsifier_ids": ["FALS-REAL-NOT-COMPLEX"],
            }
        }
        evaluated = build_extension_candidates(discovery, evaluations)
        self.assertEqual(evaluated["candidate_evaluations"][0]["frame_id"], "MATH::COMPLEX")
        self.assertEqual(evaluated["candidate_evaluations"][0]["target_constraint_verdict"], PASS)

    def test_missing_proofs_blocks_candidate(self):
        boundary = detect_blocking_boundary({"A": FAIL})
        discovery = discover_candidate_frames(boundary, [FrameObservation("B", "A", "SRC", SHA_A, ("A",), ("REL-1",), 1)])
        evaluations = {
            "B": {
                "target_constraint_verdict": PASS,
                "preserved_frames": {},
                "peer_frames": {},
                "superior_benefits": {},
                "causal_evidence_ids": [],
                "falsifier_ids": [],
            }
        }
        evaluated = build_extension_candidates(discovery, evaluations)
        self.assertEqual(evaluated["candidate_evaluations"], [])

    def test_deterministic_hash(self):
        values = {"B": FAIL, "A": PASS}
        self.assertEqual(
            detect_blocking_boundary(values)["boundary_sha256"],
            detect_blocking_boundary(values)["boundary_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
