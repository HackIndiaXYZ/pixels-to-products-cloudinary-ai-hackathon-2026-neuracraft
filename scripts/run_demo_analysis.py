"""
Complete demo analysis pipeline

This script demonstrates the entire CreativePulse workflow:
1. Generate demo data
2. Create demo assets
3. Run feature extraction
4. Compute metrics
5. Generate Creative DNA
6. Display results
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.sample_data import generate_demo_dataset
from app.services.feature_service import FeatureService
from app.analytics.metrics import MetricsCalculator
from app.analytics.statistical import CreativeDNAGenerator
import pandas as pd


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_demo():
    """Run complete demo analysis"""
    print_section("CreativePulse AI - Demo Analysis Pipeline")
    
    # Step 1: Generate demo dataset
    print_section("STEP 1: Generate Demo Dataset")
    df, num_creatives = generate_demo_dataset()
    
    print(f"\nDataset Summary:")
    print(f"  Total creatives: {num_creatives}")
    print(f"  Total records: {len(df)}")
    print(f"  Platforms: {', '.join(df['platform'].unique())}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    
    print(f"\nSample records:")
    print(df.head(10).to_string(index=False))
    
    # Step 2: Compute aggregated metrics
    print_section("STEP 2: Compute Performance Metrics")
    
    # Group by creative_id and compute metrics
    creative_groups = df.groupby('creative_id').agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'conversions': 'sum',
        'spend': 'sum',
        'revenue': 'sum'
    }).reset_index()
    
    # Calculate derived metrics
    creative_groups['ctr'] = creative_groups['clicks'] / creative_groups['impressions']
    creative_groups['cvr'] = creative_groups['conversions'] / creative_groups['clicks']
    creative_groups['cpc'] = creative_groups['spend'] / creative_groups['clicks']
    creative_groups['roas'] = creative_groups['revenue'] / creative_groups['spend']
    creative_groups['cpm'] = (creative_groups['spend'] / creative_groups['impressions']) * 1000
    
    print(f"\nTop 10 creatives by ROAS:")
    top_roas = creative_groups.nlargest(10, 'roas')[['creative_id', 'roas', 'ctr', 'spend', 'revenue']]
    print(top_roas.to_string(index=False))
    
    print(f"\nOverall metrics:")
    print(f"  Total impressions: {creative_groups['impressions'].sum():,}")
    print(f"  Total clicks: {creative_groups['clicks'].sum():,}")
    print(f"  Total conversions: {creative_groups['conversions'].sum():,}")
    print(f"  Total spend: ${creative_groups['spend'].sum():,.2f}")
    print(f"  Total revenue: ${creative_groups['revenue'].sum():,.2f}")
    print(f"  Average CTR: {creative_groups['ctr'].mean():.4f}")
    print(f"  Average ROAS: {creative_groups['roas'].mean():.2f}x")
    
    # Step 3: Generate demo features
    print_section("STEP 3: Extract Visual Features (Demo)")
    
    features_data = []
    for creative_id in df['creative_id'].unique():
        # Generate demo features
        demo_features = FeatureService._get_demo_features(creative_id)
        demo_features['creative_id'] = creative_id
        features_data.append(demo_features)
    
    print(f"Extracted features for {len(features_data)} creatives")
    print(f"\nSample features:")
    for i, feature in enumerate(features_data[:5]):
        print(f"\n  {feature['creative_id']}:")
        print(f"    Aspect ratio: {feature['aspect_ratio']:.2f}")
        print(f"    Brightness: {feature['brightness']:.2f}")
        print(f"    Dominant color: {feature['dominant_color']}")
        print(f"    Portrait: {feature['portrait']}")
        print(f"    Human present: {feature['human_present']}")
    
    # Step 4: Generate Creative DNA
    print_section("STEP 4: Generate Creative DNA Insights")
    
    # Convert metrics to dictionary format
    metrics_dict = {}
    for _, row in creative_groups.iterrows():
        metrics_dict[row['creative_id']] = {
            'roas': row['roas'],
            'ctr': row['ctr'],
            'cvr': row['cvr'],
            'cpc': row['cpc'],
            'cpm': row['cpm']
        }
    
    # Generate insights
    insights = CreativeDNAGenerator.generate_insights(features_data, metrics_dict)
    
    print(f"Generated {len(insights)} Creative DNA insights")
    
    # Group by evidence tier
    tier_counts = {}
    for insight in insights:
        tier = insight['evidence_tier']
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    print(f"\nEvidence tier breakdown:")
    for tier, count in sorted(tier_counts.items()):
        print(f"  {tier}: {count}")
    
    # Show top insights
    print_section("STEP 5: Top Creative DNA Insights")
    
    # Sort by evidence strength and effect size
    tier_order = {
        'strong': 1,
        'moderate': 2,
        'weak': 3,
        'no_clear_evidence': 4,
        'insufficient_evidence': 5
    }
    
    sorted_insights = sorted(
        insights,
        key=lambda x: (tier_order.get(x['evidence_tier'], 99), -abs(x['percent_difference']))
    )
    
    print("\nTop 10 insights:")
    for i, insight in enumerate(sorted_insights[:10], 1):
        print(f"\n{i}. {insight['feature_name'].replace('_', ' ').title()} vs {insight['metric_name'].upper()}")
        print(f"   Evidence: {insight['evidence_tier']}")
        print(f"   Difference: {insight['percent_difference']:.1f}%")
        print(f"   Sample sizes: {insight['sample_size_positive']} vs {insight['sample_size_negative']}")
        if insight['p_value']:
            print(f"   P-value: {insight['p_value']:.4f}")
        if insight['effect_size']:
            print(f"   Effect size: {insight['effect_size']:.4f}")
        print(f"   Explanation: {insight['explanation'][:150]}...")
    
    # Summary statistics
    print_section("STEP 6: Summary")
    
    strong_insights = [i for i in insights if i['evidence_tier'] == 'strong']
    moderate_insights = [i for i in insights if i['evidence_tier'] == 'moderate']
    
    print(f"Analysis Summary:")
    print(f"  ✓ {num_creatives} creatives analyzed")
    print(f"  ✓ {len(df)} performance records processed")
    print(f"  ✓ {len(features_data)} visual feature sets extracted")
    print(f"  ✓ {len(insights)} Creative DNA insights generated")
    print(f"  ✓ {len(strong_insights)} strong evidence findings")
    print(f"  ✓ {len(moderate_insights)} moderate evidence findings")
    
    print(f"\n{'='*70}")
    print("Demo analysis completed successfully!")
    print(f"{'='*70}\n")
    
    return {
        'creatives': num_creatives,
        'records': len(df),
        'features': len(features_data),
        'insights': len(insights),
        'strong_insights': len(strong_insights)
    }


if __name__ == "__main__":
    results = run_demo()
    
    print("\n📊 Key Takeaways:")
    print("  1. CreativePulse analyzed 40 unique marketing creatives")
    print("  2. Statistical analysis identified patterns in visual features")
    print("  3. Evidence-based insights use Mann-Whitney U tests")
    print("  4. All findings presented with proper association language")
    print("  5. Ready for production use with real Cloudinary assets")
