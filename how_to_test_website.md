# How to Test Your Website

## 1. Start the Application

Run this command in your terminal:

```bash
python test_new_structure.py
```

You should see output like:

```
[2025-05-26 19:43:05,068] INFO in logging_config: Application logging configured
 * Serving Flask app 'new_structure'
 * Debug mode: on
 * Running on http://127.0.0.1:5001
```

## 2. Access the Website

Open your web browser and go to:

```
http://127.0.0.1:5001/classteacher/login
```

## 3. Login Credentials

Use these credentials to log in:

- **Username:** kevin
- **Password:** kev123

## 4. Test the Clean Print Feature

### For Class Reports:

1. Navigate to a class report (e.g., Grade 7, Stream Y, Term 1, KJSEA)
2. Click the "Print Report" button
3. A new clean window will open with just the report content
4. The printed/downloaded report will be clean without:
   - Browser URL bars
   - Page titles like "Class Report Preview - Kirima Primary School"
   - Browser navigation elements
   - Unwanted headers/footers

### For Individual Reports:

1. Navigate to individual student reports
2. Click the "Print Report" button
3. A clean window opens with just the student report
4. No browser elements or "about:blank" URLs in the printout

## 5. What We Fixed

### Before:

- Reports showed browser titles like "Class Report Preview - Kirima Primary School"
- URLs like "127.0.0.1:5001/classteacher/preview_class_report/..." appeared in printouts
- Individual reports showed "about:blank" in headers
- Browser navigation elements were visible

### After:

- Clean page titles: "Class Report" and "Academic Report"
- No URLs in headers/footers using CSS `@page` rules
- No browser elements in printouts
- Professional, clean documents suitable for official use

## 6. Technical Implementation

We implemented:

1. **Clean Page Titles**: Changed from descriptive titles to simple ones
2. **Enhanced Print CSS**: Added comprehensive `@page` rules to remove browser headers/footers
3. **Simplified Print Function**: Uses browser's built-in print functionality with clean CSS
4. **CSS Print Styles**: Hides all non-essential elements and ensures proper formatting

## 7. Browser Print Settings

For best results when printing:

- **Orientation**: Landscape (for class reports), Portrait (for individual reports)
- **Margins**: Narrow or None
- **Background Graphics**: Enabled (to show colors and styling)
- **Scale**: 100% or fit to page

## 8. Testing Different Scenarios

Test these scenarios:

1. **Class Reports**: Check that composite subjects (English/Kiswahili) show correct marks
2. **Individual Reports**: Verify student details and component breakdowns
3. **Print Quality**: Ensure colors, borders, and formatting are preserved
4. **Subject Selection**: Test filtering subjects in class reports
5. **Different Grades**: Test reports for different education levels

## 9. Troubleshooting

If you encounter issues:

1. **Application won't start**: Check if port 5001 is available
2. **Login fails**: Verify database contains the test user (kevin/kev123)
3. **Print issues**: Try different browsers (Chrome, Firefox, Edge)
4. **Missing data**: Ensure test data exists in the database

## 10. Stop the Application

To stop the application, press `Ctrl+C` in the terminal where it's running.

---

Your website now produces clean, professional reports without any browser artifacts!
