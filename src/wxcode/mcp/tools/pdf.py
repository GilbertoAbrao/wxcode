"""MCP tools for PDF documentation access.

Provides tools to locate and access PDF documentation and screenshots
for WinDev elements during conversion.
"""

from pathlib import Path
from typing import Any

from bson import DBRef
from fastmcp import Context

from wxcode.config import get_settings
from wxcode.mcp.server import mcp
from wxcode.models.element import Element
from wxcode.models.output_project import OutputProject
from wxcode.models.project import Project


async def _find_element(
    ctx: Context, element_name: str, project_name: str | None
) -> tuple[Element | None, str | None]:
    """
    Find element by name, optionally scoped to project.

    Returns:
        (element, error_message) - element is None if not found
    """
    if project_name:
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return None, f"Project '{project_name}' not found"

        settings = get_settings()
        mongo_client = ctx.request_context.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]
        collection = db["elements"]

        project_dbref = DBRef("projects", project.id)
        elem_dict = await collection.find_one(
            {"source_name": element_name, "project_id": project_dbref}
        )

        if not elem_dict:
            return None, f"Element '{element_name}' not found in project '{project_name}'"

        element = await Element.get(elem_dict["_id"])
        return element, None
    else:
        elements = await Element.find(Element.source_name == element_name).to_list()

        if not elements:
            return None, f"Element '{element_name}' not found"

        if len(elements) > 1:
            return (
                None,
                f"Element '{element_name}' found in multiple projects. Use project_name to specify.",
            )

        return elements[0], None


def _find_pdf_file(workspace_path: str | None, element_name: str) -> Path | None:
    """
    Find PDF file for an element in the workspace.

    Looks in common locations:
    - {workspace}/pdf_docs/{element_name}.pdf
    - {workspace}/docs/{element_name}.pdf
    - {workspace}/documentation/{element_name}.pdf
    """
    if not workspace_path:
        return None

    workspace = Path(workspace_path)

    # Common PDF locations
    locations = [
        workspace / "pdf_docs" / f"{element_name}.pdf",
        workspace / "docs" / f"{element_name}.pdf",
        workspace / "documentation" / f"{element_name}.pdf",
        workspace / "pdfs" / f"{element_name}.pdf",
    ]

    # Also try without common prefixes
    base_name = element_name
    for prefix in ["PAGE_", "WIN_", "REPORT_", "PROC_"]:
        if element_name.upper().startswith(prefix):
            base_name = element_name[len(prefix) :]
            locations.extend(
                [
                    workspace / "pdf_docs" / f"{base_name}.pdf",
                    workspace / "docs" / f"{base_name}.pdf",
                ]
            )
            break

    for location in locations:
        if location.exists():
            return location

    return None


def _find_screenshot(
    workspace_path: str | None, element_name: str, screenshot_path: str | None
) -> Path | None:
    """
    Find screenshot file for an element.

    First checks screenshot_path from element, then common locations.
    """
    # Check element's stored screenshot path first
    if screenshot_path:
        path = Path(screenshot_path)
        if path.exists():
            return path
        # Try relative to workspace
        if workspace_path:
            relative = Path(workspace_path) / screenshot_path
            if relative.exists():
                return relative

    if not workspace_path:
        return None

    workspace = Path(workspace_path)

    # Common screenshot locations and extensions
    extensions = [".png", ".jpg", ".jpeg", ".gif"]
    locations = ["screenshots", "images", "pdf_docs", "docs"]

    for location in locations:
        for ext in extensions:
            path = workspace / location / f"{element_name}{ext}"
            if path.exists():
                return path

    return None


@mcp.tool
async def get_element_pdf_slice(
    ctx: Context,
    element_name: str,
    output_project_id: str | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    """
    Get path to PDF documentation and screenshot for a WinDev element.

    Returns the filesystem path to the PDF documentation and UI screenshot
    for an element, if available. The PDF contains detailed WinDev technical
    documentation, and the screenshot shows the visual appearance.

    PDFs are typically stored in {workspace}/pdf_docs/{element_name}.pdf

    Args:
        element_name: Name of the element (e.g., PAGE_Login)
        output_project_id: Optional Output Project ID to determine workspace path
        project_name: Optional project name to scope the element search

    Returns:
        Paths to PDF and screenshot files if they exist
    """
    try:
        # Find the element
        element, error = await _find_element(ctx, element_name, project_name)

        if error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": error,
                "suggestion": "Use list_elements to see available elements",
            }

        # Get workspace path from output project if provided
        workspace_path = None
        if output_project_id:
            output_project = await OutputProject.get(output_project_id)
            if output_project and output_project.workspace_path:
                workspace_path = output_project.workspace_path

        # If no workspace from output project, try to get from project
        if not workspace_path:
            project = await element.project_id.fetch()
            if project and hasattr(project, "workspace_path"):
                workspace_path = project.workspace_path

        # Look for PDF
        pdf_path = _find_pdf_file(workspace_path, element_name)

        # Look for screenshot
        screenshot_path = _find_screenshot(workspace_path, element_name, element.screenshot_path)

        # Build response
        response: dict[str, Any] = {
            "error": False,
            "element": element_name,
            "element_type": element.source_type.value,
        }

        if workspace_path:
            response["workspace_path"] = workspace_path

        # PDF info
        if pdf_path:
            response["pdf"] = {
                "exists": True,
                "path": str(pdf_path),
                "size_bytes": pdf_path.stat().st_size,
            }
        else:
            response["pdf"] = {
                "exists": False,
                "searched_locations": [
                    f"{{workspace}}/pdf_docs/{element_name}.pdf",
                    f"{{workspace}}/docs/{element_name}.pdf",
                ]
                if workspace_path
                else [],
                "message": "PDF not found" if workspace_path else "No workspace path available",
            }

        # Screenshot info
        if screenshot_path:
            response["screenshot"] = {
                "exists": True,
                "path": str(screenshot_path),
                "size_bytes": screenshot_path.stat().st_size,
            }
        else:
            response["screenshot"] = {"exists": False, "message": "Screenshot not found"}
            # Check if element has stored screenshot path
            if element.screenshot_path:
                response["screenshot"]["stored_path"] = element.screenshot_path
                response["screenshot"]["message"] = (
                    f"Stored path '{element.screenshot_path}' not found on filesystem"
                )

        # Add helpful summary
        has_pdf = pdf_path is not None
        has_screenshot = screenshot_path is not None

        if has_pdf and has_screenshot:
            response["summary"] = "Both PDF documentation and screenshot available"
        elif has_pdf:
            response["summary"] = "PDF documentation available, no screenshot"
        elif has_screenshot:
            response["summary"] = "Screenshot available, no PDF documentation"
        else:
            response["summary"] = "No visual documentation available for this element"

        return response

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }
