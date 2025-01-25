from pydantic import BaseModel, Field
from typing import Literal, Tuple

class Action(BaseModel):
    thoughts: str
    action: Literal["navigate", "click", "type", "scroll_down", "scroll_up", "look", "wait", "finished"]
    action_goal: str
    param: str = Field(description="The parameter for the action (e.g. URL for navigate, text for type, visual element description for click)")

class ActionResult(BaseModel):
    success: bool
    error: str = None
    output: str = None

class RelevantInteraction(BaseModel):
    type: str
    label: str
    description: str

class ScreenOutput(BaseModel):
    observation: str
    reflection: str
    relevant_page_actions: list[RelevantInteraction]

class Decision(BaseModel):
    observation: str
    reflection: str
    subgoal: str 