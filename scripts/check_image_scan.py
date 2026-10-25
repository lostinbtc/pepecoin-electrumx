"""Evaluate Trivy results without printing secret matches; write a public summary.

Candidate gate: block detected secrets, any Critical findings, and fixable High
findings. Unfixed High findings remain visible; passing is not a security certificate.
--report-only records findings but MUST NOT authorize image publication.
"""
import argparse
import collections
import json
from pathlib import Path

def evaluate(report):
    metadata = report.get('Metadata', {})
    if (report.get('ArtifactType') != 'container_image'
            or not str(metadata.get('ImageID', '')).startswith('sha256:')
            or not isinstance(report.get('Results'), list)
            or not report['Results']):
        raise ValueError('Missing or malformed container-image scan; refusing to pass')
    findings = [v for result in report.get('Results', []) for v in result.get('Vulnerabilities', [])]
    secrets = sum(len(result.get('Secrets', [])) for result in report.get('Results', []))
    blockers = [v for v in findings if v.get('Severity') == 'CRITICAL' or
                (v.get('Severity') == 'HIGH' and v.get('FixedVersion'))]
    return {
        'artifact': report.get('ArtifactName'),
        'image_id': report.get('Metadata', {}).get('ImageID'),
        'severity_counts': dict(collections.Counter(v.get('Severity', 'UNKNOWN') for v in findings)),
        'secret_findings_count': secrets,
        'candidate_gate_passed': not secrets and not blockers,
        'blocking_findings': [{key: v.get(key) for key in
            ('VulnerabilityID','PkgName','InstalledVersion','FixedVersion','Severity','Status')} for v in blockers],
        'high_findings_without_available_fix': sorted({v['VulnerabilityID'] for v in findings
            if v.get('Severity') == 'HIGH' and not v.get('FixedVersion')}),
        'notice': 'Package scan only; exploit reachability and third-party integrations are not established.',
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report-only', action='store_true')
    args = parser.parse_args()
    summary = evaluate(json.loads(args.report.read_text()))
    summary['report_only'] = args.report_only
    args.output.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    if not args.report_only and not summary['candidate_gate_passed']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
