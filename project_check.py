#!/usr/bin/env python3
"""
IRIS Project Validation & Health Check Script
Comprehensive analysis of project readiness for hackathon submissions
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str) -> None:
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"{text:^70}")
    print(f"{'='*70}{Colors.END}\n")

def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


class IRISProjectValidator:
    """Validate IRIS project structure and implementation"""
    
    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'info': []
        }
        self.metrics = {}
    
    def check_file_exists(self, file_path: str, description: str) -> bool:
        """Check if required file exists"""
        full_path = self.root / file_path
        if full_path.exists():
            self.results['passed'].append(f"{description}: {file_path}")
            return True
        else:
            self.results['failed'].append(f"Missing: {description}")
            return False
    
    def check_directory_exists(self, dir_path: str, description: str) -> bool:
        """Check if required directory exists"""
        full_path = self.root / dir_path
        if full_path.is_dir():
            self.results['passed'].append(f"{description}: {dir_path}")
            return True
        else:
            self.results['failed'].append(f"Missing directory: {description}")
            return False
    
    def count_files_by_extension(self, extension: str) -> int:
        """Count files with specific extension"""
        return len(list(self.root.rglob(f"*.{extension}")))
    
    def calculate_project_statistics(self) -> Dict:
        """Calculate project statistics"""
        stats = {
            'python_files': self.count_files_by_extension('py'),
            'html_files': self.count_files_by_extension('html'),
            'js_files': self.count_files_by_extension('js'),
            'css_files': self.count_files_by_extension('css'),
            'arduino_files': self.count_files_by_extension('ino'),
            'total_files': len(list(self.root.rglob('*'))),
        }
        self.metrics['file_statistics'] = stats
        return stats
    
    def validate_core_components(self) -> None:
        """Validate core system components"""
        print_header("CORE COMPONENTS VALIDATION")
        
        # Backend
        print("\n📦 Backend Components:")
        self.check_file_exists('main.py', 'Main application entry')
        self.check_file_exists('web/app.py', 'Flask web application')
        self.check_file_exists('config.py', 'Configuration file')
        
        # Database
        print("\n📊 Database Layer:")
        self.check_directory_exists('database', 'Database module')
        self.check_file_exists('database/db_manager.py', 'Database manager')
        
        # Detection
        print("\n🔍 Detection Engine:")
        self.check_directory_exists('detector', 'Detector module')
        self.check_file_exists('detector/yolo_detector.py', 'YOLO detector')
        self.check_file_exists('models/best.pt', 'YOLOv8 trained model')
        
        # Frontend
        print("\n🎨 Frontend Assets:")
        self.check_directory_exists('web/templates', 'HTML templates')
        self.check_directory_exists('web/static', 'Static assets')
        self.check_file_exists('web/templates/login.html', 'Login page')
        self.check_file_exists('web/templates/dashboard.html', 'Dashboard')
        
        # Hardware
        print("\n⚙️  Hardware Integration:")
        self.check_directory_exists('arduino', 'Arduino directory')
        self.check_file_exists('arduino/iris_controller/iris_controller.ino', 'Arduino controller')
        
        # Authentication
        print("\n🔐 Authentication:")
        self.check_file_exists('auth.py', 'Authentication module')
        self.check_file_exists('biometric.py', 'Biometric module')
        self.check_file_exists('biometric_auth.py', 'Biometric auth handler')
    
    def validate_dependencies(self) -> None:
        """Validate dependencies and requirements"""
        print_header("DEPENDENCIES VALIDATION")
        
        req_file = self.root / 'requirements.txt'
        if req_file.exists():
            self.results['passed'].append("Requirements file exists")
            
            with open(req_file, 'r') as f:
                requirements = f.read()
                
            required_packages = [
                ('flask', 'Web framework'),
                ('firebase', 'Cloud database'),
                ('opencv', 'Computer vision'),
                ('torch', 'PyTorch for YOLOv8'),
                ('google', 'Google Gemini API'),
                ('insightface', 'Facial recognition'),
            ]
            
            print("\n📋 Required Packages Check:")
            for package, description in required_packages:
                if package.lower() in requirements.lower():
                    self.results['passed'].append(f"✅ {description}: {package}")
                    print_success(f"{description}: {package}")
                else:
                    self.results['warnings'].append(f"Missing: {description}")
                    print_warning(f"Missing: {description}")
        else:
            self.results['failed'].append("requirements.txt not found")
    
    def validate_cloud_integration(self) -> None:
        """Validate cloud integration"""
        print_header("CLOUD INTEGRATION VALIDATION")
        
        print("\n☁️  Firebase/Google Cloud:")
        self.check_file_exists('firestore-key.json', 'Firebase credentials')
        self.check_file_exists('firebase.json', 'Firebase config')
        self.check_file_exists('firestore.rules', 'Firestore security rules')
        
        # Check for Gemini API setup
        print("\n🤖 AI Integration:")
        self.check_file_exists('gemini_analyzer.py', 'Gemini analyzer')
        self.results['info'].append("Google Gemini integration configured")
    
    def validate_documentation(self) -> None:
        """Validate project documentation"""
        print_header("DOCUMENTATION VALIDATION")
        
        docs = [
            ('README.md', 'Project README'),
            ('IMPLEMENTATION_COMPLETE.md', 'Implementation status'),
            ('DEPLOYMENT_STATUS.txt', 'Deployment status'),
        ]
        
        print("\n📚 Documentation Files:")
        for doc_file, description in docs:
            if self.check_file_exists(doc_file, description):
                print_success(description)
            else:
                print_warning(description)
    
    def validate_deployment(self) -> None:
        """Validate deployment configuration"""
        print_header("DEPLOYMENT CONFIGURATION VALIDATION")
        
        print("\n🚀 Deployment Files:")
        self.check_file_exists('Dockerfile', 'Docker configuration')
        self.check_file_exists('Procfile', 'Heroku/Cloud Run config')
        self.check_file_exists('runtime.txt', 'Python version spec')
        self.check_file_exists('app.yaml', 'Google Cloud config')
    
    def validate_testing(self) -> None:
        """Validate testing setup"""
        print_header("TESTING & QUALITY ASSURANCE")
        
        print("\n🧪 Test Files:")
        tests = [
            'test_integration.py',
            'test_dashboard_flow.py',
            'test_all_pages.py',
        ]
        
        for test_file in tests:
            if self.check_file_exists(test_file, f"Test suite: {test_file}"):
                print_success(test_file)
            else:
                print_warning(f"Missing test: {test_file}")
    
    def validate_config_files(self) -> None:
        """Validate configuration files"""
        print_header("CONFIGURATION FILES")
        
        print("\n⚙️  Config Files:")
        self.check_file_exists('config.py', 'Main config')
        self.check_file_exists('biometric_config.py', 'Biometric config')
        
        # Check for environment variables
        print("\n🔑 Environment Setup:")
        self.results['info'].append("Ensure all required environment variables are set")
        self.results['info'].append("Firebase credentials should be in .env or firestore-key.json")
    
    def calculate_code_metrics(self) -> None:
        """Calculate code metrics"""
        print_header("CODE METRICS")
        
        stats = self.calculate_project_statistics()
        
        print("\n📊 File Statistics:")
        print(f"  Python files: {stats['python_files']}")
        print(f"  HTML files: {stats['html_files']}")
        print(f"  JavaScript files: {stats['js_files']}")
        print(f"  CSS files: {stats['css_files']}")
        print(f"  Arduino files: {stats['arduino_files']}")
        print(f"  Total files: {stats['total_files']}")
        
        # Estimate lines of code
        total_lines = 0
        py_lines = 0
        for py_file in self.root.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    total_lines += lines
                    py_lines += lines
            except:
                pass
        
        self.metrics['estimated_lines_of_code'] = py_lines
        print(f"  Estimated Python LOC: {py_lines:,}")
    
    def validate_hackathon_readiness(self) -> None:
        """Check hackathon readiness"""
        print_header("HACKATHON READINESS CHECKLIST")
        
        checklist = {
            'Core Implementation': self.check_file_exists('main.py', '') and self.check_file_exists('web/app.py', ''),
            'AI/ML Model': self.check_file_exists('models/best.pt', '') and self.check_file_exists('detector/yolo_detector.py', ''),
            'Cloud Integration': self.check_file_exists('firestore-key.json', '') and self.check_file_exists('firebase.json', ''),
            'Biometric Auth': self.check_file_exists('biometric_auth.py', '') and self.check_file_exists('biometric.py', ''),
            'Documentation': self.check_file_exists('README.md', ''),
            'Deployment Ready': self.check_file_exists('Dockerfile', '') and self.check_file_exists('app.yaml', ''),
            'Frontend': self.check_directory_exists('web/templates', '') and self.check_directory_exists('web/static', ''),
            'Hardware Integration': self.check_directory_exists('arduino', ''),
        }
        
        print("\n✅ Hackathon Readiness Score:\n")
        passed = sum(1 for v in checklist.values() if v)
        total = len(checklist)
        
        for item, status in checklist.items():
            if status:
                print_success(item)
            else:
                print_warning(item)
        
        score = (passed / total) * 100
        print(f"\n📊 Overall Readiness: {score:.1f}% ({passed}/{total})")
        
        self.metrics['hackathon_readiness_score'] = score
    
    def generate_report(self) -> Dict:
        """Generate validation report"""
        print_header("VALIDATION REPORT SUMMARY")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'project_path': str(self.root),
            'results': self.results,
            'metrics': self.metrics,
            'summary': {
                'passed_checks': len(self.results['passed']),
                'failed_checks': len(self.results['failed']),
                'warnings': len(self.results['warnings']),
                'info_items': len(self.results['info']),
            }
        }
        
        print(f"\n✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print(f"ℹ️  Info: {len(self.results['info'])}")
        
        if self.results['failed']:
            print("\n❌ Issues to Address:")
            for issue in self.results['failed']:
                print(f"  • {issue}")
        
        if self.results['warnings']:
            print("\n⚠️  Warnings:")
            for warning in self.results['warnings'][:5]:
                print(f"  • {warning}")
        
        print("\n" + "="*70)
        print("RECOMMENDATIONS:")
        print("="*70)
        print("""
