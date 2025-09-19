# Python WADEPS Validator

Commandline tool for batch validation of WADEPS CSV files.

## Setup

### 1. Create Required Folders

```
mkdir input_source
mkdir output
```

- **`input_source/`** - Place your CSV files to validate here
- **`output/`** - Validation reports will be generated here

### 2. Install Dependencies

```bash
pip install pandas
```

## Usage

```
python wadeps_validator.py
```

The tool will:
1. Process all CSV files in the `input_source` folder
2. Validate them against the WADEPS template specifications (from `../templates/wadeps_uof_template.json`)
3. Generate validation reports in the `output` folder

## Input Requirements

- CSV files must be placed in the `input_source` folder
- Files should have `.csv` extension
- First row must contain headers

## Output

For each input file, creates a JSON report in `output/` with:
- Header validation results
- Data validation errors by row and column
- Subject ID issues
- Summary statistics