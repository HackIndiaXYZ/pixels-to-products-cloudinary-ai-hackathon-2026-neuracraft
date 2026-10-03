"""Feature extraction service for analysis assets.

DATA INTEGRITY RULES
====================
1. Visual features are extracted ONLY from real Cloudinary-hosted images.
2. Placeholder / local_demo assets produce NULL features marked as "Unavailable".
3. Placeholder assets NEVER contribute to Creative DNA generation.
4. The caller (pipeline) is responsible for checking `real_features_extracted`
   before triggering DNA analysis.

Why this matters:
  If synthetic/random features were generated for placeholder assets, the
  resulting Creative DNA insights would appear statistically significant but
  would be based on fabricated data rather than real image characteristics.
  A user with 10 placeholder assets would see DNA insights that look real
  but are completely made up — a direct violation of the product's promise of
  evidence-based insights.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.feature import CreativeFeature
from app.analytics.features import FeatureExtractor


logger = logging.getLogger(__name__)


class FeatureService:
    """Service for extracting and storing visual features from creative assets."""

    @staticmethod
    def extract_features_for_analysis(db: Session, analysis_id: int) -> int:
        """
        Extract visual features for all assets in an analysis.

        Only real Cloudinary-hosted images produce actual feature values.
        Placeholder (local_demo) assets produce null features marked as
        'Unavailable' — they are recorded so the UI can show the asset exists,
        but they NEVER contribute numeric feature values for DNA analysis.

        Args:
            db: Database session
            analysis_id: Analysis ID

        Returns:
            Number of REAL assets that had features successfully extracted.
            Placeholder assets are NOT counted in this return value.
        """
        assets = db.query(Asset).filter(
            Asset.analysis_id == analysis_id
        ).all()

        if not assets:
            logger.warning(f"No assets found for analysis {analysis_id}")
            return 0

        # Delete existing features so a re-run starts clean
        db.query(CreativeFeature).filter(
            CreativeFeature.analysis_id == analysis_id
        ).delete()

        real_features_extracted = 0

        for asset in assets:
            try:
                if asset.source == 'cloudinary' and asset.secure_url:
                    # ── Real image: extract genuine visual features ────────────
                    features = FeatureExtractor.extract_from_url(asset.secure_url)
                    real_features_extracted += 1
                    logger.info(f"Extracted real features for asset {asset.creative_id}")
                else:
                    # ── Placeholder/demo asset: all features unavailable ───────
                    # We record the row so the UI knows the asset exists, but
                    # every feature value is NULL and every source is "Unavailable".
                    # These rows will NOT be used for Creative DNA generation.
                    features = FeatureService._unavailable_features()
                    logger.info(
                        f"Asset {asset.creative_id} is a placeholder "
                        f"(source='{asset.source}') — features marked Unavailable"
                    )

                creative_feature = CreativeFeature(
                    analysis_id=analysis_id,
                    creative_id=asset.creative_id,
                    aspect_ratio=features.get('aspect_ratio'),
                    brightness=features.get('brightness'),
                    contrast=features.get('contrast'),
                    edge_density=features.get('edge_density'),
                    dominant_color=features.get('dominant_color'),
                    bright_background=features.get('bright_background'),
                    portrait=features.get('portrait'),
                    landscape=features.get('landscape'),
                    human_present=features.get('human_present'),
                    feature_sources=features.get('feature_sources'),
                )
                db.add(creative_feature)

            except Exception as e:
                logger.error(
                    f"Error extracting features for asset "
                    f"{asset.id} ({asset.creative_id}): {e}"
                )
                continue

        db.commit()

        logger.info(
            f"Feature extraction complete for analysis {analysis_id}: "
            f"{real_features_extracted} real assets processed, "
            f"{len(assets) - real_features_extracted} placeholder(s) marked Unavailable"
        )
        return real_features_extracted

    @staticmethod
    def _unavailable_features() -> dict:
        """
        Return a features dict where every value is None and every source is
        'Unavailable'.

        Used for placeholder assets that have no real image to analyse.
        These features will NOT be used for Creative DNA generation.
        """
        sources = {
            k: 'Unavailable'
            for k in [
                'aspect_ratio', 'brightness', 'contrast', 'edge_density',
                'dominant_color', 'bright_background', 'portrait', 'landscape',
                'human_present',
            ]
        }
        return {
            'aspect_ratio': None,
            'brightness': None,
            'contrast': None,
            'edge_density': None,
            'dominant_color': None,
            'bright_background': None,
            'portrait': None,
            'landscape': None,
            'human_present': None,
            'feature_sources': sources,
        }

    # ── Read helpers ────────────────────────────────────────────────────────

    @staticmethod
    def get_features_by_creative_id(
        db: Session, analysis_id: int, creative_id: str
    ) -> Optional[CreativeFeature]:
        return db.query(CreativeFeature).filter(
            CreativeFeature.analysis_id == analysis_id,
            CreativeFeature.creative_id == creative_id,
        ).first()

    @staticmethod
    def get_all_features(db: Session, analysis_id: int) -> List[CreativeFeature]:
        return db.query(CreativeFeature).filter(
            CreativeFeature.analysis_id == analysis_id
        ).all()
