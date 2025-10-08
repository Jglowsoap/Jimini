#!/usr/bin/env python3
"""
🧹 JIMINI CODEBASE CLEANUP SCRIPT 🧹

Comprehensive cleanup tool to remove unused files, consolidate duplicates,
and organize the Jimini codebase for production readiness.

CLEANUP CATEGORIES:
✅ Remove duplicate demo and test files
✅ Clean up phase completion documentation
✅ Remove backup files and old configurations  
✅ Consolidate duplicate deployment files
✅ Remove unused development artifacts
✅ Organize core application files
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Set
import json
from datetime import datetime

class JiminiCodebaseCleanup:
    def __init__(self, workspace_path: str = "/workspaces/Jimini"):
        self.workspace = Path(workspace_path)
        self.cleanup_summary = {
            'files_removed': [],
            'directories_removed': [],
            'files_consolidated': [],
            'space_saved': 0,
            'cleanup_timestamp': datetime.now().isoformat()
        }
        
    def analyze_codebase(self) -> Dict[str, List[str]]:
        """Analyze codebase and categorize files for cleanup"""
        
        analysis = {
            'core_files': [],
            'demo_files': [],
            'phase_docs': [],
            'backup_files': [],
            'duplicate_configs': [],
            'test_artifacts': [],
            'deployment_duplicates': [],
            'unused_scripts': []
        }
        
        print("🔍 Analyzing codebase structure...")
        
        for file_path in self.workspace.rglob('*'):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(self.workspace))
                
                # Core application files (keep these)
                if any(pattern in relative_path for pattern in [
                    'app/main.py', 'app/models.py', 'app/enforcement.py', 
                    'jimini_cli/main.py', 'policy_rules.yaml'
                ]) and not any(exclude in relative_path for exclude in ['backup', 'duplicate', 'replit-deployment']):
                    analysis['core_files'].append(relative_path)
                
                # Demo files (remove most)
                elif any(pattern in relative_path for pattern in [
                    'demo_', '_demo.py', 'quick_demo', 'complete_integration_demo',
                    'dashboard_api_flow_demo', 'complete_api_demonstration', 'full_platform_demo'
                ]):
                    analysis['demo_files'].append(relative_path)
                
                # Phase documentation (consolidate/remove)
                elif any(pattern in relative_path for pattern in [
                    'PHASE_', 'COMPLETION', 'SUCCESS.md', '_VICTORY.md', '_COMPLETE.md'
                ]):
                    analysis['phase_docs'].append(relative_path)
                
                # Backup files (remove)
                elif any(pattern in relative_path for pattern in [
                    '.backup', 'backup.yaml', '.backup.', '_backup.'
                ]):
                    analysis['backup_files'].append(relative_path)
                
                # Test artifacts (clean up)
                elif any(pattern in relative_path for pattern in [
                    'test_results_', '_report_', '.json', '.log'
                ]) and any(exclude in relative_path for exclude in ['20251007', 'test_', 'security_']):
                    analysis['test_artifacts'].append(relative_path)
                
                # Deployment duplicates
                elif 'replit-deployment/' in relative_path:
                    analysis['deployment_duplicates'].append(relative_path)
                
                # Unused phase scripts
                elif any(pattern in relative_path for pattern in [
                    'phase_2_', 'phase_3_', 'phase_4_', 'phase_5_', 'phase_6_', 'phase_7_', 'phase_8_'
                ]) and relative_path.endswith('.py'):
                    analysis['unused_scripts'].append(relative_path)
        
        return analysis
    
    def remove_demo_files(self, demo_files: List[str]) -> None:
        """Remove demo files but keep one example"""
        
        print("\n🗑️ Removing demo files...")
        
        # Keep one main demo file
        keep_demo = 'complete_integration_demo.py'
        
        for demo_file in demo_files:
            if demo_file != keep_demo:
                file_path = self.workspace / demo_file
                if file_path.exists():
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        self.cleanup_summary['files_removed'].append(demo_file)
                        self.cleanup_summary['space_saved'] += file_size
                        print(f"   ✅ Removed: {demo_file}")
                    except Exception as e:
                        print(f"   ❌ Failed to remove {demo_file}: {e}")
        
        print(f"   📝 Kept demo file: {keep_demo}")
    
    def clean_phase_documentation(self, phase_docs: List[str]) -> None:
        """Clean up excessive phase documentation"""
        
        print("\n📚 Cleaning up phase documentation...")
        
        # Keep only essential docs
        keep_docs = [
            'ARCHITECTURE.md', 'README.md', 'CHANGELOG.md', 
            'DEPLOYMENT_CHECKLIST.md', 'LICENSE'
        ]
        
        for doc_file in phase_docs:
            if not any(keep in doc_file for keep in keep_docs):
                file_path = self.workspace / doc_file
                if file_path.exists():
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        self.cleanup_summary['files_removed'].append(doc_file)
                        self.cleanup_summary['space_saved'] += file_size
                        print(f"   ✅ Removed: {doc_file}")
                    except Exception as e:
                        print(f"   ❌ Failed to remove {doc_file}: {e}")
    
    def remove_backup_files(self, backup_files: List[str]) -> None:
        """Remove all backup files"""
        
        print("\n💾 Removing backup files...")
        
        for backup_file in backup_files:
            file_path = self.workspace / backup_file
            if file_path.exists():
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    self.cleanup_summary['files_removed'].append(backup_file)
                    self.cleanup_summary['space_saved'] += file_size
                    print(f"   ✅ Removed: {backup_file}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {backup_file}: {e}")
    
    def clean_test_artifacts(self, test_artifacts: List[str]) -> None:
        """Clean up old test artifacts and reports"""
        
        print("\n🧪 Cleaning test artifacts...")
        
        for artifact in test_artifacts:
            file_path = self.workspace / artifact
            if file_path.exists():
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    self.cleanup_summary['files_removed'].append(artifact)
                    self.cleanup_summary['space_saved'] += file_size
                    print(f"   ✅ Removed: {artifact}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {artifact}: {e}")
    
    def remove_deployment_duplicates(self, duplicates: List[str]) -> None:
        """Remove duplicate deployment files"""
        
        print("\n🚀 Removing deployment duplicates...")
        
        # Remove entire replit-deployment directory as it's duplicate
        replit_deploy_dir = self.workspace / 'replit-deployment'
        if replit_deploy_dir.exists():
            try:
                # Calculate directory size
                dir_size = sum(f.stat().st_size for f in replit_deploy_dir.rglob('*') if f.is_file())
                shutil.rmtree(replit_deploy_dir)
                self.cleanup_summary['directories_removed'].append('replit-deployment/')
                self.cleanup_summary['space_saved'] += dir_size
                print(f"   ✅ Removed directory: replit-deployment/ ({dir_size} bytes)")
            except Exception as e:
                print(f"   ❌ Failed to remove replit-deployment/: {e}")
    
    def remove_unused_scripts(self, unused_scripts: List[str]) -> None:
        """Remove unused phase scripts"""
        
        print("\n📜 Removing unused phase scripts...")
        
        # Keep only the latest innovative scripts
        keep_scripts = [
            'ai_powered_rule_generation.py',
            'multilanguage_obfuscation_engine.py', 
            'zero_day_prediction_engine.py',
            'enterprise_ai_security_copilot.py'
        ]
        
        for script in unused_scripts:
            if not any(keep in script for keep in keep_scripts):
                file_path = self.workspace / script
                if file_path.exists():
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        self.cleanup_summary['files_removed'].append(script)
                        self.cleanup_summary['space_saved'] += file_size
                        print(f"   ✅ Removed: {script}")
                    except Exception as e:
                        print(f"   ❌ Failed to remove {script}: {e}")
        
        print(f"   📝 Kept innovative scripts: {', '.join(keep_scripts)}")
    
    def consolidate_requirements(self) -> None:
        """Consolidate multiple requirements files"""
        
        print("\n📦 Consolidating requirements files...")
        
        # Read all requirements files
        requirements_files = [
            'requirements.txt',
            'requirements-intelligence.txt',
            'replit_requirements.txt'
        ]
        
        all_requirements = set()
        
        for req_file in requirements_files:
            file_path = self.workspace / req_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                all_requirements.add(line)
                except Exception as e:
                    print(f"   ⚠️ Error reading {req_file}: {e}")
        
        # Write consolidated requirements
        main_requirements = self.workspace / 'requirements.txt'
        try:
            with open(main_requirements, 'w') as f:
                f.write("# Jimini AI Policy Gateway - Consolidated Requirements\n")
                f.write("# Generated by cleanup script\n\n")
                for req in sorted(all_requirements):
                    f.write(f"{req}\n")
            
            print(f"   ✅ Consolidated {len(all_requirements)} requirements into requirements.txt")
            
            # Remove duplicate files
            for req_file in requirements_files[1:]:  # Keep main requirements.txt
                file_path = self.workspace / req_file
                if file_path.exists():
                    file_path.unlink()
                    self.cleanup_summary['files_removed'].append(req_file)
                    print(f"   ✅ Removed duplicate: {req_file}")
                    
        except Exception as e:
            print(f"   ❌ Failed to consolidate requirements: {e}")
    
    def consolidate_configs(self) -> None:
        """Consolidate configuration files"""
        
        print("\n⚙️ Consolidating configuration files...")
        
        # Remove duplicate pyproject files
        enhanced_pyproject = self.workspace / 'pyproject_enhanced.toml'
        update_pyproject = self.workspace / 'pyproject.toml (update)'
        
        for duplicate in [enhanced_pyproject, update_pyproject]:
            if duplicate.exists():
                try:
                    file_size = duplicate.stat().st_size
                    duplicate.unlink()
                    self.cleanup_summary['files_removed'].append(str(duplicate.name))
                    self.cleanup_summary['space_saved'] += file_size
                    print(f"   ✅ Removed duplicate: {duplicate.name}")
                except Exception as e:
                    print(f"   ❌ Failed to remove {duplicate.name}: {e}")
        
        print("   📝 Kept main pyproject.toml")
    
    def clean_temporary_files(self) -> None:
        """Clean temporary and cache files"""
        
        print("\n🗂️ Cleaning temporary files...")
        
        # Remove cache directories
        cache_dirs = ['.pytest_cache', '.ruff_cache', '__pycache__', 'htmlcov']
        
        for cache_dir in cache_dirs:
            cache_path = self.workspace / cache_dir
            if cache_path.exists():
                try:
                    dir_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
                    shutil.rmtree(cache_path)
                    self.cleanup_summary['directories_removed'].append(f"{cache_dir}/")
                    self.cleanup_summary['space_saved'] += dir_size
                    print(f"   ✅ Removed cache: {cache_dir}/")
                except Exception as e:
                    print(f"   ❌ Failed to remove {cache_dir}: {e}")
        
        # Remove log files
        log_files = list(self.workspace.glob('*.log'))
        for log_file in log_files:
            try:
                file_size = log_file.stat().st_size
                log_file.unlink()
                self.cleanup_summary['files_removed'].append(log_file.name)
                self.cleanup_summary['space_saved'] += file_size
                print(f"   ✅ Removed log: {log_file.name}")
            except Exception as e:
                print(f"   ❌ Failed to remove {log_file.name}: {e}")
    
    def organize_core_files(self) -> None:
        """Organize and document core application files"""
        
        print("\n🗂️ Documenting core application structure...")
        
        core_structure = {
            'application_core': [
                'app/main.py - FastAPI application entry point',
                'app/models.py - Data models and schemas', 
                'app/enforcement.py - Policy enforcement engine',
                'app/rules_loader.py - Rules loading and management',
                'jimini_cli/main.py - Command line interface'
            ],
            'innovation_engines': [
                'ai_powered_rule_generation.py - ML-based rule generation',
                'multilanguage_obfuscation_engine.py - Global language security',
                'zero_day_prediction_engine.py - Predictive attack intelligence',
                'enterprise_ai_security_copilot.py - AI security assistant'
            ],
            'configuration': [
                'policy_rules.yaml - Security rules configuration',
                'pyproject.toml - Project configuration',
                'requirements.txt - Python dependencies'
            ],
            'documentation': [
                'README.md - Project documentation',
                'ARCHITECTURE.md - System architecture',
                'CHANGELOG.md - Version history'
            ]
        }
        
        # Write core structure documentation
        core_doc = self.workspace / 'CORE_APPLICATION_STRUCTURE.md'
        try:
            with open(core_doc, 'w') as f:
                f.write("# 🛡️ Jimini Core Application Structure\n\n")
                f.write("## Post-Cleanup Core Files\n\n")
                
                for category, files in core_structure.items():
                    f.write(f"### {category.replace('_', ' ').title()}\n\n")
                    for file_desc in files:
                        f.write(f"- `{file_desc}`\n")
                    f.write("\n")
                
                f.write("## Innovation Features\n\n")
                f.write("The Jimini platform includes 4 revolutionary AI security innovations:\n\n")
                f.write("1. **AI-Powered Dynamic Rule Generation** - Learns from attacks\n")
                f.write("2. **Multi-Language Obfuscation Detection** - Global language support\n")
                f.write("3. **Zero-Day Attack Prediction Engine** - Predictive security\n")
                f.write("4. **Enterprise AI Security Copilot** - AI security assistant\n\n")
                f.write(f"Generated by cleanup script on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            print("   ✅ Created CORE_APPLICATION_STRUCTURE.md")
        except Exception as e:
            print(f"   ❌ Failed to create core structure doc: {e}")
    
    def generate_cleanup_report(self) -> None:
        """Generate comprehensive cleanup report"""
        
        print("\n📊 Generating cleanup report...")
        
        # Save cleanup summary
        report_file = self.workspace / 'CLEANUP_REPORT.json'
        try:
            with open(report_file, 'w') as f:
                json.dump(self.cleanup_summary, f, indent=2)
            print(f"   ✅ Saved cleanup report: CLEANUP_REPORT.json")
        except Exception as e:
            print(f"   ❌ Failed to save cleanup report: {e}")
        
        # Print summary
        files_removed = len(self.cleanup_summary['files_removed'])
        dirs_removed = len(self.cleanup_summary['directories_removed'])
        space_saved_kb = self.cleanup_summary['space_saved'] / 1024
        
        print(f"\n📈 Cleanup Summary:")
        print(f"   📁 Files removed: {files_removed}")
        print(f"   🗂️ Directories removed: {dirs_removed}")
        print(f"   💾 Space saved: {space_saved_kb:.1f} KB")
        print(f"   ⏰ Cleanup completed: {self.cleanup_summary['cleanup_timestamp']}")
    
    def run_cleanup(self, dry_run: bool = False) -> None:
        """Run comprehensive codebase cleanup"""
        
        print("🧹 JIMINI CODEBASE CLEANUP")
        print("=" * 50)
        
        if dry_run:
            print("🔍 DRY RUN MODE - No files will be deleted")
            print("=" * 50)
        
        # Analyze codebase
        analysis = self.analyze_codebase()
        
        print(f"\n📊 Cleanup Analysis:")
        for category, files in analysis.items():
            print(f"   • {category.replace('_', ' ').title()}: {len(files)} files")
        
        if not dry_run:
            # Execute cleanup steps
            self.remove_demo_files(analysis['demo_files'])
            self.clean_phase_documentation(analysis['phase_docs'])
            self.remove_backup_files(analysis['backup_files'])
            self.clean_test_artifacts(analysis['test_artifacts'])
            self.remove_deployment_duplicates(analysis['deployment_duplicates'])
            self.remove_unused_scripts(analysis['unused_scripts'])
            self.consolidate_requirements()
            self.consolidate_configs()
            self.clean_temporary_files()
            self.organize_core_files()
            self.generate_cleanup_report()
            
            print(f"\n🎉 CLEANUP COMPLETE!")
            print(f"   🛡️ Jimini codebase is now clean and production-ready")
            print(f"   🚀 Core innovation files preserved")
            print(f"   📚 Documentation organized")
        
        return analysis

def main():
    cleanup = JiminiCodebaseCleanup()
    
    # First run dry run to show what would be cleaned
    print("🔍 Running cleanup analysis...")
    analysis = cleanup.run_cleanup(dry_run=True)
    
    print(f"\n" + "=" * 50)
    response = input("Proceed with cleanup? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        cleanup.run_cleanup(dry_run=False)
    else:
        print("🚫 Cleanup cancelled")

if __name__ == '__main__':
    main()