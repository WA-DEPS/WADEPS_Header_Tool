# WADEPS Header Validation Tool

Validation Tools for WADEPS (Washington State Data Exchange for Public Safety) data files with both Python and HTML validators.

## Available Validators

### 1. HTML Validator (Browser-Based)
- **Location**: `html_validator/`
- **Features**: Drag-and-drop interface, instant validation, no installation required
- **Documentation**: See [html_validator/README_HTML.md](html_validator/README_HTML.md)

### 2. Python Validator (Command-Line)
- **Location**: `python_validator/`
- **Features**: Batch processing, automated validation, detailed reports
- **Documentation**: See [python_validator/README_Python.md](python_validator/README_Python.md)

## Quick Start

### For HTML Validator (Easiest)
1. Go to the folder `html_validator and open wadeps_validator.html` in your web browser
2. Drag and drop your CSV file
3. Review instant validation results

### For Python Validator (Batch Processing)
```
cd python_validator
python wadeps_validator.py
```
## File Structure

```
WADEPS_Header_Tool/
├── html_validator/
│   ├── wadeps_validator.html     #browser_based_validator
│   ├── WADEPS_green-logo-acronym.png
│   └── README_HTML.md
├── python_validator/
│   ├── wadeps_validator.py       #command_line_validator
│   ├── input_source/              #place_CSV_files_here
│   ├── output/                    #reports_generated_here
│   └── README_Python.md
└── templates/
    └── wadeps_uof_template.json  #validation
```

## Requirements

### HTML Validator
- Any modern web browser (Chrome, Firefox, Safari, Edge)
- No installation required

### Python Validator
- Python 3.x
- pandas

## Notes

- The `input_source` and `output` folders are not tracked in Git
- Ensure your CSV files follow the WADEPS header structure
- Check the output folder for validation reports after running