"""
WADEPS CSV Validator
Validates CSV files against WADEPS SmartForm Template requirements
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
import sys
import os
import argparse


class WADEPSValidator:
    """WADEPS data validation class"""
    
    def __init__(self, template_path: str = None):
        self.template_path = template_path or "../templates/wadeps_uof_template.json"
        self.headers = []
        self.validations = {}
        
    def load_template_data(self) -> Dict[str, Any]:
        """Load headers and validation rules from JSON template"""
        print(f"Reading template: {self.template_path}")

        try:
            with open(self.template_path, 'r') as f:
                data = json.load(f)

            self.headers = data.get('headers', [])
            self.validations = data.get('validations', {})

            print(f"{len(self.headers)} headers")
            print(f"{len(self.validations)} validation rules")

            return data

        except Exception as e:
            print(f"Error reading template: {e}")
            raise
    
#template_based_validation
    
    def validate_csv(self, csv_path: str) -> Dict[str, Any]:
        """Validate a CSV file against the template"""
        print(f"\nValidating: {Path(csv_path).name}")
        
        results = {
            'file': str(Path(csv_path).name),
            'timestamp': datetime.now().isoformat(),
            'header_validation': {
                'matching': [],
                'missing': [],
                'extra': [],
                'is_valid': False
            },
            'data_validation': {
                'errors': [],
                'warnings': [],
                'total_rows': 0
            },
            'subject_id_validation': {
                'unknown_count': 0,
                'name_count': 0,
                'invalid_count': 0,
                'examples': []
            }
        }
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                csv_headers = reader.fieldnames
                
#header_check
                template_set = set(self.headers)
                csv_set = set(csv_headers)
                
                results['header_validation']['matching'] = list(template_set & csv_set)
                results['header_validation']['missing'] = list(template_set - csv_set)
                results['header_validation']['extra'] = list(csv_set - template_set)
                results['header_validation']['is_valid'] = len(results['header_validation']['missing']) == 0
                
                print(f"  Headers: {len(results['header_validation']['matching'])} matching, "
                      f"{len(results['header_validation']['missing'])} missing, "
                      f"{len(results['header_validation']['extra'])} extra")
                
#row_processing
                for row_num, row in enumerate(reader, start=2):
                    results['data_validation']['total_rows'] += 1
                    
#field_validation
                    for header in csv_headers:
                        if header in self.validations:
                            value = row.get(header, '')
                            validation_result = self._validate_field(header, value, row_num)
                            if validation_result:
                                if validation_result['severity'] == 'error':
                                    results['data_validation']['errors'].append(validation_result)
                                else:
                                    results['data_validation']['warnings'].append(validation_result)
                    
#special_validation_subject_id
                    if 'subject_id' in row:
                        subject_result = self._validate_subject_id(row['subject_id'], row_num)
                        if subject_result:
                            if subject_result['type'] == 'unknown':
                                results['subject_id_validation']['unknown_count'] += 1
                            elif subject_result['type'] == 'name':
                                results['subject_id_validation']['name_count'] += 1
                            elif subject_result['type'] == 'invalid':
                                results['subject_id_validation']['invalid_count'] += 1
                            
                            if len(results['subject_id_validation']['examples']) < 5:
                                results['subject_id_validation']['examples'].append(subject_result)
                
                print(f"  Validated {results['data_validation']['total_rows']} rows")
                print(f"  {len(results['data_validation']['errors'])} errors, "
                      f"{len(results['data_validation']['warnings'])} warnings")
                
                subject_issues = (results['subject_id_validation']['unknown_count'] + 
                                results['subject_id_validation']['name_count'] + 
                                results['subject_id_validation']['invalid_count'])
                if subject_issues > 0:
                    print(f"  Subject ID issues: {subject_issues}")
                
        except Exception as e:
            print(f"  Error validating CSV: {e}")
            raise
        
        return results
    
    def _validate_field(self, header: str, value: str, row_num: int) -> Optional[Dict]:
        """Validate a single field value"""
        if not value or value.strip() == '':
            return None
        
        rule = self.validations.get(header)
        if not rule:
            return None
        
        value = value.strip()
        
#list_validation
        if rule['type'] == 'list':
            if value not in rule['values']:
#yes_no_case_check
                if len(rule['values']) == 2 and 'Yes' in rule['values'] and 'No' in rule['values']:
                    if value.lower() not in [v.lower() for v in rule['values']]:
                        return {
                            'row': row_num,
                            'column': header,
                            'value': value,
                            'error': f"Must be one of: {', '.join(rule['values'][:5])}{'...' if len(rule['values']) > 5 else ''}",
                            'severity': 'error'
                        }
                else:
                    return {
                        'row': row_num,
                        'column': header,
                        'value': value,
                        'error': f"Must be one of: {', '.join(rule['values'][:5])}{'...' if len(rule['values']) > 5 else ''}",
                        'severity': 'error'
                    }
        
#date_validation
        elif rule['type'] == 'date':
            if not re.match(r'^(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/\d{4}$', value):
                return {
                    'row': row_num,
                    'column': header,
                    'value': value,
                    'error': f"Invalid date format. Expected {rule.get('format', 'MM/DD/YYYY')}",
                    'severity': 'error'
                }
        
#time_validation
        elif rule['type'] == 'time':
            if not re.match(r'^\d{2}:\d{2}$', value):
                return {
                    'row': row_num,
                    'column': header,
                    'value': value,
                    'error': f"Invalid time format. Expected {rule.get('format', 'HH:MM')}",
                    'severity': 'error'
                }
        
#number_validation
        elif rule['type'] == 'number':
            try:
                num = float(value)
                if 'min' in rule and num < rule['min']:
                    return {
                        'row': row_num,
                        'column': header,
                        'value': value,
                        'error': f"Value must be >= {rule['min']}",
                        'severity': 'error'
                    }
                if 'max' in rule and num > rule['max']:
                    return {
                        'row': row_num,
                        'column': header,
                        'value': value,
                        'error': f"Value must be <= {rule['max']}",
                        'severity': 'error'
                    }
            except ValueError:
                return {
                    'row': row_num,
                    'column': header,
                    'value': value,
                    'error': "Must be a number",
                    'severity': 'error'
                }
        
#pattern_validation
        elif rule['type'] == 'pattern':
            if not re.match(rule['pattern'], value.upper()):
                return {
                    'row': row_num,
                    'column': header,
                    'value': value,
                    'error': rule.get('description', f"Must match pattern: {rule['pattern']}"),
                    'severity': 'error'
                }
        
        return None
    
    def _validate_subject_id(self, value: str, row_num: int) -> Optional[Dict]:
        """Validate subject_id format"""
        if not value or value.strip() == '':
            return None
        
        val = value.strip()
        
#unknown_check
        if val.lower() in ['unknown', 'unk']:
            return {
                'row': row_num,
                'value': val,
                'type': 'unknown',
                'error': 'Subject ID should not be "unknown"'
            }
        
#name_check
        if ' ' in val:
            parts = val.split()
            if len(parts) >= 2 and any(len(p) > 3 for p in parts):
                return {
                    'row': row_num,
                    'value': val,
                    'type': 'name',
                    'error': 'Subject ID appears to be a full name. Use initials instead'
                }
        
#initials_check
        if not re.match(r'^[A-Za-z]{1,4}$|^[A-Za-z](\.[A-Za-z])*\.?$', val):
            return {
                'row': row_num,
                'value': val,
                'type': 'invalid',
                'error': 'Subject ID must be initials (e.g., "JD", "J.D.", "J.D.S")'
            }
        
        return None
    
    def save_template_data(self, output_path: str = "../templates/wadeps_uof_template.json"):
        """Save extracted template data to JSON file"""
        template_data = {
            'headers': self.headers,
            'validations': self.validations,
            'totalHeaders': len(self.headers),
            'totalValidations': len(self.validations),
            'source': self.template_path,
            'convertedDate': datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        print(f"Template data saved to: {output_path}")
        return output_path
    
    def save_validation_results(self, results: Dict, output_path: str = None):
        """Save validation results to JSON file"""
        if not output_path:
#use_input_filename_as_base
            base_name = Path(results['file']).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/{base_name}_validation_{timestamp}.json"
        
#create_output_directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"  Results saved to: {output_path}")
        return output_path
    
    def generate_dashboard(self, results: Dict) -> str:
        """Generate HTML dashboard for validation results"""
        base_name = Path(results['file']).stem
        dashboard_path = f"output/{base_name}_dashboard.html"
        
#calculate_metrics
        total_rows = results.get('data_validation', {}).get('total_rows', 0)
        total_errors = len(results.get('data_validation', {}).get('errors', []))
        total_warnings = len(results.get('data_validation', {}).get('warnings', []))
        header_issues = len(results.get('header_validation', {}).get('missing', [])) + len(results.get('header_validation', {}).get('extra', []))
        subject_issues = (results.get('subject_id_validation', {}).get('unknown_count', 0) + 
                         results.get('subject_id_validation', {}).get('name_count', 0) + 
                         results.get('subject_id_validation', {}).get('invalid_count', 0))
        
        quality_score = max(0, 100 - (total_errors / max(total_rows, 1) * 100))
        
#determine_status
        hv = results.get('header_validation', {})
        if not hv.get('is_valid', False) or total_errors > 0:
            status = 'failed'
            status_color = '#e53e3e'
            status_text = 'Validation Failed'
        elif total_warnings > 0 or subject_issues > 0:
            status = 'warning'
            status_color = '#dd6b20'
            status_text = 'Warnings Found'
        else:
            status = 'passed'
            status_color = '#48bb78'
            status_text = 'Validation Passed'
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WADEPS Validation Results - {results['file']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ background: white; border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 10px 0; color: #333; }}
        .status-badge {{ display: inline-block; padding: 5px 10px; color: white; font-weight: bold; background: {status_color}; }}
        .stats {{ display: table; width: 100%; margin-bottom: 20px; }}
        .stat-row {{ display: table-row; }}
        .stat-card {{ display: table-cell; background: white; border: 1px solid #ddd; padding: 15px; text-align: center; }}
        .stat-card h3 {{ margin: 0 0 10px 0; color: #666; font-size: 12px; text-transform: uppercase; }}
        .stat-card .value {{ font-size: 1.5em; font-weight: bold; color: #333; margin: 0; }}
        .panel {{ background: white; border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; }}
        .panel h2 {{ margin: 0 0 15px 0; color: #333; }}
        .error-item {{ padding: 10px; border-left: 3px solid #e53e3e; background: #fef5f5; margin-bottom: 10px; }}
        .warning-item {{ padding: 10px; border-left: 3px solid #dd6b20; background: #fffaf0; margin-bottom: 10px; }}
        .error-item h4, .warning-item h4 {{ margin: 0 0 5px 0; color: #333; }}
        .error-item p, .warning-item p {{ margin: 0; color: #666; }}
        .meta {{ font-size: 11px; color: #999; margin-top: 5px; }}
        .recommendations {{ background: #ebf8ff; padding: 15px; border: 1px solid #bee3f8; }}
        .recommendations h3 {{ margin: 0 0 10px 0; color: #2b6cb0; }}
        .recommendations ul {{ margin: 0; padding-left: 20px; }}
        .recommendations li {{ margin-bottom: 5px; color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>WADEPS Validation Results</h1>
            <p>File: {results['file']} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <span class="status-badge">{status_text}</span>
        </div>
        
         <div class="stats">
             <div class="stat-row">
                 <div class="stat-card">
                     <h3>Total Rows</h3>
                     <div class="value">{total_rows}</div>
                 </div>
                 <div class="stat-card">
                     <h3>Headers Match</h3>
                     <div class="value" style="color: {'#48bb78' if hv.get('is_valid', False) else '#e53e3e'};">{'Yes' if hv.get('is_valid', False) else 'No'}</div>
                 </div>
                 <div class="stat-card">
                     <h3>Data Errors</h3>
                     <div class="value" style="color: {'#48bb78' if total_errors == 0 else '#e53e3e'};">{total_errors}</div>
                 </div>
                 <div class="stat-card">
                     <h3>Subject ID Issues</h3>
                     <div class="value" style="color: {'#48bb78' if subject_issues == 0 else '#e53e3e'};">{subject_issues}</div>
                 </div>
             </div>
         </div>"""
        
