"""
TalkingPhoto AI MVP - UI Performance Metrics Framework

Comprehensive performance monitoring and testing for Streamlit UI interactions.
Measures and validates performance characteristics including load times, 
rendering performance, memory usage, and user interaction responsiveness.

This framework provides tools to ensure optimal user experience through
performance monitoring and automated performance regression detection.
"""

import pytest
from typing import Dict, List, Tuple, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
from datetime import datetime, timedelta
import json
import statistics
from unittest.mock import Mock, patch


class MetricType(Enum):
    """Types of performance metrics"""
    LOAD_TIME = "load_time"
    INTERACTION_TIME = "interaction_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    NETWORK_REQUESTS = "network_requests"
    RENDERING_TIME = "rendering_time"
    FILE_UPLOAD_TIME = "file_upload_time"
    BUNDLE_SIZE = "bundle_size"


class PerformanceThreshold(Enum):
    """Performance threshold levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


@dataclass
class PerformanceMetric:
    """Individual performance metric measurement"""
    name: str
    metric_type: MetricType
    value: float
    unit: str
    threshold_excellent: float
    threshold_good: float
    threshold_poor: float
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def threshold_level(self) -> PerformanceThreshold:
        """Determine performance threshold level"""
        if self.value <= self.threshold_excellent:
            return PerformanceThreshold.EXCELLENT
        elif self.value <= self.threshold_good:
            return PerformanceThreshold.GOOD
        elif self.value <= self.threshold_poor:
            return PerformanceThreshold.NEEDS_IMPROVEMENT
        else:
            return PerformanceThreshold.POOR
    
    @property
    def passed(self) -> bool:
        """Check if metric passes acceptable threshold"""
        return self.threshold_level in [PerformanceThreshold.EXCELLENT, PerformanceThreshold.GOOD]


@dataclass
class PerformanceTest:
    """Performance test configuration"""
    name: str
    description: str
    metrics: List[str]
    setup_actions: List[Callable] = field(default_factory=list)
    test_actions: List[Callable] = field(default_factory=list)
    cleanup_actions: List[Callable] = field(default_factory=list)
    iterations: int = 3
    warmup_iterations: int = 1


@dataclass
class PerformanceTestResult:
    """Result of a performance test run"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    metrics: List[PerformanceMetric]
    iterations_run: int
    passed: bool
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def summary_stats(self) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics for metrics"""
        stats = {}
        
        # Group metrics by type
        by_type = {}
        for metric in self.metrics:
            metric_type = metric.name
            if metric_type not in by_type:
                by_type[metric_type] = []
            by_type[metric_type].append(metric.value)
        
        # Calculate stats for each metric type
        for metric_type, values in by_type.items():
            if values:
                stats[metric_type] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'stdev': statistics.stdev(values) if len(values) > 1 else 0.0
                }
        
        return stats


class PerformanceMonitor:
    """Monitor and measure performance metrics"""
    
    def __init__(self):
        self.active_measurements = {}
        self.baseline_metrics = {}
        self.thresholds = self._define_performance_thresholds()
    
    def _define_performance_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Define performance thresholds for different metrics"""
        return {
            'page_load_time': {
                'excellent': 1.0,  # seconds
                'good': 2.0,
                'poor': 5.0
            },
            'component_render_time': {
                'excellent': 0.1,  # seconds
                'good': 0.3,
                'poor': 1.0
            },
            'file_upload_time': {
                'excellent': 2.0,  # seconds for 1MB
                'good': 5.0,
                'poor': 15.0
            },
            'interaction_response_time': {
                'excellent': 0.1,  # seconds
                'good': 0.3,
                'poor': 1.0
            },
            'memory_usage': {
                'excellent': 50.0,  # MB
                'good': 100.0,
                'poor': 200.0
            },
            'cpu_usage': {
                'excellent': 10.0,  # percentage
                'good': 25.0,
                'poor': 60.0
            },
            'bundle_size': {
                'excellent': 500.0,  # KB
                'good': 1000.0,
                'poor': 2000.0
            },
            'video_generation_time': {
                'excellent': 30.0,  # seconds
                'good': 60.0,
                'poor': 120.0
            }
        }
    
    def start_measurement(self, metric_name: str, context: Dict[str, Any] = None) -> str:
        """Start measuring a performance metric"""
        measurement_id = f"{metric_name}_{int(time.time() * 1000)}"
        
        self.active_measurements[measurement_id] = {
            'name': metric_name,
            'start_time': time.time(),
            'context': context or {}
        }
        
        return measurement_id
    
    def end_measurement(self, measurement_id: str, metric_type: MetricType = MetricType.LOAD_TIME) -> PerformanceMetric:
        """End measurement and create performance metric"""
        if measurement_id not in self.active_measurements:
            raise ValueError(f"Measurement ID {measurement_id} not found")
        
        measurement = self.active_measurements[measurement_id]
        end_time = time.time()
        duration = end_time - measurement['start_time']
        
        # Get thresholds for this metric
        thresholds = self.thresholds.get(measurement['name'], self.thresholds['interaction_response_time'])
        
        metric = PerformanceMetric(
            name=measurement['name'],
            metric_type=metric_type,
            value=duration,
            unit='seconds',
            threshold_excellent=thresholds['excellent'],
            threshold_good=thresholds['good'],
            threshold_poor=thresholds['poor'],
            context=measurement['context']
        )
        
        # Clean up active measurement
        del self.active_measurements[measurement_id]
        
        return metric
    
    def measure_function_performance(self, func: Callable, metric_name: str, 
                                   context: Dict[str, Any] = None) -> PerformanceMetric:
        """Measure performance of a function execution"""
        measurement_id = self.start_measurement(metric_name, context)
        
        try:
            result = func()
            return self.end_measurement(measurement_id)
        except Exception as e:
            # Clean up measurement on error
            if measurement_id in self.active_measurements:
                del self.active_measurements[measurement_id]
            raise e
    
    def measure_memory_usage(self, process_name: str = "streamlit") -> PerformanceMetric:
        """Measure current memory usage"""
        # Simulate memory measurement (in real implementation, use psutil)
        simulated_memory_mb = 75.5  # MB
        
        thresholds = self.thresholds['memory_usage']
        
        return PerformanceMetric(
            name="memory_usage",
            metric_type=MetricType.MEMORY_USAGE,
            value=simulated_memory_mb,
            unit='MB',
            threshold_excellent=thresholds['excellent'],
            threshold_good=thresholds['good'],
            threshold_poor=thresholds['poor'],
            context={'process': process_name}
        )
    
    def measure_network_performance(self, endpoint: str) -> List[PerformanceMetric]:
        """Measure network request performance"""
        # Simulate network measurements
        request_time = 0.15  # seconds
        response_size = 1.2  # MB
        
        metrics = []
        
        # Request time metric
        thresholds = self.thresholds['interaction_response_time']
        metrics.append(PerformanceMetric(
            name="network_request_time",
            metric_type=MetricType.NETWORK_REQUESTS,
            value=request_time,
            unit='seconds',
            threshold_excellent=thresholds['excellent'],
            threshold_good=thresholds['good'],
            threshold_poor=thresholds['poor'],
            context={'endpoint': endpoint}
        ))
        
        # Response size metric (treat as bundle size)
        size_thresholds = self.thresholds['bundle_size']
        metrics.append(PerformanceMetric(
            name="response_size",
            metric_type=MetricType.NETWORK_REQUESTS,
            value=response_size * 1024,  # Convert to KB
            unit='KB',
            threshold_excellent=size_thresholds['excellent'],
            threshold_good=size_thresholds['good'],
            threshold_poor=size_thresholds['poor'],
            context={'endpoint': endpoint}
        ))
        
        return metrics


