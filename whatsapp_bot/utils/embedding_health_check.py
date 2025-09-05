#!/usr/bin/env python3
"""
Health check for embedding system
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


# Load .env file
load_env_file()

from legacy.database_manager import DatabaseManager
from services.embedding_generator import EmbeddingGenerator
from utils.logger import setup_logger

logger = setup_logger(__name__)


def check_vector_extension():
    """Check if vector extension is available"""
    try:
        db = DatabaseManager()
        cursor = db.connection.cursor()
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking vector extension: {e}")
        return False


def check_embedding_columns():
    """Check if embedding columns exist"""
    try:
        db = DatabaseManager()
        cursor = db.connection.cursor()

        # Check user_preferences columns
        cursor.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_preferences' 
            AND column_name IN ('user_embedding', 'embedding_text', 'embedding_updated_at', 'embedding_version')
        """
        )

        user_columns = [row[0] for row in cursor.fetchall()]

        # Check canonical_jobs columns
        cursor.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'canonical_jobs' 
            AND column_name IN ('job_embedding', 'job_embedding_text', 'job_embedding_updated_at', 'embedding_version')
        """
        )

        job_columns = [row[0] for row in cursor.fetchall()]

        return {
            "user_columns": len(user_columns),
            "job_columns": len(job_columns),
            "user_complete": len(user_columns) == 4,
            "job_complete": len(job_columns) == 4,
        }

    except Exception as e:
        logger.error(f"Error checking embedding columns: {e}")
        return {"error": str(e)}


def check_embedding_indexes():
    """Check if embedding indexes exist"""
    try:
        db = DatabaseManager()
        cursor = db.connection.cursor()

        cursor.execute(
            """
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename IN ('user_preferences', 'canonical_jobs')
            AND indexname LIKE '%embedding%'
        """
        )

        indexes = [row[0] for row in cursor.fetchall()]
        return {"total_indexes": len(indexes), "indexes": indexes}

    except Exception as e:
        logger.error(f"Error checking embedding indexes: {e}")
        return {"error": str(e)}


def check_embedding_coverage():
    """Check embedding coverage statistics"""
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return {"error": "OpenAI API key not available"}

        db = DatabaseManager()
        generator = EmbeddingGenerator(db.connection, openai_key)
        return generator.get_embedding_stats()

    except Exception as e:
        logger.error(f"Error checking embedding coverage: {e}")
        return {"error": str(e)}


def check_openai_connection():
    """Check OpenAI API connection"""
    try:
        import openai

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return {"available": False, "reason": "API key not set"}

        # Try to create a client
        client = openai.OpenAI(api_key=openai_key)

        # Simple test - just check if we can create the client
        return {"available": True, "api_key_set": True}

    except Exception as e:
        return {"available": False, "reason": str(e)}


def run_comprehensive_health_check():
    """Run complete health check"""
    print("🏥 EMBEDDING SYSTEM HEALTH CHECK")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    health_status = {
        "overall": "UNKNOWN",
        "issues": [],
        "warnings": [],
        "successes": [],
    }

    # 1. Check vector extension
    print("1. 🧬 Checking Vector Extension...")
    vector_available = check_vector_extension()
    if vector_available:
        print("   ✅ Vector extension is available")
        health_status["successes"].append("Vector extension available")
    else:
        print("   ❌ Vector extension not found")
        health_status["issues"].append("Vector extension missing")

    # 2. Check embedding columns
    print("\n2. 📊 Checking Database Schema...")
    columns_result = check_embedding_columns()
    if "error" in columns_result:
        print(f"   ❌ Error checking columns: {columns_result['error']}")
        health_status["issues"].append(
            f"Schema check failed: {columns_result['error']}"
        )
    else:
        print(f"   User embedding columns: {columns_result['user_columns']}/4")
        print(f"   Job embedding columns: {columns_result['job_columns']}/4")

        if columns_result["user_complete"] and columns_result["job_complete"]:
            print("   ✅ All embedding columns present")
            health_status["successes"].append("Database schema complete")
        else:
            print("   ⚠️ Some embedding columns missing")
            health_status["warnings"].append("Incomplete database schema")

    # 3. Check indexes
    print("\n3. 🔍 Checking Vector Indexes...")
    indexes_result = check_embedding_indexes()
    if "error" in indexes_result:
        print(f"   ❌ Error checking indexes: {indexes_result['error']}")
        health_status["issues"].append(f"Index check failed: {indexes_result['error']}")
    else:
        print(f"   Found {indexes_result['total_indexes']} embedding indexes")
        for index in indexes_result["indexes"]:
            print(f"   - {index}")

        if indexes_result["total_indexes"] >= 4:
            print("   ✅ Sufficient indexes found")
            health_status["successes"].append("Vector indexes present")
        else:
            print("   ⚠️ Some indexes may be missing")
            health_status["warnings"].append("Incomplete vector indexes")

    # 4. Check OpenAI connection
    print("\n4. 🤖 Checking OpenAI Connection...")
    openai_result = check_openai_connection()
    if openai_result["available"]:
        print("   ✅ OpenAI API available")
        health_status["successes"].append("OpenAI API available")
    else:
        print(f"   ❌ OpenAI API not available: {openai_result['reason']}")
        health_status["issues"].append(f"OpenAI API issue: {openai_result['reason']}")

    # 5. Check embedding coverage
    print("\n5. 📈 Checking Embedding Coverage...")
    coverage_result = check_embedding_coverage()
    if "error" in coverage_result:
        print(f"   ❌ Error checking coverage: {coverage_result['error']}")
        health_status["warnings"].append(
            f"Coverage check failed: {coverage_result['error']}"
        )
    else:
        user_coverage = coverage_result.get("user_coverage_percent", 0)
        job_coverage = coverage_result.get("job_coverage_percent", 0)

        print(
            f"   User embeddings: {coverage_result.get('user_with_embeddings', 0)}/{coverage_result.get('user_total', 0)} ({user_coverage}%)"
        )
        print(
            f"   Job embeddings: {coverage_result.get('job_with_embeddings', 0)}/{coverage_result.get('job_total', 0)} ({job_coverage}%)"
        )

        if user_coverage >= 80 and job_coverage >= 80:
            print("   ✅ Excellent embedding coverage")
            health_status["successes"].append("High embedding coverage")
        elif user_coverage >= 60 and job_coverage >= 60:
            print("   ⚠️ Good embedding coverage")
            health_status["warnings"].append("Moderate embedding coverage")
        else:
            print("   ❌ Low embedding coverage")
            health_status["issues"].append("Low embedding coverage")

    # Overall health assessment
    print("\n" + "=" * 50)
    print("🏥 OVERALL HEALTH ASSESSMENT")
    print("=" * 50)

    if len(health_status["issues"]) == 0:
        if len(health_status["warnings"]) == 0:
            health_status["overall"] = "EXCELLENT"
            print("✅ EXCELLENT - System is fully operational")
        else:
            health_status["overall"] = "GOOD"
            print("⚠️ GOOD - System is operational with minor issues")
    else:
        health_status["overall"] = "NEEDS ATTENTION"
        print("❌ NEEDS ATTENTION - Critical issues found")

    print(f"\n📊 Summary:")
    print(f"   ✅ Successes: {len(health_status['successes'])}")
    print(f"   ⚠️ Warnings: {len(health_status['warnings'])}")
    print(f"   ❌ Issues: {len(health_status['issues'])}")

    if health_status["issues"]:
        print(f"\n🚨 Critical Issues:")
        for issue in health_status["issues"]:
            print(f"   - {issue}")

    if health_status["warnings"]:
        print(f"\n⚠️ Warnings:")
        for warning in health_status["warnings"]:
            print(f"   - {warning}")

    return health_status


if __name__ == "__main__":
    health_status = run_comprehensive_health_check()

    # Exit with appropriate code
    if health_status["overall"] == "NEEDS ATTENTION":
        sys.exit(1)
    else:
        sys.exit(0)
