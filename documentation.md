# Java to MongoDB Migration Tool - Documentation

## Overview

The Java to MongoDB Migration Tool is a Python-based utility designed to analyze Java applications that use relational databases and create comprehensive migration plans for transitioning to MongoDB. The tool leverages GPT-4 for intelligent code analysis and provides detailed guidance on schema design, code transformations, and migration steps.

## Features

- **Repository Analysis**: Scans Java repositories to identify database-related components
- **LLM-Powered Migration Planning**: Uses GPT-4 to generate intelligent migration recommendations
- **File Impact Analysis**: Identifies files requiring changes and estimates effort
- **MongoDB Connection Validation**: Tests MongoDB connections and basic operations
- **Streamlit UI**: User-friendly interface for repository input and results visualization

## Installation

### Prerequisites

- Python 3.8+
- Java repository to analyze
- MongoDB (for connection testing)
- OpenAI API key (for GPT-4 access)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/java-to-mongodb-migration-tool.git
cd java-to-mongodb-migration-tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key"
```

## Usage

### Starting the Tool

Run the Streamlit application:
```bash
streamlit run src/ui/app.py
```

### Using the Tool

1. Enter the path to your local Java repository
2. Configure migration options (if needed)
3. Click "Analyze Repository" to start the analysis
4. Review the generated migration plan
5. Test MongoDB connection (optional)
6. Export the migration plan as needed

## Architecture

The tool follows a modular architecture with the following components:

### Repository Analysis Module

Located in `src/repository_analysis/analyzer.py`, this module:
- Scans Java repositories to identify database-related files
- Extracts entity models, repositories, and database configurations
- Identifies JPA/Hibernate annotations and patterns
- Detects relationships between entities

### LLM Integration Module

Located in `src/llm_integration/llm_service.py`, this module:
- Connects to GPT-4 API
- Prepares prompts based on repository analysis
- Processes LLM responses
- Extracts structured migration plans from responses

### Migration Plan Generator

Located in `src/migration_plan/plan_generator.py`, this module:
- Generates MongoDB schema designs
- Creates code transformation suggestions
- Provides step-by-step migration instructions
- Explains MongoDB concepts relevant to the migration

### File Impact Analyzer

Located in `src/file_impact/impact_analyzer.py`, this module:
- Identifies files requiring changes
- Estimates the scope of changes needed
- Categorizes changes by type (entity, repository, configuration)
- Generates detailed reports on impacted components

### MongoDB Connection Validator

Located in `src/mongodb_validator/validator.py`, this module:
- Validates MongoDB connection strings
- Tests basic MongoDB operations
- Verifies schema compatibility
- Provides feedback on connection issues

### Streamlit UI

Located in `src/ui/app.py`, this module:
- Provides user interface for repository input
- Displays analysis results and migration plans
- Offers MongoDB connection testing
- Allows exporting of migration plans

## Data Flow

1. User inputs repository path via Streamlit UI
2. Repository Analysis Module scans the codebase
3. Analysis results are passed to the LLM Integration Module
4. LLM generates migration recommendations
5. Migration Plan Generator creates structured migration plan
6. File Impact Analyzer identifies affected files
7. Results are displayed to the user via Streamlit UI
8. Optional: MongoDB Connection Validator tests the connection

## Example Migration Plan

A typical migration plan includes:

1. **MongoDB Schema Design**:
   - Document structure for each entity
   - Embedding vs. referencing decisions
   - Indexing recommendations

2. **Code Transformations**:
   - Changes needed for entity classes (JPA to MongoDB annotations)
   - Repository interface modifications
   - Configuration changes

3. **Step-by-Step Migration Process**:
   - Data migration approach
   - Code refactoring sequence
   - Testing strategy

4. **MongoDB Concepts**:
   - Explanations of relevant MongoDB concepts
   - Best practices for the migration

## Common Migration Patterns

### Entity Transformations

JPA entities are transformed to MongoDB documents:

```java
// JPA Entity
@Entity
@Table(name = "owners")
public class Owner {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;
    
    @Column(name = "first_name")
    private String firstName;
    
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "owner")
    private Set<Pet> pets;
}

// MongoDB Document
@Document(collection = "owners")
public class Owner {
    @Id
    private String id;
    
    @Field("first_name")
    private String firstName;
    
    private List<Pet> pets;  // Embedded documents
}
```

### Repository Transformations

JPA repositories are transformed to MongoDB repositories:

```java
// JPA Repository
public interface OwnerRepository extends JpaRepository<Owner, Long> {
    @Query("SELECT o FROM Owner o WHERE o.lastName LIKE %?1%")
    Collection<Owner> findByLastName(String lastName);
}

// MongoDB Repository
public interface OwnerRepository extends MongoRepository<Owner, String> {
    @Query("{ 'lastName': { $regex: ?0, $options: 'i' } }")
    Collection<Owner> findByLastName(String lastName);
}
```

### Configuration Transformations

Database configuration is updated for MongoDB:

```properties
# JPA Configuration
spring.datasource.url=jdbc:mysql://localhost:3306/petclinic
spring.datasource.username=petclinic
spring.datasource.password=petclinic
spring.jpa.hibernate.ddl-auto=update

# MongoDB Configuration
spring.data.mongodb.uri=mongodb://localhost:27017/petclinic
```

## Best Practices

1. **Document Design**:
   - Embed related entities when they are always accessed together
   - Use references for many-to-many relationships
   - Consider read/write patterns when deciding between embedding and referencing

2. **Indexing**:
   - Create indexes on frequently queried fields
   - Use compound indexes for multi-field queries
   - Consider text indexes for full-text search

3. **Migration Process**:
   - Update dependencies first
   - Transform entity classes
   - Update repository interfaces
   - Migrate data
   - Test thoroughly

## Troubleshooting

### Common Issues

1. **Connection Problems**:
   - Verify MongoDB is running
   - Check connection string format
   - Ensure network connectivity

2. **Analysis Errors**:
   - Ensure Java repository is accessible
   - Check for non-standard code patterns
   - Verify file permissions

3. **LLM Integration Issues**:
   - Verify OpenAI API key is set
   - Check for rate limiting
   - Ensure internet connectivity


## Acknowledgments

- Spring PetClinic for providing a reference application
- JBoss KitchenSink for providing another reference application
- OpenAI for GPT-4 API access