"""
CrewAI Crew Definition

DEVELOPERS: This is where you customize your CrewAI crew!

This file contains the crew configuration separate from the service wrapper.
You can modify agents, tasks, and crew behavior here without touching
the Masumi API compliance code in agentic_service.py.

To customize:
1. Edit config/agents.yaml for agent definitions
2. Edit config/tasks.yaml for task definitions  
3. Modify this file for crew logic and flow
"""

import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class MyCrew():
    """A simple CrewAI setup"""

    @agent
    def summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['summarizer'],
            verbose=True
        )

    @task
    def summarization_task(self) -> Task:
        return Task(
            config=self.tasks_config['summarization_task']
        )

    @crew
    def crew(self) -> Crew:
        """Creates the crew with defined agents and tasks"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )