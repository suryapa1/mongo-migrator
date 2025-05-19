"""
MongoDB Connection Validator Module for Java to MongoDB Migration Tool

This module validates MongoDB connection strings, tests basic MongoDB operations,
and verifies schema compatibility.
"""

import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class ConnectionValidationResult:
    """Contains the results of MongoDB connection validation."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class MongoDBValidator:
    """Validates MongoDB connections and operations."""

    def __init__(self, connection_string: str):
        """
        Initialize the MongoDB validator.
        
        Args:
            connection_string: MongoDB connection string
        """
        self.connection_string = connection_string
        self.client = None

    def validate_connection(self) -> ConnectionValidationResult:
        """
        Validate the MongoDB connection.
        
        Returns:
            Connection validation result
        """
        try:
            # Attempt to connect with a short timeout
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            
            # Force a connection to verify it works
            self.client.admin.command('ping')
            
            # Get server info for details
            server_info = self.client.server_info()
            
            return ConnectionValidationResult(
                success=True,
                message="Successfully connected to MongoDB server",
                details={
                    "version": server_info.get("version", "Unknown"),
                    "connection": self.connection_string.split("@")[-1] if "@" in self.connection_string else self.connection_string
                }
            )
        
        except ServerSelectionTimeoutError:
            return ConnectionValidationResult(
                success=False,
                message="Failed to connect to MongoDB server: Connection timed out",
                details={"error_type": "timeout"}
            )
        
        except ConnectionFailure:
            return ConnectionValidationResult(
                success=False,
                message="Failed to connect to MongoDB server: Connection refused",
                details={"error_type": "connection_refused"}
            )
        
        except OperationFailure as e:
            return ConnectionValidationResult(
                success=False,
                message=f"Failed to authenticate with MongoDB server: {str(e)}",
                details={"error_type": "authentication", "error_message": str(e)}
            )
        
        except Exception as e:
            return ConnectionValidationResult(
                success=False,
                message=f"An unexpected error occurred: {str(e)}",
                details={"error_type": "unexpected", "error_message": str(e)}
            )

    def test_basic_operations(self, database_name: str = "test") -> ConnectionValidationResult:
        """
        Test basic MongoDB operations.
        
        Args:
            database_name: Name of the database to use for testing
            
        Returns:
            Operation validation result
        """
        if not self.client:
            return ConnectionValidationResult(
                success=False,
                message="No active MongoDB connection",
                details={"error_type": "no_connection"}
            )
        
        try:
            # Create a test collection
            db = self.client[database_name]
            collection_name = "migration_tool_test"
            collection = db[collection_name]
            
            # Insert a test document
            test_doc = {"test_key": "test_value", "migration_tool": True}
            insert_result = collection.insert_one(test_doc)
            
            # Find the document
            find_result = collection.find_one({"_id": insert_result.inserted_id})
            
            # Update the document
            update_result = collection.update_one(
                {"_id": insert_result.inserted_id},
                {"$set": {"updated": True}}
            )
            
            # Delete the document
            delete_result = collection.delete_one({"_id": insert_result.inserted_id})
            
            # Clean up by dropping the test collection
            collection.drop()
            
            return ConnectionValidationResult(
                success=True,
                message="Successfully tested basic MongoDB operations",
                details={
                    "operations_tested": ["insert", "find", "update", "delete"],
                    "database": database_name,
                    "collection": collection_name
                }
            )
        
        except Exception as e:
            return ConnectionValidationResult(
                success=False,
                message=f"Failed to perform basic MongoDB operations: {str(e)}",
                details={"error_type": "operation_failure", "error_message": str(e)}
            )

    def verify_schema_compatibility(self, schema: Dict) -> ConnectionValidationResult:
        """
        Verify that the proposed schema is compatible with MongoDB.
        
        Args:
            schema: Proposed MongoDB schema
            
        Returns:
            Schema compatibility validation result
        """
        if not self.client:
            return ConnectionValidationResult(
                success=False,
                message="No active MongoDB connection",
                details={"error_type": "no_connection"}
            )
        
        try:
            # Check for any schema features that might not be supported
            issues = []
            
            # Check collection names
            if "collections" in schema:
                for collection in schema["collections"]:
                    if "name" in collection:
                        name = collection["name"]
                        
                        # Check for invalid characters in collection names
                        if "$" in name:
                            issues.append(f"Collection name '{name}' contains invalid character '$'")
                        
                        # Check for system collection names
                        if name.startswith("system."):
                            issues.append(f"Collection name '{name}' starts with reserved prefix 'system.'")
            
            # Check for any other potential issues
            # (This could be expanded based on specific MongoDB version features)
            
            if issues:
                return ConnectionValidationResult(
                    success=False,
                    message="Schema compatibility issues detected",
                    details={"issues": issues}
                )
            else:
                return ConnectionValidationResult(
                    success=True,
                    message="Schema is compatible with MongoDB",
                    details={"schema_validated": True}
                )
        
        except Exception as e:
            return ConnectionValidationResult(
                success=False,
                message=f"Failed to verify schema compatibility: {str(e)}",
                details={"error_type": "schema_validation_failure", "error_message": str(e)}
            )

    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None


def validate_mongodb_connection(connection_string: str) -> ConnectionValidationResult:
    """
    Validate MongoDB connection.
    
    Args:
        connection_string: MongoDB connection string
        
    Returns:
        Connection validation result
    """
    validator = MongoDBValidator(connection_string)
    result = validator.validate_connection()
    validator.close()
    return result


def test_mongodb_operations(connection_string: str, database_name: str = "test") -> ConnectionValidationResult:
    """
    Test basic MongoDB operations.
    
    Args:
        connection_string: MongoDB connection string
        database_name: Name of the database to use for testing
        
    Returns:
        Operation validation result
    """
    validator = MongoDBValidator(connection_string)
    connection_result = validator.validate_connection()
    
    if not connection_result.success:
        validator.close()
        return connection_result
    
    result = validator.test_basic_operations(database_name)
    validator.close()
    return result


def verify_schema_compatibility(connection_string: str, schema: Dict) -> ConnectionValidationResult:
    """
    Verify that the proposed schema is compatible with MongoDB.
    
    Args:
        connection_string: MongoDB connection string
        schema: Proposed MongoDB schema
        
    Returns:
        Schema compatibility validation result
    """
    validator = MongoDBValidator(connection_string)
    connection_result = validator.validate_connection()
    
    if not connection_result.success:
        validator.close()
        return connection_result
    
    result = validator.verify_schema_compatibility(schema)
    validator.close()
    return result
