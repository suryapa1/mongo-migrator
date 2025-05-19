"""
Streamlit UI for Java to MongoDB Migration Tool

This module provides a user-friendly interface for repository input,
displays analysis results and migration plans, and offers MongoDB connection testing.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import os
import streamlit as st
import json
from pathlib import Path

# Import modules
from repository_analysis.analyzer import analyze_repository
from llm_integration.llm_service import generate_migration_recommendations
from migration_plan.plan_generator import create_migration_plan
from file_impact.impact_analyzer import identify_impacted_files
from mongodb_validator.validator import validate_mongodb_connection, test_mongodb_operations


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Java to MongoDB Migration Tool",
        page_icon="🔄",
        layout="wide"
    )
    
    st.title("Java to MongoDB Migration Tool")
    st.write("""
    This tool analyzes Java applications using relational databases and creates 
    comprehensive migration plans for transitioning to MongoDB.
    """)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Repository path input
        repo_path = st.text_input(
            "Repository Path",
            placeholder="/path/to/java/repository",
            help="Enter the absolute path to your local Java repository"
        )
        
        # OpenAI API key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="APIKEY",
            help="Enter your OpenAI API key for GPT-4 access"
        )
        
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        
        # MongoDB connection string
        mongodb_uri = st.text_input(
            "MongoDB Connection String",
            placeholder="mongodb://localhost:27017",
            help="Enter your MongoDB connection string for testing"
        )
        
        # Analysis options
        st.subheader("Analysis Options")
        
        analyze_entities = st.checkbox("Analyze Entities", value=True)
        analyze_repositories = st.checkbox("Analyze Repositories", value=True)
        analyze_configs = st.checkbox("Analyze Configurations", value=True)
        
        # Start analysis button
        analyze_button = st.button("Analyze Repository", type="primary")
    
    # Main content area
    if not repo_path:
        st.info("Please enter a repository path to begin analysis.")
        
        # Example repositories
        st.header("Example Repositories")
        st.write("""
        You can use these example repositories for testing:
        
        1. **Spring PetClinic**: A sample Spring Boot application with JPA
           - GitHub: https://github.com/spring-projects/spring-petclinic
        
        2. **JBoss KitchenSink**: A JBoss EAP quickstart with JPA
           - GitHub: https://github.com/jboss-developer/jboss-eap-quickstarts/tree/8.0.x/kitchensink
        """)
        
        # Migration patterns
        st.header("Common Migration Patterns")
        st.write("""
        When migrating from a relational database to MongoDB, these patterns are commonly applied:
        
        1. **Entity to Document**: JPA entities become MongoDB documents
        2. **Embedding vs. Referencing**: Decide on document structure based on relationships
        3. **Repository Conversion**: JPA repositories become MongoDB repositories
        4. **Query Transformation**: JPQL queries become MongoDB queries
        """)
        
        return
    
    # Check if repository path exists
    if not os.path.exists(repo_path):
        st.error(f"Repository path does not exist: {repo_path}")
        return
    
    # Run analysis when button is clicked
    if analyze_button:
        with st.spinner("Analyzing repository..."):
            try:
                # Step 1: Repository Analysis
                st.subheader("Repository Analysis")
                analysis_result = analyze_repository(repo_path)
                
                # Display analysis results
                st.write(f"Found {len(analysis_result.entities)} entities, {len(analysis_result.repositories)} repositories, and {len(analysis_result.configurations)} configuration files.")
                
                # Entities
                if analyze_entities and analysis_result.entities:
                    with st.expander("Entities", expanded=True):
                        for entity in analysis_result.entities:
                            st.write(f"**{entity.name}**")
                            st.write(f"File: `{entity.file_path}`")
                            st.write(f"Annotations: {', '.join(entity.annotations)}")
                            st.write(f"Fields: {len(entity.fields)}")
                            
                            # Display fields in a table
                            field_data = []
                            for field in entity.fields:
                                field_data.append({
                                    "Name": field.name,
                                    "Type": field.type,
                                    "Annotations": ", ".join(field.annotations),
                                    "Is ID": "✓" if field.is_id else "",
                                    "Relationship": field.relationship_type if field.is_relationship else ""
                                })
                            
                            if field_data:
                                st.table(field_data)
                            
                            st.markdown("---")
                
                # Repositories
                if analyze_repositories and analysis_result.repositories:
                    with st.expander("Repositories", expanded=True):
                        for repo in analysis_result.repositories:
                            st.write(f"**{repo.name}**")
                            st.write(f"File: `{repo.file_path}`")
                            st.write(f"Entity: {repo.entity_name}")
                            st.write(f"Extends: {', '.join(repo.extends)}")
                            st.write(f"Methods: {len(repo.methods)}")
                            
                            # Display methods in a table
                            method_data = []
                            for method in repo.methods:
                                method_data.append({
                                    "Name": method.name,
                                    "Return Type": method.return_type,
                                    "Parameters": len(method.parameters),
                                    "Has Query": "✓" if method.query else ""
                                })
                            
                            if method_data:
                                st.table(method_data)
                            
                            st.markdown("---")
                
                # Configurations
                if analyze_configs and analysis_result.configurations:
                    with st.expander("Configurations", expanded=True):
                        for config in analysis_result.configurations:
                            st.write(f"**{os.path.basename(config.file_path)}**")
                            st.write(f"File: `{config.file_path}`")
                            st.write(f"Type: {config.file_type}")
                            show = st.checkbox(f"Show content of {os.path.basename(config.file_path)}", key=config.file_path)
                            if show:
                                st.code(config.content)
                            
                            st.markdown("---")
                
                # Step 2: Generate Migration Recommendations
                st.subheader("Migration Recommendations")
                
                with st.spinner("Generating migration recommendations with GPT-4..."):
                    llm_response = generate_migration_recommendations(analysis_result)
                
                # Step 3: Create Migration Plan
                with st.spinner("Creating migration plan..."):
                    migration_plan = create_migration_plan(llm_response, analysis_result)
                
                # Display migration plan
                st.write("### Migration Plan Summary")
                st.write(migration_plan.summary)
                
                # MongoDB Schema
                with st.expander("MongoDB Schema Design", expanded=True):
                    st.write(f"**Embedding Strategy**: {migration_plan.mongodb_schema.embedding_strategy}")
                    
                    if migration_plan.mongodb_schema.indexing_strategy:
                        st.write(f"**Indexing Strategy**: {migration_plan.mongodb_schema.indexing_strategy}")
                    
                    st.write("**Collections**:")
                    for collection in migration_plan.mongodb_schema.collections:
                        st.write(f"- **{collection['name']}**")
                        
                        # Display fields in a table
                        if 'fields' in collection:
                            field_data = []
                            for field in collection['fields']:
                                field_data.append({
                                    "Name": field.get('name', ''),
                                    "Type": field.get('type', ''),
                                    "Description": field.get('description', '')
                                })
                            
                            if field_data:
                                st.table(field_data)
                
                # Code Transformations
                with st.expander("Code Transformations", expanded=True):
                    for i, transformation in enumerate(migration_plan.code_transformations):
                        st.write(f"**Transformation {i+1}**: {transformation.file_type}")
                        st.write(f"**Explanation**: {transformation.explanation}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Original Code**:")
                            st.code(transformation.original_code)
                        
                        with col2:
                            st.write("**Transformed Code**:")
                            st.code(transformation.transformed_code)
                        
                        st.markdown("---")
                
                # Migration Steps
                with st.expander("Migration Steps", expanded=True):
                    for step in migration_plan.migration_steps:
                        st.write(f"**Step {step.step_number}**: {step.title}")
                        st.write(step.description)
                        
                        if step.code_example:
                            st.code(step.code_example)
                        
                        st.markdown("---")
                
                # MongoDB Concepts
                with st.expander("MongoDB Concepts", expanded=True):
                    for concept in migration_plan.mongodb_concepts:
                        st.write(f"**{concept.name}**")
                        st.write(concept.description)
                        st.write(f"**Relevance**: {concept.relevance}")
                        st.markdown("---")
                
                # Step 4: File Impact Analysis
                st.subheader("File Impact Analysis")
                
                with st.spinner("Analyzing file impact..."):
                    impact_analysis = identify_impacted_files(analysis_result, migration_plan, repo_path)
                
                # Display impact summary
                summary = impact_analysis.summary
                st.write(f"**Total Files Impacted**: {summary.total_files}")
                st.write(f"**Entity Files**: {summary.entity_files}")
                st.write(f"**Repository Files**: {summary.repository_files}")
                st.write(f"**Configuration Files**: {summary.configuration_files}")
                
                # Display complexity breakdown
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("High Complexity", summary.high_complexity_changes)
                with col2:
                    st.metric("Medium Complexity", summary.medium_complexity_changes)
                with col3:
                    st.metric("Low Complexity", summary.low_complexity_changes)
                
                st.metric("Estimated Effort (hours)", summary.estimated_effort_hours)
                
                # Display impacted files
                with st.expander("Impacted Files", expanded=True):
                    for file_change in impact_analysis.impacted_files:
                        st.write(f"**{os.path.basename(file_change.file_path)}**")
                        st.write(f"File: `{file_change.file_path}`")
                        st.write(f"Change Type: {file_change.change_type}")
                        st.write(f"Complexity: {file_change.complexity}")
                        st.write(f"Description: {file_change.description}")
                        st.markdown("---")
                
                # Step 5: MongoDB Connection Testing (if connection string provided)
                if mongodb_uri:
                    st.subheader("MongoDB Connection Testing")
                    
                    test_connection = st.button("Test MongoDB Connection")
                    
                    if test_connection:
                        with st.spinner("Testing MongoDB connection..."):
                            connection_result = validate_mongodb_connection(mongodb_uri)
                        
                        if connection_result.success:
                            st.success(connection_result.message)
                            
                            if connection_result.details:
                                st.json(connection_result.details)
                            
                            # Test basic operations
                            test_operations = st.button("Test Basic MongoDB Operations")
                            
                            if test_operations:
                                with st.spinner("Testing basic MongoDB operations..."):
                                    operations_result = test_mongodb_operations(mongodb_uri)
                                
                                if operations_result.success:
                                    st.success(operations_result.message)
                                    
                                    if operations_result.details:
                                        st.json(operations_result.details)
                                else:
                                    st.error(operations_result.message)
                                    
                                    if operations_result.details:
                                        st.json(operations_result.details)
                        else:
                            st.error(connection_result.message)
                            
                            if connection_result.details:
                                st.json(connection_result.details)
                
                # Export options
                st.subheader("Export Options")
                
                export_dir = st.text_input(
                    "Export Directory",
                    value=os.path.join(os.path.dirname(repo_path), "migration_plan"),
                    help="Directory where migration plan files will be saved"
                )
                
                export_button = st.button("Export Migration Plan")
                
                if export_button:
                    try:
                        # Create export directory if it doesn't exist
                        os.makedirs(export_dir, exist_ok=True)
                        
                        # Export migration plan summary
                        with open(os.path.join(export_dir, "migration_plan_summary.md"), "w") as f:
                            f.write(migration_plan.summary)
                        
                        # Export MongoDB schema
                        with open(os.path.join(export_dir, "mongodb_schema.json"), "w") as f:
                            schema_dict = {
                                "collections": migration_plan.mongodb_schema.collections,
                                "embedding_strategy": migration_plan.mongodb_schema.embedding_strategy
                            }
                            if migration_plan.mongodb_schema.indexing_strategy:
                                schema_dict["indexing_strategy"] = migration_plan.mongodb_schema.indexing_strategy
                            
                            json.dump(schema_dict, f, indent=2)
                        
                        # Export code transformations
                        with open(os.path.join(export_dir, "code_transformations.md"), "w") as f:
                            f.write("# Code Transformations\n\n")
                            
                            for i, transformation in enumerate(migration_plan.code_transformations):
                                f.write(f"## Transformation {i+1}: {transformation.file_type}\n\n")
                                f.write(f"**Explanation**: {transformation.explanation}\n\n")
                                f.write("**Original Code**:\n```java\n")
                                f.write(transformation.original_code)
                                f.write("\n```\n\n")
                                f.write("**Transformed Code**:\n```java\n")
                                f.write(transformation.transformed_code)
                                f.write("\n```\n\n")
                                f.write("---\n\n")
                        
                        # Export migration steps
                        with open(os.path.join(export_dir, "migration_steps.md"), "w") as f:
                            f.write("# Migration Steps\n\n")
                            
                            for step in migration_plan.migration_steps:
                                f.write(f"## Step {step.step_number}: {step.title}\n\n")
                                f.write(f"{step.description}\n\n")
                                
                                if step.code_example:
                                    f.write("```java\n")
                                    f.write(step.code_example)
                                    f.write("\n```\n\n")
                                
                                f.write("---\n\n")
                        
                        # Export file impact analysis
                        with open(os.path.join(export_dir, "file_impact_analysis.md"), "w") as f:
                            f.write("# File Impact Analysis\n\n")
                            
                            summary = impact_analysis.summary
                            f.write(f"**Total Files Impacted**: {summary.total_files}\n")
                            f.write(f"**Entity Files**: {summary.entity_files}\n")
                            f.write(f"**Repository Files**: {summary.repository_files}\n")
                            f.write(f"**Configuration Files**: {summary.configuration_files}\n\n")
                            
                            f.write("## Complexity Breakdown\n\n")
                            f.write(f"- **High Complexity**: {summary.high_complexity_changes}\n")
                            f.write(f"- **Medium Complexity**: {summary.medium_complexity_changes}\n")
                            f.write(f"- **Low Complexity**: {summary.low_complexity_changes}\n\n")
                            
                            f.write(f"**Estimated Effort (hours)**: {summary.estimated_effort_hours}\n\n")
                            
                            f.write("## Impacted Files\n\n")
                            
                            for file_change in impact_analysis.impacted_files:
                                f.write(f"### {os.path.basename(file_change.file_path)}\n\n")
                                f.write(f"- **File**: `{file_change.file_path}`\n")
                                f.write(f"- **Change Type**: {file_change.change_type}\n")
                                f.write(f"- **Complexity**: {file_change.complexity}\n")
                                f.write(f"- **Description**: {file_change.description}\n\n")
                                f.write("---\n\n")
                        
                        st.success(f"Migration plan exported to {export_dir}")
                        
                        # Provide download links
                        st.write("### Download Files")
                        
                        for filename in os.listdir(export_dir):
                            file_path = os.path.join(export_dir, filename)
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label=f"Download {filename}",
                                    data=f,
                                    file_name=filename,
                                    mime="application/octet-stream"
                                )
                    
                    except Exception as e:
                        st.error(f"Error exporting migration plan: {str(e)}")
            
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")


if __name__ == "__main__":
    main()
