from pydantic import BaseModel, Field

class Action(BaseModel):
    command: str = Field(
        ..., 
        description="The bash command to execute in the terminal (e.g., 'ls -la', 'cat flag.txt')."
    )

class Observation(BaseModel):
    output: str = Field(
        ..., 
        description="The standard output or standard error returned by the terminal."
    )
    error: bool = Field(
        ..., 
        description="True if the command failed or returned a non-zero exit code."
    )

class Reward(BaseModel):
    score: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0, 
        description="The current progress of the agent on the task, from 0.0 to 1.0."
    )