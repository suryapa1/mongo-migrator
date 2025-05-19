"""
Repository Analysis Module for Java to MongoDB Migration Tool

This module scans Java repositories to identify database-related files,
extract entity models, repositories, and database configurations.
"""

import os
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Set


@dataclass
class Field:
    """Represents a field in an entity class."""
    name: str
    type: str
    annotations: List[str]
    is_id: bool = False
    is_relationship: bool = False
    relationship_type: Optional[str] = None  # OneToMany, ManyToOne, etc.
    target_entity: Optional[str] = None


@dataclass
class Entity:
    """Represents a JPA entity."""
    name: str
    file_path: str
    fields: List[Field]
    annotations: List[str]
    table_name: Optional[str] = None


@dataclass
class Method:
    """Represents a method in a repository."""
    name: str
    return_type: str
    parameters: List[Dict[str, str]]
    query: Optional[str] = None


@dataclass
class Repository:
    """Represents a repository interface or class."""
    name: str
    file_path: str
    entity_name: str
    methods: List[Method]
    extends: List[str]  # e.g., JpaRepository, CrudRepository


@dataclass
class Configuration:
    """Represents a database configuration file."""
    file_path: str
    file_type: str  # xml, properties, java
    content: str


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    source_entity: str
    target_entity: str
    relationship_type: str  # OneToMany, ManyToOne, etc.
    source_field: str
    target_field: Optional[str] = None


@dataclass
class RepositoryAnalysis:
    """Contains the results of repository analysis."""
    entities: List[Entity]
    repositories: List[Repository]
    configurations: List[Configuration]
    relationships: List[Relationship]


