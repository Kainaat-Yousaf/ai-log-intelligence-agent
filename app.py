<<<<<<< HEAD
"""
Bob Log Intelligence - Flask Backend
A production-ready log file analyzer using IBM watsonx.ai
"""

import os
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
ALLOWED_EXTENSIONS = {'log', 'txt'}
MAX_LINES_TO_ANALYZE = 500

# Environment variables
BOB_API_KEY = os.getenv('BOB_API_KEY')
BOB_PROJECT_ID = os.getenv('BOB_PROJECT_ID')
BOB_URL = os.getenv('BOB_URL', 'https://us-south.ml.cloud.ibm.com')
BOB_MODEL = os.getenv('BOB_MODEL', 'ibm/granite-13b-chat-v2')

# Regex pattern for filtering log lines
LOG_FILTER_PATTERN = re.compile(
    r'(ERROR|CRITICAL|FATAL|Exception|NullPointerException|'
    r'OutOfMemoryError|StackOverflowError|WARN|WARNING|timeout|'
    r'rollback|retry|failed)',
    re.IGNORECASE
)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def filter_log_lines(log_content):
    """
    Filter log lines using regex pattern
    Returns list of relevant log lines
    """
    lines = log_content.split('\n')
    filtered_lines = []
    
    for line in lines:
        if line.strip() and LOG_FILTER_PATTERN.search(line):
            filtered_lines.append(line)
    
    logger.info(f"Filtered {len(filtered_lines)} relevant lines from {len(lines)} total lines")
    return filtered_lines


def analyze_with_watsonx(log_lines):
    """
    Send filtered log lines to watsonx.ai for analysis
    Returns JSON array of findings
    """
    try:
        # Validate environment variables
        if not BOB_API_KEY or not BOB_PROJECT_ID:
            raise ValueError("BOB_API_KEY and BOB_PROJECT_ID must be set")
        
        # Limit lines to analyze
        lines_to_analyze = log_lines[:MAX_LINES_TO_ANALYZE]
        log_content = '\n'.join(lines_to_analyze)
        
        logger.info(f"Analyzing {len(lines_to_analyze)} lines with watsonx.ai")
        
        # Prepare the prompt
        prompt = f"""You are a senior SRE. Analyze this log and return ONLY a JSON array.
Each object must have: severity (critical/warning/info), title (max 8 words),
explanation (2 sentences plain English), root_cause (1 sentence),
fix (1 actionable sentence), line_reference (relevant log line).
Sort critical first. Return ONLY valid JSON, no markdown.
LOG: {log_content}"""
        
        # Configure watsonx.ai credentials
        credentials = {
            "url": BOB_URL,
            "apikey": BOB_API_KEY
        }
        
        # Set up model parameters
        parameters = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 4000,
            GenParams.MIN_NEW_TOKENS: 100,
            GenParams.TEMPERATURE: 0.1,
            GenParams.STOP_SEQUENCES: ["```"]
        }
        
        # Initialize the model
        model = Model(
            model_id=BOB_MODEL,
            params=parameters,
            credentials=credentials,
            project_id=BOB_PROJECT_ID
        )
        
        # Generate response
        logger.info("Sending request to watsonx.ai...")
        response = model.generate_text(prompt=prompt)
        
        logger.info("Received response from watsonx.ai")
        
        # Parse JSON response
        # Remove markdown code blocks if present
        response_text = str(response).strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        findings = json.loads(response_text)
        
        # Validate response structure
        if not isinstance(findings, list):
            raise ValueError("Response is not a JSON array")
        
        logger.info(f"Successfully parsed {len(findings)} findings")
        return findings
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        if 'response_text' in locals():
            logger.error(f"Response text: {response_text[:500]}")
        raise ValueError(f"Failed to parse watsonx.ai response as JSON: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error analyzing with watsonx.ai: {str(e)}")
        raise


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Bob Log Intelligence',
        'version': '1.0.0',
        'watsonx_configured': bool(BOB_API_KEY and BOB_PROJECT_ID)
    }), 200


