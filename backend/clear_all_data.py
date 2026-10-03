"""
Script to clear all analysis data from the database.
This will delete all analyses, assets, performance records, features, and DNA insights.
User accounts are preserved.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import Analysis, Asset, PerformanceRecord, CreativeFeature, CreativeDNAInsight, GeneratedAsset

def clear_all_analysis_data():
    """Clear all analysis-related data while preserving user accounts"""
    
    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("CLEARING ALL ANALYSIS DATA")
        print("=" * 80)
        
        # Count existing data
        analysis_count = db.query(Analysis).count()
        asset_count = db.query(Asset).count()
        perf_count = db.query(PerformanceRecord).count()
        feature_count = db.query(CreativeFeature).count()
        dna_count = db.query(CreativeDNAInsight).count()
        generated_count = db.query(GeneratedAsset).count()
        
        print(f"\nCurrent data:")
        print(f"  - Analyses: {analysis_count}")
        print(f"  - Assets: {asset_count}")
        print(f"  - Performance Records: {perf_count}")
        print(f"  - Creative Features: {feature_count}")
        print(f"  - DNA Insights: {dna_count}")
        print(f"  - Generated Assets: {generated_count}")
        
        if analysis_count == 0:
            print("\n✓ Database is already clean - no analyses to delete")
            return
        
        print("\nDeleting all analysis data...")
        
        # Delete in correct order (respecting foreign keys)
        # Generated assets reference analyses
        deleted_generated = db.query(GeneratedAsset).delete()
        print(f"  ✓ Deleted {deleted_generated} generated assets")
        
        # DNA insights reference analyses
        deleted_dna = db.query(CreativeDNAInsight).delete()
        print(f"  ✓ Deleted {deleted_dna} DNA insights")
        
        # Features reference analyses
        deleted_features = db.query(CreativeFeature).delete()
        print(f"  ✓ Deleted {deleted_features} creative features")
        
        # Performance records reference analyses
        deleted_perf = db.query(PerformanceRecord).delete()
        print(f"  ✓ Deleted {deleted_perf} performance records")
        
        # Assets reference analyses
        deleted_assets = db.query(Asset).delete()
        print(f"  ✓ Deleted {deleted_assets} assets")
        
        # Finally delete analyses
        deleted_analyses = db.query(Analysis).delete()
        print(f"  ✓ Deleted {deleted_analyses} analyses")
        
        # Commit all deletions
        db.commit()
        
        print("\n" + "=" * 80)
        print("✓ ALL ANALYSIS DATA CLEARED SUCCESSFULLY")
        print("=" * 80)
        print("\nUser accounts have been preserved.")
        print("The database is now fresh and ready for new analyses.")
        print("\nYou can now:")
        print("  1. Refresh the frontend")
        print("  2. Create new analyses")
        print("  3. Upload fresh data")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error clearing data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    print("\n⚠️  WARNING: This will delete ALL analysis data from the database!")
    print("User accounts will be preserved, but all analyses will be removed.")
    
    # Ask for confirmation
    response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
    
    if response == "yes":
        clear_all_analysis_data()
    else:
        print("\n✗ Operation cancelled")
        sys.exit(0)
