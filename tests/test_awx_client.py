import pytest

from boip.core.awx_client import (
    AWXLaunchNotConfirmed,
    AWXNotConfigured,
    build_launch_payload,
    launch_job_template,
    list_job_templates,
)


def test_build_launch_payload_is_pure():
    payload = build_launch_payload(42, {"asset": "vm-07", "path": "memory_mb"})
    assert payload == {"template_id": 42, "extra_vars": {"asset": "vm-07", "path": "memory_mb"}}


def test_launch_without_confirm_raises_and_makes_no_network_call():
    with pytest.raises(AWXLaunchNotConfirmed):
        launch_job_template(42, {"asset": "vm-07"}, confirm=False)


def test_launch_defaults_to_not_confirmed():
    with pytest.raises(AWXLaunchNotConfirmed):
        launch_job_template(42, {"asset": "vm-07"})


def test_list_job_templates_requires_configuration(monkeypatch):
    monkeypatch.delenv("AWX_URL", raising=False)
    monkeypatch.delenv("AWX_TOKEN", raising=False)
    with pytest.raises(AWXNotConfigured):
        list_job_templates()
