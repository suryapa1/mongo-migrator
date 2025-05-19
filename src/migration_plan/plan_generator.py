"""
Migration Plan Generator Module for Java to MongoDB Migration Tool

This module creates structured migration plans based on repository analysis and LLM recommendations.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from repository_analysis.analyzer import RepositoryAnalysis
from llm_integration.llm_service import LLMResponse


@dataclass
class MongoDBSchema:
    """Represents a MongoDB schema design."""
    collections: List[Dict]
    embedding_strategy: str
    indexing_strategy: Optional[str] = None


@dataclass
class CodeTransformation:
    """Represents a code transformation for migration."""
    file_type: str
    original_code: str
    transformed_code: str
    explanation: str


@dataclass
class MigrationStep:
    """Represents a step in the migration process."""
    step_number: int
    title: str
    description: str
    code_example: Optional[str] = None


@dataclass
class MongoDBConcept:
    """Represents a MongoDB concept relevant to the migration."""
    name: str
    description: str
    relevance: str


@dataclass
class MigrationPlan:
    """Contains the complete migration plan."""
    mongodb_schema: MongoDBSchema
    code_transformations: List[CodeTransformation]
    migration_steps: List[MigrationStep]
    mongodb_concepts: List[MongoDBConcept]
    summary: str


class MigrationPlanGenerator:
    """Generates structured migration plans."""

    def __init__(self, analysis: RepositoryAnalysis, llm_response: LLMResponse):
        """
        Initialize the migration plan generator.
        
        Args:
            analysis: Repository analysis results
            llm_response: LLM recommendations
        """
        self.analysis = analysis
        self.llm_response = llm_response

    def create_migration_plan(self) -> MigrationPlan:
        """
        Create a structured migration plan.
        
        Returns:
            Structured migration plan
        """
        mongodb_schema = self._process_schema()
        code_transformations = self._process_transformations()
        migration_steps = self._process_steps()
        mongodb_concepts = self._process_concepts()
        summary = self._generate_summary(mongodb_schema, code_transformations, migration_steps)
        
        return MigrationPlan(
            mongodb_schema=mongodb_schema,
            code_transformations=code_transformations,
            migration_steps=migration_steps,
            mongodb_concepts=mongodb_concepts,
            summary=summary
        )

    def _process_schema(self) -> MongoDBSchema:
        """
        Process the MongoDB schema from LLM response.
        
        Returns:
            MongoDB schema
        """
        schema_data = self.llm_response.mongodb_schema
        
        # Handle different response formats
        collections = []
        embedding_strategy = ""
        indexing_strategy = ""
        
        if isinstance(schema_data, dict):
            if 'collections' in schema_data:
                collections = schema_data.get('collections', [])
            elif 'description' in schema_data:
                # Handle text-based description
                description = schema_data.get('description', '')
                collections = self._extract_collections_from_text(description)
                embedding_strategy = self._extract_strategy_from_text(description, 'embedding')
                indexing_strategy = self._extract_strategy_from_text(description, 'indexing')
            
            embedding_strategy = schema_data.get('embedding_strategy', embedding_strategy)
            indexing_strategy = schema_data.get('indexing_strategy', indexing_strategy)
        
        # If no collections were found, create default ones based on entities
        if not collections:
            collections = self._create_default_collections()
        
        # If no embedding strategy was found, create a default one
        if not embedding_strategy:
            embedding_strategy = self._create_default_embedding_strategy()
        
        return MongoDBSchema(
            collections=collections,
            embedding_strategy=embedding_strategy,
            indexing_strategy=indexing_strategy
        )

    def _extract_collections_from_text(self, text: str) -> List[Dict]:
        """
        Extract collection information from text description.
        
        Args:
            text: Text description
            
        Returns:
            List of collection dictionaries
        """
        collections = []
        lines = text.split('\n')
        current_collection = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for collection name
            if line.endswith(' Collection') or line.endswith(' collection'):
                name = line.split(' Collection')[0].split(' collection')[0].lower()
                current_collection = {'name': name, 'fields': []}
                collections.append(current_collection)
            
            # Check for field definitions
            elif current_collection and (':' in line or '-' in line):
                parts = line.split(':', 1) if ':' in line else line.split('-', 1)
                if len(parts) == 2:
                    field_name = parts[0].strip().strip('`').strip('*')
                    field_desc = parts[1].strip()
                    
                    field_type = 'String'  # Default type
                    if 'ObjectId' in field_desc or 'id' in field_name.lower():
                        field_type = 'ObjectId'
                    elif 'array' in field_desc.lower() or 'list' in field_desc.lower():
                        field_type = 'Array'
                    elif 'date' in field_desc.lower() or 'time' in field_desc.lower():
                        field_type = 'Date'
                    elif 'number' in field_desc.lower() or 'int' in field_desc.lower():
                        field_type = 'Number'
                    
                    current_collection['fields'].append({
                        'name': field_name,
                        'type': field_type,
                        'description': field_desc
                    })
        
        return collections

    def _extract_strategy_from_text(self, text: str, strategy_type: str) -> str:
        """
        Extract strategy information from text description.
        
        Args:
            text: Text description
            strategy_type: Type of strategy to extract (embedding, indexing)
            
        Returns:
            Strategy description
        """
        lines = text.split('\n')
        strategy = ""
        
        for i, line in enumerate(lines):
            if strategy_type.lower() in line.lower():
                # Try to capture the next few lines as the strategy
                strategy_lines = []
                j = i
                while j < len(lines) and j < i + 5:  # Look at up to 5 lines
                    if lines[j].strip():
                        strategy_lines.append(lines[j].strip())
                    j += 1
                
                if strategy_lines:
                    strategy = " ".join(strategy_lines)
                    break
        
        return strategy

    def _create_default_collections(self) -> List[Dict]:
        """
        Create default collections based on entities.
        
        Returns:
            List of collection dictionaries
        """
        collections = []
        
        for entity in self.analysis.entities:
            fields = []
            
            for field in entity.fields:
                field_type = 'String'  # Default type
                
                if field.is_id:
                    field_type = 'ObjectId'
                elif 'int' in field.type.lower() or 'long' in field.type.lower():
                    field_type = 'Number'
                elif 'date' in field.type.lower() or 'time' in field.type.lower():
                    field_type = 'Date'
                elif 'list' in field.type.lower() or 'set' in field.type.lower():
                    field_type = 'Array'
                
                fields.append({
                    'name': field.name,
                    'type': field_type,
                    'description': f"From {entity.name}.{field.name}"
                })
            
            collections.append({
                'name': entity.name.lower() + 's',
                'fields': fields
            })
        
        return collections

    def _create_default_embedding_strategy(self) -> str:
        """
        Create a default embedding strategy based on relationships.
        
        Returns:
            Embedding strategy description
        """
        one_to_many = []
        many_to_many = []
        
        for rel in self.analysis.relationships:
            if rel.relationship_type == 'OneToMany':
                one_to_many.append((rel.source_entity, rel.target_entity))
            elif rel.relationship_type == 'ManyToMany':
                many_to_many.append((rel.source_entity, rel.target_entity))
        
        strategy_parts = []
        
        if one_to_many:
            embed_suggestions = [f"{target} within {source}" for source, target in one_to_many]
            strategy_parts.append(f"Embed {', '.join(embed_suggestions)} for better read performance.")
        
        if many_to_many:
            ref_suggestions = [f"{source} and {target}" for source, target in many_to_many]
            strategy_parts.append(f"Use references between {', '.join(ref_suggestions)} to avoid duplication.")
        
        if not strategy_parts:
            strategy_parts.append("Use embedding for entities with strong parent-child relationships and referencing for many-to-many relationships.")
        
        return " ".join(strategy_parts)

    def _process_transformations(self) -> List[CodeTransformation]:
        """
        Process code transformations from LLM response.
        
        Returns:
            List of code transformations
        """
        transformations_data = self.llm_response.code_transformations
        transformations = []
        
        if isinstance(transformations_data, list):
            for item in transformations_data:
                if isinstance(item, dict):
                    if 'file' in item and 'changes' in item:
                        # Handle structured format
                        for change in item['changes']:
                            transformations.append(CodeTransformation(
                                file_type=item['file'],
                                original_code=change.get('from', ''),
                                transformed_code=change.get('to', ''),
                                explanation=change.get('explanation', 'No explanation provided')
                            ))
                    elif 'description' in item:
                        # Handle text-based format
                        description = item['description']
                        file_type, original, transformed = self._parse_transformation_text(description)
                        
                        transformations.append(CodeTransformation(
                            file_type=file_type,
                            original_code=original,
                            transformed_code=transformed,
                            explanation=description
                        ))
        
        # If no transformations were found, create default ones
        if not transformations:
            transformations = self._create_default_transformations()
        
        return transformations

    def _parse_transformation_text(self, text: str) -> tuple:
        """
        Parse transformation text to extract file type, original code, and transformed code.
        
        Args:
            text: Transformation description
            
        Returns:
            Tuple of (file_type, original_code, transformed_code)
        """
        file_type = "Java"
        original = ""
        transformed = ""
        
        # Try to identify file type
        if "entity" in text.lower() or "model" in text.lower():
            file_type = "Entity"
        elif "repository" in text.lower() or "dao" in text.lower():
            file_type = "Repository"
        elif "config" in text.lower() or "properties" in text.lower() or "application" in text.lower():
            file_type = "Configuration"
        
        # Try to extract original and transformed code
        if "from" in text.lower() and "to" in text.lower():
            parts = text.lower().split("from")
            if len(parts) > 1:
                from_to_parts = parts[1].split("to")
                if len(from_to_parts) > 1:
                    original = from_to_parts[0].strip()
                    transformed = from_to_parts[1].strip()
        
        return file_type, original, transformed

    def _create_default_transformations(self) -> List[CodeTransformation]:
        """
        Create default code transformations based on entities and repositories.
        
        Returns:
            List of code transformations
        """
        transformations = []
        
        # Entity transformations
        transformations.append(CodeTransformation(
            file_type="Entity",
            original_code="@Entity\n@Table(name = \"table_name\")",
            transformed_code="@Document(collection = \"collection_name\")",
            explanation="Replace JPA entity annotations with MongoDB document annotations"
        ))
        
        transformations.append(CodeTransformation(
            file_type="Entity",
            original_code="@Id\n@GeneratedValue(strategy = GenerationType.AUTO)\nprivate Long id;",
            transformed_code="@Id\nprivate String id;",
            explanation="Replace JPA ID generation with MongoDB ObjectId"
        ))
        
        transformations.append(CodeTransformation(
            file_type="Entity",
            original_code="@Column(name = \"column_name\")",
            transformed_code="@Field(\"field_name\")",
            explanation="Replace JPA column annotations with MongoDB field annotations"
        ))
        
        # Repository transformations
        transformations.append(CodeTransformation(
            file_type="Repository",
            original_code="extends JpaRepository<Entity, Long>",
            transformed_code="extends MongoRepository<Entity, String>",
            explanation="Replace JPA repository with MongoDB repository"
        ))
        
        transformations.append(CodeTransformation(
            file_type="Repository",
            original_code="@Query(\"SELECT e FROM Entity e WHERE e.field = ?1\")",
            transformed_code="@Query(\"{field: ?0}\")",
            explanation="Replace JPQL queries with MongoDB queries"
        ))
        
        # Configuration transformations
        transformations.append(CodeTransformation(
            file_type="Configuration",
            original_code="spring.datasource.url=jdbc:mysql://localhost:3306/db\nspring.jpa.hibernate.ddl-auto=update",
            transformed_code="spring.data.mongodb.uri=mongodb://localhost:27017/db",
            explanation="Replace JPA datasource configuration with MongoDB configuration"
        ))
        
        return transformations

    def _process_steps(self) -> List[MigrationStep]:
        """
        Process migration steps from LLM response.
        
        Returns:
            List of migration steps
        """
        steps_data = self.llm_response.migration_steps
        steps = []
        
        if isinstance(steps_data, list):
            for i, item in enumerate(steps_data):
                if isinstance(item, dict):
                    if 'step' in item and 'title' in item and 'description' in item:
                        # Handle structured format
                        steps.append(MigrationStep(
                            step_number=item['step'],
                            title=item['title'],
                            description=item['description'],
                            code_example=item.get('code_example')
                        ))
                    elif 'description' in item:
                        # Handle text-based format
                        description = item['description']
                        title = description.split('.')[0] if '.' in description else description
                        
                        steps.append(MigrationStep(
                            step_number=i + 1,
                            title=title,
                            description=description,
                            code_example=None
                        ))
        
        # If no steps were found, create default ones
        if not steps:
            steps = self._create_default_steps()
        
        return steps

    def _create_default_steps(self) -> List[MigrationStep]:
        """
        Create default migration steps.
        
        Returns:
            List of migration steps
        """
        return [
            MigrationStep(
                step_number=1,
                title="Set up MongoDB environment",
                description="Install MongoDB and create the necessary databases and users.",
                code_example=None
            ),
            MigrationStep(
                step_number=2,
                title="Update dependencies",
                description="Replace JPA dependencies with Spring Data MongoDB in pom.xml or build.gradle.",
                code_example="<dependency>\n    <groupId>org.springframework.boot</groupId>\n    <artifactId>spring-boot-starter-data-mongodb</artifactId>\n</dependency>"
            ),
            MigrationStep(
                step_number=3,
                title="Transform entity classes",
                description="Convert JPA annotations to MongoDB annotations.",
                code_example=None
            ),
            MigrationStep(
                step_number=4,
                title="Update repository interfaces",
                description="Change from JPA repositories to MongoDB repositories.",
                code_example=None
            ),
            MigrationStep(
                step_number=5,
                title="Update configuration",
                description="Replace database configuration properties.",
                code_example=None
            ),
            MigrationStep(
                step_number=6,
                title="Migrate data",
                description="Write a script to migrate data from the relational database to MongoDB.",
                code_example=None
            ),
            MigrationStep(
                step_number=7,
                title="Test the application",
                description="Verify that all functionality works with MongoDB.",
                code_example=None
            )
        ]

    def _process_concepts(self) -> List[MongoDBConcept]:
        """
        Process MongoDB concepts from LLM response.
        
        Returns:
            List of MongoDB concepts
        """
        concepts_data = self.llm_response.mongodb_concepts
        concepts = []
        
        if isinstance(concepts_data, list):
            for item in concepts_data:
                if isinstance(item, dict):
                    if 'concept' in item and 'description' in item:
                        # Handle structured format
                        concepts.append(MongoDBConcept(
                            name=item['concept'],
                            description=item['description'],
                            relevance=item.get('relevance', 'General MongoDB concept')
                        ))
                    elif 'description' in item:
                        # Handle text-based format
                        description = item['description']
                        name = description.split(':')[0] if ':' in description else description.split(' ')[0]
                        
                        concepts.append(MongoDBConcept(
                            name=name,
                            description=description,
                            relevance='Extracted from LLM response'
                        ))
        
        # If no concepts were found, create default ones
        if not concepts:
            concepts = self._create_default_concepts()
        
        return concepts

    def _create_default_concepts(self) -> List[MongoDBConcept]:
        """
        Create default MongoDB concepts.
        
        Returns:
            List of MongoDB concepts
        """
        return [
            MongoDBConcept(
                name="Document Model",
                description="MongoDB stores data in flexible, JSON-like documents, allowing for nested data and arrays.",
                relevance="Core MongoDB concept"
            ),
            MongoDBConcept(
                name="Embedding vs. Referencing",
                description="Embedding documents is preferred for one-to-many relationships with strong ownership, while referencing is better for many-to-many relationships.",
                relevance="Data modeling strategy"
            ),
            MongoDBConcept(
                name="Indexing",
                description="Create indexes on frequently queried fields to improve performance.",
                relevance="Performance optimization"
            ),
            MongoDBConcept(
                name="Aggregation Pipeline",
                description="Use MongoDB's aggregation framework for complex queries instead of JPA's JPQL.",
                relevance="Query capability"
            )
        ]

    def _generate_summary(self, schema: MongoDBSchema, transformations: List[CodeTransformation], steps: List[MigrationStep]) -> str:
        """
        Generate a summary of the migration plan.
        
        Args:
            schema: MongoDB schema
            transformations: Code transformations
            steps: Migration steps
            
        Returns:
            Summary string
        """
        collection_count = len(schema.collections)
        transformation_count = len(transformations)
        step_count = len(steps)
        
        summary = f"""
# Migration Plan Summary

This migration plan will convert your Java application from a relational database to MongoDB.

## Overview
- {collection_count} MongoDB collections will be created
- {transformation_count} code transformations are required
- The migration process consists of {step_count} steps

## Key Changes
- Entity classes will be converted to MongoDB documents
- JPA repositories will be replaced with MongoDB repositories
- Database configuration will be updated for MongoDB

## Embedding Strategy
{schema.embedding_strategy}

Follow the step-by-step migration process to complete the transition to MongoDB.
"""
        return summary


def create_migration_plan(llm_response: LLMResponse, analysis: RepositoryAnalysis) -> MigrationPlan:
    """
    Create a structured migration plan.
    
    Args:
        llm_response: LLM recommendations
        analysis: Repository analysis results
        
    Returns:
        Structured migration plan
    """
    generator = MigrationPlanGenerator(analysis, llm_response)
    return generator.create_migration_plan()
