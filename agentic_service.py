class ServiceResult:
    """Simple result object to mimic CrewAI result structure"""
    def __init__(self, original_text: str, reversed_text: str):
        self.original_text = original_text
        self.reversed_text = reversed_text
        self.raw = reversed_text
        self.json_dict = {
            "original_text": original_text,
            "reversed_text": reversed_text,
            "task": "reverse_echo"
        }

class AgenticService:
    """Simple service that reverses input text"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    async def execute_task(self, input_data: dict) -> ServiceResult:
        """
        Execute reverse echo task
        
        Args:
            input_data: Dictionary containing 'input_string' key
            
        Returns:
            ServiceResult with reversed text
        """
        text = input_data.get("input_string", "")
        
        if self.logger:
            self.logger.info(f"Processing reverse echo for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        # simple reverse operation
        reversed_text = text[::-1]
        
        if self.logger:
            self.logger.info(f"Reverse echo completed: '{reversed_text[:50]}{'...' if len(reversed_text) > 50 else ''}'")
        
        return ServiceResult(text, reversed_text)

def get_agentic_service(logger=None):
    """
    Factory function to get the appropriate service for this branch.
    This enables easy switching between different implementations across branches.
    
    Main branch: Simple text reversal service (no dependencies)
    Other branches: CrewAI, LangChain, n8n implementations
    """
    return AgenticService(logger) 