#add_header_validation_section
        html_content += f"""
        <div class="panel">
            <h2>Header Validation</h2>
            <p style="color: #666; margin-bottom: 15px;">Your CSV file's column headers are compared against the WADEPS template requirements. Headers must match exactly (including spelling, spacing, and capitalization).</p>
            <div style="display: table; width: 100%;">
                <div style="display: table-row;">
                    <div style="display: table-cell; width: 33%; padding: 10px; text-align: center; border: 1px solid #ddd;">
                        <h3 style="margin: 0 0 5px 0; color: #333;">Matching Headers</h3>
                        <div style="font-size: 1.5em; font-weight: bold; color: #48bb78;">{len(hv.get('matching', []))}</div>
                        <div style="font-size: 11px; color: #666;">Correct headers</div>
                    </div>
                    <div style="display: table-cell; width: 33%; padding: 10px; text-align: center; border: 1px solid #ddd;">
                        <h3 style="margin: 0 0 5px 0; color: #333;">Missing Headers</h3>
                        <div style="font-size: 1.5em; font-weight: bold; color: #e53e3e;">{len(hv.get('missing', []))}</div>
                        <div style="font-size: 11px; color: #666;">Need to add</div>
                    </div>
                    <div style="display: table-cell; width: 33%; padding: 10px; text-align: center; border: 1px solid #ddd;">
                        <h3 style="margin: 0 0 5px 0; color: #333;">Extra Headers</h3>
                        <div style="font-size: 1.5em; font-weight: bold; color: #dd6b20;">{len(hv.get('extra', []))}</div>
                        <div style="font-size: 11px; color: #666;">Need to remove</div>
                    </div>
                </div>
            </div>"""
        
        if hv.get('missing'):
            html_content += f"""
            <h3 style="margin: 15px 0 10px 0; color: #e53e3e;">Missing Required Headers ({len(hv['missing'])}):</h3>
            <div style="background: #fef5f5; padding: 10px; border-left: 3px solid #e53e3e; margin-bottom: 10px;">
                <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;"><strong>Action Required:</strong> Add these column headers to your CSV file.</p>
                <div style="max-height: 200px; overflow-y: auto; border: 1px solid #e53e3e; background: white; padding: 10px;">
                    <ul style="margin: 0; padding-left: 20px; font-family: monospace; font-size: 12px;">"""
            for header in hv['missing'][:15]:
