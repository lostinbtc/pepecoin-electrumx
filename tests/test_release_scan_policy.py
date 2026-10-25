"""The candidate security gate must fail closed without exposing matched secrets."""
import importlib.util
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[1]/'scripts/check_image_scan.py'
spec = importlib.util.spec_from_file_location('check_image_scan', path)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

def report(*findings, secrets=None):
    return {'ArtifactType': 'container_image', 'Metadata': {'ImageID': 'sha256:' + '0'*64},
            'Results': [{'Vulnerabilities': list(findings), 'Secrets': secrets or []}]}

def test_missing_scan_does_not_pass():
    with pytest.raises(ValueError):
        policy.evaluate({})

def finding(severity, fixed=None):
    return {'VulnerabilityID': 'TEST-1', 'Severity': severity, 'FixedVersion': fixed}

def test_critical_always_blocks():
    assert not policy.evaluate(report(finding('CRITICAL')))['candidate_gate_passed']

def test_fixable_high_blocks():
    assert not policy.evaluate(report(finding('HIGH', '2')))['candidate_gate_passed']

def test_unfixed_high_is_disclosed():
    result = policy.evaluate(report(finding('HIGH')))
    assert result['candidate_gate_passed']
    assert result['high_findings_without_available_fix'] == ['TEST-1']

def test_secret_blocks_without_leaking_match():
    result = policy.evaluate(report(secrets=[{'Match': 'deliberately-sensitive-test-value'}]))
    assert not result['candidate_gate_passed']
    assert 'deliberately-sensitive-test-value' not in str(result)
