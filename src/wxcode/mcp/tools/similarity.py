"""MCP tools for finding similar converted elements.

Provides tools to search for already-converted elements that are similar
to the current element being converted. Enables pattern reuse and
consistency across the conversion process.
"""

import re
from typing import Any

from bson import DBRef
from fastmcp import Context

from wxcode.config import get_settings
from wxcode.mcp.instance import mcp
from wxcode.models.control import Control
from wxcode.models.element import Element, ConversionStatus, ElementType
from wxcode.models.milestone import Milestone, MilestoneStatus
from wxcode.models.output_project import OutputProject
from wxcode.models.project import Project


def _calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two element names.

    Uses prefix matching and common word detection.
    Returns 0.0 to 1.0
    """
    if name1 == name2:
        return 1.0

    # Normalize names (remove prefixes like PAGE_, BTN_, EDT_)
    def normalize(name: str) -> str:
        # Remove common WinDev prefixes
        prefixes = ["PAGE_", "WIN_", "REPORT_", "PROC_", "CLASS_", "QRY_"]
        for prefix in prefixes:
            if name.upper().startswith(prefix):
                name = name[len(prefix) :]
                break
        return name.lower()

    n1 = normalize(name1)
    n2 = normalize(name2)

    if n1 == n2:
        return 0.95

    # Check if one contains the other
    if n1 in n2 or n2 in n1:
        return 0.7

    # Split into words and check overlap
    words1 = set(re.split(r"[_\s]", n1))
    words2 = set(re.split(r"[_\s]", n2))

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    if not union:
        return 0.0

    return len(intersection) / len(union) * 0.6  # Max 0.6 for word overlap


def _calculate_type_similarity(type1: ElementType, type2: ElementType) -> float:
    """Calculate similarity based on element types."""
    if type1 == type2:
        return 1.0

    # Group similar types
    ui_types = {ElementType.PAGE, ElementType.PAGE_TEMPLATE, ElementType.WINDOW}
    logic_types = {ElementType.PROCEDURE_GROUP, ElementType.BROWSER_PROCEDURE, ElementType.CLASS}
    data_types = {ElementType.QUERY, ElementType.STRUCTURE}

    for group in [ui_types, logic_types, data_types]:
        if type1 in group and type2 in group:
            return 0.5

    return 0.0


def _calculate_structure_similarity(controls1: list[dict], controls2: list[dict]) -> float:
    """
    Calculate structural similarity based on control types.

    Compares the distribution of control types between elements.
    """
    if not controls1 or not controls2:
        return 0.0 if not controls1 and not controls2 else 0.0

    # Count control types
    def type_distribution(controls: list[dict]) -> dict[int, int]:
        dist: dict[int, int] = {}
        for ctrl in controls:
            type_code = ctrl.get("type_code", 0)
            dist[type_code] = dist.get(type_code, 0) + 1
        return dist

    dist1 = type_distribution(controls1)
    dist2 = type_distribution(controls2)

    # Jaccard-like similarity on type sets
    types1 = set(dist1.keys())
    types2 = set(dist2.keys())

    if not types1 or not types2:
        return 0.0

    intersection = types1 & types2
    union = types1 | types2

    if not union:
        return 0.0

    # Basic Jaccard
    jaccard = len(intersection) / len(union)

    # Bonus for similar counts
    count_similarity = 0.0
    if intersection:
        for type_code in intersection:
            c1 = dist1[type_code]
            c2 = dist2[type_code]
            count_similarity += min(c1, c2) / max(c1, c2)
        count_similarity /= len(intersection)

    return jaccard * 0.6 + count_similarity * 0.4


def _calculate_dependency_similarity(deps1: dict[str, list], deps2: dict[str, list]) -> float:
    """
    Calculate similarity based on shared dependencies (tables, elements).
    """
    # Combine all dependency lists
    all_deps1 = set(
        deps1.get("data_files", []) + deps1.get("uses", []) + deps1.get("bound_tables", [])
    )
    all_deps2 = set(
        deps2.get("data_files", []) + deps2.get("uses", []) + deps2.get("bound_tables", [])
    )

    if not all_deps1 or not all_deps2:
        return 0.0

    intersection = all_deps1 & all_deps2
    union = all_deps1 | all_deps2

    if not union:
        return 0.0

    return len(intersection) / len(union)


@mcp.tool
async def search_converted_similar(
    ctx: Context,
    element_name: str,
    output_project_id: str,
    min_similarity: float = 0.3,
    max_results: int = 5,
    include_conversion_details: bool = True,
) -> dict[str, Any]:
    """
    Search for similar already-converted elements within the same Output Project.

    Finds elements that have been successfully converted and are structurally
    similar to the given element. Useful for reusing patterns and maintaining
    consistency during conversion.

    Similarity is calculated based on:
    - Name similarity (common prefixes, words)
    - Element type (page, procedure, class, etc.)
    - Control structure (for UI elements)
    - Dependencies (shared tables, procedures)

    Args:
        element_name: Name of the element to find similar matches for
        output_project_id: ID of the Output Project (search only within this project)
        min_similarity: Minimum similarity score (0.0 to 1.0, default 0.3)
        max_results: Maximum number of results to return (default 5)
        include_conversion_details: Include conversion status and files (default True)

    Returns:
        List of similar converted elements with similarity scores and details
    """
    try:
        # Find Output Project
        output_project = await OutputProject.get(output_project_id)
        if not output_project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Output Project '{output_project_id}' not found",
            }

        # Find the source element
        settings = get_settings()
        mongo_client = ctx.request_context.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]

        # Get the KB project associated with the output project
        project = await Project.get(output_project.kb_id)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": "Knowledge Base project not found",
            }

        # Find source element
        elements_collection = db["elements"]
        project_dbref = DBRef("projects", project.id)

        source_elem_dict = await elements_collection.find_one(
            {"source_name": element_name, "project_id": project_dbref}
        )

        if not source_elem_dict:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Element '{element_name}' not found in project",
                "suggestion": "Use list_elements to see available elements",
            }

        source_element = await Element.get(source_elem_dict["_id"])
        if not source_element:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Element '{element_name}' could not be loaded",
            }

        # Get completed milestones in this output project
        completed_milestones = await Milestone.find(
            Milestone.output_project_id == output_project.id,
            Milestone.status == MilestoneStatus.COMPLETED,
        ).to_list()

        if not completed_milestones:
            return {
                "error": False,
                "element": element_name,
                "message": "No completed conversions found in this Output Project",
                "similar_elements": [],
                "total_completed": 0,
            }

        # Get completed element IDs (exclude the source element)
        completed_element_ids = [
            m.element_id for m in completed_milestones if m.element_id != source_element.id
        ]

        if not completed_element_ids:
            return {
                "error": False,
                "element": element_name,
                "message": "No other completed conversions to compare against",
                "similar_elements": [],
                "total_completed": len(completed_milestones),
            }

        # Get source element controls for structure comparison
        source_controls = await Control.find({"element_id": source_element.id}).to_list()
        source_controls_data = [{"type_code": c.type_code, "name": c.name} for c in source_controls]

        # Get source dependencies
        source_deps = {}
        if source_element.dependencies:
            source_deps = {
                "data_files": source_element.dependencies.data_files,
                "uses": source_element.dependencies.uses,
                "bound_tables": source_element.dependencies.bound_tables,
            }

        # Calculate similarity for each completed element
        similar_elements = []

        for element_id in completed_element_ids:
            candidate = await Element.get(element_id)
            if not candidate:
                continue

            # Calculate individual similarity scores
            name_score = _calculate_name_similarity(
                source_element.source_name, candidate.source_name
            )
            type_score = _calculate_type_similarity(
                source_element.source_type, candidate.source_type
            )

            # Get candidate controls
            candidate_controls = await Control.find({"element_id": candidate.id}).to_list()
            candidate_controls_data = [
                {"type_code": c.type_code, "name": c.name} for c in candidate_controls
            ]

            structure_score = _calculate_structure_similarity(
                source_controls_data, candidate_controls_data
            )

            # Get candidate dependencies
            candidate_deps = {}
            if candidate.dependencies:
                candidate_deps = {
                    "data_files": candidate.dependencies.data_files,
                    "uses": candidate.dependencies.uses,
                    "bound_tables": candidate.dependencies.bound_tables,
                }

            dep_score = _calculate_dependency_similarity(source_deps, candidate_deps)

            # Weighted overall score
            # Type match is important, structure is very important for UI elements
            weights = {"name": 0.15, "type": 0.25, "structure": 0.35, "dependencies": 0.25}

            overall_score = (
                name_score * weights["name"]
                + type_score * weights["type"]
                + structure_score * weights["structure"]
                + dep_score * weights["dependencies"]
            )

            if overall_score >= min_similarity:
                match_info: dict[str, Any] = {
                    "element_name": candidate.source_name,
                    "element_type": candidate.source_type.value,
                    "similarity_score": round(overall_score, 3),
                    "scores": {
                        "name": round(name_score, 3),
                        "type": round(type_score, 3),
                        "structure": round(structure_score, 3),
                        "dependencies": round(dep_score, 3),
                    },
                }

                if include_conversion_details and candidate.conversion:
                    match_info["conversion"] = {
                        "status": candidate.conversion.status.value,
                        "target_stack": candidate.conversion.target_stack,
                        "converted_at": candidate.conversion.converted_at.isoformat()
                        if candidate.conversion.converted_at
                        else None,
                        "file_count": len(candidate.conversion.target_files),
                        "files": [
                            {"path": f.path, "type": f.file_type}
                            for f in candidate.conversion.target_files
                        ]
                        if candidate.conversion.target_files
                        else [],
                    }

                # Add shared dependencies info
                if candidate_deps and source_deps:
                    shared_tables = set(source_deps.get("data_files", [])) & set(
                        candidate_deps.get("data_files", [])
                    )
                    shared_bound = set(source_deps.get("bound_tables", [])) & set(
                        candidate_deps.get("bound_tables", [])
                    )
                    if shared_tables or shared_bound:
                        match_info["shared_dependencies"] = {
                            "tables": list(shared_tables),
                            "bound_tables": list(shared_bound),
                        }

                similar_elements.append(match_info)

        # Sort by similarity score (descending) and limit results
        similar_elements.sort(key=lambda x: x["similarity_score"], reverse=True)
        similar_elements = similar_elements[:max_results]

        # Build response
        response: dict[str, Any] = {
            "error": False,
            "element": element_name,
            "element_type": source_element.source_type.value,
            "output_project_id": output_project_id,
            "total_completed": len(completed_milestones),
            "matches_found": len(similar_elements),
            "similar_elements": similar_elements,
        }

        if similar_elements:
            response["best_match"] = similar_elements[0]["element_name"]
            response["best_match_score"] = similar_elements[0]["similarity_score"]

        return response

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }
