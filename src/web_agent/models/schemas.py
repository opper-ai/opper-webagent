from pydantic import BaseModel
from typing import Literal, Tuple

class Action(BaseModel):
    thoughts: str
    action: Literal["navigate", "click", "type", "scroll_down", "scroll_up", "look", "wait", "finished"]
    action_goal: str
    param: str

class ActionResult(BaseModel):
    success: bool
    error: str = None
    output: str = None

class RelevantInteraction(BaseModel):
    type: str
    description: str
    label: str
    #xy_coordinate: Tuple[float, float] = (0.0, 0.0)

class ScreenOutput(BaseModel):
    observation: str
    reflection: str
    relevant_page_actions: list[RelevantInteraction]

class Decision(BaseModel):
    observation: str
    reflection: str
    subgoal: str 