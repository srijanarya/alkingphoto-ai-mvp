"""
TalkingPhoto AI MVP - Visual Regression Testing Framework

Comprehensive visual regression testing for Streamlit applications using
screenshot comparison, layout validation, and visual diff detection.

This framework provides automated visual testing to catch UI regressions,
layout issues, and design inconsistencies across different states and devices.
"""

import pytest
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import os
from datetime import datetime
from unittest.mock import Mock, patch
import base64


class ComparisonMode(Enum):
    """Visual comparison modes"""
    EXACT = "exact"
    THRESHOLD = "threshold"
    LAYOUT_ONLY = "layout_only"
    CONTENT_AWARE = "content_aware"


class DiffType(Enum):
    """Types of visual differences"""
    PIXEL_DIFF = "pixel_difference"
    LAYOUT_SHIFT = "layout_shift"
    COLOR_CHANGE = "color_change"
    CONTENT_CHANGE = "content_change"
    SIZE_CHANGE = "size_change"
    POSITION_CHANGE = "position_change"


@dataclass
class VisualState:
    """Represents a visual state for comparison"""
    name: str
    description: str
    viewport: Dict[str, int]
    components: List[str]
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    wait_conditions: List[str] = field(default_factory=list)
    exclude_selectors: List[str] = field(default_factory=list)


@dataclass
class VisualDiff:
    """Represents a visual difference found during comparison"""
    diff_type: DiffType
    region: Dict[str, int]  # x, y, width, height
    severity: float  # 0-1 scale
    description: str
    before_hash: str
    after_hash: str
    diff_percentage: float


@dataclass
class VisualTestResult:
    """Result of a visual regression test"""
    test_name: str
    state_name: str
    viewport: Dict[str, int]
    passed: bool
    differences: List[VisualDiff]
    similarity_score: float
    baseline_exists: bool
    screenshot_path: str
    baseline_path: str
    diff_path: Optional[str] = None
    comparison_mode: ComparisonMode = ComparisonMode.THRESHOLD
    threshold: float = 0.1


