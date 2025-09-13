#!/usr/bin/env python3
"""
TalkingPhoto AI MVP - Comprehensive AI/ML Test Runner
Execute all AI component tests and generate detailed reports
"""

import sys
import os
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
import pytest
import coverage


class AITestRunner:
    """Comprehensive test runner for AI/ML components"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent / "tests"
        self.report_dir = Path(__file__).parent / "test_reports"
        self.report_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
    
    def run_unit_tests(self):
        """Run unit tests for AI providers"""
        print("\n" + "="*60)
        print("Running Unit Tests for AI Providers...")
        print("="*60)
        
        test_files = [
            "tests/unit/test_ai_providers.py",
            "tests/unit/test_cost_optimization.py"
        ]
        
        results = {}
        for test_file in test_files:
            print(f"\nTesting: {test_file}")
            result = pytest.main([
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={self.report_dir}/unit_{Path(test_file).stem}_{self.timestamp}.json"
            ])
            results[test_file] = "PASSED" if result == 0 else "FAILED"
        
        self.results['unit_tests'] = results
        return all(r == "PASSED" for r in results.values())
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("\n" + "="*60)
        print("Running Integration Tests...")
        print("="*60)
        
        test_files = [
            "tests/integration/test_provider_integration.py"
        ]
        
        results = {}
        for test_file in test_files:
            if not Path(test_file).exists():
                print(f"Skipping {test_file} (not found)")
                continue
                
            print(f"\nTesting: {test_file}")
            result = pytest.main([
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={self.report_dir}/integration_{Path(test_file).stem}_{self.timestamp}.json"
            ])
            results[test_file] = "PASSED" if result == 0 else "FAILED"
        
        self.results['integration_tests'] = results
        return all(r == "PASSED" for r in results.values())
    
    def run_performance_tests(self):
        """Run performance and benchmark tests"""
        print("\n" + "="*60)
        print("Running Performance Benchmarks...")
        print("="*60)
        
        test_files = [
            "tests/performance/test_latency_benchmarks.py"
        ]
        
        results = {}
        for test_file in test_files:
            if not Path(test_file).exists():
                print(f"Skipping {test_file} (not found)")
                continue
                
            print(f"\nTesting: {test_file}")
            result = pytest.main([
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={self.report_dir}/performance_{Path(test_file).stem}_{self.timestamp}.json"
            ])
            results[test_file] = "PASSED" if result == 0 else "FAILED"
        
        self.results['performance_tests'] = results
        return all(r == "PASSED" for r in results.values())
    
    def run_e2e_tests(self):
        """Run end-to-end tests"""
        print("\n" + "="*60)
        print("Running End-to-End Tests...")
        print("="*60)
        
        test_files = [
            "tests/e2e/test_complete_pipeline.py"
        ]
        
        results = {}
        for test_file in test_files:
            if not Path(test_file).exists():
                print(f"Skipping {test_file} (not found)")
                continue
                
            print(f"\nTesting: {test_file}")
            result = pytest.main([
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={self.report_dir}/e2e_{Path(test_file).stem}_{self.timestamp}.json"
            ])
            results[test_file] = "PASSED" if result == 0 else "FAILED"
        
        self.results['e2e_tests'] = results
        return all(r == "PASSED" for r in results.values())
    
    def run_coverage_analysis(self):
        """Run tests with coverage analysis"""
        print("\n" + "="*60)
        print("Running Coverage Analysis...")
        print("="*60)
        
        # Initialize coverage
        cov = coverage.Coverage(source=['services', 'models'])
        cov.start()
        
        # Run all tests with coverage
        pytest.main([
            "tests/",
            "--cov=services",
            "--cov=models",
            "--cov-report=html",
            f"--cov-report=html:{self.report_dir}/coverage_{self.timestamp}",
            "--cov-report=term"
        ])
        
        cov.stop()
        cov.save()
        
        # Generate coverage report
        print(f"\nCoverage report saved to: {self.report_dir}/coverage_{self.timestamp}/index.html")
    
    def generate_summary_report(self):
        """Generate comprehensive test summary report"""
        print("\n" + "="*60)
        print("Generating Test Summary Report...")
        print("="*60)
        
        report = {
            "timestamp": self.timestamp,
            "test_results": self.results,
            "statistics": self.calculate_statistics(),
            "recommendations": self.generate_recommendations()
        }
        
        # Save JSON report
        report_file = self.report_dir / f"ai_test_summary_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self.print_summary(report)
        
        return report_file
    
    def calculate_statistics(self):
        """Calculate test statistics"""
        stats = {
            "total_test_suites": 0,
            "passed_suites": 0,
            "failed_suites": 0,
            "pass_rate": 0
        }
        
        for category, results in self.results.items():
            for test, status in results.items():
                stats["total_test_suites"] += 1
                if status == "PASSED":
                    stats["passed_suites"] += 1
                else:
                    stats["failed_suites"] += 1
        
        if stats["total_test_suites"] > 0:
            stats["pass_rate"] = (stats["passed_suites"] / stats["total_test_suites"]) * 100
        
        return stats
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check unit test results
        if 'unit_tests' in self.results:
            unit_failures = [t for t, s in self.results['unit_tests'].items() if s == "FAILED"]
            if unit_failures:
                recommendations.append({
                    "type": "critical",
                    "message": f"Unit test failures detected in: {', '.join(unit_failures)}",
                    "action": "Fix unit test failures before deployment"
                })
        
        # Check integration test results
        if 'integration_tests' in self.results:
            integration_failures = [t for t, s in self.results['integration_tests'].items() if s == "FAILED"]
            if integration_failures:
                recommendations.append({
                    "type": "warning",
                    "message": "Integration test failures may indicate provider communication issues",
                    "action": "Review provider API configurations and network connectivity"
                })
        
        # Check performance test results
        if 'performance_tests' in self.results:
            perf_failures = [t for t, s in self.results['performance_tests'].items() if s == "FAILED"]
            if perf_failures:
                recommendations.append({
                    "type": "warning",
                    "message": "Performance benchmarks not meeting targets",
                    "action": "Optimize slow operations and consider caching strategies"
                })
        
        # Check E2E test results
        if 'e2e_tests' in self.results:
            e2e_failures = [t for t, s in self.results['e2e_tests'].items() if s == "FAILED"]
            if e2e_failures:
                recommendations.append({
                    "type": "critical",
                    "message": "End-to-end pipeline failures detected",
                    "action": "Review complete pipeline integration and error handling"
                })
        
        if not recommendations:
            recommendations.append({
                "type": "success",
                "message": "All tests passing successfully",
                "action": "Ready for deployment"
            })
        
        return recommendations
    
    def print_summary(self, report):
        """Print test summary to console"""
        stats = report['statistics']
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Test Suites: {stats['total_test_suites']}")
        print(f"Passed: {stats['passed_suites']}")
        print(f"Failed: {stats['failed_suites']}")
        print(f"Pass Rate: {stats['pass_rate']:.1f}%")
        
        print("\n" + "-"*60)
        print("RECOMMENDATIONS")
        print("-"*60)
        for rec in report['recommendations']:
            icon = {
                'critical': '❌',
                'warning': '⚠️',
                'success': '✅'
            }.get(rec['type'], '📝')
            
            print(f"{icon} {rec['type'].upper()}: {rec['message']}")
            print(f"   Action: {rec['action']}")
        
        print("\n" + "="*60)
    
    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*60)
        print("TALKINGPHOTO AI MVP - COMPREHENSIVE TEST SUITE")
        print("="*60)
        print(f"Starting tests at: {datetime.now()}")
        
        start_time = time.time()
        
        # Run test suites
        unit_passed = self.run_unit_tests()
        integration_passed = self.run_integration_tests()
        performance_passed = self.run_performance_tests()
        e2e_passed = self.run_e2e_tests()
        
        # Run coverage analysis
        if os.getenv('COVERAGE', 'false').lower() == 'true':
            self.run_coverage_analysis()
        
        # Generate summary report
        report_file = self.generate_summary_report()
        
        elapsed_time = time.time() - start_time
        
        print(f"\nTotal test execution time: {elapsed_time:.2f} seconds")
        print(f"Report saved to: {report_file}")
        
        # Return exit code
        all_passed = all([unit_passed, integration_passed, performance_passed, e2e_passed])
        return 0 if all_passed else 1


def main():
    """Main entry point"""
    runner = AITestRunner()
    exit_code = runner.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()