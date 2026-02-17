import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from agents.project_manager import ProjectManager
from agents.coder_agent import CoderAgent
from agents.designer_agent import DesignerAgent
from agents.researcher_agent import ResearcherAgent
from agents.integrator_agent import IntegratorAgent
from agents.tester_agent import TesterAgent
from services.file_service import FileService
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ProjectOrchestrator:
    """Main orchestrator that manages all phases"""
    
    def __init__(self):
        # Initialize all agents
        self.project_manager = ProjectManager()
        self.coder_agent = CoderAgent()
        self.designer_agent = DesignerAgent()
        self.researcher_agent = ResearcherAgent()
        self.integrator_agent = IntegratorAgent()
        self.tester_agent = TesterAgent()
        
        # Services
        self.file_service = FileService()
        
        # State
        self.current_project = None
        self.phase_results = {}
        
    async def process_project(self, user_prompt: str) -> Dict[str, Any]:
        """Process project through all 4 phases"""
        logger.info(f"🚀 Starting project: {user_prompt[:100]}...")
        
        # Create project directory
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = f"generated_projects/project_{project_id}"
        os.makedirs(project_dir, exist_ok=True)
        
        # Phase 1: Project Analysis
        logger.info("🔄 PHASE 1: Project Analysis")
        phase1_result = await self.project_manager.analyze_project(user_prompt)
        self.phase_results[1] = phase1_result
        project_spec = phase1_result["result"]
        
        # Save phase 1 result
        await self.file_service.save_json(
            os.path.join(project_dir, "phase1_analysis.json"),
            phase1_result
        )
        
        # Phase 2: Task Execution
        logger.info("🔄 PHASE 2: Task Execution")
        phase2_results = []
        
        for task in project_spec["tasks"]:
            agent_type = task.get("agent_type", "coder")
            
            if agent_type == "coder":
                result = await self.coder_agent.execute_task(task, project_spec)
            elif agent_type == "designer":
                result = await self.designer_agent.execute_task(task, project_spec)
            elif agent_type == "researcher":
                result = await self.researcher_agent.execute_task(task, project_spec)
            else:
                # Default to coder
                result = await self.coder_agent.execute_task(task, project_spec)
            
            phase2_results.append(result)
            
            # Save each task result
            await self.file_service.save_json(
                os.path.join(project_dir, f"task_{task['id']}_{agent_type}.json"),
                result
            )
        
        self.phase_results[2] = phase2_results
        
        # Phase 3: Integration
        logger.info("🔄 PHASE 3: Integration")
        phase3_result = await self.integrator_agent.integrate(
            phase2_results, project_spec
        )
        self.phase_results[3] = phase3_result
        
        await self.file_service.save_json(
            os.path.join(project_dir, "phase3_integration.json"),
            phase3_result
        )
        
        # Phase 4: Testing and Refinement Loop
        logger.info("🔄 PHASE 4: Testing and Refinement")
        max_iterations = 3
        
        for iteration in range(max_iterations):
            logger.info(f"🔧 Iteration {iteration + 1}/{max_iterations}")
            
            # Test the integrated project
            test_result = await self.tester_agent.test_project(
                phase3_result["output"], project_spec
            )
            
            self.phase_results[4] = test_result
            
            await self.file_service.save_json(
                os.path.join(project_dir, f"phase4_iteration_{iteration+1}.json"),
                test_result
            )
            
            if test_result["output"].get("status") == "pass":
                logger.info(f"✅ Project passed QA on iteration {iteration + 1}")
                break
                
            elif test_result["output"].get("needs_phase1_restart"):
                logger.info("🔄 Restarting from Phase 1 with improvements")
                # Modify prompt based on test results
                improved_prompt = f"{user_prompt}\n\nIssues to fix: {test_result['output'].get('errors', [])}"
                return await self.process_project(improved_prompt)
                
            elif test_result["output"].get("needs_phase2_modifications"):
                logger.info(f"🔧 Fixing specific tasks")
                # Re-execute specific tasks
                tasks_to_fix = test_result["output"].get("specific_tasks_to_fix", [])
                for task_id in tasks_to_fix:
                    task = next((t for t in project_spec["tasks"] if t["id"] == task_id), None)
                    if task:
                        # Re-execute the task
                        if task["agent_type"] == "coder":
                            new_result = await self.coder_agent.execute_task(task, project_spec)
                        # Update the result
                        for i, res in enumerate(phase2_results):
                            if res["task_id"] == task_id:
                                phase2_results[i] = new_result
                                break
                
                # Re-integrate
                phase3_result = await self.integrator_agent.integrate(
                    phase2_results, project_spec
                )
        
        # Generate final project files
        logger.info("💾 Generating final project files")
        final_project = await self._generate_final_project(
            project_dir, phase3_result["output"], project_spec
        )
        
        # Return final result
        return {
            "status": "success",
            "project_id": project_id,
            "project_name": project_spec.get("project_name", "Untitled Project"),
            "description": user_prompt,
            "phases": self.phase_results,
            "project_path": project_dir,
            "download_url": f"/api/projects/{project_id}/download",
            "final_project": final_project,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_final_project(self, project_dir: str, 
                                    integration: Dict[str, Any],
                                    project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final project files"""
        files_created = []
        
        # Create main file
        if "main_file" in integration:
            main_file_path = os.path.join(project_dir, "main.py")
            await self.file_service.save_file(main_file_path, integration["main_file"])
            files_created.append("main.py")
        
        # Create README
        if "documentation" in integration:
            readme_path = os.path.join(project_dir, "README.md")
            await self.file_service.save_file(readme_path, integration["documentation"])
            files_created.append("README.md")
        
        # Create requirements.txt
        if "dependencies" in integration:
            req_path = os.path.join(project_dir, "requirements.txt")
            deps = "\n".join(integration["dependencies"])
            await self.file_service.save_file(req_path, deps)
            files_created.append("requirements.txt")
        
        # Create project structure
        if "project_structure" in integration:
            structure = integration["project_structure"]
            for file_name, content in structure.items():
                if isinstance(content, str) and len(content) > 10:  # Simple check
                    file_path = os.path.join(project_dir, file_name)
                    await self.file_service.save_file(file_path, content)
                    files_created.append(file_name)
        
        return {
            "files_created": files_created,
            "total_files": len(files_created),
            "project_dir": project_dir,
            "instructions": integration.get("build_commands", ["python main.py"])
        }