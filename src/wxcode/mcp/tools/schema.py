"""MCP tools for Schema queries.

Provides tools to query the database schema extracted from WinDev Analysis
files (.xdd). Essential for understanding data structures during conversion.
"""

from typing import Any

from fastmcp import Context

from wxcode.mcp.instance import mcp
from wxcode.models.project import Project
from wxcode.models.schema import DatabaseSchema


@mcp.tool
async def list_kb_connections(
    ctx: Context,
    project_name: str,
) -> dict[str, Any]:
    """
    List database connections from the KB (Knowledge Base) schema.

    Returns all connections defined in the WinDev Analysis file.
    Use this to see available connections before configuring OutputProject.

    Args:
        project_name: Name of the KB project

    Returns:
        List of connections with database type, source, port, etc.
    """
    try:
        # Find project
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Project '{project_name}' not found",
            }

        # Find schema for project
        schema = await DatabaseSchema.find_one({"project_id": project.id})
        if not schema:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"No schema found for project '{project_name}'",
                "suggestion": "Run 'wxcode parse-schema' to import the database schema",
            }

        # Build connections list
        connections_data = []
        for conn in schema.connections or []:
            connections_data.append({
                "name": conn.name,
                "type_code": conn.type_code,
                "database_type": conn.database_type,
                "driver_name": conn.driver_name,
                "source": conn.source,
                "port": conn.port,
                "database": conn.database,
                "user": conn.user,
            })

        return {
            "error": False,
            "project": project_name,
            "total_connections": len(connections_data),
            "connections": connections_data,
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def get_schema(
    ctx: Context,
    project_name: str
) -> dict:
    """
    Get the complete database schema for a WinDev project.

    Returns all tables, connections, and schema metadata.
    Use this to understand the data model before conversion.

    Args:
        project_name: Name of the project (required)

    Returns:
        Complete schema including tables and connections
    """
    try:
        # Find project
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Project '{project_name}' not found"
            }

        # Find schema for project
        schema = await DatabaseSchema.find_one({"project_id": project.id})
        if not schema:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"No schema found for project '{project_name}'",
                "suggestion": "Run 'wxcode parse-schema' to import the database schema"
            }

        # Build connections list
        connections_data = []
        for conn in (schema.connections or []):
            connections_data.append({
                "name": conn.name,
                "database_type": conn.database_type,
                "driver_name": conn.driver_name,
                "source": conn.source,
                "port": conn.port,
                "database": conn.database,
                "user": conn.user
            })

        # Build tables summary (without full column details)
        tables_data = []
        for table in (schema.tables or []):
            # Get primary key column names
            pk_columns = [col.name for col in (table.columns or []) if col.is_primary_key]

            tables_data.append({
                "name": table.name,
                "physical_name": table.physical_name,
                "connection_name": table.connection_name,
                "column_count": len(table.columns) if table.columns else 0,
                "index_count": len(table.indexes) if table.indexes else 0,
                "primary_key": pk_columns
            })

        return {
            "error": False,
            "project": project_name,
            "source_file": schema.source_file,
            "version": schema.version,
            "total_connections": len(connections_data),
            "connections": connections_data,
            "total_tables": len(tables_data),
            "tables": tables_data
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__
        }


@mcp.tool
async def get_table(
    ctx: Context,
    table_name: str,
    project_name: str
) -> dict:
    """
    Get detailed definition for a specific database table.

    Returns all columns, types, constraints, and indexes.
    Use this when you need full table structure for conversion.

    Args:
        table_name: Name of the table (e.g., USUARIO, CLIENTE)
        project_name: Name of the project (required)

    Returns:
        Complete table definition with columns and indexes
    """
    try:
        # Find project
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Project '{project_name}' not found"
            }

        # Find schema for project
        schema = await DatabaseSchema.find_one({"project_id": project.id})
        if not schema:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"No schema found for project '{project_name}'",
                "suggestion": "Run 'wxcode parse-schema' to import the database schema"
            }

        # Find table in schema (case-insensitive)
        table = next(
            (t for t in (schema.tables or []) if t.name.upper() == table_name.upper()),
            None
        )

        if not table:
            # List available tables as suggestion
            available = [t.name for t in (schema.tables or [])[:15]]
            suggestion = f"Available tables (first 15): {', '.join(available)}" if available else "No tables in schema"
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Table '{table_name}' not found in schema",
                "suggestion": suggestion
            }

        # Build columns list with full details
        columns_data = []
        for col in (table.columns or []):
            columns_data.append({
                "name": col.name,
                "hyperfile_type": col.hyperfile_type,
                "python_type": col.python_type,
                "size": col.size,
                "nullable": col.nullable,
                "default_value": col.default_value,
                "is_primary_key": col.is_primary_key,
                "is_indexed": col.is_indexed,
                "is_unique": col.is_unique,
                "is_auto_increment": col.is_auto_increment
            })

        # Build indexes list
        indexes_data = []
        for idx in (table.indexes or []):
            indexes_data.append({
                "name": idx.name,
                "columns": idx.columns,
                "is_unique": idx.is_unique,
                "is_primary": idx.is_primary
            })

        return {
            "error": False,
            "table": {
                "name": table.name,
                "physical_name": table.physical_name,
                "connection_name": table.connection_name,
                "supports_null": table.supports_null,
                "topological_order": table.topological_order,
                "layer": table.layer,
                "conversion_status": table.conversion_status,
                "columns": columns_data,
                "indexes": indexes_data
            }
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__
        }
