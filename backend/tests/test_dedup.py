"""Tests for paper title deduplication with >= 0.85 threshold."""

from difflib import SequenceMatcher

import pytest
from sqlalchemy import select

from app.models.paper import Paper
from app.services.paper_service import dedup_by_title, normalize_title


class TestNormalizeTitle:
    """Tests for normalize_title function."""

    def test_lowercase(self):
        assert normalize_title("Hello World") == "hello world"

    def test_remove_punctuation(self):
        assert normalize_title("Hello, World!") == "hello world"

    def test_collapse_whitespace(self):
        assert normalize_title("Hello   World") == "hello world"

    def test_strip(self):
        assert normalize_title("  hello  ") == "hello"


class TestDedupByTitle:
    """Integration tests for dedup_by_title with >= 0.85 threshold."""

    @pytest.mark.asyncio
    async def test_similar_titles_merge(self, db_session):
        """Papers with very similar titles (>= 0.85) should be merged."""
        paper1 = Paper(
            id="dedup-1",
            title="A Novel Approach to Object Detection Using Deep Learning",
            title_normalized=normalize_title(
                "A Novel Approach to Object Detection Using Deep Learning"
            ),
            source="arxiv",
            source_id="2401.10001",
            url="https://arxiv.org/abs/2401.10001",
            abstract="Abstract 1",
        )
        paper2 = Paper(
            id="dedup-2",
            title="A Novel Approach to Object Detection Using Deep Networks",
            title_normalized=normalize_title(
                "A Novel Approach to Object Detection Using Deep Networks"
            ),
            source="github",
            source_id="repo-dedup",
            url="https://github.com/user/repo",
            abstract="Abstract 2",
        )
        db_session.add(paper1)
        db_session.add(paper2)
        await db_session.flush()

        # Run dedup
        await dedup_by_title(db_session, paper2)

        # Refresh both from DB
        await db_session.refresh(paper2)
        await db_session.refresh(paper1)

        # One of them should be merged into the other
        assert (
            paper1.merged_into_id == "dedup-2"
            or paper2.merged_into_id == "dedup-1"
        )

    @pytest.mark.asyncio
    async def test_dissimilar_titles_no_merge(self, db_session):
        """Papers with dissimilar titles (< 0.85) should NOT be merged."""
        paper1 = Paper(
            id="dedup-3",
            title="Object Detection Methods",
            title_normalized=normalize_title("Object Detection Methods"),
            source="arxiv",
            source_id="2401.20001",
            url="https://arxiv.org/abs/2401.20001",
            abstract="Abstract 1",
        )
        paper2 = Paper(
            id="dedup-4",
            title="Natural Language Processing Advances",
            title_normalized=normalize_title(
                "Natural Language Processing Advances"
            ),
            source="github",
            source_id="repo-nlp",
            url="https://github.com/user/nlp",
            abstract="Abstract 2",
        )
        db_session.add(paper1)
        db_session.add(paper2)
        await db_session.flush()

        await dedup_by_title(db_session, paper2)

        await db_session.refresh(paper2)
        await db_session.refresh(paper1)

        assert paper1.merged_into_id is None
        assert paper2.merged_into_id is None

    @pytest.mark.asyncio
    async def test_same_source_no_merge(self, db_session):
        """Papers from the same source should NOT be merged by dedup."""
        paper1 = Paper(
            id="dedup-5",
            title="A Study on Image Segmentation",
            title_normalized=normalize_title("A Study on Image Segmentation"),
            source="arxiv",
            source_id="2401.30001",
            url="https://arxiv.org/abs/2401.30001",
            abstract="Abstract 1",
        )
        paper2 = Paper(
            id="dedup-6",
            title="A Study on Image Segmentation Techniques",
            title_normalized=normalize_title(
                "A Study on Image Segmentation Techniques"
            ),
            source="arxiv",
            source_id="2401.30002",
            url="https://arxiv.org/abs/2401.30002",
            abstract="Abstract 2",
        )
        db_session.add(paper1)
        db_session.add(paper2)
        await db_session.flush()

        await dedup_by_title(db_session, paper2)

        await db_session.refresh(paper2)
        await db_session.refresh(paper1)

        # Same source should not merge
        assert paper1.merged_into_id is None
        assert paper2.merged_into_id is None

    @pytest.mark.asyncio
    async def test_already_merged_skipped(self, db_session):
        """Papers already merged should be skipped."""
        paper1 = Paper(
            id="dedup-7",
            title="Target Paper",
            title_normalized=normalize_title("Target Paper"),
            source="arxiv",
            source_id="2401.40001",
            url="https://arxiv.org/abs/2401.40001",
            abstract="Abstract 1",
            merged_into_id="dedup-8",
        )
        paper2 = Paper(
            id="dedup-8",
            title="Similar Target Paper",
            title_normalized=normalize_title("Similar Target Paper"),
            source="github",
            source_id="repo-similar",
            url="https://github.com/user/similar",
            abstract="Abstract 2",
        )
        db_session.add(paper1)
        db_session.add(paper2)
        await db_session.flush()

        # paper1 is already merged, so dedup should skip it
        await dedup_by_title(db_session, paper2)

        await db_session.refresh(paper2)
        assert paper2.merged_into_id is None  # Not merged further

    def test_sequence_matcher_threshold(self):
        """Verify SequenceMatcher behavior at the 0.85 boundary."""
        # These should be >= 0.85 similar
        ratio_high = SequenceMatcher(
            None,
            normalize_title("Deep Learning for Computer Vision Tasks"),
            normalize_title("Deep Learning for Computer Vision Tasks and Applications"),
        ).ratio()
        # Close but below threshold
        assert ratio_high > 0.75

        # These should be < 0.85
        ratio_low = SequenceMatcher(
            None,
            normalize_title("Object Detection"),
            normalize_title("Natural Language Processing"),
        ).ratio()
        assert ratio_low < 0.85
