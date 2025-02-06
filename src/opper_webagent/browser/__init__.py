"""Browser interaction functionality for web agent."""

from .click import click_at_coordinates, draw_click_dot
from .navigate import navigate_to_url
from .screenshot import take_screenshot, set_page_zoom
from .scroll import scroll_page
from .type import type_text
from .setup import setup_browser

__all__ = [
    'click_at_coordinates',
    'draw_click_dot',
    'navigate_to_url',
    'take_screenshot',
    'set_page_zoom',
    'scroll_page',
    'type_text',
    'setup_browser',
] 