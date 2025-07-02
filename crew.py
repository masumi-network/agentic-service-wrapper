"""
CrewAI Crew Definition

DEVELOPERS: This is where you customize your CrewAI crew!

This file contains the crew configuration separate from the service wrapper.
You can modify agents, tasks, and crew behavior here without touching
the Masumi API compliance code in agentic_service.py.
"""

from crewai import Agent, Crew, Task
from logging_config import setup_logging

class MyCrew:
    """Simple CrewAI crew using direct instantiation """
    
    def __init__(self, verbose=True, logger=None):
        self.verbose = verbose
        self.logger = logger or setup_logging()
        self.crew = self.create_crew()
        if self.logger:
            self.logger.info("MyCrew initialized")

    def create_crew(self):
        if self.logger:
            self.logger.info("Creating crew with agents")
        
        # Define your agents here 
        summarizer = Agent(
            role='Text Summarizer',
            goal='Create clear and concise summaries of any given text',
            backstory='You\'re an expert text summarizer with the ability to distill complex information into clear, actionable insights. You focus on identifying the most important points while maintaining the original context and meaning.',
            verbose=self.verbose
        )

        if self.logger:
            self.logger.info("Created summarizer agent")

        # Define your tasks here 
        summarization_task = Task(
            description='Summarize the following text in 2-3 clear, concise sentences. Focus on the main points and key information.\n\nText to summarize: {text}',
            expected_output='A 2-3 sentence summary highlighting the main points and key information',
            agent=summarizer
        )

        # Create crew with agents and tasks 
        crew = Crew(
            agents=[summarizer],
            tasks=[summarization_task],
            verbose=self.verbose
        )
        
        if self.logger:
            self.logger.info("Crew setup completed")
            
        return crew