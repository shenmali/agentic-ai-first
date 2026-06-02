import os

# Gradio runs a version check / analytics call over the network when imported,
# which makes the app smoke tests flaky and slow (and non-hermetic). Disable it
# for the whole test process. Set before any test imports gradio.
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
