# WADEPS Header Validation Tool

A Python tool for validating WADEPS (Washington State Data Exchange for Public Safety) data files against official template specifications.

## Setup Instructions

### 1. Create Required Folders

Before running the tool, you need to create two folders:

```bash
mkdir input_source
mkdir output
```

- **`input_source/`** - Place your CSV files to validate here
- **`output/`** - Validation reports will be generated here

### 2. Running the Validator

```bash
python wadeps_validator.py
```

The tool will:
1. Process all CSV files in the `input_source` folder
2. Validate them against the WADEPS template specifications
3. Generate validation reports in the `output` folder

## File Structures

```
WADEPS_Header_Tool/
├── wadeps_validator.py           # Main validation script
├── template_data.json            # Validation rules and specifications
├── WADEPS_Smartform_Template.xlsx # Official WADEPS template
├── input_source/                 # (Create this) Place CSV files here
└── output/                       # (Create this) Reports generated here
```

## Date Format Support

The tool accepts dates in two formats:
- `MM/DD/YYYY` (e.g., 12/31/2024)
- `YYYY-MM-DD` (e.g., 2024-12-31)

## Requirements

- Python 3.x
- pandas
- openpyxl

## Notes

- The `input_source` and `output` folders are not tracked in Git
- Ensure your CSV files follow the WADEPS header structure
- Check the output folder for validation reports after running