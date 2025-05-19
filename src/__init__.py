"""
Package initialization file for Java to MongoDB Migration Tool
"""

# Import main modules for easy access
from .repository_analysis.analyzer import analyze_repository
from .llm_integration.llm_service import generate_migration_recommendations
from .migration_plan.plan_generator import create_migration_plan
from .file_impact.impact_analyzer import identify_impacted_files
from .mongodb_validator.validator import validate_mongodb_connection, test_mongodb_operations

__version__ = "1.0.0"
