"""Complete analysis pipeline orchestration.

DATA INTEGRITY GUARANTEE
========================
This pipeline processes ONLY the data the user has explicitly uploaded.

It will NEVER:
  - inject demo assets
  - inject demo performance records
  - silently seed placeholder data
  - add creative IDs that did not come from the user's uploaded CSV
  - generate Creative DNA from placeholder or synthetic features

If no creative assets have been registered, OR if all registered assets are
placeholders (local_demo), the pipeline proceeds with performance analysis only.
Visual feature extraction records Unavailable values for placeholders.
Creative DNA is only generated when at least one REAL Cloudinary image was
successfully analysed.
"""
from sqlalchemy.orm import Session
from app.models.analysis import Analysis, AnalysisStatus
from app.models.performance import PerformanceRecord
from app.models.asset import Asset
from app.services.analysis_service import AnalysisService
from app.services.feature_service import FeatureService
from app.services.dna_service import DNAService
import logging


logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Orchestrates the complete analysis pipeline."""

    @staticmethod
    def run_complete_pipeline(db: Session, analysis: Analysis) -> bool:
        """
        Run the complete analysis pipeline.

        Pipeline stages (all 7 are always emitted, even when skipped):
          1. Loading data
          2. Validating data presence
          3. Computing metrics        (on-demand from DB — signals the stage only)
          4. Visual feature extraction (skipped / Unavailable for placeholders)
          5. Running statistical analysis
          6. Building Creative DNA    (only when real Cloudinary features exist)
          7. Finalizing

        DNA generation requires REAL visual features from Cloudinary images.
        Placeholder assets produce Unavailable features and never contribute to DNA.

        Returns:
            True if successful, False if a blocking error occurred.
        """
        try:
            logger.info(f"Starting pipeline for analysis {analysis.id}")

            # ── Stage 1: Loading data ──────────────────────────────────────────
            AnalysisService.update_status(
                db, analysis, AnalysisStatus.PROCESSING, "Stage 1: Loading data"
            )
            db.refresh(analysis)

            perf_count = len(analysis.performance_records)
            asset_count = len(analysis.assets)

            # Count real (Cloudinary) vs placeholder assets
            real_asset_count = sum(
                1 for a in analysis.assets
                if a.source == 'cloudinary' and a.secure_url
            )
            placeholder_count = asset_count - real_asset_count

            logger.info(
                f"Analysis {analysis.id}: {perf_count} performance records, "
                f"{real_asset_count} real assets, {placeholder_count} placeholder(s)"
            )

            # ── Stage 2: Validating data presence ─────────────────────────────
            AnalysisService.update_status(
                db, analysis, AnalysisStatus.PROCESSING, "Stage 2: Validating data"
            )

            if perf_count == 0:
                AnalysisService.mark_failed(
                    db, analysis,
                    "No performance data found. Please upload a performance CSV or "
                    "Excel file before running the analysis."
                )
                return False

            # ── Stage 3: Computing metrics ─────────────────────────────────────
            AnalysisService.update_status(
                db, analysis, AnalysisStatus.PROCESSING, "Stage 3: Computing metrics"
            )
            # Metrics are calculated on-demand by MetricsCalculator from
            # PerformanceRecord rows — no work needed here.

            # ── Stage 4: Visual feature extraction ────────────────────────────
            real_features_extracted = 0
            if asset_count == 0:
                # No assets registered at all
                AnalysisService.update_status(
                    db, analysis,
                    AnalysisStatus.PROCESSING,
                    "Stage 4: Visual analysis — skipped (no creative assets registered)"
                )
                logger.info(
                    f"Analysis {analysis.id}: no assets — skipping visual extraction"
                )
            elif real_asset_count == 0:
                # Assets exist but all are placeholders — record Unavailable features
                # but do NOT generate DNA from them.
                AnalysisService.update_status(
                    db, analysis,
                    AnalysisStatus.PROCESSING,
                    "Stage 4: Visual analysis — skipped "
                    f"({placeholder_count} placeholder asset(s) — no real images)"
                )
                # Still call extract so placeholder rows are recorded in the DB
                # (the service now marks everything Unavailable for local_demo)
                FeatureService.extract_features_for_analysis(db, analysis.id)
                logger.info(
                    f"Analysis {analysis.id}: only placeholder assets — "
                    "features marked Unavailable, DNA will be skipped"
                )
            else:
                # At least one real Cloudinary image — extract genuine features
                AnalysisService.update_status(
                    db, analysis,
                    AnalysisStatus.PROCESSING,
                    "Stage 4: Extracting visual features"
                )
                real_features_extracted = FeatureService.extract_features_for_analysis(
                    db, analysis.id
                )
                logger.info(
                    f"Extracted real features for {real_features_extracted} asset(s)"
                )

            # ── Stage 5: Running statistical analysis ─────────────────────────
            AnalysisService.update_status(
                db, analysis,
                AnalysisStatus.PROCESSING,
                "Stage 5: Running statistical analysis"
            )

            # ── Stage 6: Building Creative DNA ────────────────────────────────
            # DNA requires at least 2 real creatives with extracted visual
            # features so that the statistical comparator has something to
            # compare.  With only 1 real asset every feature-metric pairing
            # would immediately fall back to "insufficient_evidence" (the
            # Mann-Whitney test requires ≥5 samples per group), producing
            # misleading-looking insights from a single data point.
            #
            # Minimum gate: real_features_extracted >= 2
            # Placeholder features (all None) never feed the DNA engine.
            insights_generated = 0
            # Minimum real assets required before attempting DNA
            DNA_MIN_REAL_ASSETS = 2
            if real_features_extracted >= DNA_MIN_REAL_ASSETS:
                AnalysisService.update_status(
                    db, analysis,
                    AnalysisStatus.PROCESSING,
                    "Stage 6: Building Creative DNA"
                )
                insights_generated = DNAService.generate_dna_for_analysis(
                    db, analysis.id
                )
                logger.info(f"Generated {insights_generated} Creative DNA insights")
            else:
                if asset_count == 0:
                    reason = "no creative assets registered"
                elif real_features_extracted == 0:
                    reason = (
                        f"all {placeholder_count} asset(s) are placeholders "
                        "without real images"
                    )
                else:
                    # real_features_extracted == 1
                    reason = (
                        f"only {real_features_extracted} real creative image "
                        f"— at least {DNA_MIN_REAL_ASSETS} are required to "
                        "compare visual characteristics against performance"
                    )
                AnalysisService.update_status(
                    db, analysis,
                    AnalysisStatus.PROCESSING,
                    f"Stage 6: Creative DNA — skipped ({reason})"
                )
                logger.info(
                    f"Analysis {analysis.id}: Creative DNA unavailable — {reason}"
                )

            # ── Stage 7: Finalizing ───────────────────────────────────────────
            AnalysisService.update_status(
                db, analysis, AnalysisStatus.COMPLETED, "Completed"
            )

            logger.info(
                f"Pipeline completed for analysis {analysis.id}: "
                f"{perf_count} perf records, "
                f"{real_asset_count} real assets, "
                f"{placeholder_count} placeholder(s), "
                f"{real_features_extracted} real features, "
                f"{insights_generated} DNA insights"
            )
            return True

        except Exception as e:
            logger.error(
                f"Pipeline error for analysis {analysis.id}: {e}",
                exc_info=True,
            )
            AnalysisService.mark_failed(
                db, analysis,
                "An error occurred during analysis processing. "
                "Please check your data and try again.",
            )
            return False
