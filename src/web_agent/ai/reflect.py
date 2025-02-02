from opperai import Opper
from opperai.types import CallConfiguration
from ..models import Reflection

opper = Opper()

def reflect_on_progress(goal, current_url, trajectory, current_view):
    """Reflect on the current progress and decide whether to continue, finish, or break."""
    instruction = """Given the goal, the content of the current page and the trajectory of what you have attempted, decide on weather to continue working towards the goal. Once you have fully completed the goal, you can decide to complete the task with finish. If you are repeatedly failing to complete the goal, you can decide to break.

    Important:
    * If the trajectory is empty, you should always continue .
    * Always continue until the trajectory fully shows you have fully met the goal, including collecting any necessary data and information. Provide subgoal as input to the continue decision.
    * If you have repeated the same action multiple times without success, you may break the task
    * The finish decision should be used when you have fully met the goal. Provide all the necessary details as params.
    """
    
    subgoal, _ = opper.call(
        name="reflect_on_progress",
        instructions=instruction,
        input={
            "goal": goal,
            "trajectory": trajectory[-10:],
            "current_url": current_url, 
            "current_page": current_view.observation
        },
        model="fireworks/deepseek-v3",
        output_type=Reflection,
        configuration=CallConfiguration(evaluation={"enabled": False}),
    )
    return subgoal 