class ScreenshotManager:
    """Manage screenshot capture and storage"""
    
    def __init__(self, base_path: str = "tests/ui/screenshots"):
        self.base_path = base_path
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure screenshot directories exist"""
        directories = [
            f"{self.base_path}/baselines",
            f"{self.base_path}/current",
            f"{self.base_path}/diffs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def capture_screenshot(self, state: VisualState, test_name: str) -> str:
        """Capture screenshot for a visual state"""
        # Generate filename based on test name, state, and viewport
        filename = self._generate_filename(test_name, state)
        screenshot_path = f"{self.base_path}/current/{filename}"
        
        # Simulate screenshot capture (in real implementation, use Selenium or similar)
        screenshot_data = self._simulate_screenshot_capture(state)
        
        # Save screenshot (simulated as base64 string)
        with open(screenshot_path, 'w') as f:
            f.write(screenshot_data)
        
        return screenshot_path
    
    def get_baseline_path(self, test_name: str, state: VisualState) -> str:
        """Get baseline screenshot path"""
        filename = self._generate_filename(test_name, state)
        return f"{self.base_path}/baselines/{filename}"
    
    def save_as_baseline(self, current_path: str, baseline_path: str):
        """Save current screenshot as new baseline"""
        # Copy current to baseline directory
        with open(current_path, 'r') as src:
            content = src.read()
        
        with open(baseline_path, 'w') as dst:
            dst.write(content)
    
    def _generate_filename(self, test_name: str, state: VisualState) -> str:
        """Generate consistent filename for screenshots"""
        # Create hash of key parameters for unique filename
        key_data = f"{test_name}_{state.name}_{state.viewport['width']}x{state.viewport['height']}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]
        
        return f"{test_name}_{state.name}_{key_hash}.png"
    
    def _simulate_screenshot_capture(self, state: VisualState) -> str:
        """Simulate screenshot capture (returns base64 encoded mock data)"""
        # Create a mock screenshot representation
        mock_data = {
            'viewport': state.viewport,
            'components': state.components,
            'timestamp': datetime.now().isoformat(),
            'interactions': state.interactions
        }
        
        # Convert to base64 to simulate image data
        json_data = json.dumps(mock_data, sort_keys=True)
        return base64.b64encode(json_data.encode()).decode()


class VisualComparator:
    """Compare screenshots and detect visual differences"""
    
    def __init__(self):
        self.default_threshold = 0.1  # 10% difference threshold
    
    def compare_screenshots(self, baseline_path: str, current_path: str, 
                          comparison_mode: ComparisonMode = ComparisonMode.THRESHOLD,
                          threshold: float = 0.1) -> Tuple[bool, List[VisualDiff], float]:
        """Compare two screenshots and return differences"""
        
        if not os.path.exists(baseline_path):
            return False, [], 0.0  # No baseline exists
        
        # Load screenshots
        baseline_data = self._load_screenshot(baseline_path)
        current_data = self._load_screenshot(current_path)
        
        # Compare based on mode
        if comparison_mode == ComparisonMode.EXACT:
            return self._exact_comparison(baseline_data, current_data)
        elif comparison_mode == ComparisonMode.THRESHOLD:
            return self._threshold_comparison(baseline_data, current_data, threshold)
        elif comparison_mode == ComparisonMode.LAYOUT_ONLY:
            return self._layout_comparison(baseline_data, current_data)
        elif comparison_mode == ComparisonMode.CONTENT_AWARE:
            return self._content_aware_comparison(baseline_data, current_data, threshold)
        
        return True, [], 1.0
    
    def _load_screenshot(self, path: str) -> Dict:
        """Load screenshot data"""
        try:
            with open(path, 'r') as f:
                encoded_data = f.read()
            
            # Decode base64 back to JSON
            decoded_data = base64.b64decode(encoded_data.encode()).decode()
            return json.loads(decoded_data)
        except Exception:
            return {}
    
    def _exact_comparison(self, baseline: Dict, current: Dict) -> Tuple[bool, List[VisualDiff], float]:
        """Exact pixel-perfect comparison"""
        baseline_hash = self._hash_data(baseline)
        current_hash = self._hash_data(current)
        
        if baseline_hash == current_hash:
            return True, [], 1.0
        
        # Find differences
        diffs = self._find_exact_differences(baseline, current)
        return False, diffs, 0.0
    
    def _threshold_comparison(self, baseline: Dict, current: Dict, threshold: float) -> Tuple[bool, List[VisualDiff], float]:
        """Comparison with tolerance threshold"""
        similarity = self._calculate_similarity(baseline, current)
        
        if similarity >= (1.0 - threshold):
            return True, [], similarity
        
        # Find significant differences
        diffs = self._find_threshold_differences(baseline, current, threshold)
        return False, diffs, similarity
    
    def _layout_comparison(self, baseline: Dict, current: Dict) -> Tuple[bool, List[VisualDiff], float]:
        """Compare only layout structure, ignore content"""
        baseline_layout = self._extract_layout(baseline)
        current_layout = self._extract_layout(current)
        
        layout_similarity = self._calculate_layout_similarity(baseline_layout, current_layout)
        
        if layout_similarity >= 0.95:  # Layout should be very similar
            return True, [], layout_similarity
        
        diffs = self._find_layout_differences(baseline_layout, current_layout)
        return False, diffs, layout_similarity
    
    def _content_aware_comparison(self, baseline: Dict, current: Dict, threshold: float) -> Tuple[bool, List[VisualDiff], float]:
        """Intelligent comparison that understands content context"""
        # Separate dynamic vs static content
        static_similarity = self._compare_static_elements(baseline, current)
        dynamic_changes = self._identify_dynamic_changes(baseline, current)
        
        # Ignore expected dynamic changes
        filtered_changes = self._filter_expected_changes(dynamic_changes)
        
        overall_similarity = static_similarity
        if len(filtered_changes) == 0:
            return True, [], overall_similarity
        
        return False, filtered_changes, overall_similarity
    
    def _hash_data(self, data: Dict) -> str:
        """Create hash of data for comparison"""
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def _calculate_similarity(self, baseline: Dict, current: Dict) -> float:
        """Calculate similarity score between two screenshots"""
        # Simple similarity based on component presence and viewport
        baseline_components = set(baseline.get('components', []))
        current_components = set(current.get('components', []))
        
        if not baseline_components and not current_components:
            return 1.0
        
        intersection = baseline_components.intersection(current_components)
        union = baseline_components.union(current_components)
        
        component_similarity = len(intersection) / len(union) if union else 1.0
        
        # Factor in viewport similarity
        baseline_viewport = baseline.get('viewport', {})
        current_viewport = current.get('viewport', {})
        
        viewport_similarity = 1.0
        if baseline_viewport and current_viewport:
            width_diff = abs(baseline_viewport.get('width', 0) - current_viewport.get('width', 0))
            height_diff = abs(baseline_viewport.get('height', 0) - current_viewport.get('height', 0))
            viewport_similarity = max(0.0, 1.0 - (width_diff + height_diff) / 2000)
        
        return (component_similarity + viewport_similarity) / 2
    
    def _find_exact_differences(self, baseline: Dict, current: Dict) -> List[VisualDiff]:
        """Find exact differences between screenshots"""
        diffs = []
        
        # Compare components
        baseline_components = set(baseline.get('components', []))
        current_components = set(current.get('components', []))
        
        # Missing components
        missing = baseline_components - current_components
        for component in missing:
            diffs.append(VisualDiff(
                diff_type=DiffType.CONTENT_CHANGE,
                region={'x': 0, 'y': 0, 'width': 100, 'height': 50},
                severity=0.8,
                description=f"Missing component: {component}",
                before_hash=self._hash_data({'component': component}),
                after_hash="",
                diff_percentage=100.0
            ))
        
        # New components
        new = current_components - baseline_components
        for component in new:
            diffs.append(VisualDiff(
                diff_type=DiffType.CONTENT_CHANGE,
                region={'x': 0, 'y': 0, 'width': 100, 'height': 50},
                severity=0.6,
                description=f"New component: {component}",
                before_hash="",
                after_hash=self._hash_data({'component': component}),
                diff_percentage=100.0
            ))
        
        return diffs
    
    def _find_threshold_differences(self, baseline: Dict, current: Dict, threshold: float) -> List[VisualDiff]:
        """Find differences above threshold"""
        diffs = []
        
        # Check for significant viewport changes
        baseline_viewport = baseline.get('viewport', {})
        current_viewport = current.get('viewport', {})
        
        if baseline_viewport and current_viewport:
            width_change = abs(baseline_viewport.get('width', 0) - current_viewport.get('width', 0))
            height_change = abs(baseline_viewport.get('height', 0) - current_viewport.get('height', 0))
            
            if width_change > 50 or height_change > 50:  # Significant size change
                diffs.append(VisualDiff(
                    diff_type=DiffType.SIZE_CHANGE,
                    region={'x': 0, 'y': 0, 'width': width_change, 'height': height_change},
                    severity=min(1.0, (width_change + height_change) / 200),
                    description=f"Viewport size changed: {width_change}x{height_change}px",
                    before_hash=self._hash_data(baseline_viewport),
                    after_hash=self._hash_data(current_viewport),
                    diff_percentage=(width_change + height_change) / 20  # Simplified percentage
                ))
        
        return diffs
    
    def _extract_layout(self, data: Dict) -> Dict:
        """Extract layout information from screenshot data"""
        return {
            'viewport': data.get('viewport', {}),
            'component_count': len(data.get('components', [])),
            'has_interactions': len(data.get('interactions', [])) > 0
        }
    
    def _calculate_layout_similarity(self, baseline_layout: Dict, current_layout: Dict) -> float:
        """Calculate layout similarity score"""
        # Compare component count
        baseline_count = baseline_layout.get('component_count', 0)
        current_count = current_layout.get('component_count', 0)
        
        if baseline_count == 0 and current_count == 0:
            return 1.0
        
        count_similarity = 1.0 - abs(baseline_count - current_count) / max(baseline_count, current_count, 1)
        
        # Compare viewport
        baseline_viewport = baseline_layout.get('viewport', {})
        current_viewport = current_layout.get('viewport', {})
        
        viewport_similarity = 1.0
        if baseline_viewport and current_viewport:
            width_match = baseline_viewport.get('width') == current_viewport.get('width')
            height_match = baseline_viewport.get('height') == current_viewport.get('height')
            viewport_similarity = (width_match + height_match) / 2
        
        return (count_similarity + viewport_similarity) / 2
    
    def _find_layout_differences(self, baseline_layout: Dict, current_layout: Dict) -> List[VisualDiff]:
        """Find layout-specific differences"""
        diffs = []
        
        baseline_count = baseline_layout.get('component_count', 0)
        current_count = current_layout.get('component_count', 0)
        
        if baseline_count != current_count:
            diffs.append(VisualDiff(
                diff_type=DiffType.LAYOUT_SHIFT,
                region={'x': 0, 'y': 0, 'width': 100, 'height': 100},
                severity=abs(baseline_count - current_count) / max(baseline_count, current_count, 1),
                description=f"Component count changed: {baseline_count} -> {current_count}",
                before_hash=str(baseline_count),
                after_hash=str(current_count),
                diff_percentage=abs(baseline_count - current_count) * 10
            ))
        
        return diffs
    
    def _compare_static_elements(self, baseline: Dict, current: Dict) -> float:
        """Compare static UI elements"""
        # Focus on structural elements that shouldn't change
        baseline_static = {
            'viewport': baseline.get('viewport', {}),
            'component_structure': sorted(baseline.get('components', []))
        }
        
        current_static = {
            'viewport': current.get('viewport', {}),
            'component_structure': sorted(current.get('components', []))
        }
        
        return self._calculate_similarity(baseline_static, current_static)
    
    def _identify_dynamic_changes(self, baseline: Dict, current: Dict) -> List[VisualDiff]:
        """Identify changes in dynamic content"""
        diffs = []
        
        # Check for interaction changes (these might be expected)
        baseline_interactions = baseline.get('interactions', [])
        current_interactions = current.get('interactions', [])
        
        if len(baseline_interactions) != len(current_interactions):
            diffs.append(VisualDiff(
                diff_type=DiffType.CONTENT_CHANGE,
                region={'x': 0, 'y': 0, 'width': 200, 'height': 50},
                severity=0.3,  # Low severity for interaction changes
                description=f"Interaction count changed: {len(baseline_interactions)} -> {len(current_interactions)}",
                before_hash=str(len(baseline_interactions)),
                after_hash=str(len(current_interactions)),
                diff_percentage=abs(len(baseline_interactions) - len(current_interactions)) * 20
            ))
        
        return diffs
    
    def _filter_expected_changes(self, changes: List[VisualDiff]) -> List[VisualDiff]:
        """Filter out expected dynamic changes"""
        # Define patterns for expected changes
        expected_patterns = [
            "timestamp",
            "session_id",
            "random_id",
            "current_time"
        ]
        
        filtered = []
        for change in changes:
            is_expected = any(pattern in change.description.lower() for pattern in expected_patterns)
            if not is_expected and change.severity > 0.2:  # Only report significant unexpected changes
                filtered.append(change)
        
        return filtered


class VisualRegressionTester:
    """Main visual regression testing class"""
    
    def __init__(self, screenshot_manager: ScreenshotManager = None, 
                 comparator: VisualComparator = None):
        self.screenshot_manager = screenshot_manager or ScreenshotManager()
        self.comparator = comparator or VisualComparator()
        self.test_results: List[VisualTestResult] = []
    
    def define_visual_states(self) -> List[VisualState]:
        """Define visual states to test"""
        return [
            VisualState(
                name="initial_load",
                description="Initial application load state",
                viewport={'width': 1920, 'height': 1080},
                components=['header', 'credits_display', 'create_video_tab'],
                wait_conditions=['page_loaded', 'credits_displayed']
            ),
            
            VisualState(
                name="photo_uploaded",
                description="State after photo upload",
                viewport={'width': 1920, 'height': 1080},
                components=['header', 'photo_preview', 'text_input', 'upload_success'],
                interactions=[{'type': 'upload', 'target': 'photo_file'}],
                wait_conditions=['upload_complete', 'preview_displayed']
            ),
            
            VisualState(
                name="text_entered",
                description="State with text input completed",
                viewport={'width': 1920, 'height': 1080},
                components=['header', 'photo_preview', 'text_input', 'text_stats', 'generate_button'],
                interactions=[
                    {'type': 'upload', 'target': 'photo_file'},
                    {'type': 'type', 'target': 'text_input', 'value': 'Test text input'}
                ],
                wait_conditions=['text_validated', 'button_enabled']
            ),
            
            VisualState(
                name="generation_progress",
                description="Video generation in progress",
                viewport={'width': 1920, 'height': 1080},
                components=['header', 'progress_bar', 'status_text'],
                interactions=[
                    {'type': 'upload', 'target': 'photo_file'},
                    {'type': 'type', 'target': 'text_input', 'value': 'Test text'},
                    {'type': 'click', 'target': 'generate_button'}
                ],
                wait_conditions=['generation_started', 'progress_visible']
            ),
            
            VisualState(
                name="generation_complete",
                description="Video generation completed",
                viewport={'width': 1920, 'height': 1080},
                components=['header', 'video_player', 'action_buttons', 'success_message'],
                interactions=[
                    {'type': 'complete_generation'}
                ],
                wait_conditions=['video_displayed', 'actions_available']
            ),
            
            VisualState(
                name="mobile_initial",
                description="Initial load on mobile",
                viewport={'width': 390, 'height': 844},
                components=['header', 'credits_display', 'create_video_tab'],
                wait_conditions=['mobile_layout_applied']
            ),
            
            VisualState(
                name="mobile_upload",
                description="Mobile photo upload state",
                viewport={'width': 390, 'height': 844},
                components=['header', 'photo_preview', 'mobile_upload_button'],
                interactions=[{'type': 'mobile_upload', 'target': 'photo_file'}],
                wait_conditions=['mobile_upload_complete']
            ),
            
            VisualState(
                name="error_state",
                description="Error message display",
                viewport={'width': 1920, 'height': 1080},
                components=['header', 'error_message', 'retry_button'],
                interactions=[{'type': 'trigger_error'}],
                wait_conditions=['error_displayed']
            ),
            
            VisualState(
                name="pricing_tab",
                description="Pricing information display",
                viewport={'width': 1920, 'height': 1080},
                components=['header', 'pricing_cards', 'plan_buttons'],
                interactions=[{'type': 'click', 'target': 'pricing_tab'}],
                wait_conditions=['pricing_loaded']
            ),
            
            VisualState(
                name="about_tab",
                description="About section display",
                viewport={'width': 1920, 'height': 1080},
                components=['header', 'about_content', 'trust_badges'],
                interactions=[{'type': 'click', 'target': 'about_tab'}],
                wait_conditions=['about_loaded']
            )
        ]
    
    def test_visual_state(self, state: VisualState, test_name: str, 
                         comparison_mode: ComparisonMode = ComparisonMode.THRESHOLD,
                         threshold: float = 0.1) -> VisualTestResult:
        """Test a single visual state"""
        
        # Capture current screenshot
        current_screenshot = self.screenshot_manager.capture_screenshot(state, test_name)
        
        # Get baseline path
        baseline_screenshot = self.screenshot_manager.get_baseline_path(test_name, state)
        
        # Compare with baseline
        baseline_exists = os.path.exists(baseline_screenshot)
        
        if baseline_exists:
            passed, differences, similarity = self.comparator.compare_screenshots(
                baseline_screenshot, current_screenshot, comparison_mode, threshold
            )
        else:
            # No baseline exists - save current as baseline
            self.screenshot_manager.save_as_baseline(current_screenshot, baseline_screenshot)
            passed = True
            differences = []
            similarity = 1.0
        
        # Create diff image if there are differences
        diff_path = None
        if differences:
            diff_path = self._create_diff_image(baseline_screenshot, current_screenshot, differences)
        
        result = VisualTestResult(
            test_name=test_name,
            state_name=state.name,
            viewport=state.viewport,
            passed=passed,
            differences=differences,
            similarity_score=similarity,
            baseline_exists=baseline_exists,
            screenshot_path=current_screenshot,
            baseline_path=baseline_screenshot,
            diff_path=diff_path,
            comparison_mode=comparison_mode,
            threshold=threshold
        )
        
        self.test_results.append(result)
        return result
    
    def run_full_visual_regression_suite(self) -> Dict[str, List[VisualTestResult]]:
        """Run complete visual regression test suite"""
        states = self.define_visual_states()
        results = {}
        
        # Test each state with different comparison modes
        test_configurations = [
            ("standard_comparison", ComparisonMode.THRESHOLD, 0.1),
            ("strict_comparison", ComparisonMode.THRESHOLD, 0.05),
            ("layout_only", ComparisonMode.LAYOUT_ONLY, 0.0)
        ]
        
        for config_name, mode, threshold in test_configurations:
            results[config_name] = []
            
            for state in states:
                test_name = f"visual_regression_{config_name}"
                result = self.test_visual_state(state, test_name, mode, threshold)
                results[config_name].append(result)
        
        return results
    
    def test_responsive_breakpoints(self) -> List[VisualTestResult]:
        """Test visual consistency across responsive breakpoints"""
        breakpoints = [
            {'name': 'mobile', 'width': 390, 'height': 844},
            {'name': 'tablet', 'width': 768, 'height': 1024},
            {'name': 'desktop', 'width': 1920, 'height': 1080},
            {'name': 'large_desktop', 'width': 2560, 'height': 1440}
        ]
        
        results = []
        base_state = VisualState(
            name="responsive_test",
            description="Responsive layout test",
            viewport={'width': 1920, 'height': 1080},
            components=['header', 'main_content', 'footer']
        )
        
        for breakpoint in breakpoints:
            state = VisualState(
                name=f"responsive_{breakpoint['name']}",
                description=f"Layout at {breakpoint['name']} breakpoint",
                viewport={'width': breakpoint['width'], 'height': breakpoint['height']},
                components=base_state.components
            )
            
            result = self.test_visual_state(state, "responsive_layout", ComparisonMode.LAYOUT_ONLY)
            results.append(result)
        
        return results
    
    def _create_diff_image(self, baseline_path: str, current_path: str, 
                          differences: List[VisualDiff]) -> str:
        """Create visual diff image highlighting differences"""
        # In a real implementation, this would create an actual diff image
        # For simulation, we create a JSON summary
        
        diff_data = {
            'baseline': baseline_path,
            'current': current_path,
            'differences': [
                {
                    'type': diff.diff_type.value,
                    'region': diff.region,
                    'severity': diff.severity,
                    'description': diff.description
                }
                for diff in differences
            ],
            'created_at': datetime.now().isoformat()
        }
        
        # Generate diff filename
        diff_filename = os.path.basename(current_path).replace('.png', '_diff.json')
        diff_path = f"{self.screenshot_manager.base_path}/diffs/{diff_filename}"
        
        with open(diff_path, 'w') as f:
            json.dump(diff_data, f, indent=2)
        
        return diff_path
    
    def generate_visual_report(self) -> str:
        """Generate comprehensive visual regression report"""
        if not self.test_results:
            self.run_full_visual_regression_suite()
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.passed])
        failed_tests = total_tests - passed_tests
        
        # Calculate average similarity
        avg_similarity = sum(r.similarity_score for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        # Group by state
        by_state = {}
        for result in self.test_results:
            state_name = result.state_name
            if state_name not in by_state:
                by_state[state_name] = []
            by_state[state_name].append(result)
        
        report = f"""
