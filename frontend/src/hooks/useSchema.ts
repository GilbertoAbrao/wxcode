"use client";

/**
 * Hook para buscar schema do banco de dados (tables e connections).
 */

import { useQuery } from "@tanstack/react-query";

export interface SchemaTable {
  name: string;
  physical_name: string;
  connection_name: string;
  column_count: number;
  index_count: number;
  primary_key: string[];
}

export interface SchemaConnection {
  name: string;
  database_type: string;
  driver_name: string;
  source: string;
  port: string;
  database: string;
  user: string;
}

export interface Schema {
  project: string;
  source_file: string;
  version: number;
  total_tables: number;
  tables: SchemaTable[];
  total_connections: number;
  connections: SchemaConnection[];
}

async function fetchSchema(projectName: string): Promise<Schema | null> {
  try {
    const response = await fetch(`/api/schema/${projectName}`);
    if (!response.ok) {
      console.warn("Schema endpoint failed");
      return null;
    }
    return response.json();
  } catch (error) {
    console.error("Failed to fetch schema:", error);
    return null;
  }
}

export function useSchema(projectName: string | undefined) {
  return useQuery({
    queryKey: ["schema", projectName],
    queryFn: () => fetchSchema(projectName!),
    enabled: !!projectName,
  });
}
