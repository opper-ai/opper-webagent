from opperai import Opper
from opperai.types import ImageInput, Message, CallConfiguration
from PIL import Image
import re
import logging

opper = Opper()

def find_coordinates(image_path: str, input: str, debug: bool = False):
    f = opper.functions.create(
        model="opper/molmo-7b-d-0924",
        instructions="given a screenshot, find the coordinates of the object in question",
        name="find_coordinate",
    )
    output = f.chat(
        messages=[
            Message(
                role="user",
                content="Given a screenshot, find the coordinates of the object in question. Answer with the coordinates in the format Click(x, y) where x and y are percentages of the screen",
            ),
            Message(role="assistant", content="ok"),
            Message(
                role="user",
                content=[
                    {"type": "text", "text": input},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": ImageInput.from_path(image_path)._opper_image_input,
                        },
                    },
                ],
            ),
        ],
    )

    match = re.search(r'Click\((\d+\.?\d*),\s*(\d+\.?\d*)\)', output.message)
    if match:
        x_percent, y_percent = map(float, match.groups())
        
        with Image.open(image_path) as img:
            width, height = img.size
        
        x_pixel = (x_percent / 100) * width
        y_pixel = (y_percent / 100) * height
        
        return x_pixel, y_pixel
    else:
        raise ValueError("Couldn't extract coordinates from the output") 