#truncate_long_headers
                display_header = header if len(header) <= 60 else header[:57] + "..."
                html_content += f'<li style="margin-bottom: 2px; word-break: break-all;">{display_header}</li>'
            if len(hv['missing']) > 15:
                html_content += f'<li style="color: #666; font-style: italic;">... and {len(hv["missing"]) - 15} more headers</li>'
            html_content += """</ul>
                </div>
                <p style="margin: 10px 0 0 0; color: #666; font-size: 12px;"><strong>Tip:</strong> Copy these exact header names into your CSV file's first row.</p>
            </div>"""
        
        if hv.get('extra'):
            html_content += f"""
            <h3 style="margin: 15px 0 10px 0; color: #dd6b20;">Extra Headers ({len(hv['extra'])}):</h3>
            <div style="background: #fffaf0; padding: 10px; border-left: 3px solid #dd6b20; margin-bottom: 10px;">
                <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;"><strong>Action Required:</strong> Remove these column headers from your CSV file or rename them to match the template.</p>
                <div style="max-height: 200px; overflow-y: auto; border: 1px solid #dd6b20; background: white; padding: 10px;">
                    <ul style="margin: 0; padding-left: 20px; font-family: monospace; font-size: 12px;">"""
            for header in hv['extra'][:15]:
                display_header = header if len(header) <= 60 else header[:57] + "..."
                html_content += f'<li style="margin-bottom: 2px; word-break: break-all;">{display_header}</li>'
            if len(hv['extra']) > 15:
                html_content += f'<li style="color: #666; font-style: italic;">... and {len(hv["extra"]) - 15} more headers</li>'
            html_content += """</ul>
                </div>
                <p style="margin: 10px 0 0 0; color: #666; font-size: 12px;"><strong>Tip:</strong> These headers don't match the template. Check for typos, remove unnecessary columns, or check for hidden newline characters in your header row.</p>
            </div>"""
        
