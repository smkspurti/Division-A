import sys, os
from pathlib import Path
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
sys.path.insert(0, 'd:/genai hack')

from engine.ehr_parser import extract_ehr_facts
from engine.criterion_parser import parse_criteria
from engine.eligibility_matcher import match_criteria

ehr = Path('data/sample_ehrs/patient_001_diabetes.txt').read_text('utf-8')
trial = Path('data/sample_trials/trial_001_glp1_diabetes.txt').read_text('utf-8')

print('Parsing EHR...')
f = extract_ehr_facts(ehr, client)
print('Parsing Criteria...')
c = parse_criteria(trial, client)
print(f'Matching {len(c)} criteria...')

for i, crit in enumerate(c):
    from engine.eligibility_matcher import _match_single_criterion
    import json
    try:
        res = _match_single_criterion(json.dumps(f), crit, client)
        if 'processing error' in res.get('rationale', ''):
            print('Criterion', i, 'FAILED:', res.get('missing_data'))
        else:
            print('Criterion', i, 'SUCCESS')
    except Exception as e:
        print('Criterion', i, 'FATAL ERROR:', e)
