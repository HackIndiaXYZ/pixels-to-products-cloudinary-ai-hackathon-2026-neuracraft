"""Performance data validation service.

Column normalization
--------------------
The validator accepts many common real-world CSV/Excel naming conventions for
the same semantic field.  After normalization all downstream code sees only the
canonical column names listed in REQUIRED_COLUMNS.

Canonical name   Accepted aliases (case-insensitive, spaces/underscores ignored)
---------------- ---------------------------------------------------------------
creative_id      creative, creativeid, ad_id, adid, asset_id, assetid,
                 ad_name, adname, creative_name, creativename
platform         channel, source, network, ad_platform, adplatform
impressions      impression, views, view, reach
clicks           click, link_clicks, linkclicks, link_click
conversions      conversion, purchases, purchase, leads, lead,
                 results, result, actions, action
spend            cost, ad_spend, adspend, amount_spent, amountspent,
                 total_spend, totalspend, budget_spent, budgetspent
revenue          sales, conversion_value, conversionvalue,
                 purchase_value, purchasevalue, total_revenue, totalrevenue,
                 roas_value, roasvalue
date             day, timestamp, report_date, reportdate, week, month
"""
import re
import pandas as pd
from typing import List, Dict, Optional, Tuple
from app.schemas.validation import ValidationResult, ValidationWarning, ValidationError
import logging


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Column alias map
# Key   = canonical name (always lowercase, underscored)
# Value = list of accepted alternative names (will be normalised before lookup)
# ---------------------------------------------------------------------------
COLUMN_ALIASES: Dict[str, List[str]] = {
    "creative_id": [
        "creative", "creativeid", "ad_id", "adid",
        "asset_id", "assetid", "ad_name", "adname",
        "creative_name", "creativename",
    ],
    "platform": [
        "channel", "source", "network", "ad_platform", "adplatform",
    ],
    "impressions": [
        "impression", "impr", "views", "view", "reach",
    ],
    "clicks": [
        "click", "link_clicks", "linkclicks", "link_click",
    ],
    "conversions": [
        "conversion", "purchases", "purchase", "leads", "lead",
        "results", "result", "actions", "action",
    ],
    "spend": [
        "cost", "ad_spend", "adspend", "amount_spent", "amountspent",
        "total_spend", "totalspend", "budget_spent", "budgetspent",
    ],
    "revenue": [
        "sales", "conversion_value", "conversionvalue",
        "purchase_value", "purchasevalue", "total_revenue", "totalrevenue",
        "roas_value", "roasvalue",
    ],
    "date": [
        "day", "timestamp", "report_date", "reportdate", "week", "month",
    ],
}


def _normalise_token(raw: str) -> str:
    """Lower-case, strip whitespace, collapse internal spaces/dashes to underscore."""
    return re.sub(r"[\s\-]+", "_", raw.strip().lower())


def _build_reverse_alias_map() -> Dict[str, str]:
    """Return {normalised_alias: canonical_name} for every known alias."""
    m: Dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        # The canonical name maps to itself
        m[_normalise_token(canonical)] = canonical
        for alias in aliases:
            m[_normalise_token(alias)] = canonical
    return m


_REVERSE_ALIAS_MAP = _build_reverse_alias_map()


