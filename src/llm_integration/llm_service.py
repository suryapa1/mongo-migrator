"""
LLM Integration Module for Java to MongoDB Migration Tool

This module connects to GPT-4 API, prepares prompts based on repository analysis,
and processes LLM responses to extract structured migration plans.
"""

import os
import json
from typing import Dict, List, Any, Optional
import openai
from dataclasses import dataclass, asdict

from repository_analysis.analyzer import RepositoryAnalysis


@dataclass
class LLMResponse:
    """Contains the structured response from the LLM."""
    mongodb_schema: Dict
    code_transformations: List[Dict]
    migration_steps: List[Dict]
    mongodb_concepts: List[Dict]
    raw_response: str


class LLMIntegration:
    """Handles integration with GPT-4 for migration plan generation."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM integration.
        
        Args:
            api_key: OpenAI API key (optional, can be set via environment variable)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key

    def generate_migration_recommendations(self, analysis: RepositoryAnalysis) -> LLMResponse:
        """
        Generate migration recommendations using GPT-4.
        
        Args:
            analysis: Repository analysis results
            
        Returns:
            Structured LLM response with migration recommendations
        """
        prompt = self._create_prompt(analysis)
        response = self._call_llm(prompt)
        structured_response = self._process_response(response)
        return structured_response

    def _create_prompt(self, analysis: RepositoryAnalysis) -> str:
        """
        Create a prompt for the LLM based on repository analysis.
        
        Args:
            analysis: Repository analysis results
            
        Returns:
            Formatted prompt string
        """
        # Convert analysis to a more readable format for the prompt
        entities_info = []
        for entity in analysis.entities:
            fields_info = []
            for field in entity.fields:
                field_info = {
                    "name": field.name,
                    "type": field.type,
                    "annotations": field.annotations
                }
                if field.is_id:
                    field_info["is_id"] = True
                if field.is_relationship:
                    field_info["is_relationship"] = True
                    field_info["relationship_type"] = field.relationship_type
                    if field.target_entity:
                        field_info["target_entity"] = field.target_entity
                fields_info.append(field_info)
            
            entity_info = {
                "name": entity.name,
                "annotations": entity.annotations,
                "fields": fields_info
            }
            if entity.table_name:
                entity_info["table_name"] = entity.table_name
            
            entities_info.append(entity_info)
        
        repositories_info = []
        for repo in analysis.repositories:
            methods_info = []
            for method in repo.methods:
                method_info = {
                    "name": method.name,
                    "return_type": method.return_type,
                    "parameters": method.parameters
                }
                if method.query:
                    method_info["query"] = method.query
                methods_info.append(method_info)
            
            repo_info = {
                "name": repo.name,
                "entity": repo.entity_name,
                "extends": repo.extends,
                "methods": methods_info
            }
            repositories_info.append(repo_info)
        
        # Create a structured prompt
        prompt = f"""
You are an expert Java developer specializing in database migrations from relational databases to MongoDB.
Your task is to analyze the following Java application components and create a detailed migration plan.

# Application Analysis

## Entities
{json.dumps(entities_info, indent=2)}

## Repositories
{json.dumps(repositories_info, indent=2)}

## Database Configurations
{[config.file_path for config in analysis.configurations]}

## Entity Relationships
{[(rel.source_entity, rel.relationship_type, rel.target_entity) for rel in analysis.relationships]}

# Migration Task

Create a comprehensive plan to migrate this application from a relational database to MongoDB.
Your response should include:

1. MongoDB Schema Design:
   - Document structure for each entity
   - Embedding vs. referencing decisions
   - Indexing recommendations

2. Code Transformations:
   - Changes needed for entity classes (JPA to MongoDB annotations)
   - Repository interface modifications
   - Configuration changes

3. Step-by-Step Migration Process:
   - Data migration approach
   - Code refactoring sequence
   - Testing strategy

4. MongoDB Concepts:
   - Explain relevant MongoDB concepts for this specific migration
   - Best practices for the migration

