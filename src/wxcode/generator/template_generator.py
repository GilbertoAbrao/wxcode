"""Template Generator - Generates Jinja2 templates from pages.

Converts WinDev pages (.wwh) and their controls into Jinja2 HTML templates.
"""

from pathlib import Path
from typing import Any

from bson import ObjectId

from wxcode.models.control import Control
from wxcode.models.control_type import (
    PREFIX_TO_TYPE_NAME,
    infer_type_name_from_prefix,
)
from wxcode.models.element import Element

from .base import BaseGenerator, ElementFilter


class TemplateGenerator(BaseGenerator):
    """Generates Jinja2 HTML templates from WinDev pages.

    Reads page elements and their controls from MongoDB and generates:
    - One HTML template per page
    - Control mappings from WinDev types to HTML/Bootstrap
    - Static files (CSS, JS) for common functionality

    Supports selective element conversion via ElementFilter.
    """

    # WinDev control type to HTML template mapping
    CONTROL_TYPE_MAP: dict[str, str] = {
        # Input controls
        "Edit": "edit",
        "RichTextArea": "edit",
        "CodeEditor": "edit",
        "HTMLEditor": "edit",
        "WordProcessing": "edit",

        # Button controls
        "Button": "button",
        "Link": "button",
        "SegmentedButton": "button",

        # Selection controls
        "ComboBox": "combo",
        "List": "combo",
        "RadioButton": "radio",
        "CheckBox": "checkbox",

        # Display controls
        "Static": "static",
        "FormattedStatic": "static",
        "HTMLStatic": "static",
        "Image": "image",
        "Thumbnail": "image",

        # Data controls
        "Table": "table",
        "TreeViewTable": "table",
        "TreeView": "table",
        "Looper": "table",
        "ListView": "table",

        # Container controls
        "Cell": "cell",
        "LayoutZone": "cell",
        "Tab": "tab",
        "Popup": "modal",

        # Navigation controls
        "NavigationBar": "navbar",
        "Menu": "menu",
        "Breadcrumb": "breadcrumb",

        # Chart/Visual controls
        "Chart": "chart",
        "ProgressBar": "progress",
        "Slider": "slider",
        "RangeSlider": "slider",
        "Rating": "rating",

        # Calendar/Date controls
        "Calendar": "calendar",
        "Scheduler": "scheduler",
        "Organizer": "scheduler",

        # File controls
        "Upload": "upload",
        "PDFReader": "pdf",

        # Map/Location controls
        "Map": "map",

        # Multimedia controls
        "Video": "video",
        "Multimedia": "video",
        "Camera": "camera",
    }

    # Input type mapping based on control properties
    INPUT_TYPE_MAP: dict[str, str] = {
        "Text": "text",
        "Password": "password",
        "Email": "email",
        "Number": "number",
        "Date": "date",
        "DateTime": "datetime-local",
        "Time": "time",
        "Phone": "tel",
        "URL": "url",
        "Multiline": "textarea",
        "Currency": "number",
        "Duration": "text",
        "Token": "text",
    }

    template_subdir: str = "html"

    def __init__(
        self,
        project_id: str,
        output_dir: Path,
        element_filter: ElementFilter | None = None,
    ):
        """Initialize TemplateGenerator.

        Args:
            project_id: MongoDB ObjectId string for the project
            output_dir: Root directory where files will be written
            element_filter: Optional filter for selective element conversion
        """
        super().__init__(project_id, output_dir, element_filter)

    async def generate(self) -> list[Path]:
        """Generate Jinja2 templates from pages.

        Supports selective conversion via element_filter.
        Idempotent: cleans previous files before regenerating.

        Returns:
            List of generated file paths
        """
        # Find page elements with filter applied
        query = self.get_element_query(["page", "window"])
        elements = await Element.find(query).to_list()

        if not elements:
            return []

        # Generate template for each page
        for element in elements:
            # Clean previous template files only (not routes or other types)
            await self.clean_previous_files(
                element, file_types=["template", "style", "script"]
            )

            # Get controls for this page
            controls = await Control.find(
                {"element_id": element.id}
            ).sort("+depth", "+name").to_list()

            content = self._generate_template(element, controls)
            filename = self._element_to_filename(element.source_name)

            # Write file and track for element
            self.write_file_for_element(
                element, f"app/templates/pages/{filename}.html", content, "template"
            )

        # Generate base template
        self._generate_base_template()

        # Generate static files
        self._generate_static_files()

        # Update conversion status for all converted elements
        await self.update_all_converted_elements()

        return self.generated_files

    def _generate_template(
        self, element: Element, controls: list[Control]
    ) -> str:
        """Generate HTML template for a page.

        Args:
            element: Element representing the page
            controls: List of controls in the page

        Returns:
            Jinja2 HTML template string
        """
        page_name = self._element_to_filename(element.source_name)
        page_title = self._element_to_title(element.source_name)
        page_type = self._detect_page_type(controls)

        # Build control tree
        control_tree = self._build_control_tree(controls)

        # Generate content based on page type
        if page_type == "form":
            content = self._generate_form_content(control_tree)
        elif page_type == "list":
            content = self._generate_list_content(control_tree)
        elif page_type == "dashboard":
            content = self._generate_dashboard_content(control_tree)
        else:
            content = self._generate_simple_content(control_tree)

        context = {
            "page_name": page_name,
            "page_title": page_title,
            "original_page": element.source_file,
            "page_type": page_type,
            "form_content": content if page_type == "form" else "",
            "list_content": content if page_type == "list" else "",
            "dashboard_content": content if page_type == "dashboard" else "",
            "simple_content": content if page_type == "simple" else "",
        }

        return self.render_template("page.html.j2", context)

    def _detect_page_type(self, controls: list[Control]) -> str:
        """Detect the type of page based on controls.

        Args:
            controls: List of controls

        Returns:
            Page type: "form", "list", "dashboard", or "simple"
        """
        edit_count = 0
        button_count = 0
        table_count = 0

        for control in controls:
            type_name = self._get_control_type_name(control)
            name_lower = control.name.lower() if control.name else ""

            if type_name == "Edit" or name_lower.startswith("edt_"):
                edit_count += 1
            elif type_name == "Button" or name_lower.startswith("btn_"):
                button_count += 1
            elif type_name in ("Table", "TreeViewTable", "Looper") or \
                 name_lower.startswith("table_") or name_lower.startswith("tbl_"):
                table_count += 1

        if table_count > 0:
            return "list"
        elif edit_count >= 2 and button_count >= 1:
            return "form"
        elif edit_count > 5:
            return "dashboard"
        else:
            return "simple"

    def _build_control_tree(
        self, controls: list[Control]
    ) -> list[dict[str, Any]]:
        """Build hierarchical control tree.

        Args:
            controls: Flat list of controls

        Returns:
            List of root control dicts with children
        """
        # Index controls by ID
        control_map: dict[str, dict[str, Any]] = {}
        for ctrl in controls:
            control_map[str(ctrl.id)] = {
                "control": ctrl,
                "html": self._control_to_html(ctrl),
                "children": [],
            }

        # Build tree
        roots = []
        for ctrl in controls:
            ctrl_dict = control_map[str(ctrl.id)]
            if ctrl.parent_control_id:
                parent_id = str(ctrl.parent_control_id)
                if parent_id in control_map:
                    control_map[parent_id]["children"].append(ctrl_dict)
            else:
                roots.append(ctrl_dict)

        return roots

    def _control_to_html(self, control: Control) -> str:
        """Convert a control to HTML.

        Args:
            control: Control to convert

        Returns:
            HTML string for the control
        """
        type_name = self._get_control_type_name(control)
        template_type = self.CONTROL_TYPE_MAP.get(type_name, "static")

        context = self._build_control_context(control, type_name)

        try:
            return self.render_template(f"controls/{template_type}.html.j2", context)
        except Exception:
            # Fallback to static if template not found
            return self.render_template("controls/static.html.j2", context)

    def _build_control_context(
        self, control: Control, type_name: str
    ) -> dict[str, Any]:
        """Build template context for a control.

        Args:
            control: Control to process
            type_name: Detected type name

        Returns:
            Context dictionary for template
        """
        props = control.properties or {}

        # Base context
        context: dict[str, Any] = {
            "name": self._to_snake_case(control.name),
            "original_name": control.name,
            "label": self._extract_label(control),
            "css_classes": "",
            "htmx_attrs": {},
        }

        # Add properties
        if hasattr(props, "caption"):
            context["text"] = props.caption
        if hasattr(props, "hint_text"):
            context["placeholder"] = props.hint_text
        if hasattr(props, "required"):
            context["required"] = props.required
        if hasattr(props, "read_only"):
            context["readonly"] = props.read_only
        if hasattr(props, "visible"):
            context["visible"] = props.visible
        if hasattr(props, "enabled"):
            context["disabled"] = not props.enabled

        # Type-specific context
        if type_name == "Edit":
            context["input_type"] = self._detect_input_type(control, props)
        elif type_name == "Button":
            context["button_type"] = self._detect_button_type(control)
            context["style"] = self._detect_button_style(control)
        elif type_name == "ComboBox":
            context["options"] = []  # TODO: Extract from data binding
            context["placeholder"] = "Selecione..."
        elif type_name == "CheckBox":
            context["switch_style"] = False
        elif type_name == "Tab":
            context["tabs"] = self._extract_tabs(control)
        elif type_name in ("Table", "TreeViewTable", "Looper"):
            context["columns"] = self._extract_table_columns(control)
            context["data_url"] = f"/api/{context['name']}"
            context["striped"] = True
            context["hover"] = True

        # Data binding
        if control.data_binding:
            binding = control.data_binding
            if binding.table_name and binding.field_name:
                context["data_binding"] = f"{binding.table_name}.{binding.field_name}"
                context["value"] = "{{ " + f"{binding.table_name.lower()}.{binding.field_name.lower()}" + " }}"

        return context

    def _get_control_type_name(self, control: Control) -> str:
        """Get the type name for a control.

        Args:
            control: Control to check

        Returns:
            Type name string
        """
        # Try to infer from control name prefix
        inferred = infer_type_name_from_prefix(control.name)
        if inferred:
            return inferred

        # Fallback to generic based on type code
        return f"Type{control.type_code}"

    def _detect_input_type(self, control: Control, props: Any) -> str:
        """Detect HTML input type for an edit control.

        Args:
            control: Edit control
            props: Control properties

        Returns:
            HTML input type
        """
        name_lower = control.name.lower()

        # Infer from control name
        if "password" in name_lower or "senha" in name_lower:
            return "password"
        if "email" in name_lower:
            return "email"
        if "phone" in name_lower or "telefone" in name_lower or "fone" in name_lower:
            return "tel"
        if "date" in name_lower or "data" in name_lower:
            return "date"
        if "url" in name_lower or "site" in name_lower:
            return "url"
        if any(x in name_lower for x in ["valor", "preco", "price", "total", "qtd", "quantidade"]):
            return "number"

        # Check properties
        if hasattr(props, "input_type") and props.input_type:
            return self.INPUT_TYPE_MAP.get(props.input_type, "text")

        return "text"

    def _detect_button_type(self, control: Control) -> str:
        """Detect button type from control name.

        Args:
            control: Button control

        Returns:
            HTML button type
        """
        name_lower = control.name.lower()

        if "submit" in name_lower or "salvar" in name_lower or "save" in name_lower:
            return "submit"
        if "reset" in name_lower or "limpar" in name_lower or "clear" in name_lower:
            return "reset"

        return "button"

    def _detect_button_style(self, control: Control) -> str:
        """Detect Bootstrap button style from control name.

        Args:
            control: Button control

        Returns:
            Bootstrap button style
        """
        name_lower = control.name.lower()

        if any(x in name_lower for x in ["delete", "excluir", "remover", "cancel", "cancelar"]):
            return "danger"
        if any(x in name_lower for x in ["save", "salvar", "submit", "confirmar", "confirm"]):
            return "primary"
        if any(x in name_lower for x in ["add", "novo", "new", "criar", "create"]):
            return "success"
        if any(x in name_lower for x in ["edit", "editar", "alterar", "update"]):
            return "warning"
        if any(x in name_lower for x in ["back", "voltar", "return", "cancel"]):
            return "secondary"

        return "primary"

    def _extract_label(self, control: Control) -> str:
        """Extract label text from control.

        Args:
            control: Control to extract label from

        Returns:
            Label text
        """
        # Try caption property
        if control.properties and hasattr(control.properties, "caption"):
            if control.properties.caption:
                return control.properties.caption

        # Generate from name
        name = control.name
        for prefix in PREFIX_TO_TYPE_NAME.keys():
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # Convert to title case with spaces
        snake = self._to_snake_case(name)
        return snake.replace("_", " ").title()

    def _extract_tabs(self, control: Control) -> list[dict[str, Any]]:
        """Extract tab information from a tab control.

        Args:
            control: Tab control

        Returns:
            List of tab dicts
        """
        # TODO: Extract from control properties/children
        return [
            {"id": "tab1", "label": "Tab 1", "content": "", "active": True},
        ]

    def _extract_table_columns(self, control: Control) -> list[dict[str, Any]]:
        """Extract column definitions from a table control.

        Args:
            control: Table control

        Returns:
            List of column dicts
        """
        # TODO: Extract from control properties/data binding
        return [
            {"name": "id", "label": "ID", "sortable": True, "width": "80px"},
            {"name": "name", "label": "Nome", "sortable": True},
            {"name": "created_at", "label": "Criado em", "sortable": True},
        ]

    def _generate_form_content(
        self, control_tree: list[dict[str, Any]]
    ) -> str:
        """Generate form content from control tree.

        Args:
            control_tree: Hierarchical control tree

        Returns:
            HTML string for form content
        """
        lines = ['<form class="needs-validation" novalidate>']
        lines.append(self._render_control_tree(control_tree))
        lines.append('    <div class="d-flex justify-content-end gap-2 mt-4">')
        lines.append('        <button type="button" class="btn btn-secondary">Cancelar</button>')
        lines.append('        <button type="submit" class="btn btn-primary">Salvar</button>')
        lines.append('    </div>')
        lines.append('</form>')
        return "\n".join(lines)

    def _generate_list_content(
        self, control_tree: list[dict[str, Any]]
    ) -> str:
        """Generate list content from control tree.

        Args:
            control_tree: Hierarchical control tree

        Returns:
            HTML string for list content
        """
        lines = ['<div class="table-toolbar mb-3">']
        lines.append('    <div class="d-flex justify-content-between">')
        lines.append('        <div class="search-box">')
        lines.append('            <input type="search" class="form-control" placeholder="Buscar...">')
        lines.append('        </div>')
        lines.append('        <button class="btn btn-primary">Novo</button>')
        lines.append('    </div>')
        lines.append('</div>')
        lines.append(self._render_control_tree(control_tree))
        return "\n".join(lines)

    def _generate_dashboard_content(
        self, control_tree: list[dict[str, Any]]
    ) -> str:
        """Generate dashboard content from control tree.

        Args:
            control_tree: Hierarchical control tree

        Returns:
            HTML string for dashboard content
        """
        lines = ['<div class="row g-4">']
        lines.append(self._render_control_tree(control_tree))
        lines.append('</div>')
        return "\n".join(lines)

    def _generate_simple_content(
        self, control_tree: list[dict[str, Any]]
    ) -> str:
        """Generate simple content from control tree.

        Args:
            control_tree: Hierarchical control tree

        Returns:
            HTML string for simple content
        """
        return self._render_control_tree(control_tree)

    def _render_control_tree(
        self, tree: list[dict[str, Any]], indent: int = 0
    ) -> str:
        """Recursively render control tree to HTML.

        Args:
            tree: List of control dicts with children
            indent: Current indentation level

        Returns:
            HTML string
        """
        lines = []
        prefix = "    " * indent

        for node in tree:
            html = node["html"]
            children = node["children"]

            if children:
                # Container control - wrap children
                lines.append(f"{prefix}<div class=\"control-container\">")
                lines.append(f"{prefix}    {html}")
                lines.append(self._render_control_tree(children, indent + 1))
                lines.append(f"{prefix}</div>")
            else:
                lines.append(f"{prefix}{html}")

        return "\n".join(lines)

    def _generate_base_template(self) -> None:
        """Generate base.html template.

        Copies the base template as-is (without rendering) so it remains
        a valid Jinja2 template for the generated application.
        """
        import importlib.resources

        # Read the template source directly (without rendering)
        template_source = self.jinja_env.loader.get_source(
            self.jinja_env, "base.html.j2"
        )[0]
        self.write_file("app/templates/base.html", template_source)

    def _generate_static_files(self) -> None:
        """Generate static CSS and JS files."""
        # app.css
        css_content = """/* Application styles generated by wxcode */

/* Page container styles */
.page-container {
    padding: 1rem 0;
}

/* Control styles */
.control-container {
    margin-bottom: 1rem;
}

.control-edit,
.control-combo,
.control-checkbox,
.control-radio {
    margin-bottom: 1rem;
}

.control-table {
    margin-bottom: 1.5rem;
}

.control-static {
    display: block;
    margin-bottom: 0.5rem;
}

/* Table styles */
.table-toolbar {
    margin-bottom: 1rem;
}

/* Form validation styles */
.was-validated .form-control:invalid,
.was-validated .form-select:invalid {
    border-color: #dc3545;
}

.was-validated .form-control:valid,
.was-validated .form-select:valid {
    border-color: #198754;
}

/* Card styles */
.card {
    margin-bottom: 1rem;
}

/* Modal improvements */
.modal-body {
    padding: 1.5rem;
}

/* HTMX loading indicator */
.htmx-request {
    opacity: 0.7;
}

.htmx-request .htmx-indicator {
    display: inline-block;
}

.htmx-indicator {
    display: none;
}
"""
        self.write_file("app/static/css/app.css", css_content)

        # app.js
        js_content = """// Application scripts generated by wxcode

document.addEventListener('DOMContentLoaded', function() {
    console.log('Application initialized');

    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // HTMX event handlers
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        // Show loading indicator
    });

    document.body.addEventListener('htmx:afterRequest', function(evt) {
        // Hide loading indicator
    });

    document.body.addEventListener('htmx:responseError', function(evt) {
        console.error('HTMX request failed:', evt.detail);
        // Show error notification
    });
});

// Utility functions
function showNotification(message, type = 'info') {
    const container = document.querySelector('.container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    container.insertBefore(alert, container.firstChild);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

function confirmDelete(message = 'Deseja realmente excluir?') {
    return confirm(message);
}
"""
        self.write_file("app/static/js/app.js", js_content)

    def _element_to_filename(self, source_name: str) -> str:
        """Convert element name to template filename.

        Args:
            source_name: Source name from element

        Returns:
            Snake case filename (without .html)
        """
        name = source_name
        for prefix in ["PAGE_", "PAGE", "page_", "FEN_", "WIN_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        return self._to_snake_case(name)

    def _element_to_title(self, source_name: str) -> str:
        """Convert element name to page title.

        Args:
            source_name: Source name from element

        Returns:
            Title case page title
        """
        name = source_name
        for prefix in ["PAGE_", "PAGE", "page_", "FEN_", "WIN_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        snake = self._to_snake_case(name)
        return snake.replace("_", " ").title()
