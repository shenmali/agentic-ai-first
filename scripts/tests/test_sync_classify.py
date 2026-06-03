from scripts.sync_spaces import classify_targets


def test_core_change_syncs_all_demos():
    changed = ["demos/_core/llm.py"]
    all_demos = ["01-react-from-scratch", "02-plan-execute"]
    assert classify_targets(changed, all_demos) == all_demos


def test_demo_change_syncs_only_that_demo():
    changed = ["demos/01-react-from-scratch/agent.py", "README.md"]
    all_demos = ["01-react-from-scratch", "02-plan-execute"]
    assert classify_targets(changed, all_demos) == ["01-react-from-scratch"]


def test_no_demo_change_syncs_nothing():
    changed = ["site/src/pages/index.astro"]
    all_demos = ["01-react-from-scratch"]
    assert classify_targets(changed, all_demos) == []


def test_sync_script_change_syncs_all_demos():
    changed = ["scripts/sync_spaces.py"]
    all_demos = ["01-react-from-scratch", "02-plan-execute"]
    assert classify_targets(changed, all_demos) == all_demos
