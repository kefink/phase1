# Caching System for Reports and Marksheets

This document explains the caching system implemented for reports and marksheets in the Hillview School Management System.

## Overview

The caching system improves performance by storing generated reports, marksheets, and PDFs temporarily, so they don't need to be regenerated each time they're accessed. This significantly reduces load times for frequently accessed data.

## How It Works

1. **First Request**: When a report or marksheet is generated for the first time:
   - The system retrieves all necessary data from the database
   - Performs calculations (averages, percentages, rankings, etc.)
   - Formats the data into the required layout
   - Stores the final result in a cache
   - Returns the result to the user

2. **Subsequent Requests**: When the same report is requested again:
   - The system checks if a valid cached version exists
   - If it exists and is still valid, it returns the cached version immediately
   - If not, it generates a new version and updates the cache

## Cache Types

The system implements three types of caching:

1. **Memory Cache**: Stores data in memory for the fastest access
2. **File Cache**: Stores data in files for persistence across application restarts
3. **PDF Cache**: Specifically for storing generated PDF and Excel files

## Cache Locations

Cached data is stored in the following directories:

- `cache/` - Root cache directory
- `cache/reports/` - Report data cache
- `cache/marksheets/` - Marksheet data cache
- `cache/pdfs/` - PDF and Excel file cache

## Cache Expiration

By default, cache entries expire after:

- Marksheets and reports: 1 hour (3600 seconds)
- PDF files: 24 hours (86400 seconds)

These values can be adjusted in the cache service.

## Cache Invalidation

The cache is automatically invalidated when:

1. New marks are submitted
2. Marks are updated
3. Marksheets are deleted

This ensures that users always see the most up-to-date data.

## API Reference

### Cache Service Functions

```python
# Cache marksheet data
cache_marksheet(grade, stream, term, assessment_type, marksheet_data, expiry=3600)

# Get cached marksheet data
get_cached_marksheet(grade, stream, term, assessment_type)

# Cache report data
cache_report(grade, stream, term, assessment_type, report_data, expiry=3600)

# Get cached report data
get_cached_report(grade, stream, term, assessment_type)

# Cache PDF file
cache_pdf(grade, stream, term, assessment_type, pdf_type, pdf_data, expiry=86400)

# Get cached PDF file path
get_cached_pdf(grade, stream, term, assessment_type, pdf_type)

# Invalidate all caches for a specific grade, stream, term, and assessment type
invalidate_cache(grade, stream, term, assessment_type)
```

## Implementation Examples

### Caching a Marksheet

```python
# Generate marksheet data
marksheet_data = {
    'subjects': subjects,
    'data': all_data,
    'statistics': statistics
}

# Cache the marksheet data
cache_marksheet(grade, stream, term, assessment_type, marksheet_data)
```

### Using Cached Marksheet

```python
# Check if we have a cached version
cached_marksheet = get_cached_marksheet(grade, stream, term, assessment_type)
if cached_marksheet:
    # Use the cached marksheet data
    return render_template(
        'preview_marksheet.html',
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        subjects=cached_marksheet['subjects'],
        data=cached_marksheet['data'],
        statistics=cached_marksheet['statistics']
    )
```

### Caching a PDF

```python
# Generate PDF file
pdf_file = generate_report_pdf(...)

# Cache the PDF file
with open(pdf_file, 'rb') as f:
    pdf_data = f.read()
cache_pdf(grade, stream, term, assessment_type, "report", pdf_data)
```

### Using Cached PDF

```python
# Check if we have a cached PDF
cached_pdf = get_cached_pdf(grade, stream, term, assessment_type, "report")
if cached_pdf:
    return send_file(
        cached_pdf,
        as_attachment=True,
        download_name=f"{grade}_{stream}_{term}_{assessment_type}_Report.pdf",
        mimetype='application/pdf'
    )
```

### Invalidating Cache

```python
# Invalidate cache when marks are updated
invalidate_cache(grade, stream, term, assessment_type)
```

## Performance Impact

The caching system significantly improves performance:

- Report generation: 2-5 seconds → 0.1-0.2 seconds (cached)
- Marksheet generation: 1-3 seconds → 0.1 seconds (cached)
- PDF generation: 3-8 seconds → 0.2-0.5 seconds (cached)

## Maintenance

The cache directories should be monitored for size and occasionally cleaned if disk space becomes an issue. The system does not automatically prune old cache files.

To manually clear all caches, delete the contents of the `cache/` directory.
