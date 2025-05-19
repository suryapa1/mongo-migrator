"""
File Impact Analyzer Module for Java to MongoDB Migration Tool

This module identifies files requiring changes, estimates the scope of changes needed,
and categorizes changes by type (entity, repository, configuration).
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Set

from repository_analysis.analyzer import RepositoryAnalysis
from migration_plan.plan_generator import MigrationPlan, CodeTransformation


@dataclass
class FileChange:
    """Represents a change required for a specific file."""
    file_path: str
    change_type: str  # entity, repository, configuration
    original_code: Optional[str] = None
    new_code: Optional[str] = None
    description: str = ""
    complexity: str = "medium"  # low, medium, high


@dataclass
class ImpactSummary:
    """Summary of the impact analysis."""
    total_files: int
    entity_files: int
    repository_files: int
    configuration_files: int
    high_complexity_changes: int
    medium_complexity_changes: int
    low_complexity_changes: int
    estimated_effort_hours: float


@dataclass
class ImpactAnalysis:
    """Contains the results of the impact analysis."""
    impacted_files: List[FileChange]
    summary: ImpactSummary


class FileImpactAnalyzer:
    """Analyzes the impact of migration on files."""

    def __init__(self, repo_path: str, analysis: RepositoryAnalysis, plan: MigrationPlan):
        """
        Initialize the file impact analyzer.
        
        Args:
            repo_path: Path to the local repository
            analysis: Repository analysis results
            plan: Migration plan
        """
        self.repo_path = repo_path
        self.analysis = analysis
        self.plan = plan
        self.impacted_files = []

    def analyze_impact(self) -> ImpactAnalysis:
        """
        Analyze the impact of migration on files.
        
        Returns:
            Impact analysis results
        """
        self._analyze_entity_files()
        self._analyze_repository_files()
        self._analyze_configuration_files()
        
        summary = self._generate_summary()
        
        return ImpactAnalysis(
            impacted_files=self.impacted_files,
            summary=summary
        )

    def _analyze_entity_files(self):
        """Analyze the impact on entity files."""
        entity_transformations = [t for t in self.plan.code_transformations 
                                if t.file_type.lower() in ['entity', 'model']]
        
        for entity in self.analysis.entities:
            # Determine complexity based on number of fields and relationships
            complexity = "low"
            if len(entity.fields) > 10:
                complexity = "high"
            elif len(entity.fields) > 5:
                complexity = "medium"
            
            # Check for relationships that might increase complexity
            relationship_fields = [f for f in entity.fields if f.is_relationship]
            if len(relationship_fields) > 3:
                complexity = "high"
            elif len(relationship_fields) > 1:
                complexity = "medium"
            
            # Create description of changes needed
            changes_needed = []
            for transformation in entity_transformations:
                if transformation.original_code and transformation.original_code in open(entity.file_path, 'r').read():
                    changes_needed.append(f"Replace '{transformation.original_code}' with '{transformation.transformed_code}'")
            
            description = f"Convert JPA entity to MongoDB document. " + " ".join(changes_needed)
            
            self.impacted_files.append(FileChange(
                file_path=entity.file_path,
                change_type="entity",
                description=description,
                complexity=complexity
            ))

    def _analyze_repository_files(self):
        """Analyze the impact on repository files."""
        repo_transformations = [t for t in self.plan.code_transformations 
                              if t.file_type.lower() in ['repository', 'dao']]
        
        for repo in self.analysis.repositories:
            # Determine complexity based on number of methods and custom queries
            complexity = "low"
            custom_queries = [m for m in repo.methods if m.query]
            
            if len(repo.methods) > 10 or len(custom_queries) > 5:
                complexity = "high"
            elif len(repo.methods) > 5 or len(custom_queries) > 2:
                complexity = "medium"
            
            # Create description of changes needed
            changes_needed = []
            for transformation in repo_transformations:
                if transformation.original_code and transformation.original_code in open(repo.file_path, 'r').read():
                    changes_needed.append(f"Replace '{transformation.original_code}' with '{transformation.transformed_code}'")
            
            description = f"Convert JPA repository to MongoDB repository. " + " ".join(changes_needed)
            
            self.impacted_files.append(FileChange(
                file_path=repo.file_path,
                change_type="repository",
                description=description,
                complexity=complexity
            ))

    def _analyze_configuration_files(self):
        """Analyze the impact on configuration files."""
        config_transformations = [t for t in self.plan.code_transformations 
                                if t.file_type.lower() in ['configuration', 'config', 'properties', 'application']]
        
        for config in self.analysis.configurations:
            # Determine complexity based on file type and content
            complexity = "medium"  # Default for configuration files
            
            if config.file_type == 'xml' and 'persistence' in config.file_path:
                complexity = "high"  # persistence.xml requires significant changes
            elif config.file_type in ['properties', 'yml', 'yaml']:
                complexity = "low"  # Simple property changes
            
            # Create description of changes needed
            changes_needed = []
            for transformation in config_transformations:
                if transformation.original_code and transformation.original_code in config.content:
                    changes_needed.append(f"Replace '{transformation.original_code}' with '{transformation.transformed_code}'")
            
            description = f"Update database configuration for MongoDB. " + " ".join(changes_needed)
            
            self.impacted_files.append(FileChange(
                file_path=config.file_path,
                change_type="configuration",
                description=description,
                complexity=complexity
            ))

    def _generate_summary(self) -> ImpactSummary:
        """
        Generate a summary of the impact analysis.
        
        Returns:
            Impact summary
        """
        entity_files = len([f for f in self.impacted_files if f.change_type == "entity"])
        repository_files = len([f for f in self.impacted_files if f.change_type == "repository"])
        configuration_files = len([f for f in self.impacted_files if f.change_type == "configuration"])
        
        high_complexity = len([f for f in self.impacted_files if f.complexity == "high"])
        medium_complexity = len([f for f in self.impacted_files if f.complexity == "medium"])
        low_complexity = len([f for f in self.impacted_files if f.complexity == "low"])
        
        # Estimate effort in hours based on complexity
        estimated_effort = (high_complexity * 4) + (medium_complexity * 2) + (low_complexity * 1)
        
        return ImpactSummary(
            total_files=len(self.impacted_files),
            entity_files=entity_files,
            repository_files=repository_files,
            configuration_files=configuration_files,
            high_complexity_changes=high_complexity,
            medium_complexity_changes=medium_complexity,
            low_complexity_changes=low_complexity,
            estimated_effort_hours=estimated_effort
        )


def identify_impacted_files(analysis: RepositoryAnalysis, plan: MigrationPlan, repo_path: str) -> ImpactAnalysis:
    """
    Identify files impacted by the migration.
    
    Args:
        analysis: Repository analysis results
        plan: Migration plan
        repo_path: Path to the local repository
        
    Returns:
        Analysis of impacted files and required changes
    """
    analyzer = FileImpactAnalyzer(repo_path, analysis, plan)
    return analyzer.analyze_impact()
