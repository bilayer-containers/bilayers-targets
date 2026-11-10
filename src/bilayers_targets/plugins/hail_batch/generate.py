"""Generate a standalone Hail Batch runner (run_batch.py) from a Bilayers config.

Unlike the interfaces, this target produces no UI and no Docker image. It writes a
command-line script that fans an algorithm's image out over many input files as
Hail Batch jobs, on the local machine (LocalBackend + Docker) or on the Hail Batch
Service (Google Cloud). The script needs only `hail` installed to run; it does not
import bilayers.
"""

from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader

from bilayers_schema import Citations, InterfaceInput
from bilayers_targets.shared.utils import generate_top_level_text

CITATION: Citations = {
    "name": "Hail Batch",
    "doi": "",
    "license": "MIT",
    "description": "Run many containerized jobs locally or on the Hail Batch Service (Google Cloud)",
}

FILE_TYPES = ("image", "measurement", "array", "file", "executable")
TEMPLATE_NAME = "hail_batch_template.py.j2"
OUTPUT_FILE = "run_batch.py"


def pick_chunked_input(inputs: dict[str, Any]) -> Optional[str]:
    """The input whose files are split across jobs: the first multi-file input, else the first file input."""
    file_inputs = [name for name, conf in inputs.items() if conf.get("type") in FILE_TYPES]
    for name in file_inputs:
        if inputs[name].get("file_count") == "multiple":
            return name
    return file_inputs[0] if file_inputs else None


def pick_output_dir_param(parameters: dict[str, Any]) -> Optional[str]:
    """The parameter that receives the output folder (output_dir_set: True), if any."""
    for name, conf in (parameters or {}).items():
        if conf.get("output_dir_set"):
            return name
    return None


def render_runner(interface_input: InterfaceInput) -> str:
    inputs = interface_input["inputs"] or {}
    parameters = interface_input["parameters"] or {}
    outputs = interface_input["outputs"] or {}

    chunked_input = pick_chunked_input(inputs)
    if chunked_input is None:
        raise RuntimeError("Hail Batch runner needs at least one file-type input to split across jobs.")

    output_dir_param = pick_output_dir_param(parameters)
    output_dir = parameters[output_dir_param].get("default") if output_dir_param else None
    if not output_dir:
        # Fall back to the first output's folder_name; the job tars whatever lands there.
        output_dir = next((o.get("folder_name") for o in outputs.values() if o.get("folder_name")), "/bilayers/output")

    file_inputs = {
        name: {
            "cli_tag": conf.get("cli_tag"),
            "folder_name": conf.get("folder_name") or f"/bilayers/{name}",
            "format": conf.get("format") or [],
            "optional": bool(conf.get("optional", False)),
            "label": conf.get("label", name),
            "description": conf.get("description", ""),
        }
        for name, conf in inputs.items()
        if conf.get("type") in FILE_TYPES
    }

    # Parameters the user can set on the command line. Secrets have no CLI form in Bilayers,
    # and the output-folder parameter is controlled by the runner itself.
    cli_parameters = {
        name: {
            "type": conf.get("type"),
            "label": conf.get("label", name),
            "description": conf.get("description", ""),
            "default": conf.get("default"),
            "optional": bool(conf.get("optional", False)),
            "options": [o.get("value") for o in (conf.get("options") or [])],
            "multiselect": bool(conf.get("multiselect", False)),
        }
        for name, conf in parameters.items()
        if name != output_dir_param and conf.get("type") != "secret"
    }

    docker_image = interface_input["docker_image"]
    image = f"{docker_image['org']}/{docker_image['name']}:{docker_image['tag']}"
    title, description = generate_top_level_text(CITATION, interface_input["citations"], output_html=False)

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent)), keep_trailing_newline=True)
    template = env.get_template(TEMPLATE_NAME)
    return template.render(
        title=title,
        description=description,
        algorithm=interface_input["output_dir"].name,
        image=image,
        platform=docker_image.get("platform", ""),
        cli_command=interface_input["exec_function"].get("cli_command", ""),
        cli_sequence=list(interface_input["cli_sequence"].values()),
        # Lists of [name, conf] pairs: Jinja's tojson sorts dict keys, and order matters for --help.
        file_inputs=list(file_inputs.items()),
        chunked_input=chunked_input,
        cli_parameters=list(cli_parameters.items()),
        output_dir_param=output_dir_param,
        output_dir=output_dir,
    )


def generate(interface_input: InterfaceInput) -> None:
    code = render_runner(interface_input)
    path = interface_input["output_dir"] / OUTPUT_FILE
    with open(path, "w") as f:
        f.write(code)
    path.chmod(0o755)
    print(f"{OUTPUT_FILE} generated successfully!!")
