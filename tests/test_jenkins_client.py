import pytest

from boip.core.jenkins_client import JenkinsNotConfigured, get_build_status, trigger_pipeline


def test_trigger_pipeline_requires_configuration(monkeypatch):
    monkeypatch.delenv("JENKINS_URL", raising=False)
    monkeypatch.delenv("JENKINS_USER", raising=False)
    monkeypatch.delenv("JENKINS_TOKEN", raising=False)
    with pytest.raises(JenkinsNotConfigured):
        trigger_pipeline("boip-remediation-approval", {"incident_id": 1})


def test_get_build_status_requires_configuration(monkeypatch):
    monkeypatch.delenv("JENKINS_URL", raising=False)
    monkeypatch.delenv("JENKINS_USER", raising=False)
    monkeypatch.delenv("JENKINS_TOKEN", raising=False)
    with pytest.raises(JenkinsNotConfigured):
        get_build_status("boip-remediation-approval", 42)


def test_trigger_pipeline_requires_all_three_vars(monkeypatch):
    monkeypatch.setenv("JENKINS_URL", "https://jenkins.example")
    monkeypatch.delenv("JENKINS_USER", raising=False)
    monkeypatch.delenv("JENKINS_TOKEN", raising=False)
    with pytest.raises(JenkinsNotConfigured):
        trigger_pipeline("boip-remediation-approval", {})