class PerformanceValidator:
    """Validator for performance data uploads."""

    # Canonical names for required and optional fields
    REQUIRED_COLUMNS = [
        "creative_id",
        "platform",
        "impressions",
        "clicks",
        "conversions",
        "spend",
        "revenue",
    ]
    OPTIONAL_COLUMNS = ["date"]
    NUMERIC_COLUMNS = ["impressions", "clicks", "conversions", "spend", "revenue"]

    def __init__(self) -> None:
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationWarning] = []
        self.excluded_rows: int = 0
        # populated after _normalise_columns runs
        self.column_mapping: Dict[str, str] = {}   # original → canonical

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def validate_file(self, df: pd.DataFrame) -> Tuple[ValidationResult, pd.DataFrame]:
        """
        Validate and clean a performance DataFrame.

        Steps:
          1. Normalise column names (alias mapping + case/whitespace clean-up)
          2. Check required columns are present
          3. Convert numeric and date types
          4. Remove invalid rows (nulls, negatives, logical errors)
          5. Remove exact duplicates
          6. Report missing optional values

        Returns:
            (ValidationResult, cleaned DataFrame)
        """
        total_rows = len(df)
        logger.info(f"Validating {total_rows} rows")

        # Step 1 — normalise columns (must happen before required-column check)
        df = self._normalise_columns(df)

        # Step 2 — check required columns
        if not self._check_required_columns(df):
            return self._build_result(total_rows, pd.DataFrame()), pd.DataFrame()

        # Step 3 — type conversions
        df = self._validate_data_types(df)

        # Step 4 — integrity checks (removes bad rows)
        df = self._validate_data_integrity(df)

        # Step 5 — duplicate removal
        df = self._check_duplicates(df)

        # Step 6 — optional-field warnings
        self._check_missing_values(df)

        valid_rows = len(df)
        self.excluded_rows = total_rows - valid_rows

        result = self._build_result(total_rows, df)
        logger.info(f"Validation complete: {valid_rows}/{total_rows} rows valid")
        return result, df

    # ------------------------------------------------------------------
    # Column normalisation
    # ------------------------------------------------------------------

    def _normalise_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rename DataFrame columns to their canonical equivalents.

        Algorithm:
          1. Normalise each raw column name (lowercase, strip, collapse spaces).
          2. Look it up in the reverse-alias map.
          3. If found → rename to the canonical name; record the mapping.
          4. If not found → keep the normalised name (it may be an extra column
             the user included; it will simply be ignored downstream).

        Warnings are emitted for any required fields that were resolved via an
        alias (so the user knows what happened).
        """
        new_columns: Dict[str, str] = {}  # old_name → new_name
        mapping: Dict[str, str] = {}       # original_name → canonical_name

        for raw_col in df.columns:
            normalised = _normalise_token(raw_col)
            canonical = _REVERSE_ALIAS_MAP.get(normalised)
            if canonical:
                new_columns[raw_col] = canonical
                if normalised != canonical:
                    mapping[raw_col] = canonical
            else:
                # Keep the normalised version; downstream will ignore unknowns
                new_columns[raw_col] = normalised

        # Detect if two raw columns map to the same canonical name; keep first
        seen_canonical: Dict[str, str] = {}
        deduped: Dict[str, str] = {}
        for raw, canonical in new_columns.items():
            if canonical in seen_canonical:
                logger.warning(
                    f"Column '{raw}' maps to canonical '{canonical}' but that "
                    f"canonical was already resolved from '{seen_canonical[canonical]}'. "
                    f"Keeping '{seen_canonical[canonical]}', ignoring '{raw}'."
                )
                deduped[raw] = f"_duplicate_{raw}"
            else:
                seen_canonical[canonical] = raw
                deduped[raw] = canonical

        df = df.rename(columns=deduped)
        # Drop any columns that ended up with the _duplicate_ prefix
        drop_cols = [c for c in df.columns if c.startswith("_duplicate_")]
        if drop_cols:
            df = df.drop(columns=drop_cols)

        self.column_mapping = mapping

        if mapping:
            alias_descriptions = ", ".join(
                f"'{orig}' → '{can}'" for orig, can in mapping.items()
            )
            self.warnings.append(ValidationWarning(
                type="COLUMN_ALIAS_MAPPING",
                message=f"Column names were automatically mapped: {alias_descriptions}",
                details={"mapping": mapping}
            ))

        return df

    def _check_required_columns(self, df: pd.DataFrame) -> bool:
        """After normalisation, verify all required canonical columns exist."""
        present = set(df.columns)
        missing = [c for c in self.REQUIRED_COLUMNS if c not in present]
        if missing:
            self.errors.append(ValidationError(
                type="MISSING_COLUMNS",
                message=(
                    f"Missing required columns: {', '.join(missing)}. "
                    f"Present columns after normalisation: {', '.join(sorted(present))}. "
                    "If your file uses different column names, ensure they match a known "
                    "alias (see documentation)."
                ),
                details={"missing_columns": missing, "present_columns": sorted(present)}
            ))
            return False
        return True

    # ------------------------------------------------------------------
    # Type conversion
    # ------------------------------------------------------------------

    def _validate_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in self.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                null_count = int(df[col].isnull().sum())
                if null_count > 0:
                    self.warnings.append(ValidationWarning(
                        type="TYPE_CONVERSION",
                        message=f"Could not convert {null_count} value(s) in '{col}' to numeric — those rows will be excluded",
                        count=null_count
                    ))

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            null_count = int(df['date'].isnull().sum())
            if null_count > 0:
                self.warnings.append(ValidationWarning(
                    type="DATE_CONVERSION",
                    message=f"Could not parse {null_count} date value(s)",
                    count=null_count
                ))

        return df

    # ------------------------------------------------------------------
    # Integrity checks
    # ------------------------------------------------------------------

    def _validate_data_integrity(self, df: pd.DataFrame) -> pd.DataFrame:
        initial_count = len(df)

        # Remove rows where any required field is null
        required_present = [c for c in self.REQUIRED_COLUMNS if c in df.columns]
        df = df.dropna(subset=required_present).reset_index(drop=True)
        removed = initial_count - len(df)
        if removed > 0:
            self.warnings.append(ValidationWarning(
                type="NULL_VALUES",
                message=f"Removed {removed} row(s) with missing required values",
                count=removed
            ))

        # Remove rows with negative numeric values
        for col in ["impressions", "clicks", "conversions", "spend", "revenue"]:
            if col not in df.columns:
                continue
            mask_neg = df[col] < 0
            neg_count = int(mask_neg.sum())
            if neg_count > 0:
                self.warnings.append(ValidationWarning(
                    type="NEGATIVE_VALUES",
                    message=f"Removed {neg_count} row(s) with negative values in '{col}'",
                    count=neg_count,
                    details={"column": col}
                ))
                df = df[~mask_neg].reset_index(drop=True)

        # clicks > impressions
        if 'clicks' in df.columns and 'impressions' in df.columns:
            mask = df['clicks'] > df['impressions']
            count = int(mask.sum())
            if count > 0:
                self.warnings.append(ValidationWarning(
                    type="INVALID_CTR",
                    message=f"Removed {count} row(s) where clicks > impressions",
                    count=count
                ))
                df = df[~mask].reset_index(drop=True)

        # conversions > clicks
        if 'conversions' in df.columns and 'clicks' in df.columns:
            mask = df['conversions'] > df['clicks']
            count = int(mask.sum())
            if count > 0:
                self.warnings.append(ValidationWarning(
                    type="INVALID_CVR",
                    message=f"Removed {count} row(s) where conversions > clicks",
                    count=count
                ))
                df = df[~mask].reset_index(drop=True)

        return df

    # ------------------------------------------------------------------
    # Duplicate handling
    # ------------------------------------------------------------------

    def _check_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and remove exact business-key duplicates.

        Business key: (creative_id, platform[, date])
        Rule: keep the first occurrence, remove subsequent ones.
        The duplicate count and definition are reported as a warning.
        """
        key_cols = ['creative_id', 'platform']
        if 'date' in df.columns:
            key_cols.append('date')

        dupes = df.duplicated(subset=key_cols, keep='first')
        dupe_count = int(dupes.sum())

        if dupe_count > 0:
            self.warnings.append(ValidationWarning(
                type="DUPLICATE_ROWS",
                message=(
                    f"Found and removed {dupe_count} duplicate row(s). "
                    f"Duplicate key: ({', '.join(key_cols)}). "
                    "First occurrence kept."
                ),
                count=dupe_count,
                details={"key_columns": key_cols}
            ))
            df = df[~dupes].reset_index(drop=True)

        return df

    # ------------------------------------------------------------------
    # Optional-field warnings
    # ------------------------------------------------------------------

    def _check_missing_values(self, df: pd.DataFrame) -> None:
        if 'date' in df.columns:
            missing = int(df['date'].isnull().sum())
            if missing > 0:
                self.warnings.append(ValidationWarning(
                    type="MISSING_DATES",
                    message=f"{missing} row(s) have missing dates (date is optional)",
                    count=missing
                ))

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------

    def _build_result(self, total_rows: int, valid_df: pd.DataFrame) -> ValidationResult:
        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
            excluded_rows=self.excluded_rows,
            total_rows=total_rows,
            valid_rows=len(valid_df)
        )


# ---------------------------------------------------------------------------
# File loader
# ---------------------------------------------------------------------------

def load_performance_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """
    Load a CSV or Excel file into a DataFrame.

    Raises:
        ValueError: If the file format is unsupported or the file cannot be parsed.
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    try:
        if ext == 'csv':
            df = pd.read_csv(pd.io.common.BytesIO(file_content))
        elif ext in ('xlsx', 'xls'):
            df = pd.read_excel(pd.io.common.BytesIO(file_content))
        else:
            raise ValueError(
                f"Unsupported file format: '.{ext}'. "
                "Accepted formats: .csv, .xlsx, .xls"
            )
        return df
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error loading file '{filename}': {e}")
        raise ValueError(f"Could not parse the file '{filename}': {e}")