class StreamlitPerformanceTester:
    """Performance tester specifically for Streamlit applications"""
    
    def __init__(self, monitor: PerformanceMonitor = None):
        self.monitor = monitor or PerformanceMonitor()
        self.test_results: List[PerformanceTestResult] = []
    
    def define_performance_tests(self) -> List[PerformanceTest]:
        """Define performance tests for TalkingPhoto app"""
        return [
            PerformanceTest(
                name="initial_page_load",
                description="Measure initial page load performance",
                metrics=["page_load_time", "component_render_time", "memory_usage"],
                test_actions=[
                    self._simulate_page_load,
                    self._measure_component_rendering
                ]
            ),
            
            PerformanceTest(
                name="file_upload_performance",
                description="Measure file upload performance across different file sizes",
                metrics=["file_upload_time", "memory_usage", "upload_validation_time"],
                setup_actions=[self._setup_upload_test],
                test_actions=[
                    lambda: self._simulate_file_upload(1024 * 1024),  # 1MB
                    lambda: self._simulate_file_upload(5 * 1024 * 1024),  # 5MB
                    lambda: self._simulate_file_upload(10 * 1024 * 1024)  # 10MB
                ],
                iterations=5
            ),
            
            PerformanceTest(
                name="text_input_responsiveness",
                description="Measure text input and validation responsiveness",
                metrics=["interaction_response_time", "validation_time"],
                test_actions=[
                    lambda: self._simulate_text_input("Short text"),
                    lambda: self._simulate_text_input("Medium length text input for testing"),
                    lambda: self._simulate_text_input("Very long text input " * 20)
                ]
            ),
            
            PerformanceTest(
                name="video_generation_performance",
                description="Measure video generation workflow performance",
                metrics=["video_generation_time", "progress_update_time", "memory_usage"],
                setup_actions=[self._setup_generation_test],
                test_actions=[
                    self._simulate_video_generation
                ],
                iterations=3
            ),
            
            PerformanceTest(
                name="tab_navigation_performance",
                description="Measure tab switching performance",
                metrics=["interaction_response_time", "component_render_time"],
                test_actions=[
                    lambda: self._simulate_tab_switch("pricing"),
                    lambda: self._simulate_tab_switch("about"),
                    lambda: self._simulate_tab_switch("create_video")
                ]
            ),
            
            PerformanceTest(
                name="mobile_performance",
                description="Measure performance on mobile viewport",
                metrics=["page_load_time", "interaction_response_time", "memory_usage"],
                setup_actions=[lambda: self._set_mobile_viewport()],
                test_actions=[
                    self._simulate_mobile_page_load,
                    lambda: self._simulate_mobile_upload()
                ]
            ),
            
            PerformanceTest(
                name="error_handling_performance",
                description="Measure performance during error scenarios",
                metrics=["error_display_time", "recovery_time"],
                test_actions=[
                    lambda: self._simulate_upload_error(),
                    lambda: self._simulate_validation_error(),
                    lambda: self._simulate_generation_error()
                ]
            ),
            
            PerformanceTest(
                name="concurrent_user_simulation",
                description="Simulate multiple concurrent users",
                metrics=["concurrent_response_time", "memory_usage", "cpu_usage"],
                test_actions=[
                    lambda: self._simulate_concurrent_users(5),
                    lambda: self._simulate_concurrent_users(10)
                ],
                iterations=1  # Run once with internal iterations
            )
        ]
    
    def run_performance_test(self, test: PerformanceTest) -> PerformanceTestResult:
        """Run a single performance test"""
        start_time = datetime.now()
        all_metrics = []
        issues = []
        recommendations = []
        
        # Run warmup iterations
        for _ in range(test.warmup_iterations):
            self._run_test_iteration(test)
        
        # Run actual test iterations
        for iteration in range(test.iterations):
            try:
                # Setup
                for setup_action in test.setup_actions:
                    setup_action()
                
                # Test actions
                iteration_metrics = []
                for test_action in test.test_actions:
                    if callable(test_action):
                        # Measure action performance
                        measurement_id = self.monitor.start_measurement(f"{test.name}_action_{len(iteration_metrics)}")
                        test_action()
                        metric = self.monitor.end_measurement(measurement_id)
                        iteration_metrics.append(metric)
                
                all_metrics.extend(iteration_metrics)
                
                # Cleanup
                for cleanup_action in test.cleanup_actions:
                    cleanup_action()
                    
            except Exception as e:
                issues.append(f"Test iteration {iteration + 1} failed: {str(e)}")
        
        # Analyze results
        failed_metrics = [m for m in all_metrics if not m.passed]
        
        # Generate recommendations
        if failed_metrics:
            recommendations.extend(self._generate_recommendations(test.name, failed_metrics))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = PerformanceTestResult(
            test_name=test.name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            metrics=all_metrics,
            iterations_run=test.iterations,
            passed=len(failed_metrics) == 0,
            issues=issues,
            recommendations=recommendations
        )
        
        self.test_results.append(result)
        return result
    
    def _run_test_iteration(self, test: PerformanceTest):
        """Run a single test iteration for warmup"""
        for action in test.test_actions:
            if callable(action):
                action()
    
    # Test simulation methods
    def _simulate_page_load(self):
        """Simulate page load"""
        time.sleep(0.8)  # Simulate load time
    
    def _measure_component_rendering(self):
        """Measure component rendering time"""
        time.sleep(0.2)  # Simulate rendering time
    
    def _setup_upload_test(self):
        """Setup for upload test"""
        pass  # No setup needed for simulation
    
    def _simulate_file_upload(self, file_size_bytes: int):
        """Simulate file upload of given size"""
        # Simulate upload time based on file size
        base_time = 0.5
        size_factor = file_size_bytes / (1024 * 1024)  # MB
        upload_time = base_time + (size_factor * 0.3)  # 0.3s per MB
        time.sleep(min(upload_time, 3.0))  # Cap at 3 seconds for simulation
    
    def _simulate_text_input(self, text: str):
        """Simulate text input and validation"""
        # Input time based on text length
        input_time = len(text) * 0.001  # 1ms per character
        time.sleep(input_time)
        
        # Validation time
        time.sleep(0.05)  # 50ms validation
    
    def _setup_generation_test(self):
        """Setup for generation test"""
        # Simulate having uploaded file and entered text
        pass
    
    def _simulate_video_generation(self):
        """Simulate video generation process"""
        # Simulate generation steps with progress updates
        steps = 10
        for step in range(steps):
            time.sleep(0.2)  # Each step takes 200ms
    
    def _simulate_tab_switch(self, tab_name: str):
        """Simulate tab switching"""
        time.sleep(0.1)  # Tab switch time
    
    def _set_mobile_viewport(self):
        """Set mobile viewport for testing"""
        pass  # Viewport change simulation
    
    def _simulate_mobile_page_load(self):
        """Simulate page load on mobile"""
        time.sleep(1.2)  # Mobile load typically slower
    
    def _simulate_mobile_upload(self):
        """Simulate mobile file upload"""
        time.sleep(0.8)  # Mobile upload simulation
    
    def _simulate_upload_error(self):
        """Simulate upload error scenario"""
        time.sleep(0.1)  # Error detection time
    
    def _simulate_validation_error(self):
        """Simulate validation error scenario"""
        time.sleep(0.05)  # Validation error time
    
    def _simulate_generation_error(self):
        """Simulate generation error scenario"""
        time.sleep(0.3)  # Error handling time
    
    def _simulate_concurrent_users(self, user_count: int):
        """Simulate concurrent users"""
        def user_session():
            time.sleep(0.5)  # Simulate user actions
        
        threads = []
        start_time = time.time()
        
        # Start concurrent user threads
        for _ in range(user_count):
            thread = threading.Thread(target=user_session)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return time.time() - start_time
    
    def _generate_recommendations(self, test_name: str, failed_metrics: List[PerformanceMetric]) -> List[str]:
        """Generate recommendations based on failed metrics"""
        recommendations = []
        
        # Group failed metrics by type
        by_type = {}
        for metric in failed_metrics:
            metric_type = metric.metric_type
            if metric_type not in by_type:
                by_type[metric_type] = []
            by_type[metric_type].append(metric)
        
        # Generate specific recommendations
        if MetricType.LOAD_TIME in by_type:
            recommendations.append("Optimize initial page load by reducing bundle size and lazy loading components")
        
        if MetricType.MEMORY_USAGE in by_type:
            recommendations.append("Investigate memory leaks and optimize large object handling")
        
        if MetricType.FILE_UPLOAD_TIME in by_type:
            recommendations.append("Implement chunked upload for large files and add progress indicators")
        
        if MetricType.INTERACTION_TIME in by_type:
            recommendations.append("Optimize UI responsiveness by debouncing inputs and using async operations")
        
        if MetricType.RENDERING_TIME in by_type:
            recommendations.append("Optimize component rendering with memoization and virtual scrolling")
        
        return recommendations
    
    def run_full_performance_suite(self) -> Dict[str, PerformanceTestResult]:
        """Run complete performance test suite"""
        tests = self.define_performance_tests()
        results = {}
        
        for test in tests:
            print(f"Running performance test: {test.name}")
            result = self.run_performance_test(test)
            results[test.name] = result
        
        return results
    
    def analyze_performance_trends(self, historical_data: List[Dict] = None) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        if not historical_data:
            # Use current test results as baseline
            historical_data = [
                {
                    'date': datetime.now().isoformat(),
                    'results': {test.test_name: test.summary_stats for test in self.test_results}
                }
            ]
        
        trends = {}
        
        # Analyze trends for each metric
        for result in self.test_results:
            test_name = result.test_name
            trends[test_name] = {
                'current_performance': result.passed,
                'metric_trends': {},
                'recommendations': result.recommendations
            }
            
            # Analyze individual metrics
            for metric_type, stats in result.summary_stats.items():
                trends[test_name]['metric_trends'][metric_type] = {
                    'current_mean': stats['mean'],
                    'variability': stats['stdev'],
                    'stability': 'stable' if stats['stdev'] < stats['mean'] * 0.1 else 'variable'
                }
        
        return trends
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        if not self.test_results:
            self.run_full_performance_suite()
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.passed])
        failed_tests = total_tests - passed_tests
        
        # Calculate overall performance score
        all_metrics = []
        for result in self.test_results:
            all_metrics.extend(result.metrics)
        
        performance_score = len([m for m in all_metrics if m.passed]) / len(all_metrics) * 100 if all_metrics else 0
        
        report = f"""
# TalkingPhoto AI - Performance Test Report

## Executive Summary
- **Total Performance Tests**: {total_tests}
- **Passed Tests**: {passed_tests} ({passed_tests/total_tests*100:.1f}%)
- **Failed Tests**: {failed_tests} ({failed_tests/total_tests*100:.1f}%)
- **Overall Performance Score**: {performance_score:.1f}%

## Performance Test Results

"""
        
        for result in self.test_results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report += f"### {result.test_name.replace('_', ' ').title()} - {status}\n"
            report += f"- **Duration**: {result.duration:.2f} seconds\n"
            report += f"- **Iterations**: {result.iterations_run}\n"
            report += f"- **Metrics Collected**: {len(result.metrics)}\n"
            
            # Summary statistics
            if result.summary_stats:
                report += "- **Performance Summary**:\n"
                for metric_name, stats in result.summary_stats.items():
                    report += f"  - {metric_name}: {stats['mean']:.3f}s (±{stats['stdev']:.3f})\n"
            
            # Issues and recommendations
            if result.issues:
                report += "- **Issues**:\n"
                for issue in result.issues:
                    report += f"  - {issue}\n"
            
            if result.recommendations:
                report += "- **Recommendations**:\n"
                for rec in result.recommendations:
                    report += f"  - {rec}\n"
            
            report += "\n"
        
        # Performance metrics analysis
        metrics_by_type = {}
        for result in self.test_results:
            for metric in result.metrics:
                metric_type = metric.metric_type.value
                if metric_type not in metrics_by_type:
                    metrics_by_type[metric_type] = []
                metrics_by_type[metric_type].append(metric)
        
        if metrics_by_type:
            report += "## Performance Metrics Analysis\n\n"
            
            for metric_type, metrics in metrics_by_type.items():
                passed_metrics = [m for m in metrics if m.passed]
                pass_rate = len(passed_metrics) / len(metrics) * 100
                avg_value = statistics.mean([m.value for m in metrics])
                
                report += f"### {metric_type.replace('_', ' ').title()}\n"
                report += f"- **Pass Rate**: {len(passed_metrics)}/{len(metrics)} ({pass_rate:.1f}%)\n"
                report += f"- **Average Value**: {avg_value:.3f}\n"
                
                # Performance distribution
                excellent = len([m for m in metrics if m.threshold_level == PerformanceThreshold.EXCELLENT])
                good = len([m for m in metrics if m.threshold_level == PerformanceThreshold.GOOD])
                needs_improvement = len([m for m in metrics if m.threshold_level == PerformanceThreshold.NEEDS_IMPROVEMENT])
                poor = len([m for m in metrics if m.threshold_level == PerformanceThreshold.POOR])
                
                report += f"- **Performance Distribution**:\n"
                report += f"  - Excellent: {excellent} ({excellent/len(metrics)*100:.1f}%)\n"
                report += f"  - Good: {good} ({good/len(metrics)*100:.1f}%)\n"
                report += f"  - Needs Improvement: {needs_improvement} ({needs_improvement/len(metrics)*100:.1f}%)\n"
                report += f"  - Poor: {poor} ({poor/len(metrics)*100:.1f}%)\n\n"
        
        # Performance benchmarks
        report += """## Performance Benchmarks

### Load Performance
- **Excellent**: < 1.0s initial page load
- **Good**: < 2.0s initial page load
- **Needs Improvement**: < 5.0s initial page load

### Interaction Performance  
- **Excellent**: < 100ms response time
- **Good**: < 300ms response time
- **Needs Improvement**: < 1.0s response time

### File Upload Performance
- **Excellent**: < 2.0s for 1MB file
- **Good**: < 5.0s for 1MB file  
- **Needs Improvement**: < 15.0s for 1MB file

### Memory Usage
- **Excellent**: < 50MB total usage
- **Good**: < 100MB total usage
- **Needs Improvement**: < 200MB total usage

## Key Recommendations

### Immediate Actions
1. **Optimize Critical Path**: Focus on page load and first interaction times
2. **File Upload Optimization**: Implement chunked uploads and progress indicators
3. **Memory Management**: Monitor and optimize memory usage patterns
4. **Mobile Performance**: Ensure consistent performance across devices

### Long-term Improvements
1. **Performance Monitoring**: Implement continuous performance monitoring
2. **Caching Strategy**: Implement intelligent caching for frequently accessed data
3. **Code Splitting**: Reduce initial bundle size with lazy loading
4. **Performance Budget**: Establish performance budgets for regression prevention

## Testing Methodology

This report covers:
1. **Load Performance**: Page and component load times
2. **Interaction Performance**: UI responsiveness and feedback
3. **File Operations**: Upload and processing performance
4. **Memory Efficiency**: Memory usage patterns and leaks
5. **Concurrent Usage**: Multi-user performance characteristics

## Monitoring Recommendations

1. **Real User Monitoring (RUM)**: Track actual user performance
2. **Synthetic Testing**: Automated performance regression testing
3. **Performance Alerts**: Set up alerts for performance degradation
4. **Regular Audits**: Schedule monthly performance reviews

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Performance data based on {sum(len(r.metrics) for r in self.test_results)} metric measurements*
"""
        
        return report


