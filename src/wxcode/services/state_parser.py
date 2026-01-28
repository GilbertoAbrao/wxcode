"""
Parser para STATE.md do GSD workflow.

Extrai informacoes estruturadas de progresso do arquivo STATE.md
para exibicao no dashboard da UI.
"""

import re
from dataclasses import dataclass


@dataclass
class GSDProgress:
    """
    Dados de progresso extraidos do STATE.md.

    Representa o estado atual do workflow GSD incluindo
    fase atual, status e porcentagem de conclusao.
    """

    current_phase: int
    total_phases: int
    phase_name: str
    plan_status: str
    status: str
    last_activity: str
    progress_percent: int
    progress_bar: str


def parse_state_md(content: str) -> GSDProgress | None:
    """
    Parseia conteudo do STATE.md em dados estruturados.

    Args:
        content: Conteudo completo do arquivo STATE.md

    Returns:
        GSDProgress com dados extraidos ou None se formato invalido
        (ex: arquivo nao contem linha "Phase:")

    Examples:
        >>> content = '''
        ... # Project State
        ...
        ... ## Current Position
        ...
        ... Phase: 2 of 4 (Sidebar & Navigation)
        ... Plan: 01 of 2
        ... Status: In progress
        ... Last activity: 2026-01-22 - Completed plan 01
        ...
        ... Progress: [████░░░░░░] 40%
        ... '''
        >>> result = parse_state_md(content)
        >>> result.current_phase
        2
        >>> result.total_phases
        4
        >>> result.phase_name
        'Sidebar & Navigation'
    """
    # Phase line: "Phase: 2 of 4 (Sidebar & Navigation)"
    phase_match = re.search(
        r"Phase:\s*(\d+)\s*of\s*(\d+)\s*\(([^)]+)\)",
        content
    )

    if not phase_match:
        # STATE.md existe mas nao tem linha Phase valida
        return None

    # Progress bar: "Progress: [████░░░░░░] 40%" or "Progress: ██░░░░░░░░ 25%"
    # Handle both bracketed and unbracketed formats
    progress_match = re.search(
        r"Progress:\s*\[?([█░]+)\]?\s*(\d+)%",
        content
    )

    # Plan line: "Plan: Not started" or "Plan: 01 of 2" or "Plan: 05 of 5 (gap closure)"
    plan_match = re.search(r"Plan:\s*(.+?)(?:\n|$)", content)

    # Status line: "Status: Ready to plan" or "Status: In progress"
    status_match = re.search(r"Status:\s*(.+?)(?:\n|$)", content)

    # Last activity: "Last activity: 2026-01-18 - Phase 1 complete"
    activity_match = re.search(r"Last activity:\s*(.+?)(?:\n|$)", content)

    return GSDProgress(
        current_phase=int(phase_match.group(1)),
        total_phases=int(phase_match.group(2)),
        phase_name=phase_match.group(3).strip(),
        plan_status=plan_match.group(1).strip() if plan_match else "Unknown",
        status=status_match.group(1).strip() if status_match else "Unknown",
        last_activity=activity_match.group(1).strip() if activity_match else "",
        progress_percent=int(progress_match.group(2)) if progress_match else 0,
        progress_bar=progress_match.group(1) if progress_match else "",
    )
