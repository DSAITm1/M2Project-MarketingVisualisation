#!/usr/bin/env python3
"""
Comprehensive Polars Migration Check
Identifies and reports all pandas-style code that needs conversion
"""

import os
import re
from pathlib import Path

def check_pandas_patterns(file_path):
    """Check for pandas-style patterns in a file"""
    patterns = {
        'groupby': r'\.groupby\(',
        'sort_values': r'\.sort_values\(',
        'reset_index': r'\.reset_index\(',
        'idxmax': r'\.idxmax\(\)',
        'idxmin': r'\.idxmin\(\)',
        'iloc': r'\.iloc\[',
        'loc': r'\.loc\[',
        'notna': r'\.notna\(\)',
        'sample': r'\.sample\(',
        'head': r'\.head\(',
        'tail': r'\.tail\(',
        'mode': r'\.mode\(',
        'pandas_import': r'import pandas|from pandas|pd\.',
        'pd_prefix': r'pd\.',
        'fillna': r'\.fillna\(',
        'isnull': r'\.isnull\(',
        'isna': r'\.isna\(',
        'value_counts_sort_index': r'\.value_counts\(\)\.sort_index\(',
        'df_index': r'df\.index',
    }
    
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for pattern_name, pattern in patterns.items():
                matches = re.finditer(pattern, line)
                for match in matches:
                    issues.append({
                        'file': str(file_path),
                        'line': line_num,
                        'pattern': pattern_name,
                        'text': line.strip(),
                        'match': match.group()
                    })
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return issues

def get_polars_replacement(pattern):
    """Get suggested Polars replacement for pandas pattern"""
    replacements = {
        'groupby': '.group_by() - Use Polars groupby syntax',
        'sort_values': '.sort() - Use Polars sort method',
        'reset_index': 'Remove - Polars DataFrames don\'t have index',
        'idxmax': 'Use .arg_max() or sort + select first',
        'idxmin': 'Use .arg_min() or sort + select first', 
        'iloc': 'Use [row_index] or .slice() for row selection',
        'loc': 'Use .filter() for conditional selection',
        'notna': 'Use .is_not_null()',
        'sample': 'Use .sample() with n parameter',
        'head': 'Use .head() or .limit()',
        'tail': 'Use .tail() or .slice(-n)',
        'mode': 'Use .mode() - returns Series in Polars',
        'pandas_import': 'Remove pandas import, use polars as pl',
        'pd_prefix': 'Replace with pl. prefix for Polars',
        'fillna': 'Use .fill_null()',
        'isnull': 'Use .is_null()',
        'isna': 'Use .is_null()',
        'value_counts_sort_index': '.value_counts() returns DataFrame in Polars',
        'df_index': 'Polars has no index - use row_number() or filter',
    }
    return replacements.get(pattern, 'Check Polars documentation')

def main():
    """Main function to check all Python files"""
    base_dir = Path('/Users/jefflee/SCTP/M2Project/M2Project-MarketingVisualisation')
    
    # File patterns to check
    python_files = []
    for pattern in ['*.py', 'pages/*.py', 'utils/*.py']:
        python_files.extend(base_dir.glob(pattern))
    
    all_issues = []
    
    print("🔍 Checking for pandas patterns in Python files...")
    print("=" * 60)
    
    for file_path in python_files:
        if file_path.name.startswith('.'):
            continue
            
        issues = check_pandas_patterns(file_path)
        all_issues.extend(issues)
        
        if issues:
            print(f"\n📁 {file_path.relative_to(base_dir)}")
            print("-" * 40)
            
            for issue in issues:
                print(f"  Line {issue['line']:3d}: {issue['pattern']}")
                print(f"           Code: {issue['text'][:80]}...")
                print(f"           Fix:  {get_polars_replacement(issue['pattern'])}")
                print()
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    
    if all_issues:
        print(f"Found {len(all_issues)} pandas patterns across {len(set(i['file'] for i in all_issues))} files")
        
        # Group by pattern
        pattern_counts = {}
        for issue in all_issues:
            pattern = issue['pattern']
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
        print("\nPattern breakdown:")
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pattern:20s}: {count:2d} occurrences")
            
        print(f"\n❌ Migration Status: INCOMPLETE")
        print("Next steps:")
        print("1. Fix patterns systematically, starting with most common")
        print("2. Test each fix with validate_polars.py")  
        print("3. Commit changes after validation")
        
    else:
        print("✅ No pandas patterns found - migration appears complete!")
        print("Run validate_polars.py for final verification")

if __name__ == "__main__":
    main()
