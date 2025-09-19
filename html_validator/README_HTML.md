# WADEPS HTML Validator - User Guide

## Quick Start

1. **Save the HTML file to your desktop**
   - Download or save `wadeps_validator.html` to any location on your computer
   - No installation required as it works completely offline

2. **Open in your web browser**
   - Double-click the HTML file to open it in your default browser
   - Works with Chrome, Firefox, Safari, Edge, or any modern browser

3. **Drag and drop your CSV file**
   - Simply drag your CSV file onto the upload area
   - Or click "Choose File" to browse for your file

4. **Review instant results**
   - See validation status immediately
   - Review detailed errors and warnings
   - Download reports for your records

## Template Updates

### Dynamic Template Loading
The validator now supports dynamic template updates:

1. **Embedded Template** (Default)
   - The validator comes with an embedded template for standalone use
   - Works offline without any additional files
   - Shows "Using embedded template" in the header

2. **Update Template** (Optional)
   - Click the "Update Template" button in the header
   - Select a `wadeps_uof_template.json` file to load new validation rules
   - Useful for testing with updated templates before embedding

3. **Automatic Loading** (For local development)
   - When served via HTTP server, attempts to load `../templates/wadeps_uof_template.json`
   - Falls back to embedded template if external file not found
   - To use: Run `python -m http.server` from project root

## How to Use

### Step 1: Prepare Your CSV File
- Ensure your file is in CSV format (.csv extension)
- First row must contain column headers
- Data should be properly formatted according to WADEPS requirements

### Step 2: Upload Your File
Two options:
- **Drag & Drop**: Drag your CSV file from your file explorer onto the upload area
- **Browse**: Click "Choose File" and select your CSV from the file dialog

### Step 3: Review Results

#### Status Indicators
- 🟢 **Green (Passed)** - No errors found, file is ready for submission
- 🟡 **Yellow (Warning)** - File has warnings but can be submitted
- 🔴 **Red (Failed)** - Critical errors must be fixed before submission

#### Result Tabs
1. **Headers Tab** - Shows missing, extra, and matching headers
2. **Errors Tab** - Lists all validation errors that must be fixed
3. **Warnings Tab** - Shows non-critical issues to review
4. **Subject IDs Tab** - Displays subject ID formatting issues

### Step 4: Fix Issues
For each error, you'll see:
- **Row number** - Where the error occurred in your CSV
- **Column name** - Which field has the issue
- **Current value** - What you entered
- **Error description** - What needs to be fixed

### Step 5: Download Reports
Click the download buttons to save:
- **Text format** - For documentation and review to address issues
- **JSON format** - For programmatic processing (mostly for developers and vendors)

### Step 6: Re-validate
After fixing issues in your CSV:
1. Click "Validate Another"
2. Upload your corrected file
3. Repeat until all errors are resolved

## Common Issues and Solutions

### Missing Headers
**Problem**: "Missing Headers" error
**Solution**: Add the exact header names shown in the error list to your CSV's first row. Download the WADEPS SmartTemplate from the Web Application (https://report.wadeps.org/) 

### Invalid Dropdown Values
**Problem**: "Must be one of: Yes, No" error
**Solution**: Use exact values from the dropdown list (case-sensitive)

### Date Format Errors
**Problem**: "Invalid date format" error
**Solution**: Use MM/DD/YYYY format (e.g., 09/19/2025)

### Time Format Errors
**Problem**: "Invalid time format" error
**Solution**: Use HH:MM format (e.g., 2:30 PM instead of 14:30 )

### Subject ID Issues
**Problem**: Full names or "unknown" in subject_id field
**Solution**: Use initials only (e.g., "JD" or "J.D.")

## Tips for Success

1. **Start with the template** - Use the WADEPS SmartForm Template as your starting point
2. **Fix headers first** - Ensure all column headers match exactly before adding data
3. **Test with a few rows** - Validate a small sample before processing large files
4. **Use exact values** - Copy dropdown values exactly as shown in errors
5. **Check for hidden characters** - Remove any line breaks or special characters from headers

## Browser Compatibility

Works with all modern browsers:
- 🟢 Chrome
- 🦊 Firefox
- 🧭 Safari
- 🌐 Edge
- 🅾️ Opera

## Privacy & Security

- **100% Offline** = No internet connection required
- **No Data Transmission** = Your data never leaves your computer
- **No Server Processing** = All validation happens in your browser
- **No Data Storage** = Nothing is saved after you close the page
- **Secure by Design** = No external dependencies or tracking

## Troubleshooting

### File Won't Upload
- Ensure file has .csv extension
- Check file isn't open in another program
- Try using the "Choose File" button instead of drag & drop

### Results Don't Appear
- Refresh the page and try again
- Try a different browser
- Check browser console for errors (F12 key)

## Support

For issues or questions about:
- **The validator tool**: Check this guide or the main README
- **WADEPS requirements**: Please contact wadeps.techsupport.servicedesk@wsu.edu or visit the website at https://wadeps.org/ 
- **CSV formatting**: Use Excel or Google Sheets to properly format your data

---