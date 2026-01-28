"""ConversionTracker - Rastreia status de conversão no MongoDB."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from motor.motor_asyncio import AsyncIOMotorDatabase

if TYPE_CHECKING:
    from ..models import Element

ConversionStatus = Literal["pending", "proposal_generated", "converted", "archived"]


@dataclass
class PendingItem:
    """Item pendente de conversão (pode ser Element, Procedure, Class, etc.)."""

    collection: str
    doc: dict[str, Any]
    topological_order: int | None
    layer: str | None
    name: str
    item_type: str  # "page", "procedure", "class", "table"


class ConversionTracker:
    """Rastreia status de conversão de elementos no MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Inicializa o tracker.

        Args:
            db: Conexão com MongoDB
        """
        self.db = db
        self.elements = db.elements
        self.procedures = db.procedures
        self.classes = db.class_definitions
        self.schemas = db.database_schemas

    async def get_next_pending(self, project_name: str) -> "Element | None":
        """Busca próximo elemento pendente por ordem topológica.

        Args:
            project_name: Nome do projeto

        Returns:
            Próximo elemento pendente ou None se todos convertidos
        """
        from ..models import Element

        item = await self.get_next_pending_item(project_name)
        if not item:
            return None

        # Se for um Element, retorna diretamente
        if item.collection == "elements":
            return Element(**item.doc)

        # Para outros tipos, cria um Element "virtual" para compatibilidade
        # TODO: No futuro, retornar o tipo correto ou um wrapper
        return Element(**item.doc) if item.collection == "elements" else None

    async def get_next_pending_item(self, project_name: str) -> PendingItem | None:
        """Busca próximo item pendente de qualquer collection.

        Segue ordem topológica através de todas as collections:
        - elements (pages)
        - procedures
        - class_definitions

        Args:
            project_name: Nome do projeto

        Returns:
            PendingItem com dados do próximo item ou None
        """
        project = await self.db.projects.find_one({"name": project_name})
        if not project:
            return None

        project_id = project["_id"]

        # Query base para items pendentes
        pending_filter = {
            "$or": [
                {"conversion.status": "pending"},
                {"conversion.status": {"$exists": False}},
                {"conversion": {"$exists": False}},
            ],
        }

        candidates: list[PendingItem] = []

        # 1. Buscar em Elements (pages) - usa DBRef
        cursor = self.elements.find(
            {
                "project_id.$id": project_id,
                "topological_order": {"$ne": None},
                **pending_filter,
            }
        ).sort("topological_order", 1).limit(1)
        docs = await cursor.to_list(length=1)
        if docs:
            doc = docs[0]
            candidates.append(PendingItem(
                collection="elements",
                doc=doc,
                topological_order=doc.get("topological_order"),
                layer=doc.get("layer"),
                name=doc.get("source_name", "unknown"),
                item_type="page",
            ))

        # 2. Buscar em Procedures - usa project_id direto
        cursor = self.procedures.find(
            {
                "project_id": project_id,
                "topological_order": {"$ne": None},
                **pending_filter,
            }
        ).sort("topological_order", 1).limit(1)
        docs = await cursor.to_list(length=1)
        if docs:
            doc = docs[0]
            candidates.append(PendingItem(
                collection="procedures",
                doc=doc,
                topological_order=doc.get("topological_order"),
                layer=doc.get("layer"),
                name=doc.get("name", "unknown"),
                item_type="procedure",
            ))

        # 3. Buscar em Classes - usa project_id direto
        cursor = self.classes.find(
            {
                "project_id": project_id,
                "topological_order": {"$ne": None},
                **pending_filter,
            }
        ).sort("topological_order", 1).limit(1)
        docs = await cursor.to_list(length=1)
        if docs:
            doc = docs[0]
            candidates.append(PendingItem(
                collection="class_definitions",
                doc=doc,
                topological_order=doc.get("topological_order"),
                layer=doc.get("layer"),
                name=doc.get("name", "unknown"),
                item_type="class",
            ))

        # Retorna o candidato com menor topological_order
        if candidates:
            candidates.sort(key=lambda x: x.topological_order or float("inf"))
            return candidates[0]

        # Se não encontrou com ordem, busca sem ordem (fallback)
        cursor = self.elements.find(
            {
                "project_id.$id": project_id,
                "topological_order": None,
                **pending_filter,
            }
        ).limit(1)
        docs = await cursor.to_list(length=1)
        if docs:
            doc = docs[0]
            return PendingItem(
                collection="elements",
                doc=doc,
                topological_order=None,
                layer=None,
                name=doc.get("source_name", "unknown"),
                item_type="page",
            )

        return None

    async def get_pending_count(self, project_name: str) -> int:
        """Conta items pendentes de conversão (todas as collections).

        Args:
            project_name: Nome do projeto

        Returns:
            Número total de items pendentes
        """
        project = await self.db.projects.find_one({"name": project_name})
        if not project:
            return 0

        project_id = project["_id"]

        pending_filter = {
            "$or": [
                {"conversion.status": "pending"},
                {"conversion.status": {"$exists": False}},
                {"conversion": {"$exists": False}},
            ],
        }

        # Contar em todas as collections
        elements_count = await self.elements.count_documents({
            "project_id.$id": project_id,
            "topological_order": {"$ne": None},
            **pending_filter,
        })

        procedures_count = await self.procedures.count_documents({
            "project_id": project_id,
            "topological_order": {"$ne": None},
            **pending_filter,
        })

        classes_count = await self.classes.count_documents({
            "project_id": project_id,
            "topological_order": {"$ne": None},
            **pending_filter,
        })

        return elements_count + procedures_count + classes_count

    async def get_stats(self, project_name: str) -> dict[str, int]:
        """Retorna estatísticas de conversão.

        Args:
            project_name: Nome do projeto

        Returns:
            Dict com contagem por status
        """
        project = await self.db.projects.find_one({"name": project_name})
        if not project:
            return {}

        project_id = project["_id"]

        pipeline = [
            {"$match": {"project_id.$id": project_id}},
            {
                "$group": {
                    "_id": {"$ifNull": ["$conversion.status", "pending"]},
                    "count": {"$sum": 1},
                }
            },
        ]

        stats = {}
        async for doc in self.elements.aggregate(pipeline):
            stats[doc["_id"]] = doc["count"]

        return stats

    async def mark_status(
        self, element_id: str, status: ConversionStatus
    ) -> bool:
        """Atualiza status de conversão de um elemento.

        Args:
            element_id: ID do elemento (ObjectId como string)
            status: Novo status

        Returns:
            True se atualizado, False se não encontrado
        """
        from bson import ObjectId

        result = await self.elements.update_one(
            {"_id": ObjectId(element_id)},
            {"$set": {"conversion.status": status}},
        )
        return result.modified_count > 0

    async def mark_proposal_generated(self, element_id: str) -> bool:
        """Marca elemento como tendo proposal gerada.

        Args:
            element_id: ID do elemento

        Returns:
            True se atualizado
        """
        return await self.mark_status(element_id, "proposal_generated")

    async def mark_converted(self, element_id: str) -> bool:
        """Marca elemento como convertido.

        Args:
            element_id: ID do elemento

        Returns:
            True se atualizado
        """
        return await self.mark_status(element_id, "converted")

    async def mark_archived(self, element_id: str) -> bool:
        """Marca elemento como arquivado.

        Args:
            element_id: ID do elemento

        Returns:
            True se atualizado
        """
        return await self.mark_status(element_id, "archived")

    async def reset_status(self, project_name: str) -> int:
        """Reseta status de todos elementos para pending.

        Args:
            project_name: Nome do projeto

        Returns:
            Número de elementos resetados
        """
        project = await self.db.projects.find_one({"name": project_name})
        if not project:
            return 0

        result = await self.elements.update_many(
            {"project_id.$id": project["_id"]},
            {"$set": {"conversion.status": "pending"}},
        )
        return result.modified_count

    async def skip_by_type(
        self, project_name: str, item_types: list[str]
    ) -> dict[str, int]:
        """Marca items de tipos específicos como 'skipped'.

        Útil para pular classes/procedures e ir direto para pages.

        Args:
            project_name: Nome do projeto
            item_types: Lista de tipos a pular ("class", "procedure", "page")

        Returns:
            Dict com contagem por tipo
        """
        project = await self.db.projects.find_one({"name": project_name})
        if not project:
            return {}

        project_id = project["_id"]
        counts: dict[str, int] = {}

        if "class" in item_types:
            result = await self.classes.update_many(
                {"project_id": project_id},
                {"$set": {"conversion.status": "skipped"}},
            )
            counts["class"] = result.modified_count

        if "procedure" in item_types:
            result = await self.procedures.update_many(
                {"project_id": project_id},
                {"$set": {"conversion.status": "skipped"}},
            )
            counts["procedure"] = result.modified_count

        if "page" in item_types:
            result = await self.elements.update_many(
                {"project_id.$id": project_id},
                {"$set": {"conversion.status": "skipped"}},
            )
            counts["page"] = result.modified_count

        return counts

    async def reset_by_type(
        self, project_name: str, item_types: list[str]
    ) -> dict[str, int]:
        """Reseta status de tipos específicos para pending.

        Args:
            project_name: Nome do projeto
            item_types: Lista de tipos a resetar

        Returns:
            Dict com contagem por tipo
        """
        project = await self.db.projects.find_one({"name": project_name})
        if not project:
            return {}

        project_id = project["_id"]
        counts: dict[str, int] = {}

        if "class" in item_types:
            result = await self.classes.update_many(
                {"project_id": project_id},
                {"$set": {"conversion.status": "pending"}},
            )
            counts["class"] = result.modified_count

        if "procedure" in item_types:
            result = await self.procedures.update_many(
                {"project_id": project_id},
                {"$set": {"conversion.status": "pending"}},
            )
            counts["procedure"] = result.modified_count

        if "page" in item_types:
            result = await self.elements.update_many(
                {"project_id.$id": project_id},
                {"$set": {"conversion.status": "pending"}},
            )
            counts["page"] = result.modified_count

        return counts