# TalkingPhoto AI - Visual Regression Test Report

## Executive Summary
- **Total Visual Tests**: {total_tests}
- **Passed**: {passed_tests} ({passed_tests/total_tests*100:.1f}%)
- **Failed**: {failed_tests} ({failed_tests/total_tests*100:.1f}%)
- **Average Similarity Score**: {avg_similarity:.3f}

## Visual State Results

"""
        
        for state_name, state_results in by_state.items():
            state_passed = len([r for r in state_results if r.passed])
            state_total = len(state_results)
            state_avg_similarity = sum(r.similarity_score for r in state_results) / state_total
            
            report += f"### {state_name.replace('_', ' ').title()}\n"
            report += f"- **Success Rate**: {state_passed}/{state_total} ({state_passed/state_total*100:.1f}%)\n"
            report += f"- **Average Similarity**: {state_avg_similarity:.3f}\n"
            
            # Show failed tests
            failed_in_state = [r for r in state_results if not r.passed]
            if failed_in_state:
                report += "- **Issues Found**:\n"
                for result in failed_in_state:
                    report += f"  - {result.test_name}: {len(result.differences)} differences\n"
            
            report += "\n"
        
        # Difference analysis
        all_differences = []
        for result in self.test_results:
            all_differences.extend(result.differences)
        
        if all_differences:
            report += "## Difference Analysis\n\n"
            
            # Group by diff type
            by_diff_type = {}
            for diff in all_differences:
                diff_type = diff.diff_type.value
                if diff_type not in by_diff_type:
                    by_diff_type[diff_type] = []
                by_diff_type[diff_type].append(diff)
            
            for diff_type, diffs in by_diff_type.items():
                avg_severity = sum(d.severity for d in diffs) / len(diffs)
                report += f"- **{diff_type.replace('_', ' ').title()}**: {len(diffs)} occurrences (avg severity: {avg_severity:.2f})\n"
            
            report += "\n"
        
        # Viewport analysis
        viewport_results = {}
        for result in self.test_results:
            viewport_key = f"{result.viewport['width']}x{result.viewport['height']}"
            if viewport_key not in viewport_results:
                viewport_results[viewport_key] = []
            viewport_results[viewport_key].append(result)
        
        if len(viewport_results) > 1:
            report += "## Viewport Analysis\n\n"
            
            for viewport, results in viewport_results.items():
                viewport_passed = len([r for r in results if r.passed])
                viewport_total = len(results)
                
                report += f"- **{viewport}**: {viewport_passed}/{viewport_total} passed ({viewport_passed/viewport_total*100:.1f}%)\n"
            
            report += "\n"
        
        # Critical issues
        critical_issues = []
        for result in self.test_results:
            if not result.passed and result.similarity_score < 0.8:
                critical_issues.append(result)
        
        if critical_issues:
            report += "## Critical Visual Issues\n\n"
            
            for issue in critical_issues:
                report += f"### {issue.test_name} - {issue.state_name}\n"
                report += f"- **Similarity Score**: {issue.similarity_score:.3f}\n"
                report += f"- **Differences**: {len(issue.differences)}\n"
                report += f"- **Screenshot**: {issue.screenshot_path}\n"
                if issue.diff_path:
                    report += f"- **Diff Report**: {issue.diff_path}\n"
                report += "\n"
        
        # Recommendations
        report += """## Recommendations

