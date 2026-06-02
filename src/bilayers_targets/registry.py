from importlib import import_module

available_ifaces = {}

_INTERFACE_MODULES = {
    "gradio": "bilayers_targets.interfaces.gradio.generate",
    "jupyter": "bilayers_targets.interfaces.jupyter.generate",
    "streamlit": "bilayers_targets.interfaces.streamlit.generate",
    "cellprofiler_plugin": "bilayers_targets.plugins.cellprofiler_plugin.generate",
}

for name, module_name in _INTERFACE_MODULES.items():
    try:
        mod = import_module(module_name)
        available_ifaces[name] = mod

    except Exception:
        # optional dependency missing
        pass