Format your response as a structured JSON with the following sections:
- mongodb_schema
- code_transformations
- migration_steps
- mongodb_concepts

Ensure your recommendations follow MongoDB best practices and maintain the application's functionality.
"""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM API with the prepared prompt.
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            Raw LLM response
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert Java developer specializing in database migrations from relational databases to MongoDB."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            # For development/testing without API key
            print(f"Error calling OpenAI API: {e}")
            return self._generate_mock_response()

    def _process_response(self, response: str) -> LLMResponse:
        """
        Process the LLM response into a structured format.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured LLM response
        """
        try:
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return LLMResponse(
                    mongodb_schema=data.get('mongodb_schema', {}),
                    code_transformations=data.get('code_transformations', []),
                    migration_steps=data.get('migration_steps', []),
                    mongodb_concepts=data.get('mongodb_concepts', []),
                    raw_response=response
                )
            else:
                # If JSON extraction fails, try to parse the response in a more flexible way
                return self._flexible_parse(response)
        except Exception as e:
            print(f"Error processing LLM response: {e}")
            # Return a basic structure with the raw response for manual inspection
            return LLMResponse(
                mongodb_schema={},
                code_transformations=[],
                migration_steps=[],
                mongodb_concepts=[],
                raw_response=response
            )

    def _flexible_parse(self, response: str) -> LLMResponse:
        """
        Attempt to parse the response in a more flexible way if JSON parsing fails.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured LLM response
        """
        # Initialize empty structures
        mongodb_schema = {}
        code_transformations = []
        migration_steps = []
        mongodb_concepts = []
        
        # Look for section headers
        sections = {
            "mongodb_schema": [],
            "code_transformations": [],
            "migration_steps": [],
            "mongodb_concepts": []
        }
        
        current_section = None
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            lower_line = line.lower()
            if "mongodb schema" in lower_line or "schema design" in lower_line:
                current_section = "mongodb_schema"
            elif "code transformation" in lower_line or "code change" in lower_line:
                current_section = "code_transformations"
            elif "migration step" in lower_line or "migration process" in lower_line:
                current_section = "migration_steps"
            elif "mongodb concept" in lower_line or "best practice" in lower_line:
                current_section = "mongodb_concepts"
            elif line and current_section:
                sections[current_section].append(line)
        
        # Process each section
        if sections["mongodb_schema"]:
            mongodb_schema = {"description": "\n".join(sections["mongodb_schema"])}
        
        for i, line in enumerate(sections["code_transformations"]):
            if line.startswith('-') or line.startswith('*') or (i > 0 and sections["code_transformations"][i-1].endswith(':')):
                code_transformations.append({"description": line})
        
        for i, line in enumerate(sections["migration_steps"]):
            if line.startswith('-') or line.startswith('*') or line[0].isdigit() or (i > 0 and sections["migration_steps"][i-1].endswith(':')):
                migration_steps.append({"description": line})
        
        for i, line in enumerate(sections["mongodb_concepts"]):
            if line.startswith('-') or line.startswith('*') or (i > 0 and sections["mongodb_concepts"][i-1].endswith(':')):
                mongodb_concepts.append({"description": line})
        
        return LLMResponse(
            mongodb_schema=mongodb_schema,
            code_transformations=code_transformations,
            migration_steps=migration_steps,
            mongodb_concepts=mongodb_concepts,
            raw_response=response
        )

    def _generate_mock_response(self) -> str:
        """
        Generate a mock response for testing without API access.
        
        Returns:
            Mock LLM response
        """
        return """
{
  "mongodb_schema": {
    "collections": [
      {
        "name": "owners",
        "fields": [
          {"name": "id", "type": "ObjectId", "description": "Primary key"},
          {"name": "firstName", "type": "String"},
          {"name": "lastName", "type": "String"},
          {"name": "address", "type": "String"},
          {"name": "city", "type": "String"},
          {"name": "telephone", "type": "String"},
          {"name": "pets", "type": "Array", "description": "Embedded pet documents"}
        ],
        "indexes": [
          {"fields": ["lastName"], "type": "text"},
          {"fields": ["telephone"], "type": "unique"}
        ]
      },
      {
        "name": "vets",
        "fields": [
          {"name": "id", "type": "ObjectId", "description": "Primary key"},
          {"name": "firstName", "type": "String"},
          {"name": "lastName", "type": "String"},
          {"name": "specialties", "type": "Array", "description": "Array of specialty references"}
        ],
        "indexes": [
          {"fields": ["lastName"], "type": "text"}
        ]
      }
    ],
    "embedding_strategy": "Embed pets within owners for better read performance and to represent the strong parent-child relationship."
  },
  "code_transformations": [
    {
      "file": "Entity.java",
      "changes": [
        {"from": "@Entity", "to": "@Document(collection = \"collectionName\")"},
        {"from": "@Table(name = \"table_name\")", "to": "Remove this annotation"},
        {"from": "@Id\\n@GeneratedValue", "to": "@Id private String id;"},
        {"from": "@Column(name = \"column_name\")", "to": "@Field(\"field_name\")"},
        {"from": "@OneToMany", "to": "Embed as List or use @DBRef"}
      ]
    },
    {
      "file": "Repository.java",
      "changes": [
        {"from": "extends JpaRepository<Entity, Long>", "to": "extends MongoRepository<Entity, String>"},
        {"from": "@Query(\"SELECT e FROM Entity e WHERE...\")", "to": "@Query(\"{field: ?0}\")"}
      ]
    },
    {
      "file": "application.properties",
      "changes": [
        {"from": "spring.datasource.url=jdbc:mysql://...", "to": "spring.data.mongodb.uri=mongodb://..."},
        {"from": "spring.jpa.hibernate.ddl-auto=update", "to": "Remove this property"}
      ]
    }
  ],
  "migration_steps": [
    {
      "step": 1,
      "title": "Set up MongoDB environment",
      "description": "Install MongoDB and create the necessary databases and users."
    },
    {
      "step": 2,
      "title": "Update dependencies",
      "description": "Replace JPA dependencies with Spring Data MongoDB in pom.xml or build.gradle."
    },
    {
      "step": 3,
      "title": "Transform entity classes",
      "description": "Convert JPA annotations to MongoDB annotations."
    },
    {
      "step": 4,
      "title": "Update repository interfaces",
      "description": "Change from JPA repositories to MongoDB repositories."
    },
    {
      "step": 5,
      "title": "Update configuration",
      "description": "Replace database configuration properties."
    },
    {
      "step": 6,
      "title": "Migrate data",
      "description": "Write a script to migrate data from the relational database to MongoDB."
    },
    {
      "step": 7,
      "title": "Test the application",
      "description": "Verify that all functionality works with MongoDB."
    }
  ],
  "mongodb_concepts": [
    {
      "concept": "Document Model",
      "description": "MongoDB stores data in flexible, JSON-like documents, allowing for nested data and arrays."
    },
    {
      "concept": "Embedding vs. Referencing",
      "description": "Embedding documents is preferred for one-to-many relationships with strong ownership, while referencing is better for many-to-many relationships."
    },
    {
      "concept": "Indexing",
      "description": "Create indexes on frequently queried fields to improve performance."
    },
    {
      "concept": "Aggregation Pipeline",
      "description": "Use MongoDB's aggregation framework for complex queries instead of JPA's JPQL."
    }
  ]
}
"""


def generate_migration_recommendations(analysis: RepositoryAnalysis) -> LLMResponse:
    """
    Generate migration recommendations using GPT-4.
    
    Args:
        analysis: Repository analysis results
        
    Returns:
        Structured LLM response with migration recommendations
    """
    llm = LLMIntegration()
    return llm.generate_migration_recommendations(analysis)
