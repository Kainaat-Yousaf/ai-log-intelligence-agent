"""
Bob Log Intelligence - Flask Backend (DEMO MODE)
Works without IBM watsonx.ai credentials using mock analysis
"""

import os
import re
import json
from collections import Counter
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'log', 'txt'}
MAX_LINES_TO_ANALYZE = 500

LOG_FILTER_PATTERN = re.compile(
    r'(ERROR|CRITICAL|FATAL|Exception|NullPointerException|'
    r'OutOfMemoryError|StackOverflowError|WARN|WARNING|timeout|'
    r'rollback|retry|failed)',
    re.IGNORECASE
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def filter_log_lines(log_content):
    """Filter log lines to only include errors and warnings"""
    lines = log_content.split('\n')
    filtered_lines = []
    
    for line in lines:
        if LOG_FILTER_PATTERN.search(line):
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines) if filtered_lines else log_content[:5000]


def mock_ai_analysis(log_content):
    """
    Mock AI analysis that simulates watsonx.ai response
    Analyzes log patterns and generates realistic issues
    """
    lines = log_content.split('\n')
    issues = []
    
    # Pattern-based issue detection
    patterns = {
        'NullPointerException': {
            'severity': 'critical',
            'title': 'NullPointerException in Application',
            'description': 'Application encounters null reference errors causing crashes. This indicates missing null checks before object access.',
            'root_cause': 'Missing null validation before accessing object properties or methods',
            'fix': 'Add null checks using if statements or Optional pattern before accessing objects'
        },
        'OutOfMemoryError': {
            'severity': 'critical',
            'title': 'Memory Exhaustion Detected',
            'description': 'System running out of memory leading to application crashes. This can cause data loss and service interruption.',
            'root_cause': 'Insufficient heap space allocation or memory leaks in application',
            'fix': 'Increase JVM heap size with -Xmx flag or investigate memory leaks using profiler'
        },
        'CRITICAL': {
            'severity': 'critical',
            'title': 'Critical System Error',
            'description': 'Critical level errors detected that require immediate attention. These errors can lead to system failure.',
            'root_cause': 'System-level failure or critical component malfunction',
            'fix': 'Review critical error logs and restart affected services immediately'
        },
        'FATAL': {
            'severity': 'critical',
            'title': 'Fatal Application Error',
            'description': 'Fatal errors causing application termination. Immediate action required to restore service.',
            'root_cause': 'Unrecoverable error in application logic or infrastructure',
            'fix': 'Check application logs, verify configuration, and restart application'
        },
        'ERROR': {
            'severity': 'warning',
            'title': 'Application Error Detected',
            'description': 'General application errors that may impact functionality. These should be investigated and resolved.',
            'root_cause': 'Application logic error or invalid input handling',
            'fix': 'Review error context and implement proper error handling'
        },
        'timeout': {
            'severity': 'warning',
            'title': 'Connection Timeout Issues',
            'description': 'Network or database connection timeouts detected. This can slow down application performance.',
            'root_cause': 'Slow network response or database query performance issues',
            'fix': 'Increase timeout values or optimize slow queries and network calls'
        },
        'WARNING': {
            'severity': 'warning',
            'title': 'System Warning',
            'description': 'Warning level issues that should be monitored. While not critical, these may indicate future problems.',
            'root_cause': 'Potential configuration issue or deprecated API usage',
            'fix': 'Review warning context and update configuration or code as needed'
        },
        'failed': {
            'severity': 'warning',
            'title': 'Operation Failure',
            'description': 'Failed operations detected in the system. This may indicate integration or service issues.',
            'root_cause': 'Service unavailability or invalid operation parameters',
            'fix': 'Verify service availability and validate operation parameters'
        },
        'Exception': {
            'severity': 'warning',
            'title': 'Exception Thrown',
            'description': 'Unhandled exceptions detected in application code. These should be caught and handled properly.',
            'root_cause': 'Missing exception handling in application code',
            'fix': 'Add try-catch blocks and implement proper exception handling'
        }
    }
    
    # Detect issues from log content
    for line in lines[:100]:  # Analyze first 100 lines
        for pattern, issue_template in patterns.items():
            if pattern.lower() in line.lower():
                issue = issue_template.copy()
                issue['line_reference'] = line[:200]
                issues.append(issue)
    
    # If no patterns matched, create generic issues
    if not issues:
        issues.append({
            'severity': 'info',
            'title': 'Log File Analyzed Successfully',
            'description': 'No critical errors or warnings detected in the log file. System appears to be operating normally.',
            'root_cause': 'No issues found',
            'fix': 'Continue monitoring system logs for any changes',
            'line_reference': lines[0] if lines else 'No log content'
        })
    
    return issues


