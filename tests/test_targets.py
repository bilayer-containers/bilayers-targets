"""Self-contained unit tests for the targets package.

These test only this repo's own surface - the registry and each generate()
entry point. They depend on bilayers-schema for types (a real dependency of
this package) but never on the bilayers orchestrator, and never run the full
pipeline. End-to-end generation is an integration concern owned by bilayers.

  G1 - registry / public surface
  G2 - entry-point type contract (validated via pydantic against InterfaceInput)
"""

import inspect

import pytest
from pydantic import TypeAdapter, ValidationError

from bilayers_schema import InterfaceInput
from bilayers_targets import available_ifaces

INTERFACES = ["gradio", "jupyter", "streamlit", "cellprofiler_plugin"]

# Build one runtime validator directly from the existing TypedDict - no parallel
# model, so bilayers-schema stays the single source of truth for the contract.
INTERFACE_INPUT_ADAPTER = TypeAdapter(InterfaceInput)


# --- G1: registry / public surface --------------------------------------------


def test_registry_exposes_expected_interfaces() -> None:
    assert set(available_ifaces) == set(INTERFACES)


@pytest.mark.parametrize("name", INTERFACES)
def test_each_module_has_callable_generate(name: str) -> None:
    module = available_ifaces[name]
    assert callable(getattr(module, "generate", None)), f"{name} has no callable generate()"


# --- G2: entry-point type contract --------------------------------------------


@pytest.mark.parametrize("name", INTERFACES)
def test_generate_takes_single_parameter(name: str) -> None:
    sig = inspect.signature(available_ifaces[name].generate)
    assert len(sig.parameters) == 1, f"{name}.generate should take exactly one argument, got {list(sig.parameters)}"


def test_well_formed_input_validates(interface_input: dict) -> None:
    # A complete InterfaceInput passes runtime type validation.
    INTERFACE_INPUT_ADAPTER.validate_python(interface_input)


def test_missing_required_key_is_rejected(interface_input: dict) -> None:
    # Dropping a required top-level key must fail validation.
    bad = dict(interface_input)
    del bad["docker_image"]
    with pytest.raises(ValidationError):
        INTERFACE_INPUT_ADAPTER.validate_python(bad)


def test_missing_nested_required_key_is_rejected(interface_input: dict) -> None:
    # docker_image is a total TypedDict: dropping one of its fields must fail.
    bad = dict(interface_input)
    bad["docker_image"] = {"org": "bilayer", "name": "example", "tag": "1.0.0"}  # no platform
    with pytest.raises(ValidationError):
        INTERFACE_INPUT_ADAPTER.validate_python(bad)
