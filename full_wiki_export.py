#!/usr/bin/env python3
"""
Full Repository Wiki Exporter - process all aggregates with monitoring
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from improved_wiki_exporter import ImprovedDDDAnalyzer


async def main():
    """Main function to process the full repository"""
    
    if len(sys.argv) < 2:
        print("Usage: python full_wiki_export.py /path/to/repo [max_aggregates]")
        print("Example: python full_wiki_export.py /path/to/repo 50")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    max_aggregates = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    print("=" * 80)
    print("🚀 FULL REPOSITORY WIKI EXPORT")
    print("=" * 80)
    print(f"📂 Repository: {repo_path}")
    print(f"🎯 Max aggregates: {max_aggregates or 'ALL'}")
    print(f"📊 Output: ./temp/")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    analyzer = ImprovedDDDAnalyzer(repo_path)
    
    # Find all aggregates
    print("🔍 Scanning repository for aggregates...")
    aggregates = analyzer.find_aggregates(limit=max_aggregates)
    
    if not aggregates:
        print("❌ No aggregates found")
        return 1
    
    print(f"\n🎯 Found {len(aggregates)} aggregates to process")
    
    # Show first 10 and last 10 if there are many
    if len(aggregates) <= 20:
        for i, agg in enumerate(aggregates, 1):
            print(f"   {i}. {agg}")
    else:
        print("📋 First 10 aggregates:")
        for i, agg in enumerate(aggregates[:10], 1):
            print(f"   {i}. {agg}")
        print(f"   ... and {len(aggregates) - 20} more ...")
        print("📋 Last 10 aggregates:")
        for i, agg in enumerate(aggregates[-10:], len(aggregates) - 9):
            print(f"   {i}. {agg}")
    
    estimated_time = len(aggregates) * 6 * 15  # 6 layers × 15 seconds per layer
    print(f"\n⏱️  Estimated time: {estimated_time//60} minutes")
    print(f"📝 Will generate {len(aggregates) * 6} documentation files")
    
    # Confirmation
    response = input(f"\n🤔 Process {len(aggregates)} aggregates? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Cancelled by user")
        return 0
    
    print(f"\n⚡ Starting processing with batch size 3...")
    
    try:
        # Process in batches of 3 for better throughput
        results = await analyzer.process_aggregate_batch(aggregates, batch_size=3)
        
        # Save results
        analyzer.save_results(results)
        
        # Summary
        total_time = time.time() - analyzer.start_time
        success_rate = (analyzer.processed_count / (analyzer.processed_count + analyzer.failed_count)) * 100 if (analyzer.processed_count + analyzer.failed_count) > 0 else 0
        
        print(f"\n" + "=" * 80)
        print(f"✅ COMPLETED SUCCESSFULLY")
        print(f"🕐 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Processed: {analyzer.processed_count} files")
        print(f"❌ Failed: {analyzer.failed_count} files")
        print(f"📈 Success rate: {success_rate:.1f}%")
        print(f"⏱️  Total time: {total_time//60:.0f}m {total_time%60:.0f}s")
        print(f"⚡ Average per file: {total_time/analyzer.processed_count:.1f}s")
        print(f"📁 Output directory: {analyzer.output_path.absolute()}")
        print("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Interrupted by user")
        total_time = time.time() - analyzer.start_time
        print(f"📊 Partial results: {analyzer.processed_count} files processed")
        print(f"⏱️  Elapsed time: {total_time//60:.0f}m {total_time%60:.0f}s")
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)