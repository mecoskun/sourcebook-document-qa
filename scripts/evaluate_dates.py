"""Check that document dates and event dates are not interchangeable."""
import json
from pathlib import Path

import httpx

CASES = [
    ((Path(__file__).resolve().parents[1] / 'samples/employee-handbook.txt').read_text(encoding='utf-8'), 'What year was Northstar Studio founded?', None),
    ('This handbook is effective 1 January 2026.', 'When was the company founded?', None),
    ('This handbook is effective 1 January 2026.', 'When is the handbook effective?', '2026'),
    ('Northstar was founded in 2019. This handbook is effective 1 January 2026.', 'When was Northstar founded?', '2019'),
]


def main():
    rows = []
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=190, trust_env=False) as client:
        for text, question, expected in CASES:
            r = client.post('/api/sessions')
            r.raise_for_status()
            client.headers['Authorization'] = 'Bearer ' + r.json()['token']
            try:
                r = client.post('/api/documents', files={'file': ('dates.txt', text.encode())})
                r.raise_for_status()
                r = client.post('/api/questions', json={'question': question})
                r.raise_for_status()
                answer = r.json()
                passed = (answer['mode'] == 'abstained' if expected is None else
                          answer['mode'] == 'generated' and expected in answer['answer'])
                rows.append({'fixture': text, 'question': question, 'passed': passed, **answer})
                print(passed, question, answer['answer'], flush=True)
            finally:
                client.delete('/api/documents').raise_for_status()
    report = {'cases': len(rows), 'passed': sum(r['passed'] for r in rows), 'results': rows}
    (Path(__file__).resolve().parents[1] / 'docs/date-regression.json').write_text(json.dumps(report, indent=2)+'\n')
    if report['passed'] != report['cases']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