class JavaRepositoryAnalyzer:
    """Analyzes Java repositories to identify database-related components."""

    def __init__(self, repo_path: str):
        """
        Initialize the analyzer with the repository path.
        
        Args:
            repo_path: Path to the local repository
        """
        self.repo_path = repo_path
        self.entities = []
        self.repositories = []
        self.configurations = []
        self.relationships = []
        self.entity_names = set()

    def analyze(self) -> RepositoryAnalysis:
        """
        Analyze the repository to identify database-related components.
        
        Returns:
            RepositoryAnalysis object containing entities, repositories, and configurations
        """
        self._find_files()
        self._extract_relationships()
        return RepositoryAnalysis(
            entities=self.entities,
            repositories=self.repositories,
            configurations=self.configurations,
            relationships=self.relationships
        )

    def _find_files(self):
        """Find and categorize files in the repository."""
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip non-relevant files
                if not self._is_relevant_file(file_path):
                    continue
                
                if file.endswith('.java'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if it's an entity
                    if self._is_entity(content):
                        entity = self._parse_entity(content, file_path)
                        self.entities.append(entity)
                        self.entity_names.add(entity.name)
                    
                    # Check if it's a repository
                    elif self._is_repository(content):
                        repository = self._parse_repository(content, file_path)
                        self.repositories.append(repository)
                
                # Check for configuration files
                elif file.endswith(('.xml', '.properties', '.yml', '.yaml')):
                    if self._is_db_config(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        file_type = file.split('.')[-1]
                        self.configurations.append(Configuration(
                            file_path=file_path,
                            file_type=file_type,
                            content=content
                        ))

    def _is_relevant_file(self, file_path: str) -> bool:
        """
        Check if a file is relevant for analysis.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is relevant, False otherwise
        """
        # Skip build directories, test files, etc.
        excluded_dirs = ['target', 'build', 'node_modules', '.git']
        for excluded_dir in excluded_dirs:
            if f'/{excluded_dir}/' in file_path:
                return False
        
        # Only include certain file types
        return file_path.endswith(('.java', '.xml', '.properties', '.yml', '.yaml'))

    def _is_entity(self, content: str) -> bool:
        """
        Check if a Java file contains a JPA entity.
        
        Args:
            content: File content
            
        Returns:
            True if the file contains an entity, False otherwise
        """
        # Look for @Entity annotation
        return bool(re.search(r'@Entity|@Table|@Document', content))

    def _parse_entity(self, content: str, file_path: str) -> Entity:
        """
        Parse a Java file to extract entity information.
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            Entity object
        """
        # Extract class name
        class_match = re.search(r'class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else os.path.basename(file_path).replace('.java', '')
        
        # Extract annotations
        annotations = re.findall(r'@(\w+)(?:\(.*?\))?', content)
        
        # Extract table name if present
        table_match = re.search(r'@Table\s*\(\s*name\s*=\s*["\']([^"\']+)["\']', content)
        table_name = table_match.group(1) if table_match else None
        
        # Extract fields
        fields = []
        field_pattern = r'(?:@(\w+)(?:\(.*?\))?[\s\n]*)*(?:private|protected|public)\s+(\w+(?:<.*?>)?)\s+(\w+)\s*;'
        field_matches = re.finditer(field_pattern, content)
        
        for field_match in field_matches:
            field_annotations_str = content[field_match.start():field_match.end()]
            field_annotations = re.findall(r'@(\w+)(?:\(.*?\))?', field_annotations_str)
            field_type = field_match.group(2)
            field_name = field_match.group(3)
            
            is_id = 'Id' in field_annotations
            is_relationship = any(rel in field_annotations for rel in 
                                ['OneToMany', 'ManyToOne', 'OneToOne', 'ManyToMany'])
            
            relationship_type = None
            target_entity = None
            
            if is_relationship:
                for rel in ['OneToMany', 'ManyToOne', 'OneToOne', 'ManyToMany']:
                    if rel in field_annotations:
                        relationship_type = rel
                        # Try to extract target entity
                        target_match = re.search(
                            rf'@{rel}\s*\(.*?targetEntity\s*=\s*(\w+)\.class', 
                            field_annotations_str
                        )
                        if target_match:
                            target_entity = target_match.group(1)
                        break
            
            fields.append(Field(
                name=field_name,
                type=field_type,
                annotations=field_annotations,
                is_id=is_id,
                is_relationship=is_relationship,
                relationship_type=relationship_type,
                target_entity=target_entity
            ))
        
        return Entity(
            name=class_name,
            file_path=file_path,
            fields=fields,
            annotations=annotations,
            table_name=table_name
        )

    def _is_repository(self, content: str) -> bool:
        """
        Check if a Java file contains a repository.
        
        Args:
            content: File content
            
        Returns:
            True if the file contains a repository, False otherwise
        """
        # Look for repository patterns
        repository_patterns = [
            r'interface\s+\w+Repository',
            r'class\s+\w+Repository',
            r'extends\s+\w*Repository',
            r'extends\s+JpaRepository',
            r'extends\s+CrudRepository'
        ]
        
        return any(re.search(pattern, content) for pattern in repository_patterns)

    def _parse_repository(self, content: str, file_path: str) -> Repository:
        """
        Parse a Java file to extract repository information.
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            Repository object
        """
        # Extract class/interface name
        class_match = re.search(r'(?:interface|class)\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else os.path.basename(file_path).replace('.java', '')
        
        # Extract what it extends
        extends_match = re.search(r'extends\s+([\w\s,<>]+)', content)
        extends = []
        if extends_match:
            extends_str = extends_match.group(1)
            extends = re.findall(r'\w+', extends_str)
        
        # Try to determine the entity name
        entity_name = None
        
        # Check if it's in the extends clause with generics
        generic_match = re.search(r'extends\s+\w+<(\w+)', content)
        if generic_match:
            entity_name = generic_match.group(1)
        
        # If not found, try to infer from the repository name
        if not entity_name and class_name.endswith('Repository'):
            entity_name = class_name[:-10]  # Remove 'Repository' suffix
        
        # Extract methods
        methods = []
        method_pattern = r'(?:@(\w+)(?:\(.*?\))?[\s\n]*)*(?:public|protected|private)?\s+(\w+(?:<.*?>)?)\s+(\w+)\s*\((.*?)\)\s*;'
        method_matches = re.finditer(method_pattern, content)
        
        for method_match in method_matches:
            method_annotations_str = content[method_match.start():method_match.end()]
            method_annotations = re.findall(r'@(\w+)(?:\(.*?\))?', method_annotations_str)
            return_type = method_match.group(2)
            method_name = method_match.group(3)
            params_str = method_match.group(4)
            
            # Parse parameters
            parameters = []
            if params_str.strip():
                param_parts = params_str.split(',')
                for part in param_parts:
                    part = part.strip()
                    if part:
                        param_match = re.match(r'(\w+(?:<.*?>)?)\s+(\w+)', part)
                        if param_match:
                            param_type = param_match.group(1)
                            param_name = param_match.group(2)
                            parameters.append({'type': param_type, 'name': param_name})
            
            # Extract query if present
            query = None
            query_match = re.search(r'@Query\s*\(\s*["\']([^"\']+)["\']', method_annotations_str)
            if query_match:
                query = query_match.group(1)
            
            methods.append(Method(
                name=method_name,
                return_type=return_type,
                parameters=parameters,
                query=query
            ))
        
        return Repository(
            name=class_name,
            file_path=file_path,
            entity_name=entity_name,
            methods=methods,
            extends=extends
        )

    def _is_db_config(self, file_path: str) -> bool:
        """
        Check if a file contains database configuration.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file contains database configuration, False otherwise
        """
        # Common database configuration file names
        db_config_patterns = [
            'persistence.xml',
            'application.properties',
            'application.yml',
            'hibernate.cfg.xml',
            'database',
            'datasource'
        ]
        
        file_name = os.path.basename(file_path).lower()
        
        # Check if the file name matches any pattern
        if any(pattern in file_name for pattern in db_config_patterns):
            return True
        
        # For other files, check content
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
                db_content_patterns = [
                    'jdbc', 'datasource', 'database', 'hibernate', 'jpa',
                    'spring.datasource', 'persistence-unit'
                ]
                return any(pattern in content.lower() for pattern in db_content_patterns)
            except UnicodeDecodeError:
                # Not a text file
                return False

    def _extract_relationships(self):
        """Extract relationships between entities."""
        for entity in self.entities:
            for field in entity.fields:
                if field.is_relationship and field.target_entity:
                    self.relationships.append(Relationship(
                        source_entity=entity.name,
                        target_entity=field.target_entity,
                        relationship_type=field.relationship_type,
                        source_field=field.name
                    ))


def analyze_repository(repo_path: str) -> RepositoryAnalysis:
    """
    Analyze a Java repository to identify database-related components.
    
    Args:
        repo_path: Path to the local repository
        
    Returns:
        RepositoryAnalysis object containing entities, repositories, and configurations
    """
    analyzer = JavaRepositoryAnalyzer(repo_path)
    return analyzer.analyze()
