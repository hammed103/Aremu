#!/usr/bin/env python3
"""
Benchmark embedding vs traditional matching performance
"""

import time
import logging
import os
import sys
import statistics
from typing import List, Dict

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embedding_job_matcher import EmbeddingJobMatcher
from legacy.intelligent_job_matcher import IntelligentJobMatcher
from legacy.database_manager import DatabaseManager
from legacy.flexible_preference_manager import FlexiblePreferenceManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingBenchmark:
    """Benchmark embedding vs traditional matching"""

    def __init__(self):
        self.db = DatabaseManager()
        self.pref_manager = FlexiblePreferenceManager(self.db.connection)

        # Initialize matchers
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.embedding_matcher = EmbeddingJobMatcher(self.db.connection, openai_key)
        else:
            self.embedding_matcher = None

        self.traditional_matcher = IntelligentJobMatcher(self.db.connection)

    def get_test_users(self, limit: int = 10) -> List[int]:
        """Get test users with preferences"""
        cursor = self.db.connection.cursor()
        cursor.execute(
            """
            SELECT user_id FROM user_preferences 
            WHERE job_roles IS NOT NULL OR job_categories IS NOT NULL
            LIMIT %s
        """,
            (limit,),
        )

        return [row[0] for row in cursor.fetchall()]

    def benchmark_embedding_search(
        self, user_ids: List[int], iterations: int = 3
    ) -> Dict:
        """Benchmark embedding-based search"""
        if not self.embedding_matcher:
            return {"error": "Embedding matcher not available"}

        times = []
        results_counts = []

        for _ in range(iterations):
            start_time = time.time()

            total_results = 0
            for user_id in user_ids:
                results = self.embedding_matcher.search_jobs_with_embeddings(
                    user_id, 50
                )
                total_results += len(results)

            end_time = time.time()
            times.append(end_time - start_time)
            results_counts.append(total_results)

        return {
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "avg_results": statistics.mean(results_counts),
            "total_searches": len(user_ids) * iterations,
        }

    def benchmark_traditional_search(
        self, user_ids: List[int], iterations: int = 3
    ) -> Dict:
        """Benchmark traditional search"""
        times = []
        results_counts = []

        for _ in range(iterations):
            start_time = time.time()

            total_results = 0
            for user_id in user_ids:
                results = self.traditional_matcher.search_jobs_for_user(user_id, 50)
                total_results += len(results)

            end_time = time.time()
            times.append(end_time - start_time)
            results_counts.append(total_results)

        return {
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "avg_results": statistics.mean(results_counts),
            "total_searches": len(user_ids) * iterations,
        }

    def check_embedding_coverage(self) -> Dict:
        """Check embedding coverage statistics"""
        cursor = self.db.connection.cursor()

        # User embedding coverage
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_users,
                COUNT(user_embedding) as users_with_embeddings,
                ROUND(COUNT(user_embedding) * 100.0 / COUNT(*), 1) as coverage_percent
            FROM user_preferences 
            WHERE job_roles IS NOT NULL OR job_categories IS NOT NULL
        """
        )

        user_stats = cursor.fetchone()

        # Job embedding coverage
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(job_embedding) as jobs_with_embeddings,
                ROUND(COUNT(job_embedding) * 100.0 / COUNT(*), 1) as coverage_percent
            FROM canonical_jobs 
            WHERE posted_date >= CURRENT_DATE - INTERVAL '60 days'
        """
        )

        job_stats = cursor.fetchone()

        return {
            "user_total": user_stats[0],
            "user_with_embeddings": user_stats[1],
            "user_coverage_percent": user_stats[2],
            "job_total": job_stats[0],
            "job_with_embeddings": job_stats[1],
            "job_coverage_percent": job_stats[2],
        }

    def run_full_benchmark(self) -> Dict:
        """Run complete benchmark suite"""
        print("🚀 EMBEDDING SYSTEM BENCHMARK")
        print("=" * 50)

        # Check embedding coverage
        print("\n📊 Checking embedding coverage...")
        coverage = self.check_embedding_coverage()

        print(
            f"User Coverage: {coverage['user_with_embeddings']}/{coverage['user_total']} ({coverage['user_coverage_percent']}%)"
        )
        print(
            f"Job Coverage: {coverage['job_with_embeddings']}/{coverage['job_total']} ({coverage['job_coverage_percent']}%)"
        )

        # Get test users
        print("\n👥 Getting test users...")
        test_users = self.get_test_users(10)
        print(f"Found {len(test_users)} test users")

        if not test_users:
            print("❌ No test users found")
            return {"error": "No test users available"}

        # Benchmark embedding search
        print("\n🧠 Benchmarking embedding search...")
        embedding_results = self.benchmark_embedding_search(test_users, 3)

        # Benchmark traditional search
        print("🔍 Benchmarking traditional search...")
        traditional_results = self.benchmark_traditional_search(test_users, 3)

        # Calculate improvements
        if not embedding_results.get("error") and traditional_results["avg_time"] > 0:
            speed_improvement = (
                traditional_results["avg_time"] / embedding_results["avg_time"]
            )
        else:
            speed_improvement = 0

        # Print results
        print("\n" + "=" * 50)
        print("📈 BENCHMARK RESULTS")
        print("=" * 50)

        if embedding_results.get("error"):
            print(f"❌ Embedding Search: {embedding_results['error']}")
        else:
            print(f"🧠 Embedding Search:")
            print(f"   Average Time: {embedding_results['avg_time']:.3f}s")
            print(f"   Min Time: {embedding_results['min_time']:.3f}s")
            print(f"   Max Time: {embedding_results['max_time']:.3f}s")
            print(f"   Average Results: {embedding_results['avg_results']:.1f}")

        print(f"\n🔍 Traditional Search:")
        print(f"   Average Time: {traditional_results['avg_time']:.3f}s")
        print(f"   Min Time: {traditional_results['min_time']:.3f}s")
        print(f"   Max Time: {traditional_results['max_time']:.3f}s")
        print(f"   Average Results: {traditional_results['avg_results']:.1f}")

        if speed_improvement > 0:
            print(f"\n⚡ Speed Improvement: {speed_improvement:.1f}x faster")

        # Health assessment
        print(f"\n🏥 System Health:")
        if (
            coverage["user_coverage_percent"] >= 80
            and coverage["job_coverage_percent"] >= 80
        ):
            print("✅ EXCELLENT - High embedding coverage")
        elif (
            coverage["user_coverage_percent"] >= 60
            and coverage["job_coverage_percent"] >= 60
        ):
            print("⚠️ GOOD - Moderate embedding coverage")
        else:
            print("❌ NEEDS ATTENTION - Low embedding coverage")

        return {
            "coverage": coverage,
            "embedding_results": embedding_results,
            "traditional_results": traditional_results,
            "speed_improvement": speed_improvement,
            "test_users_count": len(test_users),
        }


def main():
    """Main benchmark function"""
    benchmark = EmbeddingBenchmark()
    results = benchmark.run_full_benchmark()

    # Save results to file
    import json

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to benchmark_results.json")


if __name__ == "__main__":
    main()
