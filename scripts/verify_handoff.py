from pathlib import Path
import json,sys
root = Path(__file__).resolve().parent.parent
required = ["AGENTS.md","CODEX_FIRST_PROMPT.md","docs/requirements/PRD_v1.2.md","docs/context/CHAT_HANDOFF.md","docs/context/CURRENT_STATE.md","docs/tasks/BACKLOG.md","docs/design/UI_CONTRACT.md","docs/interview/INTERVIEW_GUIDE.md","docs/data/demo_fixture.json"]
missing = [x for x in required if not (root/x).is_file()]
counts = {d:len(list((root/'references'/d).glob('WB-*.png'))) for d in ('desktop','tablet','mobile')}
calendar = len(list((root/'references'/'calendar_scenarios').glob('*.png')))
backlog = json.loads((root/'docs/tasks'/'backlog.json').read_text(encoding='utf-8'))
fixture=json.loads((root/'docs/data/demo_fixture.json').read_text(encoding='utf-8'))
assert len(set(x['id'] for x in backlog))==18, 'Backlog must have 18 unique tasks'
assert all((root/'docs/tasks'/f"{x['id']}.md").exists() for x in backlog)
assert not missing, f'Missing required: {missing}'
assert counts=={'desktop':18,'tablet':18,'mobile':18}, f'Unexpected UI counts: {counts}'
assert calendar>=12, f'Unexpected calendar PNG count: {calendar}'
assert len(fixture['employees'])>=12 and len(fixture['spaces'])>=27
print('OK — Codex handoff documents and visual assets verified.')
print('Tasks:',len(backlog),'Responsive screens:',sum(counts.values()),'Calendar PNGs:',calendar,'Demo employees:',len(fixture['employees']))
print('This is NOT a product test; React/FastAPI and deployments are not present.')
