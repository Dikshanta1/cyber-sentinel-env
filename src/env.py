import os
import tempfile
import shutil
import subprocess
from typing import Tuple, Dict, Any

from .models import Action, Observation, Reward
from .tasks import get_task

class CyberEnvironment:
    def __init__(self, task_name: str = "recon"):
        self.jail_dir = None
        self.current_cwd = None
        self.step_count = 0
        self.max_steps = 30 # 30 steps to allow for more exploration
        
        # Load the specific task logic
        self.task = get_task(task_name)
        self.output_history = [] # Tracks everything the agent sees for the grader

    def reset(self) -> Observation:
        """Creates a fresh sandbox and sets up the specific task files."""
        if self.jail_dir and os.path.exists(self.jail_dir):
            shutil.rmtree(self.jail_dir)

        self.jail_dir = tempfile.mkdtemp(prefix="cyber_jail_")
        self.current_cwd = self.jail_dir
        self.step_count = 0
        self.output_history = []

        # Run the specific task's setup logic
        self.task.setup(self.jail_dir)

        initial_msg = f"System initialized. Task: {self.task.name} ({self.task.difficulty} difficulty). Start exploring!"
        self.output_history.append(initial_msg)
        
        return Observation(output=initial_msg, error=False)

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """Executes the action and runs the grader."""
        self.step_count += 1
        command = action.command
        self.output_history.append(f"> {command}")
        
        # 1. Handle "cd" manually
        if command.strip().startswith("cd "):
            target_dir = command.strip()[3:].strip()
            
            # Handle relative paths
            if target_dir.startswith("/"):
                # Absolute path - map it to jail_dir root
                new_path = os.path.abspath(os.path.join(self.jail_dir, target_dir.lstrip("/")))
            else:
                # Relative path
                new_path = os.path.abspath(os.path.join(self.current_cwd, target_dir))

            # Ensure we stay within the jail
            normalized_new_path = os.path.normpath(new_path)
            normalized_jail = os.path.normpath(self.jail_dir)
            
            if not normalized_new_path.startswith(normalized_jail):
                obs = Observation(output="Permission denied. Cannot escape jail.", error=True)
            elif os.path.isdir(new_path):
                self.current_cwd = new_path
                obs = Observation(output=f"Changed directory. Current: {self._get_virtual_path()}", error=False)
            else:
                obs = Observation(output=f"cd: {target_dir}: No such file or directory", error=True)
        
        # 2. Execute other bash commands
        else:
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.current_cwd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output_text = result.stdout if result.stdout else result.stderr
                is_error = result.returncode != 0
                
                if not output_text.strip():
                    output_text = "[Command executed with no output]"
                    
                obs = Observation(output=output_text.strip(), error=is_error)
            except subprocess.TimeoutExpired:
                obs = Observation(output="Error: Command timed out.", error=True)
            except Exception as e:
                obs = Observation(output=f"System error: {str(e)}", error=True)

        self.output_history.append(obs.output)

        # 3. Calculate Reward using the Task's Grader
        current_score = self.task.grade(self.output_history)
        reward = Reward(score=current_score)

        # 4. Check termination conditions (Done if max steps reached OR if they won)
        done = self.step_count >= self.max_steps or current_score >= 1.0
        
        return obs, reward, done, {"step_count": self.step_count, "task": self.task.name}

    def state(self) -> Dict[str, Any]:
        return {
            "virtual_cwd": self._get_virtual_path(),
            "step_count": self.step_count,
            "max_steps": self.max_steps,
            "task_name": self.task.name
        }

    def _get_virtual_path(self) -> str:
        if self.current_cwd == self.jail_dir:
            return "/"
        return self.current_cwd.replace(self.jail_dir, "")

# --- QUICK TEST BLOCK ---
if __name__ == "__main__":
    # Let's test the "Recon" task to see if the grader works!
    env = CyberEnvironment(task_name="recon")
    env.reset()
    
    print("Action: ls -la home/user/.secret_config")
    obs, rew, done, info = env.step(Action(command="ls -la home/user/.secret_config"))
    
    print("Action: cat home/user/.secret_config/flag.txt")
    obs, rew, done, info = env.step(Action(command="cat home/user/.secret_config/flag.txt"))
    
    print(f"\nFinal Output: {obs.output}")
    print(f"Final Score: {rew.score} (Should be 1.0)")
    print(f"Is Done: {done} (Should be True)")