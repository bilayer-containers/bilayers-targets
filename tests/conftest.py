"""Shared fixtures for the targets unit tests.

The `interface_input` fixture is a hand-built, well-formed InterfaceInput -
the exact payload each generate() consumes. It is defined here (not pulled
from bilayers) so the tests stay self-contained: targets depends on
bilayers-schema for the *types*, never on the bilayers orchestrator.
"""

import pytest


@pytest.fixture
def interface_input(tmp_path) -> dict:
    """A minimal but type-complete InterfaceInput payload."""
    return {
        "output_dir": tmp_path,
        "inputs": {
            "input_images": {
                "name": "input_images",
                "type": "image",
                "label": "Input images",
                "subtype": ["grayscale"],
                "description": "Images to process",
                "cli_tag": "--input",
                "cli_order": 0,
                "default": "directory",
                "optional": False,
                "format": ["tiff"],
                "folder_name": "/bilayers/input_images",
                "file_count": "multiple",
                "section_id": "inputs",
                "mode": "beginner",
                "depth": False,
                "timepoints": False,
                "tiled": False,
                "pyramidal": False,
            }
        },
        "outputs": {
            "output_images": {
                "name": "output_images",
                "type": "image",
                "label": "Output images",
                "subtype": ["grayscale"],
                "description": "Processed images",
                "cli_tag": "None",
                "cli_order": 0,
                "default": "directory",
                "optional": False,
                "format": ["tiff"],
                "folder_name": "/bilayers/output_images",
                "file_count": "single",
                "section_id": "outputs",
                "mode": "beginner",
            }
        },
        "parameters": {
            "threshold": {
                "name": "threshold",
                "type": "float",
                "label": "Threshold",
                "description": "A tunable threshold",
                "default": 1.0,
                "cli_tag": "--threshold",
                "optional": False,
                "section_id": "input-args",
                "mode": "beginner",
            }
        },
        "display_only": {},
        "exec_function": {
            "name": "generate_cli_command",
            "cli_command": "python -m example",
            "hidden_args": {},
        },
        "citations": {
            "Example Tool": {
                "name": "Example Tool",
                "doi": "10.0000/example",
                "license": "MIT",
                "description": "An example tool",
            }
        },
        "docker_image": {
            "org": "bilayer",
            "name": "example",
            "tag": "1.0.0",
            "platform": "linux/amd64",
        },
        "cli_sequence": {
            "input_images": {"name": "input_images", "source": "input", "cli_tag": "--input"},
            "threshold": {"name": "threshold", "source": "parameter", "cli_tag": "--threshold"},
        },
    }
