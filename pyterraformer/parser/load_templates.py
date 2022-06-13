import os

import jinja2

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../serializer/templates")
template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_PATH)
env = jinja2.Environment(
    loader=template_loader, autoescape=True, keep_trailing_newline=True
)


def get_template(name: str):
    return env.get_template(f"{name}.tf")