@app.route('/api/analyze', methods=['POST'])
def analyze_log():
    """
    Analyze log file endpoint
    Accepts multipart/form-data with 'file' field
    Returns JSON array of findings
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please upload a log file'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a log file to upload'
            }), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type',
                'message': f'Only {", ".join(ALLOWED_EXTENSIONS)} files are allowed'
            }), 400
        
        # Read file content
        try:
            log_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({
                'error': 'Invalid file encoding',
                'message': 'File must be UTF-8 encoded text'
            }), 400
        
        # Check if file is empty
        if not log_content.strip():
            return jsonify({
                'error': 'Empty file',
                'message': 'The uploaded log file is empty'
            }), 400
        
        # Filter log lines
        filtered_lines = filter_log_lines(log_content)
        
        if not filtered_lines:
            return jsonify({
                'findings': [],
                'message': 'No errors or warnings found in the log file',
                'lines_analyzed': 0
            }), 200
        
        # Analyze with watsonx.ai
        findings = analyze_with_watsonx(filtered_lines)
        
        return jsonify({
            'findings': findings,
            'lines_analyzed': min(len(filtered_lines), MAX_LINES_TO_ANALYZE),
            'total_filtered_lines': len(filtered_lines)
        }), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'error': 'Analysis failed',
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while analyzing the log file'
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large',
        'message': 'Maximum file size is 10MB'
    }), 413


@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    # Validate required environment variables
    if not BOB_API_KEY:
        logger.warning("BOB_API_KEY not set - watsonx.ai integration will not work")
    if not BOB_PROJECT_ID:
        logger.warning("BOB_PROJECT_ID not set - watsonx.ai integration will not work")
    
    # Run the app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Bob Log Intelligence on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)


"""
requirements.txt:

Flask==3.0.0
flask-cors==4.0.0
ibm-watsonx-ai==0.2.6
Werkzeug==3.0.1
"""

# Made with Bob
=======
"""
Bob Log Intelligence - Flask Backend
A production-ready log file analyzer using IBM watsonx.ai
"""

import os
import re
import json
from collections import Counter
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
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

BOB_API_KEY = os.getenv('BOB_API_KEY')
BOB_PROJECT_ID = os.getenv('BOB_PROJECT_ID')
BOB_URL = os.getenv('BOB_URL', 'https://us-south.ml.cloud.ibm.com')
BOB_MODEL = os.getenv('BOB_MODEL', 'ibm/granite-13b-chat-v2')

LOG_FILTER_PATTERN = re.compile(
    r'(ERROR|CRITICAL|FATAL|Exception|NullPointerException|'
    r'OutOfMemoryError|StackOverflowError|WARN|WARNING|timeout|'
    r'rollback|retry|failed)',
    re.IGNORECASE
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def filter_log_lines(log_content):
    lines = log_content.split('\n')
    filtered_lines = []
    
    for line in lines:
        if line.strip() and LOG_FILTER_PATTERN.search(line):
            filtered_lines.append(line)
    
    logger.info(f"Filtered {len(filtered_lines)} relevant lines from {len(lines)} total lines")
    return filtered_lines


def calculate_risk_analysis(findings):
    """Calculate risk level and prediction based on findings"""
    critical_count = sum(1 for f in findings if f.get('severity', '').lower() == 'critical')
    warning_count = sum(1 for f in findings if f.get('severity', '').lower() == 'warning')
    
    # Count issue frequencies
    issue_titles = [f.get('title', '') for f in findings]
    title_counts = Counter(issue_titles)
    max_frequency = max(title_counts.values()) if title_counts else 0
    
    # Determine risk level
    if critical_count >= 5 or max_frequency >= 10:
        risk_level = "HIGH"
        prediction = "Multiple critical errors detected. System stability is at risk. Immediate action required to prevent potential outages."
    elif critical_count >= 2 or warning_count >= 5 or max_frequency >= 5:
        risk_level = "MEDIUM"
        prediction = "Recurring error patterns detected. Monitor closely and address issues to prevent escalation."
    elif critical_count >= 1 or warning_count >= 2:
        risk_level = "MEDIUM"
        prediction = "Some issues detected. Review and address to maintain system health."
    else:
        risk_level = "LOW"
        prediction = "System appears stable. Continue monitoring for any emerging patterns."
    
    return {
        "risk_level": risk_level,
        "prediction": prediction,
        "critical_count": critical_count,
        "warning_count": warning_count
    }


def group_and_count_issues(findings):
    """Group similar issues and count their frequency"""
    issue_map = {}
    
    for finding in findings:
        title = finding.get('title', 'Unknown Issue')
        
        if title in issue_map:
            issue_map[title]['frequency'] += 1
        else:
            issue_map[title] = {
                'title': title,
                'severity': finding.get('severity', 'info'),
                'frequency': 1,
                'description': finding.get('explanation', ''),
                'root_cause': finding.get('root_cause', ''),
                'fix': finding.get('fix', ''),
                'line_reference': finding.get('line_reference', '')
            }
    
    return list(issue_map.values())


def analyze_with_watsonx(log_lines):
    """Send filtered log lines to watsonx.ai for analysis"""
    try:
        if not BOB_API_KEY or not BOB_PROJECT_ID:
            raise ValueError("BOB_API_KEY and BOB_PROJECT_ID must be set")
        
        lines_to_analyze = log_lines[:MAX_LINES_TO_ANALYZE]
        log_content = '\n'.join(lines_to_analyze)
        
        logger.info(f"Analyzing {len(lines_to_analyze)} lines with watsonx.ai")
        
        prompt = f"""You are a senior SRE. Analyze this log and return ONLY a JSON array.
