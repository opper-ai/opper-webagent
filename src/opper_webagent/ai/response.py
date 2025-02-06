from opperai import Opper
from opperai.types import CallConfiguration

opper = Opper()

def bake_response(raw_response: str, response_model):
    """Structure and validate a raw response according to a provided schema model."""
    try:
        result, _ = opper.call(
            name="bake_response",
            instructions="Given a raw text response, bake a final response.",
            input={
                "raw_response": raw_response,
            },
            model="gcp/gemini-1.5-flash-002-eu",
            output_type=response_model,
            configuration=CallConfiguration(evaluation={"enabled": False}),
        )
        return result
    except Exception as e:
        raise ValueError(f"Failed to validate response: {str(e)}") 