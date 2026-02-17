import json
from typing import Dict, Any

from services.llm_service import llm_service
from utils.prompts import CODER_PROMPT
from utils.logger import setup_logger

logger = setup_logger(__name__)

class CoderAgent:
    """Phase 2: Coder agent - writes code"""
    
    def __init__(self):
        self.agent_type = "coder"
    
    async def execute_task(self, task: Dict[str, Any], project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coding task"""
        logger.info(f"👨‍💻 Coder Agent: {task['title']}")
        
        try:
            prompt = CODER_PROMPT.format(
                task_description=task["description"],
                tech_stack=", ".join(project_context.get("tech_stack", ["Python"])),
                expected_output=task["expected_output"]
            )
            
            response = await llm_service.generate(prompt)
            
            # Try to parse as JSON, otherwise use raw response
            try:
                result = json.loads(response["content"])
            except:
                result = {
                    "code": response["content"],
                    "explanation": "Generated code",
                    "dependencies": ["python"],
                    "file_name": "main.py",
                    "instructions": "Run: python main.py"
                }
            
            return {
                "task_id": task["id"],
                "agent": self.agent_type,
                "status": "completed",
                "output": result,
                "model_used": response["model"]
            }
            
        except Exception as e:
            logger.error(f"Coder agent error: {e}")
            return {
                "task_id": task["id"],
                "agent": self.agent_type,
                "status": "failed",
                "output": {"error": str(e)},
                "model_used": "error"
            }