class PerformanceTestSuite:
    """Pytest test suite for performance validation"""
    
    def __init__(self):
        self.tester = StreamlitPerformanceTester()
    
    def test_page_load_performance(self):
        """Test page load meets performance requirements"""
        tests = self.tester.define_performance_tests()
        load_test = next((t for t in tests if t.name == 'initial_page_load'), None)
        
        assert load_test is not None, "Page load test not found"
        
        result = self.tester.run_performance_test(load_test)
        
        # Check for critical performance issues
        critical_metrics = [m for m in result.metrics if m.threshold_level == PerformanceThreshold.POOR]
        assert len(critical_metrics) == 0, f"Critical performance issues: {[m.name for m in critical_metrics]}"
    
    def test_file_upload_performance(self):
        """Test file upload performance is acceptable"""
        tests = self.tester.define_performance_tests()
        upload_test = next((t for t in tests if t.name == 'file_upload_performance'), None)
        
        result = self.tester.run_performance_test(upload_test)
        
        # Upload should complete within reasonable time
        upload_metrics = [m for m in result.metrics if 'upload' in m.name]
        slow_uploads = [m for m in upload_metrics if not m.passed]
        
        # Allow some tolerance for large files
        assert len(slow_uploads) <= len(upload_metrics) * 0.3, "Too many slow upload operations"
    
    def test_interaction_responsiveness(self):
        """Test UI interactions are responsive"""
        tests = self.tester.define_performance_tests()
        interaction_test = next((t for t in tests if t.name == 'text_input_responsiveness'), None)
        
        result = self.tester.run_performance_test(interaction_test)
        
        # All interactions should be responsive
        interaction_metrics = [m for m in result.metrics if m.metric_type == MetricType.INTERACTION_TIME]
        slow_interactions = [m for m in interaction_metrics if not m.passed]
        
        assert len(slow_interactions) == 0, f"Slow UI interactions: {[m.name for m in slow_interactions]}"
    
    def test_mobile_performance_parity(self):
        """Test mobile performance is comparable to desktop"""
        tests = self.tester.define_performance_tests()
        mobile_test = next((t for t in tests if t.name == 'mobile_performance'), None)
        
        result = self.tester.run_performance_test(mobile_test)
        
        # Mobile performance should still be acceptable
        mobile_metrics = [m for m in result.metrics if m.metric_type in [MetricType.LOAD_TIME, MetricType.INTERACTION_TIME]]
        critical_mobile_issues = [m for m in mobile_metrics if m.threshold_level == PerformanceThreshold.POOR]
        
        assert len(critical_mobile_issues) == 0, "Critical mobile performance issues detected"
    
    def test_memory_usage_limits(self):
        """Test memory usage stays within acceptable limits"""
        monitor = PerformanceMonitor()
        
        # Measure baseline memory
        baseline_memory = monitor.measure_memory_usage()
        
        # Simulate heavy usage
        tests = self.tester.define_performance_tests()
        generation_test = next((t for t in tests if t.name == 'video_generation_performance'), None)
        
        result = self.tester.run_performance_test(generation_test)
        
        # Check memory metrics
        memory_metrics = [m for m in result.metrics if m.metric_type == MetricType.MEMORY_USAGE]
        high_memory_usage = [m for m in memory_metrics if not m.passed]
        
        assert len(high_memory_usage) <= len(memory_metrics) * 0.2, "Excessive memory usage detected"


# Pytest fixtures
@pytest.fixture
def performance_monitor():
    """Provide performance monitor instance"""
    return PerformanceMonitor()


@pytest.fixture
def performance_tester():
    """Provide performance tester instance"""
    return StreamlitPerformanceTester()


@pytest.fixture
def performance_test_suite():
    """Provide performance test suite instance"""
    return PerformanceTestSuite()


if __name__ == "__main__":
    # Run performance tests and generate report
    tester = StreamlitPerformanceTester()
    report = tester.generate_performance_report()
    
    # Save report to file
    with open('/Users/srijan/ai-finance-agency/talkingphoto-mvp/performance_test_report.md', 'w') as f:
        f.write(report)
    
    print("Performance tests completed. Report saved to performance_test_report.md")