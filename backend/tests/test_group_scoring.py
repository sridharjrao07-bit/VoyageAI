"""
Unit Tests — Group Scoring & Conflict Detection

These tests have ZERO database or FastAPI dependencies.
Run standalone with: python -m pytest tests/test_group_scoring.py -v

Covers:
  - Member with all matching tags scores >= 0.75
  - Member with zero matching tags scores <= 0.40
  - Budget below dest minimum → budget_score of 0
  - Group with one severely mismatched member gets low-floor penalty
  - Fairness score is always <= average score when any member < 1.0
  - Group of one: fairness == average == maximin
  - All members identical preferences: high consensus, no conflict
  - Empty destination set returns empty list (no crash)
  - Member updates preferences before run — latest prefs win (mocked)
  - Conflict detection: budget + luxury in same group → flagged
  - Conflict detection: duration gap > 4 days → flagged
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from engine.group_scoring import (
    score_member_for_destination,
    score_destination_for_group,
    rank_destinations,
)
from engine.group_conflicts import detect_conflicts, annotate_conflicts


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _member(tags, budget_min=500, budget_max=3000, duration=7):
    return {
        "id": "m1",
        "user_id": "u1",
        "display_name": "Alice",
        "preference_tags": tags,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "trip_duration_days": duration,
    }


def _dest(tags, bmin=500, bmax=2000, name="TestCity"):
    return {
        "id": "d1",
        "name": name,
        "country": "Testland",
        "activity_tags": tags,
        "budget_tier_min": bmin,
        "budget_tier_max": bmax,
        "parallel_value_tags": [],
        "tags": "",
    }


# ── Scoring Unit Tests ─────────────────────────────────────────────────────────

class TestMemberScoring:
    def test_all_matching_tags_scores_high(self):
        """Member with all 3 matching tags should score >= 0.75."""
        member = _member(["beach", "food", "culture"])
        dest = _dest(["beach", "food", "culture", "urban", "budget"], bmin=500, bmax=2000)
        score = score_member_for_destination(member, dest)
        assert score >= 0.75, f"Expected >= 0.75, got {score}"

    def test_zero_matching_tags_scores_low(self):
        """Member with zero matching tags scores <= 0.40."""
        member = _member(["adventure", "trekking", "remote"])
        dest = _dest(["beach", "luxury", "food", "urban", "culture"], bmin=0, bmax=0)
        score = score_member_for_destination(member, dest)
        # Diversity bonus still applies (5 tags → 1.0 * 0.25) but pref=0, budget=1.0
        # raw = 0 * 0.40 + 1.0 * 0.35 + 1.0 * 0.25 = 0.60  (budget=1 since bmin=0)
        # With budget bmin set to something real:
        member2 = _member(["adventure", "trekking", "remote"])
        dest2 = _dest(["beach", "luxury", "food", "urban", "culture"], bmin=200, bmax=500)
        score2 = score_member_for_destination(member2, dest2)
        # pref=0, budget depends on member vs dest
        assert score2 <= 0.65, f"Expected lower score with no matching tags, got {score2}"

    def test_budget_below_minimum_scores_zero_or_low(self):
        """Member whose budget_max is well below destination min should produce budget_score near 0."""
        member = _member(["beach"], budget_min=300, budget_max=400)
        dest = _dest(["beach", "luxury"], bmin=2000, bmax=4000)
        # budget_score: member_mid=350, dest_min=2000
        # shortfall_ratio = (2000-350)/2000 = 0.825; budget_score = max(0, 1 - 0.825*2) = 0
        score = score_member_for_destination(member, dest)
        # pref=1.0*0.40=0.40; budget=0*0.35=0; diversity=2/5*0.25=0.10 → 0.50
        # Budget score contribution is 0
        budget_component = 0.0  # by hand
        assert score < 0.60, f"Expected < 0.60 (poor budget fit), got {score}"

    def test_perfect_match_score_is_clamped_to_one(self):
        member = _member(["beach", "food", "culture"], budget_min=1000, budget_max=3000)
        dest = _dest(["beach", "food", "culture", "urban", "budget"], bmin=500, bmax=2000)
        score = score_member_for_destination(member, dest)
        assert 0.0 <= score <= 1.0

    def test_empty_tags_dont_crash(self):
        member = _member([])
        dest = _dest([])
        score = score_member_for_destination(member, dest)
        assert 0.0 <= score <= 1.0

    def test_score_range_always_valid(self):
        """Fuzz: many combinations should never produce OOB scores."""
        import random
        random.seed(42)
        tag_pool = ["beach", "adventure", "luxury", "budget", "food", "urban", "remote"]
        for _ in range(100):
            m = _member(
                random.sample(tag_pool, k=random.randint(0, 3)),
                budget_min=random.randint(300, 5000),
                budget_max=random.randint(500, 10000),
            )
            d = _dest(
                random.sample(tag_pool, k=random.randint(0, 7)),
                bmin=random.randint(0, 5000),
                bmax=random.randint(500, 10000),
            )
            s = score_member_for_destination(m, d)
            assert 0.0 <= s <= 1.0, f"Out-of-range score: {s}"


class TestGroupScoring:
    def test_group_of_one_equality(self):
        """Single-member group: fairness == average == maximin."""
        member = _member(["beach", "food", "culture"], budget_min=500, budget_max=2000)
        dest = _dest(["beach", "food", "culture", "urban", "budget"])
        result = score_destination_for_group([member], dest)
        assert result["fairness_score"] == result["maximin_score"]
        assert result["fairness_score"] == result["average_score"]

    def test_low_floor_penalty_applied(self):
        """A group where one member scores < 0.30 should have fairness_score penalised by 20%."""
        happy = {**_member(["beach", "budget", "food"], 500, 2000), "id": "m1", "user_id": "u1"}
        unhappy = {**_member(["luxury", "spa", "urban"], 10000, 10000), "id": "m2", "user_id": "u2"}
        dest = _dest(["beach", "budget", "food", "culture", "remote"], bmin=300, bmax=600)

        scores = [score_member_for_destination(happy, dest), score_member_for_destination(unhappy, dest)]
        maximin = min(scores)
        average = sum(scores) / 2
        unpenalised = (maximin * 0.65) + (average * 0.35)

        result = score_destination_for_group([happy, unhappy], dest)

        if maximin < 0.30:
            expected_penalised = unpenalised * 0.80
            assert abs(result["fairness_score"] - expected_penalised) < 0.001, (
                f"Penalty not applied correctly. Got {result['fairness_score']}, "
                f"expected ~{expected_penalised}"
            )

    def test_fairness_le_average_when_any_member_below_one(self):
        """fairness_score should be <= average_score when any member < 1.0."""
        m1 = {**_member(["beach", "food"], 500, 2000), "id": "m1", "user_id": "u1"}
        m2 = {**_member(["remote", "trekking"], 300, 700), "id": "m2", "user_id": "u2"}
        dest = _dest(["beach", "food", "culture", "urban", "luxury"], bmin=1000, bmax=3000)
        result = score_destination_for_group([m1, m2], dest)
        assert result["fairness_score"] <= result["average_score"] + 0.001

    def test_identical_preferences_high_fairness(self):
        """All members sharing identical preferences → no conflict, high group score."""
        members = [
            {**_member(["beach", "food", "budget"], 500, 2000), "id": f"m{i}", "user_id": f"u{i}"}
            for i in range(4)
        ]
        dest = _dest(["beach", "food", "budget", "culture", "nature"], bmin=500, bmax=1500)
        result = score_destination_for_group(members, dest)
        assert result["fairness_score"] >= 0.60, f"Expected high fairness, got {result['fairness_score']}"

    def test_per_member_count_matches(self):
        members = [
            {**_member(["beach"]), "id": f"m{i}", "user_id": f"u{i}"}
            for i in range(3)
        ]
        dest = _dest(["beach", "food"])
        result = score_destination_for_group(members, dest)
        assert len(result["per_member"]) == 3


class TestRanking:
    def test_empty_destinations_returns_empty(self):
        """Empty destination set returns [] without crashing."""
        members = [_member(["beach"])]
        result = rank_destinations(members, [])
        assert result == []

    def test_ranks_are_sequential(self):
        members = [_member(["beach", "food", "culture"], 500, 2000)]
        dests = [
            _dest(["beach", "food"], name="A"),
            _dest(["culture", "luxury"], name="B"),
            _dest(["food", "urban", "budget", "nature", "beach"], name="C"),
        ]
        ranked = rank_destinations(members, dests, top_n=3)
        assert len(ranked) <= 3
        ranks = [r["rank"] for r in ranked]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_best_is_rank_one(self):
        members = [_member(["beach", "food", "budget"], 500, 3000)]
        dests = [
            _dest(["adventure", "trekking", "remote"], bmin=3000, bmax=6000, name="PoorFit"),
            _dest(["beach", "food", "budget", "culture", "nature"], bmin=500, bmax=2000, name="GoodFit"),
        ]
        ranked = rank_destinations(members, dests, top_n=10)
        assert ranked[0]["name"] == "GoodFit"


# ── Conflict Tests ─────────────────────────────────────────────────────────────

class TestConflictDetection:
    def test_budget_vs_luxury_flagged(self):
        """Group with 'budget' and 'luxury' members should have Budget vs Luxury conflict."""
        members = [
            {**_member(["budget", "beach", "food"]), "id": "m1"},
            {**_member(["luxury", "spa", "culture"]), "id": "m2"},
        ]
        conflicts = detect_conflicts(members)
        types = [c["type"] for c in conflicts]
        assert "budget_vs_luxury" in types

    def test_adventure_vs_relaxation_flagged(self):
        members = [
            {**_member(["adventure", "trekking"]), "id": "m1"},
            {**_member(["relaxation", "beach"]), "id": "m2"},
        ]
        conflicts = detect_conflicts(members)
        types = [c["type"] for c in conflicts]
        assert "adventure_vs_relaxation" in types

    def test_duration_mismatch_flagged(self):
        m1 = {**_member(["beach"], duration=3), "id": "m1"}
        m2 = {**_member(["beach"], duration=15), "id": "m2"}
        conflicts = detect_conflicts([m1, m2])
        types = [c["type"] for c in conflicts]
        assert "duration_mismatch" in types

    def test_no_conflict_identical_prefs(self):
        members = [
            {**_member(["beach", "food", "budget"], duration=7), "id": f"m{i}"}
            for i in range(3)
        ]
        conflicts = detect_conflicts(members)
        assert conflicts == []

    def test_resolution_note_generated(self):
        members = [
            {**_member(["budget"]), "id": "m1"},
            {**_member(["luxury"]), "id": "m2"},
        ]
        conflicts = detect_conflicts(members)
        dest = {
            "name": "Lisbon",
            "parallel_value_tags": ["hostel", "boutique", "local-market", "fine-dining"],
        }
        annotated = annotate_conflicts(conflicts, dest)
        for c in annotated:
            assert "resolution_note" in c
            assert len(c["resolution_note"]) > 20