1. ✅ Ensure all required files are present
2. ✅ Test deployment on Firebase before hackathon
3. ✅ Verify all API keys and credentials are configured
4. ✅ Run end-to-end testing (biometric → detection → dashboard)
5. ✅ Prepare demo video as backup
6. ✅ Document all features and architecture
7. ✅ Get team to memorize pitch and Q&A
8. ✅ Practice live demo 20+ times
        """)
        
        return report
    
    def run_full_validation(self) -> None:
        """Run complete validation"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 IRIS PROJECT VALIDATION SUITE{Colors.END}")
        print(f"{Colors.BOLD}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
        
        self.validate_core_components()
        self.validate_dependencies()
        self.validate_cloud_integration()
        self.validate_documentation()
        self.validate_deployment()
        self.validate_testing()
        self.validate_config_files()
        self.calculate_code_metrics()
        self.validate_hackathon_readiness()
        
        report = self.generate_report()
        
        # Save report
        report_file = self.root / 'PROJECT_VALIDATION_REPORT.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to: {report_file}")
        print(f"\n{Colors.BOLD}✅ Validation Complete!{Colors.END}\n")


def main():
    """Main entry point"""
    project_root = "d:\\Btech Projects\\IRIS"
    
    if not Path(project_root).exists():
        print_error(f"Project path not found: {project_root}")
        return
    
    validator = IRISProjectValidator(project_root)
    validator.run_full_validation()


if __name__ == "__main__":
    main()
