from pydantic import BaseModel
from typing import Dict, List, Optional

class TaskProgress(BaseModel):
    task_id: str
    title: str
    description: str
    required_item: str
    reward: str
    completed: bool = False

class PuzzleProgress(BaseModel):
    main_puzzle: str
    solution_requirements: List[str]
    total_tasks: int
    completed_tasks: int
    tasks: Dict[str, TaskProgress]
    
    def calculate_progress(self) -> float:
        """Calculate completion percentage"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    def complete_task(self, task_id: str) -> Optional[str]:
        """Complete a task and return the reward if successful"""
        if task_id in self.tasks and not self.tasks[task_id].completed:
            self.tasks[task_id].completed = True
            self.completed_tasks += 1
            return self.tasks[task_id].reward
        return None

    def is_puzzle_solved(self) -> bool:
        """Check if all tasks are completed"""
        return self.completed_tasks == self.total_tasks

    def can_perform_task(self, task_id: str, inventory: Dict[str, int]) -> bool:
        """Check if a task can be performed based on inventory"""
        if task_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        if task.completed:
            return False
            
        required_items = task.required_item.split(', ')
        if 'All items' in required_items:
            # Check if player has all possible items for their character
            all_items = {item.required_item for item in self.tasks.values()}
            return all(item in inventory for item in all_items if item != 'All items')
            
        return all(item in inventory for item in required_items)

    def get_available_tasks(self, inventory: Dict[str, int]) -> List[TaskProgress]:
        """Get list of tasks that can be performed with current inventory"""
        return [
            task for task in self.tasks.values()
            if not task.completed and self.can_perform_task(task.task_id, inventory)
        ]