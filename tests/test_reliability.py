"""
Tests for live_processing/reliability_calculator.py (pure-logic functions only)

Covers:
- compute_cohens_kappa: perfect agreement, zero agreement, known value,
                        mismatched series lengths, single label, empty series
"""

import math

import pandas as pd
import pytest

from live_processing.reliability_calculator import compute_cohens_kappa


class TestComputeCohensKappa:
    def test_perfect_agreement_returns_one(self):
        s1 = pd.Series(["pos", "neg", "neu", "pos"])
        s2 = pd.Series(["pos", "neg", "neu", "pos"])
        kappa = compute_cohens_kappa(s1, s2)
        assert kappa == pytest.approx(1.0)

    def test_empty_series_returns_nan(self):
        kappa = compute_cohens_kappa(pd.Series([], dtype=str), pd.Series([], dtype=str))
        assert math.isnan(kappa)

    def test_mismatched_lengths_returns_nan(self):
        s1 = pd.Series(["pos", "neg"])
        s2 = pd.Series(["pos"])
        kappa = compute_cohens_kappa(s1, s2)
        assert math.isnan(kappa)

    def test_single_unique_label_perfect_agreement(self):
        """All items the same label → kappa is 1 (pe would be 1, handled by guard)."""
        s1 = pd.Series(["pos"] * 10)
        s2 = pd.Series(["pos"] * 10)
        kappa = compute_cohens_kappa(s1, s2)
        # When pe == 1.0, the implementation returns 1.0 by convention
        assert kappa == pytest.approx(1.0)

    def test_known_kappa_value(self):
        """
        2-class problem: 60 items, balanced coders.

        Confusion matrix:
            coder_b_pos  coder_b_neg
        coder_a_pos  20           10
        coder_a_neg  10           20

        n = 60
        po = 40/60
        row_marg = [30/60, 30/60], col_marg = [30/60, 30/60]
        pe = (30/60)^2 + (30/60)^2 = 0.5
        kappa = (2/3 - 0.5) / (1 - 0.5) = (1/6) / (1/2) = 1/3
        """
        s1 = pd.Series(["pos"] * 30 + ["neg"] * 30)
        s2 = pd.Series(["pos"] * 20 + ["neg"] * 10 + ["pos"] * 10 + ["neg"] * 20)
        kappa = compute_cohens_kappa(s1, s2)
        assert kappa == pytest.approx(1 / 3, abs=1e-6)

    def test_result_between_negative_one_and_one(self):
        """kappa should always be in [-1, 1]."""
        s1 = pd.Series(["a", "b", "c", "a", "b"])
        s2 = pd.Series(["b", "c", "a", "b", "a"])
        kappa = compute_cohens_kappa(s1, s2)
        assert -1.0 <= kappa <= 1.0

    def test_partial_agreement_is_between_zero_and_one(self):
        s1 = pd.Series(["pos", "pos", "neg", "neg", "neu", "neu"])
        s2 = pd.Series(["pos", "neg", "neg", "neg", "neu", "pos"])
        kappa = compute_cohens_kappa(s1, s2)
        assert 0.0 <= kappa <= 1.0

    def test_asymmetric_label_sets(self):
        """Coders using different subsets of labels should not crash."""
        s1 = pd.Series(["pos", "pos", "neg"])
        s2 = pd.Series(["pos", "neu", "neg"])
        kappa = compute_cohens_kappa(s1, s2)
        assert not math.isnan(kappa)

    def test_unicode_labels(self):
        s1 = pd.Series(["中立", "positivo", "négative"])
        s2 = pd.Series(["中立", "positivo", "négative"])
        kappa = compute_cohens_kappa(s1, s2)
        assert kappa == pytest.approx(1.0)