def calculate_risk_analysis(issues):
    """Calculate risk level based on issue severity"""
    severity_counts = Counter(issue['severity'] for issue in issues)
    
    critical_count = severity_counts.get('critical', 0)
    warning_count = severity_counts.get('warning', 0)
    total_issues = len(issues)
    
    if critical_count >= 5 or total_issues >= 15:
        risk_level = "HIGH"
        prediction = f"System shows HIGH risk with {critical_count} critical errors. Immediate action required to prevent system failure."
    elif critical_count >= 2 or warning_count >= 5:
        risk_level = "MEDIUM"
        prediction = f"System shows MEDIUM risk with {critical_count} critical and {warning_count} warning issues. Monitor closely and address issues soon."
    else:
        risk_level = "LOW"
        if total_issues == 0:
            prediction = "System shows LOW risk with no significant issues detected. Continue normal monitoring."
        else:
            prediction = f"System shows LOW risk with {total_issues} minor issues. Address during regular maintenance."
    
    return {
        'risk_level': risk_level,
        'prediction': prediction,
        'critical_count': critical_count,
        'warning_count': warning_count,
        'total_issues': total_issues
    }


def group_and_count_issues(issues):
    """Group similar issues and count frequency"""
    title_counts = Counter(issue['title'] for issue in issues)
    
    seen = set()
    grouped = []
    
    for issue in issues:
        title = issue['title']
        if title not in seen:
            issue_copy = issue.copy()
            issue_copy['frequency'] = title_counts[title]
            grouped.append(issue_copy)
            seen.add(title)
    
    # Sort by severity (critical first) then by frequency
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    grouped.sort(key=lambda x: (severity_order.get(x['severity'], 3), -x['frequency']))
    
    return grouped


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mode': 'DEMO',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Running in demo mode with mock AI analysis'
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_log():
    """Analyze log file endpoint (DEMO MODE)"""
    try:
        # Validate file upload
        if 'file' not in request.files:
            return jsonify({
                'error': 'validation_error',
                'message': 'No file provided in request'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'validation_error',
                'message': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'validation_error',
                'message': f'Invalid file type. Only .log and .txt files are allowed.'
            }), 400
        
        # Read and decode file
        try:
            log_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({
                'error': 'encoding_error',
                'message': 'File encoding not supported. Please use UTF-8 encoded text files.'
            }), 400
        
        if not log_content.strip():
            return jsonify({
                'error': 'validation_error',
                'message': 'File is empty'
            }), 400
        
        logger.info(f"Analyzing file: {file.filename} ({len(log_content)} bytes)")
        
        # Filter log lines
        filtered_content = filter_log_lines(log_content)
        
        # Mock AI analysis
        issues = mock_ai_analysis(filtered_content)
        
        # Group and count issues
        grouped_issues = group_and_count_issues(issues)
        
        # Calculate risk
        risk_analysis = calculate_risk_analysis(grouped_issues)
        
        # Prepare response
        total_lines = len(log_content.split('\n'))
        critical_count = sum(1 for i in grouped_issues if i['severity'] == 'critical')
        warning_count = sum(1 for i in grouped_issues if i['severity'] == 'warning')
        
        response = {
            'summary': {
                'total_lines': total_lines,
                'critical_count': critical_count,
                'warning_count': warning_count,
                'analyzed_lines': len(filtered_content.split('\n'))
            },
            'risk_analysis': risk_analysis,
            'issues': grouped_issues,
            'mode': 'DEMO',
            'note': 'This is a demo analysis using pattern matching. For AI-powered analysis, configure IBM watsonx.ai credentials.'
        }
        
        logger.info(f"Analysis complete: {len(grouped_issues)} unique issues found")
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error analyzing log: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'server_error',
            'message': f'Error processing log file: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 AI LOG INTELLIGENCE AGENT - DEMO MODE")
    print("="*60)
    print("Running in DEMO mode with mock AI analysis")
    print("No IBM watsonx.ai credentials required")
    print("\nBackend API starting on http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

# Made with Bob
