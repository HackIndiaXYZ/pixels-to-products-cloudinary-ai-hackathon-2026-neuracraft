"""Sample data generation for testing"""
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import Tuple


def generate_sample_performance_csv() -> str:
    """
    Generate sample performance data as CSV string
    
    Returns:
        CSV string with sample performance data
    """
    creative_ids = [f"C{str(i).zfill(3)}" for i in range(1, 41)]  # 40 creatives
    platforms = ['facebook', 'instagram', 'google', 'tiktok']
    
    data = []
    base_date = datetime(2024, 1, 1)
    
    # Set random seed for reproducibility
    random.seed(42)
    
    for creative_id in creative_ids:
        for day in range(random.randint(8, 15)):  # 8-15 days per creative
            date = base_date + timedelta(days=day)
            platform = random.choice(platforms)
            
            impressions = random.randint(5000, 100000)
            clicks = random.randint(50, int(impressions * 0.08))  # 0.5-8% CTR
            conversions = random.randint(0, int(clicks * 0.15))  # 0-15% CVR
            spend = round(random.uniform(50, 1000), 2)
            revenue = round(spend * random.uniform(0.8, 6.0), 2)  # 0.8x-6x ROAS
            
            data.append({
                'creative_id': creative_id,
                'platform': platform,
                'impressions': impressions,
                'clicks': clicks,
                'conversions': conversions,
                'spend': spend,
                'revenue': revenue,
                'date': date.strftime('%Y-%m-%d')
            })
    
    # Add some intentional issues for validation testing
    # Duplicate row
    data.append(data[0].copy())
    
    # Row with clicks > impressions (should be excluded)
    data.append({
        'creative_id': 'C041',
        'platform': 'facebook',
        'impressions': 1000,
        'clicks': 1500,  # Invalid
        'conversions': 10,
        'spend': 50.0,
        'revenue': 250.0,
        'date': '2024-01-01'
    })
    
    # Row with negative spend (should be excluded)
    data.append({
        'creative_id': 'C042',
        'platform': 'instagram',
        'impressions': 5000,
        'clicks': 250,
        'conversions': 20,
        'spend': -100.0,  # Invalid
        'revenue': 500.0,
        'date': '2024-01-02'
    })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)


def generate_sample_performance_dataframe() -> pd.DataFrame:
    """
    Generate sample performance data as DataFrame
    
    Returns:
        DataFrame with sample performance data
    """
    csv_string = generate_sample_performance_csv()
    return pd.read_csv(pd.io.common.StringIO(csv_string))


def generate_demo_dataset() -> Tuple[pd.DataFrame, int]:
    """
    Generate complete demo dataset with performance data
    
    Returns:
        Tuple of (performance_dataframe, num_creatives)
    """
    random.seed(42)  # Reproducible
    
    num_creatives = 40
    creative_ids = [f"C{str(i).zfill(3)}" for i in range(1, num_creatives + 1)]
    platforms = ['facebook', 'instagram', 'google', 'tiktok']
    
    data = []
    base_date = datetime(2024, 1, 1)
    
    for creative_id in creative_ids:
        # Generate 8-15 records per creative
        num_records = random.randint(8, 15)
        
        for day in range(num_records):
            date = base_date + timedelta(days=day)
            platform = random.choice(platforms)
            
            # Generate realistic performance data with variation
            impressions = random.randint(5000, 100000)
            ctr_base = random.uniform(0.01, 0.08)
            clicks = int(impressions * ctr_base)
            
            cvr_base = random.uniform(0.02, 0.15)
            conversions = int(clicks * cvr_base)
            
            spend = round(random.uniform(50, 1000), 2)
            roas_base = random.uniform(0.8, 6.0)
            revenue = round(spend * roas_base, 2)
            
            data.append({
                'creative_id': creative_id,
                'platform': platform,
                'impressions': impressions,
                'clicks': clicks,
                'conversions': conversions,
                'spend': spend,
                'revenue': revenue,
                'date': date.strftime('%Y-%m-%d')
            })
    
    df = pd.DataFrame(data)
    
    print(f"Generated demo dataset:")
    print(f"  - {num_creatives} unique creatives")
    print(f"  - {len(df)} performance records")
    print(f"  - Platforms: {', '.join(platforms)}")
    print(f"  - Date range: {df['date'].min()} to {df['date'].max()}")
    
    return df, num_creatives


def generate_invalid_performance_csv() -> str:
    """
    Generate invalid performance data for testing validation
    
    Returns:
        CSV string with intentionally invalid data
    """
    data = [
        {
            'creative_id': 'C001',
            'platform': 'facebook',
            'impressions': 1000,
            'clicks': 100,
            'conversions': 10,
            'spend': 50.0,
            'revenue': 500.0
        },
        {
            'creative_id': 'C002',
            'platform': 'instagram',
            'impressions': 2000,
            'clicks': 2500,  # Invalid: clicks > impressions
            'conversions': 20,
            'spend': 100.0,
            'revenue': 1000.0
        },
        {
            'creative_id': 'C003',
            'platform': 'google',
            'impressions': 1500,
            'clicks': 150,
            'conversions': 200,  # Invalid: conversions > clicks
            'spend': 75.0,
            'revenue': 750.0
        },
        {
            'creative_id': 'C004',
            'platform': 'tiktok',
            'impressions': 3000,
            'clicks': 300,
            'conversions': 30,
            'spend': -150.0,  # Invalid: negative spend
            'revenue': 1500.0
        },
        {
            'creative_id': 'C001',  # Duplicate
            'platform': 'facebook',
            'impressions': 1000,
            'clicks': 100,
            'conversions': 10,
            'spend': 50.0,
            'revenue': 500.0
        }
    ]
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)

