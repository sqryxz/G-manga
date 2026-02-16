"""Module 5: Script Generation

Generates panel-by-panel manga scripts from novel analysis.

Main Classes:
- ScriptOrchestrator: Entry point for script generation
- ScriptGenerator: Core generation logic
- Script: Complete manga script
- PageScript: Single page
- PanelSpec: Individual panel

Usage:
    from stage5_script import ScriptOrchestrator
    
    orchestrator = ScriptOrchestrator(llm_client=client, model='openai/gpt-4o-mini')
    script = orchestrator.generate(analysis_result, adaptation_plan, target_pages=100)
    orchestrator.save_script(script, 'output/script.json')
"""

from .schemas import (
    Script,
    PageScript,
    PanelSpec,
    PanelSize,
    CameraAngle,
    PanelTransition,
    DialogueLine,
    Caption,
    SoundEffect
)

from .script_generator import ScriptGenerator
from .script_orchestrator import ScriptOrchestrator
from .adapter import Stage5Adapter

__all__ = [
    'Script',
    'PageScript', 
    'PanelSpec',
    'PanelSize',
    'CameraAngle',
    'PanelTransition',
    'DialogueLine',
    'Caption',
    'SoundEffect',
    'ScriptGenerator',
    'ScriptOrchestrator',
    'Stage5Adapter'
]