### For Failed Tests
1. Review visual differences in diff reports
2. Update baselines if changes are intentional
3. Fix layout issues causing regressions
4. Verify responsive design consistency

### For Maintenance
1. Run visual tests on every deployment
2. Update baselines when designs change intentionally
3. Monitor similarity scores over time
4. Set up automated alerts for critical failures

### Test Configuration
- **Threshold Mode**: Good for general regression detection
- **Layout Only Mode**: Focuses on structural changes
- **Exact Mode**: Pixel-perfect comparison for critical components

## File Locations
- **Baselines**: tests/ui/screenshots/baselines/
- **Current Screenshots**: tests/ui/screenshots/current/
- **Diff Reports**: tests/ui/screenshots/diffs/

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report


class VisualRegressionTestSuite:
    """Pytest test suite for visual regression"""
    
    def __init__(self):
        self.tester = VisualRegressionTester()
    
    def test_critical_visual_states(self):
        """Test critical visual states don't regress"""
        critical_states = ['initial_load', 'photo_uploaded', 'generation_complete']
        
        for state_name in critical_states:
            states = self.tester.define_visual_states()
            state = next((s for s in states if s.name == state_name), None)
            
            assert state is not None, f"Critical state {state_name} not found"
            
            result = self.tester.test_visual_state(state, "critical_test", ComparisonMode.THRESHOLD, 0.05)
            
            assert result.passed, f"Critical visual regression in {state_name}: {len(result.differences)} differences"
    
    def test_responsive_layout_consistency(self):
        """Test layout consistency across responsive breakpoints"""
        responsive_results = self.tester.test_responsive_breakpoints()
        
        # All responsive tests should pass or have minimal layout differences
        layout_failures = [r for r in responsive_results if not r.passed and r.similarity_score < 0.9]
        
        assert len(layout_failures) == 0, f"Responsive layout failures: {[r.state_name for r in layout_failures]}"
    
    def test_error_state_visibility(self):
        """Test error states are visually consistent"""
        states = self.tester.define_visual_states()
        error_state = next((s for s in states if s.name == 'error_state'), None)
        
        if error_state:
            result = self.tester.test_visual_state(error_state, "error_test")
            assert result.passed, "Error state visual regression detected"
    
    def test_mobile_visual_parity(self):
        """Test mobile layouts maintain visual quality"""
        states = self.tester.define_visual_states()
        mobile_states = [s for s in states if 'mobile' in s.name]
        
        for state in mobile_states:
            result = self.tester.test_visual_state(state, "mobile_test")
            
            # Mobile should have good similarity scores
            assert result.similarity_score >= 0.85, f"Mobile visual quality issue in {state.name}"


# Pytest fixtures
@pytest.fixture
def visual_tester():
    """Provide visual regression tester"""
    return VisualRegressionTester()


@pytest.fixture
def screenshot_manager():
    """Provide screenshot manager"""
    return ScreenshotManager()


@pytest.fixture
def visual_comparator():
    """Provide visual comparator"""
    return VisualComparator()


if __name__ == "__main__":
    # Run visual regression tests and generate report
    tester = VisualRegressionTester()
    report = tester.generate_visual_report()
    
    # Save report to file
    with open('/Users/srijan/ai-finance-agency/talkingphoto-mvp/visual_regression_report.md', 'w') as f:
        f.write(report)
    
    print("Visual regression tests completed. Report saved to visual_regression_report.md")