#add_quick_fix_guide
        if hv.get('missing') or hv.get('extra'):
            html_content += """
            <div style="background: #e6f3ff; padding: 15px; margin-top: 15px; border: 1px solid #b3d9ff;">
                <h3 style="margin: 0 0 10px 0; color: #0066cc;">Quick Fix Guide for Header Issues:</h3>
                <ol style="margin: 0; padding-left: 20px; color: #333;">
                    <li><strong>Open your CSV file</strong> in Excel, Google Sheets, or a text editor</li>
                    <li><strong>For Missing Headers:</strong> Add new columns with the exact header names shown above</li>
                    <li><strong>For Extra Headers:</strong> Delete the columns or rename them to match the template</li>
                    <li><strong>Save your file</strong> and run the validator again</li>
                </ol>
                <p style="margin: 10px 0 0 0; color: #666; font-size: 12px;"><strong>Note:</strong> Header names are case-sensitive and must match exactly, including spaces and punctuation.</p>
            </div>"""
        
        html_content += "</div>"
        
#add_errors_section
        if total_errors > 0:
            html_content += f"""
        <div class="panel">
            <h2>Data Validation Errors ({total_errors})</h2>
            <p style="color: #666; margin-bottom: 15px;">These errors prevent your data from being accepted. Each error shows the column, row, and what needs to be fixed.</p>"""
            
#group_errors_by_type
            error_types = self._group_errors_by_type(results.get('data_validation', {}).get('errors', []))
            
#show_error_summary
            html_content += """
            <div style="background: #f8f9fa; padding: 10px; margin-bottom: 15px; border: 1px solid #dee2e6;">
                <h3 style="margin: 0 0 10px 0; color: #333;">Error Summary:</h3>"""
            for error_type, errors in error_types.items():
                html_content += f'<div style="margin-bottom: 5px;"><strong>{error_type}:</strong> {len(errors)} errors</div>'
            html_content += "</div>"
            
