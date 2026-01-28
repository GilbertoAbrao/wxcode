"""
Módulo de integração com Neo4j para análise avançada de grafos.

Este módulo provê:
- Neo4jConnection: Gerenciamento de conexão com Neo4j
- Neo4jSyncService: Sincronização de dados MongoDB -> Neo4j
- ImpactAnalyzer: Análise de impacto e queries de grafo
"""

from wxcode.graph.neo4j_connection import Neo4jConnection
from wxcode.graph.neo4j_sync import Neo4jSyncService, SyncResult
from wxcode.graph.impact_analyzer import ImpactAnalyzer, ImpactResult

__all__ = [
    "Neo4jConnection",
    "Neo4jSyncService",
    "SyncResult",
    "ImpactAnalyzer",
    "ImpactResult",
]
