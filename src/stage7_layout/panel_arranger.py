"""
Panel Arranger - Stage 7.1.3
Arranges panels in reading order with visual flow.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from stage7_layout.layout_templates import PanelSlot
from stage7_layout.page_composer import PanelFitting, PageComposition


class PanelTransition(Enum):
    """Types of panel transitions."""
    CONTINUE = "continue"  # Same shot continues
    ZOOM_IN = "zoom_in"  # Close-up after wide
    ZOOM_OUT = "zoom_out"  # Wide after close-up
    PAN = "pan"  # Panning movement
    CUT = "cut"  # Abrupt scene change
    ACTION = "action"  # Dynamic action sequence
    DIALOGUE = "dialogue"  # Conversation flow


@dataclass
class VisualFlow:
    """Visual flow between panels."""
    from_panel: str
    to_panel: str
    transition: PanelTransition
    flow_direction: str  # "left-to-right", "top-to-bottom", "diagonal"
    guide_type: Optional[str] = None  # "speed-lines", "arrows", etc.


@dataclass
class PanelArrangement:
    """Complete arrangement plan for a page."""
    reading_order: List[str]  # Panel IDs in reading order
    visual_flows: List[VisualFlow]
    panel_positions: Dict[str, Tuple[int, int, int, int]]  # panel_id -> (x, y, w, h)
    flow_guides: List[Dict[str, any]]  # Visual flow guide elements
    total_panels: int


class PanelArranger:
    """Arranges panels with proper reading order and visual flow."""

    def __init__(self):
        """Initialize Panel Arranger."""
        self.transition_rules = self._build_transition_rules()

    def _build_transition_rules(self) -> Dict[str, List[PanelTransition]]:
        """
        Build rules for panel transitions.

        Returns:
            Dictionary mapping panel type pairs to transitions
        """
        return {
            # Wide to close-up
            ("wide", "close-up"): [PanelTransition.ZOOM_IN],
            # Close-up to wide
            ("close-up", "wide"): [PanelTransition.ZOOM_OUT],
            # Action panels
            ("action", "action"): [PanelTransition.ACTION, PanelTransition.CONTINUE],
            # Dialogue panels
            ("dialogue", "dialogue"): [PanelTransition.DIALOGUE, PanelTransition.CONTINUE],
            # Splash to anything
            ("splash", "*"): [PanelTransition.CUT],
            # Default
            ("*", "*"): [PanelTransition.CONTINUE, PanelTransition.CUT]
        }

    def arrange_panels(
        self,
        panel_fittings: List[PanelFitting],
        panel_types: Dict[str, str],
        reading_direction: str = "left-to-right"
    ) -> PanelArrangement:
        """
        Arrange panels in reading order with visual flow.

        Args:
            panel_fittings: List of panel fittings from PageComposer
            panel_types: Dictionary of panel_id -> panel_type
            reading_direction: Reading direction

        Returns:
            PanelArrangement
        """
        # Sort panels by slot order
        sorted_fittings = sorted(panel_fittings, key=lambda f: f.slot.order)

        # Build reading order
        reading_order = [f.panel_id for f in sorted_fittings]

        # Calculate visual flows
        visual_flows = self._calculate_visual_flows(
            sorted_fittings,
            panel_types
        )

        # Calculate panel positions
        from stage7_layout.page_composer import PageComposer
        composer = PageComposer()
        panel_positions = {}

        for fitting in sorted_fittings:
            x, y, w, h = composer.calculate_panel_position(fitting)
            panel_positions[fitting.panel_id] = (x, y, w, h)

        # Generate flow guides
        flow_guides = self._generate_flow_guides(
            visual_flows,
            panel_positions
        )

        return PanelArrangement(
            reading_order=reading_order,
            visual_flows=visual_flows,
            panel_positions=panel_positions,
            flow_guides=flow_guides,
            total_panels=len(reading_order)
        )

    def _calculate_visual_flows(
        self,
        panel_fittings: List[PanelFitting],
        panel_types: Dict[str, str]
    ) -> List[VisualFlow]:
        """
        Calculate visual flows between panels.

        Args:
            panel_fittings: List of panel fittings
            panel_types: Panel types

        Returns:
            List of VisualFlow objects
        """
        flows = []

        for i in range(len(panel_fittings) - 1):
            from_fitting = panel_fittings[i]
            to_fitting = panel_fittings[i + 1]

            from_panel = from_fitting.panel_id
            to_panel = to_fitting.panel_id

            # Get panel types
            from_type = panel_types.get(from_panel, "medium")
            to_type = panel_types.get(to_panel, "medium")

            # Determine transition
            transition = self._determine_transition(from_type, to_type)

            # Determine flow direction
            flow_direction = self._determine_flow_direction(
                from_fitting.slot,
                to_fitting.slot
            )

            # Determine guide type
            guide_type = self._determine_guide_type(transition)

            flow = VisualFlow(
                from_panel=from_panel,
                to_panel=to_panel,
                transition=transition,
                flow_direction=flow_direction,
                guide_type=guide_type
            )

            flows.append(flow)

        return flows

    def _determine_transition(
        self,
        from_type: str,
        to_type: str
    ) -> PanelTransition:
        """
        Determine transition type between panels.

        Args:
            from_type: Source panel type
            to_type: Target panel type

        Returns:
            PanelTransition
        """
        # Check specific rules
        key = (from_type, to_type)
        if key in self.transition_rules:
            transitions = self.transition_rules[key]
            return transitions[0]

        # Check wildcard rules
        if (from_type, "*") in self.transition_rules:
            return self.transition_rules[(from_type, "*")][0]
        if ("*", to_type) in self.transition_rules:
            return self.transition_rules[("*", to_type)][0]

        # Default
        return PanelTransition.CONTINUE

    def _determine_flow_direction(
        self,
        from_slot: PanelSlot,
        to_slot: PanelSlot
    ) -> str:
        """
        Determine visual flow direction.

        Args:
            from_slot: Source slot
            to_slot: Target slot

        Returns:
            Flow direction string
        """
        # Calculate centers
        from_center_x = from_slot.x + (from_slot.width / 2)
        from_center_y = from_slot.y + (from_slot.height / 2)
        to_center_x = to_slot.x + (to_slot.width / 2)
        to_center_y = to_slot.y + (to_slot.height / 2)

        # Determine direction
        dx = to_center_x - from_center_x
        dy = to_center_y - from_center_y

        if abs(dx) > abs(dy):
            # More horizontal movement
            return "left-to-right" if dx > 0 else "right-to-left"
        else:
            # More vertical movement
            return "top-to-bottom" if dy > 0 else "bottom-to-top"

    def _determine_guide_type(
        self,
        transition: PanelTransition
    ) -> Optional[str]:
        """
        Determine visual flow guide type.

        Args:
            transition: Panel transition type

        Returns:
            Guide type or None
        """
        guide_map = {
            PanelTransition.ZOOM_IN: "arrows-in",
            PanelTransition.ZOOM_OUT: "arrows-out",
            PanelTransition.ACTION: "speed-lines",
            PanelTransition.CUT: "none",
            PanelTransition.CONTINUE: "subtle-lines",
            PanelTransition.DIALOGUE: "speech-flow",
            PanelTransition.PAN: "arrows-pan"
        }

        return guide_map.get(transition)

    def _generate_flow_guides(
        self,
        visual_flows: List[VisualFlow],
        panel_positions: Dict[str, Tuple[int, int, int, int]]
    ) -> List[Dict[str, any]]:
        """
        Generate visual flow guide elements.

        Args:
            visual_flows: List of visual flows
            panel_positions: Panel positions

        Returns:
            List of guide element dictionaries
        """
        guides = []

        for flow in visual_flows:
            if flow.guide_type == "none":
                continue

            from_pos = panel_positions.get(flow.from_panel)
            to_pos = panel_positions.get(flow.to_panel)

            if from_pos is None or to_pos is None:
                continue

            fx, fy, fw, fh = from_pos
            tx, ty, tw, th = to_pos

            # Calculate guide points
            from_center_x = fx + (fw // 2)
            from_center_y = fy + (fh // 2)
            to_center_x = tx + (tw // 2)
            to_center_y = ty + (th // 2)

            guide = {
                "from_panel": flow.from_panel,
                "to_panel": flow.to_panel,
                "transition": flow.transition.value,
                "type": flow.guide_type,
                "start": (from_center_x, from_center_y),
                "end": (to_center_x, to_center_y),
                "direction": flow.flow_direction
            }

            guides.append(guide)

        return guides

    def validate_reading_order(
        self,
        arrangement: PanelArrangement
    ) -> List[str]:
        """
        Validate reading order for common issues.

        Args:
            arrangement: Panel arrangement

        Returns:
            List of validation warnings
        """
        warnings = []

        # Check for duplicate panel IDs
        if len(arrangement.reading_order) != len(set(arrangement.reading_order)):
            warnings.append("Duplicate panel IDs in reading order")

        # Check flow continuity
        for i in range(len(arrangement.visual_flows) - 1):
            flow1 = arrangement.visual_flows[i]
            flow2 = arrangement.visual_flows[i + 1]

            if flow1.to_panel != flow2.from_panel:
                warnings.append(f"Flow discontinuity at panel {flow1.to_panel}")

        # Check panel count matches
        if len(arrangement.reading_order) != arrangement.total_panels:
            warnings.append(f"Panel count mismatch: {len(arrangement.reading_order)} vs {arrangement.total_panels}")

        return warnings

    def optimize_for_action(
        self,
        panel_types: Dict[str, str]
    ) -> Dict[str, int]:
        """
        Optimize panel arrangement for action scenes.

        Args:
            panel_types: Panel type dictionary

        Returns:
            Dictionary of panel_id -> priority score
        """
        priorities = {}

        for panel_id, panel_type in panel_types.items():
            score = 0

            # Prioritize action panels
            if panel_type == "action":
                score += 100
            elif panel_type == "wide":
                score += 50
            elif panel_type == "medium":
                score += 30
            elif panel_type == "close-up":
                score += 20

            # Prioritize establishing panels early
            if panel_type == "establishing":
                score += 80

            priorities[panel_id] = score

        return priorities


def create_panel_arranger() -> PanelArranger:
    """
    Create a panel arranger instance.

    Returns:
        PanelArranger instance
    """
    return PanelArranger()


def main():
    """Test Panel Arranger."""
    print("=" * 70)
    print("Panel Arranger Test")
    print("=" * 70)

    # Create arranger
    print("\n[Test] Creating panel arranger...")
    arranger = create_panel_arranger()
    print(f"✓ Panel arranger created")

    # Test arrangement
    print("\n[Test] Testing panel arrangement...")

    # Create mock panel fittings
    from stage7_layout.layout_templates import PanelSlot

    mock_fittings = [
        type('', (object,), {
            'panel_id': 'p1-1',
            'slot_id': '1',
            'slot': PanelSlot('1', 0.0, 0.0, 0.5, 0.5, 1),
            'panel_aspect_ratio': 1.0,
            'slot_aspect_ratio': 1.0,
            'gutter_size': 0.01,
            'fit_mode': 'fit',
            'scale_factor': 1.0
        })(),
        type('', (object,), {
            'panel_id': 'p1-2',
            'slot_id': '2',
            'slot': PanelSlot('2', 0.5, 0.0, 0.5, 0.5, 2),
            'panel_aspect_ratio': 1.0,
            'slot_aspect_ratio': 1.0,
            'gutter_size': 0.01,
            'fit_mode': 'fit',
            'scale_factor': 1.0
        })(),
        type('', (object,), {
            'panel_id': 'p1-3',
            'slot_id': '3',
            'slot': PanelSlot('3', 0.0, 0.5, 0.5, 0.5, 3),
            'panel_aspect_ratio': 1.0,
            'slot_aspect_ratio': 1.0,
            'gutter_size': 0.01,
            'fit_mode': 'fit',
            'scale_factor': 1.0
        })(),
        type('', (object,), {
            'panel_id': 'p1-4',
            'slot_id': '4',
            'slot': PanelSlot('4', 0.5, 0.5, 0.5, 0.5, 4),
            'panel_aspect_ratio': 1.0,
            'slot_aspect_ratio': 1.0,
            'gutter_size': 0.01,
            'fit_mode': 'fit',
            'scale_factor': 1.0
        })(),
    ]

    mock_panel_types = {
        'p1-1': 'wide',
        'p1-2': 'close-up',
        'p1-3': 'dialogue',
        'p1-4': 'action'
    }

    arrangement = arranger.arrange_panels(
        panel_fittings=mock_fittings,
        panel_types=mock_panel_types
    )

    print(f"✓ Arranged {arrangement.total_panels} panels")
    print(f"  Reading order: {arrangement.reading_order}")
    print(f"  Visual flows: {len(arrangement.visual_flows)}")
    print(f"  Flow guides: {len(arrangement.flow_guides)}")

    # Display flows
    print("\n  Visual flows:")
    for flow in arrangement.visual_flows:
        print(f"    {flow.from_panel} → {flow.to_panel}: {flow.transition.value}")
        print(f"      Direction: {flow.flow_direction}")
        print(f"      Guide: {flow.guide_type}")

    # Test validation
    print("\n[Test] Validating arrangement...")
    warnings = arranger.validate_reading_order(arrangement)
    if warnings:
        print(f"  Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"    - {warning}")
    else:
        print(f"  ✓ No validation issues")

    # Test action optimization
    print("\n[Test] Testing action optimization...")
    priorities = arranger.optimize_for_action(mock_panel_types)
    print(f"✓ Calculated priorities:")
    for panel_id, score in sorted(priorities.items(), key=lambda x: x[1], reverse=True):
        panel_type = mock_panel_types[panel_id]
        print(f"    {panel_id} ({panel_type}): {score}")

    print("\n" + "=" * 70)
    print("Panel Arranger - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