#show_detailed_errors
            for error in results.get('data_validation', {}).get('errors', [])[:20]:
                html_content += f"""
            <div class="error-item">
                <h4>{error.get('column', 'Unknown')}</h4>
                <p>{error.get('error', '')}</p>
                <div class="meta">Row {error.get('row', '?')} | Value: &quot;{error.get('value', '')}&quot;</div>
            </div>"""
            if total_errors > 20:
                html_content += f'<p style="color: #666; font-style: italic;">... and {total_errors - 20} more errors (see JSON file for complete list)</p>'
            html_content += "</div>"
        
#add_warnings_section
        if total_warnings > 0:
            html_content += f"""
        <div class="panel">
            <h2>Warnings ({total_warnings})</h2>"""
            for warning in results.get('data_validation', {}).get('warnings', []):
                html_content += f"""
            <div class="warning-item">
                <h4>{warning.get('column', 'Unknown')}</h4>
                <p>{warning.get('error', '')}</p>
                <div class="meta">Row {warning.get('row', '?')} | Value: "{warning.get('value', '')}"</div>
            </div>"""
            html_content += "</div>"
        
        
#add_subject_id_issues
        if subject_issues > 0:
            sv = results.get('subject_id_validation', {})
            html_content += f"""
        <div class="panel">
            <h2>Subject ID Validation Issues ({subject_issues})</h2>
            <p style="color: #666; margin-bottom: 15px;">Subject IDs should be initials only (e.g., "JD", "J.D.", "J.D.S"). Full names and "unknown" values are not allowed.</p>
            
            <div style="display: table; width: 100%; margin-bottom: 15px;">
                <div style="display: table-row;">
                    <div style="display: table-cell; width: 33%; padding: 10px; text-align: center; border: 1px solid #ddd;">
                        <h3 style="margin: 0 0 5px 0; color: #333;">Unknown Values</h3>
                        <div style="font-size: 1.5em; font-weight: bold; color: #e53e3e;">{sv.get('unknown_count', 0)}</div>
                        <div style="font-size: 11px; color: #666;">"unknown", "unk"</div>
                    </div>
                    <div style="display: table-cell; width: 33%; padding: 10px; text-align: center; border: 1px solid #ddd;">
                        <h3 style="margin: 0 0 5px 0; color: #333;">Full Names</h3>
                        <div style="font-size: 1.5em; font-weight: bold; color: #e53e3e;">{sv.get('name_count', 0)}</div>
                        <div style="font-size: 11px; color: #666;">"John Doe"</div>
                    </div>
                    <div style="display: table-cell; width: 33%; padding: 10px; text-align: center; border: 1px solid #ddd;">
                        <h3 style="margin: 0 0 5px 0; color: #333;">Invalid Format</h3>
                        <div style="font-size: 1.5em; font-weight: bold; color: #e53e3e;">{sv.get('invalid_count', 0)}</div>
                        <div style="font-size: 11px; color: #666;">Numbers, symbols</div>
                    </div>
                </div>
            </div>"""
            
            if sv.get('examples'):
                html_content += """
                <h3 style="margin: 15px 0 10px 0; color: #333;">Examples of Issues Found:</h3>
                <div style="background: #fef5f5; padding: 10px; border-left: 3px solid #e53e3e;">"""
                for example in sv['examples'][:5]:
                    html_content += f"""
                    <div style="margin-bottom: 8px; padding: 5px; background: white; border: 1px solid #e53e3e;">
                        <strong>Row {example.get('row', '?')}:</strong> &quot;{example.get('value', '')}&quot; 
                        <span style="color: #666;">- {example.get('error', '')}</span>
                    </div>"""
                html_content += "</div>"
            
            html_content += """
            <div style="background: #ebf8ff; padding: 10px; margin-top: 15px; border: 1px solid #bee3f8;">
                <h3 style="margin: 0 0 10px 0; color: #2b6cb0;">How to Fix Subject ID Issues:</h3>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Replace "unknown" with actual initials (e.g., "JD")</li>
                    <li>Convert full names to initials (e.g., "John Doe" → "JD")</li>
                    <li>Use proper format: letters only, 1-4 characters, optional periods</li>
                    <li>Examples: "JD", "J.D.", "J.D.S", "AB"</li>
                </ul>
            </div>
        </div>"""
        