Each object must have: severity (critical/warning/info), title (max 8 words),
explanation (2 sentences plain English), root_cause (1 sentence),
fix (1 actionable sentence), line_reference (relevant log line).
Sort critical first. Return ONLY valid JSON, no markdown.
LOG: {log_content}"""
        
        credentials = {
            "url": BOB_URL,
            "apikey": BOB_API_KEY
        }
        
        parameters = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 4000,
            GenParams.MIN_NEW_TOKENS: 100,
            GenParams.TEMPERATURE: 0.1,
            GenParams.STOP_SEQUENCES: ["```"]
        }
        
        model = Model(
            model_id=BOB_MODEL,
            params=parameters,
            credentials=credentials,
            project_id=BOB_PROJECT_ID
        )
        
        logger.info("Sending request to watsonx.ai...")
        response = model.generate_text(prompt=prompt)
        
        logger.info("Received response from watsonx.ai")
        
        response_text = str(response).strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        findings = json.loads(response_text)
        
        if not isinstance(findings, list):
            raise ValueError("Response is not a JSON array")
        
        logger.info(f"Successfully parsed {len(findings)} findings")
        return findings
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        if 'response_text' in locals():
            logger.error(f"Response text: {response_text[:500]}")
        raise ValueError(f"Failed to parse watsonx.ai response as JSON: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error analyzing with watsonx.ai: {str(e)}")
        raise


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Bob Log Intelligence',
        'version': '1.0.0',
        'watsonx_configured': bool(BOB_API_KEY and BOB_PROJECT_ID)
    }), 200


@app.route('/api/analyze', methods=['POST'])
def analyze_log():
    """Analyze log file and return structured findings with risk analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please upload a log file'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a log file to upload'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type',
                'message': f'Only {", ".join(ALLOWED_EXTENSIONS)} files are allowed'
            }), 400
        
        try:
            log_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({
                'error': 'Invalid file encoding',
                'message': 'File must be UTF-8 encoded text'
            }), 400
        
        if not log_content.strip():
            return jsonify({
                'error': 'Empty file',
                'message': 'The uploaded log file is empty'
            }), 400
        
        filtered_lines = filter_log_lines(log_content)
        
        if not filtered_lines:
            return jsonify({
                'summary': {
                    'total_lines': 0,
                    'critical_count': 0,
                    'warning_count': 0
                },
                'issues': [],
                'risk_analysis': {
                    'risk_level': 'LOW',
                    'prediction': 'No errors or warnings found in the log file'
                }
            }), 200
        
        # Analyze with watsonx.ai
        raw_findings = analyze_with_watsonx(filtered_lines)
        
        # Group and count issues
        issues = group_and_count_issues(raw_findings)
        
        # Calculate risk analysis
        risk_analysis = calculate_risk_analysis(raw_findings)
        
        # Build response
        response = {
            'summary': {
                'total_lines': min(len(filtered_lines), MAX_LINES_TO_ANALYZE),
                'critical_count': risk_analysis['critical_count'],
                'warning_count': risk_analysis['warning_count']
            },
            'issues': sorted(issues, key=lambda x: (
                0 if x['severity'].lower() == 'critical' else 1 if x['severity'].lower() == 'warning' else 2,
                -x['frequency']
            )),
            'risk_analysis': {
                'risk_level': risk_analysis['risk_level'],
                'prediction': risk_analysis['prediction']
            }
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'error': 'Analysis failed',
            'message': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while analyzing the log file'
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': 'File too large',
        'message': 'Maximum file size is 10MB'
    }), 413


@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    if not BOB_API_KEY:
        logger.warning("BOB_API_KEY not set - watsonx.ai integration will not work")
    if not BOB_PROJECT_ID:
        logger.warning("BOB_PROJECT_ID not set - watsonx.ai integration will not work")
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Bob Log Intelligence on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

# Made with Bob
>>>>>>> 50a0100a5990aa7f2ff07d27c8c7af8c9a3f0767
