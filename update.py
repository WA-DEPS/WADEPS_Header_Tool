"""
Run this before pushing to Git.
Syncs the agency register and UOF template into the HTML validators
so they stay standalone without needing external file fetches.
"""

import json
import re


def build_registry_from_register(register_path: str) -> tuple[list[dict], list[str]]:
    with open(register_path, 'r') as f:
        register = json.load(f)

    registry = []
    ori_codes = []

    for name, info in register['agencies'].items():
        entry = {
            'name': name,
            'ori': info.get('ori') or 'N/A',
            'type': info.get('agency_type', 'N/A'),
            'city': info.get('city', 'N/A'),
            'county': info.get('county', 'N/A')
        }
        registry.append(entry)

        if info.get('ori'):
            ori_codes.append(info['ori'])

    registry.sort(key=lambda x: x['name'])
    ori_codes = sorted(set(ori_codes))

    return registry, ori_codes


def update_cad_validator(html_path: str, registry: list[dict], ori_codes: list[str]):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    registry_json = json.dumps(registry, separators=(',', ': '))
    pattern = r'const AGENCY_REGISTRY = \[.*?\];'
    replacement = f'const AGENCY_REGISTRY = {registry_json};'
    html, count = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)
    if count == 0:
        print("  Couldn't find AGENCY_REGISTRY in the HTML, skipping")
        return False

    ori_json = json.dumps(ori_codes)
    pattern = r'"valid_ori_codes":\s*\[.*?\]'
    replacement = f'"valid_ori_codes": {ori_json}'
    html, count = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)
    if count == 0:
        print("  Couldn't find valid_ori_codes in the HTML, skipping")
        return False

    pattern = r'View \d+ Agencies & ORI Codes'
    replacement = f'View {len(registry)} Agencies & ORI Codes'
    html = re.sub(pattern, replacement, html)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return True


def update_uof_validator(html_path: str):
    with open('templates/wadeps_uof_template.json', 'r') as f:
        template = json.load(f)

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    m = re.search(r'let TPL = ({.*?});\s*\n', html, re.DOTALL)
    if not m:
        print("  Couldn't find TPL in the UOF HTML, skipping")
        return False

    old_tpl = json.loads(m.group(1))
    old_tpl['headers'] = template['headers']
    old_tpl['validations'] = template['validations']

    new_tpl_str = json.dumps(old_tpl, separators=(',', ':'))
    html = html.replace(m.group(1), new_tpl_str)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return True


def main():
    register_path = 'templates/wadeps_agency_register.json'
    cad_html_path = 'cad_validator/cad_validator.html'
    uof_html_path = 'html_validator/wadeps_validator.html'

    print("Reading agency register...")
    registry, ori_codes = build_registry_from_register(register_path)
    print(f"  {len(registry)} agencies, {len(ori_codes)} ORI codes")

    print(f"\nUpdating {cad_html_path}...")
    if update_cad_validator(cad_html_path, registry, ori_codes):
        print(f"  {len(registry)} agencies embedded")

    print(f"\nUpdating {uof_html_path}...")
    if update_uof_validator(uof_html_path):
        print("  Template synced")

    print("\nAll synced. Review the diff and commit.")


if __name__ == '__main__':
    main()