#add_success_section
        if hv.get('is_valid', False) and total_errors == 0 and subject_issues == 0:
            html_content += """
        <div class="panel" style="background: #f0fff4; border: 1px solid #9ae6b4;">
            <h2 style="color: #22543d;">Validation Passed!</h2>
            <p style="color: #22543d; margin-bottom: 15px;">Your CSV file meets all WADEPS requirements and is ready for submission.</p>
            <div style="background: white; padding: 15px; border: 1px solid #9ae6b4;">
                <h3 style="margin: 0 0 10px 0; color: #22543d;">What was validated:</h3>
                <ul style="margin: 0; padding-left: 20px; color: #22543d;">
                    <li>All required headers are present and correctly named</li>
                    <li>All data values match the expected formats and dropdown lists</li>
                    <li>Subject IDs are properly formatted as initials</li>
                    <li>No critical validation errors found</li>
                </ul>
            </div>
        </div>"""
        
#add_recommendations
        html_content += """
        <div class="recommendations">
            <h3>Recommendations</h3>
            <ul>"""
        
        if not hv.get('is_valid', False):
            html_content += "<li>Fix missing headers before resubmission</li>"
        if total_errors > 0:
            html_content += f"<li>Address {total_errors} critical validation errors</li>"
        if total_warnings > 0:
            html_content += f"<li>Review {total_warnings} warnings for data quality</li>"
        if subject_issues > 0:
            html_content += f"<li>Fix {subject_issues} subject ID format issues</li>"
        
        if hv.get('is_valid', False) and total_errors == 0 and subject_issues == 0:
            html_content += "<li>File is ready for submission!</li>"
        
        html_content += """
            </ul>
        </div>
    </div>
</body>
</html>"""
        
#save_dashboard
        os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  Dashboard saved to: {dashboard_path}")
        return dashboard_path
    
    def _group_errors_by_type(self, errors: List[Dict]) -> Dict[str, List[Dict]]:
        """Group errors by type for consistent error categorization"""
        error_types = {}
        for error in errors:
            error_msg = error.get('error', '')
            if 'date format' in error_msg.lower():
                error_type = 'Date Format Issues'
            elif 'time format' in error_msg.lower():
                error_type = 'Time Format Issues'
            elif 'Must be one of' in error_msg:
                error_type = 'Invalid Dropdown Values'
            else:
                error_type = 'Other Validation Issues'
            
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)
        
        return error_types

    def generate_error_report(self, results: Dict) -> str:
        """Generate a detailed error report"""
        report = []
        report.append("WADEPS VALIDATION ERROR REPORT")
        report.append("=" * 60)
        report.append(f"File: {results.get('file', 'Unknown')}")
        report.append(f"Date: {results.get('timestamp', '')[:19]}")
        report.append("")
        
#header_issues
        headers = results.get('header_validation', {})
        if headers.get('missing'):
            report.append("MISSING HEADERS:")
            for h in headers['missing'][:10]:
                report.append(f"  - {h}")
            if len(headers['missing']) > 10:
                report.append(f"  ... and {len(headers['missing']) - 10} more")
            report.append("")
        
        if headers.get('extra'):
            report.append("EXTRA/MALFORMED HEADERS:")
            for h in headers['extra'][:10]:
                if '\n' in h or '\r' in h:
                    report.append(f"  - Header has line break: {repr(h)[:50]}")
                else:
                    report.append(f"  - {h}")
            report.append("  FIX: Remove line breaks from header row")
            report.append("")
        
#data_validation_errors
        data_val = results.get('data_validation', {})
        if data_val.get('errors'):
            errors = data_val['errors']
            
#group_errors_by_type
            error_types = self._group_errors_by_type(errors)
            
            # Convert to detailed format for report
            detailed_error_types = {}
            for error_type, error_list in error_types.items():
                for error in error_list:
                    header = error.get('column', 'Unknown')
                    value = error.get('value', '')
                    
                    if 'Date Format' in error_type:
                        key = f"{header}: Date format issue"
                        fix = 'Use format MM/DD/YYYY (e.g., 09/23/2025)'
                    elif 'Time Format' in error_type:
                        key = f"{header}: Time format issue"
                        fix = 'Use format HH:MM (e.g., 08:21)'
                    elif 'Dropdown' in error_type:
                        key = f"{header}: Invalid dropdown value"
                        fix = 'Use exact value from dropdown list'
                    else:
                        key = f"{header}: {error.get('error', '')[:30]}"
                        fix = 'Check validation requirements'
                    
                    if key not in detailed_error_types:
                        detailed_error_types[key] = {
                            'count': 0,
                            'example': value,
                            'fix': fix
                        }
                    
                    detailed_error_types[key]['count'] += 1
            
            error_types = detailed_error_types
            
            report.append("DATA VALIDATION ISSUES:")
            for error_type, info in sorted(error_types.items(), key=lambda x: -x[1]['count']):
                report.append(f"  {info['count']:3d} × {error_type}")
                report.append(f"       Example: \"{info['example']}\"")
                report.append(f"       Fix: {info['fix']}")
            report.append("")
        
#overall_status
        report.append("VALIDATION STATUS:")
        status = results.get('status', 'UNKNOWN')
        if status == 'PASSED':
            report.append("  PASSED - No critical issues")
        else:
            report.append("  FAILED - Issues must be fixed before submission")
        
        return "\n".join(report)
    
    def print_summary(self, results: Dict):
        """Print a summary of validation results"""
        print(f"\n  Summary for {results['file']}:")
        
#header_validation
        hv = results['header_validation']
        if len(hv['missing']) > 0:
            print(f"    Missing {len(hv['missing'])} required headers")
        
#data_validation
        dv = results['data_validation']
        if len(dv['errors']) > 0:
            print(f"    {len(dv['errors'])} data errors found")
        
#subject_id_validation
        sv = results['subject_id_validation']
        total_issues = sv['unknown_count'] + sv['name_count'] + sv['invalid_count']
        if total_issues > 0:
            print(f"    {total_issues} subject ID issues")
        
#overall_status
        if hv['is_valid'] and len(dv['errors']) == 0 and total_issues == 0:
            print(f"    PASSED - File meets all requirements")
        elif len(hv['missing']) > 0 or len(dv['errors']) > 10:
            print(f"    FAILED - Critical issues found")
        else:
            print(f"    PASSED WITH WARNINGS")
    
    def print_detailed_results(self, results: Dict):
        """Print detailed validation results with formatting"""
        print(f"\n{'='*60}")
        print(f"DETAILED VALIDATION RESULTS: {results['file']}")
        print(f"{'='*60}")
        
#header_issues
        hv = results['header_validation']
        if hv['missing'] or hv['extra']:
            print(f"\nHEADER VALIDATION:")
            if hv['missing']:
                print(f"  Missing headers ({len(hv['missing'])}):")
                for header in hv['missing'][:10]:
                    print(f"    - {header}")
                if len(hv['missing']) > 10:
                    print(f"    ... and {len(hv['missing']) - 10} more")
            
            if hv['extra']:
                print(f"  Extra headers ({len(hv['extra'])}):")
                for header in hv['extra'][:10]:
                    print(f"    + {header}")
                if len(hv['extra']) > 10:
                    print(f"    ... and {len(hv['extra']) - 10} more")
        
#data_errors
        dv = results['data_validation']
        if dv['errors']:
            print(f"\nDATA VALIDATION ERRORS ({len(dv['errors'])}):")
            for error in dv['errors'][:20]:
                print(f"  Row {error['row']}, {error['column']}: {error['error']}")
                if error.get('value'):
                    print(f"    Value: \"{error['value']}\"")
            if len(dv['errors']) > 20:
                print(f"  ... and {len(dv['errors']) - 20} more errors")
        
#warnings
        if dv['warnings']:
            print(f"\nWARNINGS ({len(dv['warnings'])}):")
            for warning in dv['warnings'][:10]:
                print(f"  Row {warning['row']}, {warning['column']}: {warning['error']}")
            if len(dv['warnings']) > 10:
                print(f"  ... and {len(dv['warnings']) - 10} more warnings")
        
#subject_id_issues
        sv = results['subject_id_validation']
        total_subject_issues = sv['unknown_count'] + sv['name_count'] + sv['invalid_count']
        if total_subject_issues > 0:
            print(f"\nSUBJECT ID ISSUES ({total_subject_issues}):")
            print(f"  Unknown values: {sv['unknown_count']}")
            print(f"  Full names: {sv['name_count']}")
            print(f"  Invalid format: {sv['invalid_count']}")
            
            if sv['examples']:
                print(f"  Examples:")
                for example in sv['examples'][:5]:
                    print(f"    Row {example['row']}: \"{example['value']}\" - {example['error']}")
        
#recommendations
        print(f"\nRECOMMENDATIONS:")
        if not hv['is_valid']:
            print(f"  - Fix missing headers before resubmission")
        if dv['errors']:
            print(f"  - Address {len(dv['errors'])} critical validation errors")
        if dv['warnings']:
            print(f"  - Review {len(dv['warnings'])} warnings for data quality")
        if total_subject_issues > 0:
            print(f"  - Fix {total_subject_issues} subject ID format issues")
        
        if hv['is_valid'] and not dv['errors'] and total_subject_issues == 0:
            print(f"  - ✅ File is ready for submission!")
        
        print(f"\n{'='*60}")


def process_auto_mode():
    """Process files in input_source folder automatically"""
    print("="*60)
    print("WADEPS DATA VALIDATOR - AUTO MODE")
    print("="*60)
    print("Automatically processing files in 'input_source' folder")
    print("-"*60)
    
#set_up_paths
    input_folder = Path("input_source")
    output_folder = Path("output")
    
#create_folders_if_needed
    if not input_folder.exists():
        input_folder.mkdir()
        print(f"Created '{input_folder}' folder")
        print("Please place your CSV files in this folder and run again")
        return
    
    if not output_folder.exists():
        output_folder.mkdir()
        print(f"Created '{output_folder}' folder for results")
    
#find_csv_files
    csv_files = list(input_folder.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in '{input_folder}' folder")
        print("Please place your CSV files in the 'input_source' folder and run again")
        return
    
    print(f"{len(csv_files)} CSV file(s) to process\n")
    
#initialize_validator
    try:
        validator = WADEPSValidator()
        
#load_template_data
        template_json = Path("../templates/wadeps_uof_template.json")
        if not template_json.exists():
            print("Error: Template data file not found at '../templates/wadeps_uof_template.json'!")
            print("Please ensure the wadeps_uof_template.json file is in the templates directory")
            return

        with open(template_json, 'r') as f:
            data = json.load(f)
            validator.headers = data['headers']
            validator.validations = data['validations']
            print(f"Loaded template with {len(validator.headers)} headers, "
                  f"{len(validator.validations)} validation rules\n")
    
    except FileNotFoundError:
        print("Template file not found at '../templates/template_data.json'!")
        print("Please ensure the template_data.json file is in the templates directory")
        return
    except Exception as e:
        print(f"Error initializing validator: {e}")
        return
    
#process_each_csv_file
    all_results = []
    for csv_file in csv_files:
        try:
            print(f"{'='*40}")
            results = validator.validate_csv(csv_file)
            
#save_individual_results
            output_path = output_folder / f"{csv_file.stem}_validation.json"
            validator.save_validation_results(results, str(output_path))
            
#generate_dashboard
            dashboard_path = validator.generate_dashboard(results)
            
#print_detailed_results
            validator.print_detailed_results(results)
            
            all_results.append(results)
            
        except Exception as e:
            print(f"  Error processing {csv_file.name}: {e}")
            continue
    
#print_overall_summary
    print(f"\n{'='*60}")
    print("VALIDATION COMPLETE")
    print(f"{'='*60}")
    print(f"Processed {len(all_results)} file(s)")
    
#count_overall_stats
    total_passed = sum(1 for r in all_results 
                      if r['header_validation']['is_valid'] 
                      and len(r['data_validation']['errors']) == 0)
    total_failed = len(all_results) - total_passed
    
    if total_passed > 0:
        print(f"{total_passed} file(s) passed validation")
    if total_failed > 0:
        print(f"{total_failed} file(s) failed validation")
    
    print(f"\nResults saved in '{output_folder}' folder")
    print(f"Check individual JSON files and HTML dashboards for detailed validation reports")
    
#create_summary_report
    summary = {
        'validation_run': datetime.now().isoformat(),
        'total_files': len(all_results),
        'passed': total_passed,
        'failed': total_failed,
        'files_processed': [r['file'] for r in all_results],
        'template_info': {
            'headers': len(validator.headers),
            'validation_rules': len(validator.validations)
        }
    }
    
    summary_path = output_folder / f"validation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary report: {summary_path}")
    
    print("\n" + "="*60)
    print("Thank you for using WADEPS Data Validator")
    print("="*60)


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description='WADEPS Data Validator')
    parser.add_argument('--template', default='../templates/wadeps_uof_template.json',
                       help='Path to JSON template (default: ../templates/wadeps_uof_template.json)')
    parser.add_argument('--extract-only', action='store_true',
                       help='Only extract template data without validation')
    parser.add_argument('--output', help='Output file for results')
    parser.add_argument('--dashboard', action='store_true',
                       help='Generate interactive dashboard after validation')
    parser.add_argument('--summary-only', action='store_true',
                       help='Show only summary results (default shows detailed)')
    
    args = parser.parse_args()
    
#extract_only_mode
    if args.extract_only:
        validator = WADEPSValidator(args.template)
        try:
            validator.load_template_data()
            validator.save_template_data()
            print("Template extraction complete")
        except FileNotFoundError:
            print(f"Template file not found: {args.template}")
            print("   Please ensure wadeps_uof_template.json is in the templates directory")
            sys.exit(1)
        return
    
#default_auto_mode
    process_auto_mode()


if __name__ == "__main__":
    main()
