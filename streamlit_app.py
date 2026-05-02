"""
AI Log Intelligence Agent - Streamlit Frontend
Hackathon-winning log analysis interface
"""

import streamlit as st
import requests
import pandas as pd
from typing import Dict, List
import time

# Page configuration
st.set_page_config(
    page_title="AI Log Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .risk-high {
        background-color: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .risk-medium {
        background-color: #ffaa00;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .risk-low {
        background-color: #00cc66;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .issue-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
    }
    .critical-card {
        border-left-color: #ff4444;
        background-color: #fff5f5;
    }
    .warning-card {
        border-left-color: #ffaa00;
        background-color: #fffbf0;
    }
    .info-card {
        border-left-color: #4444ff;
        background-color: #f5f5ff;
    }
    </style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:5000"


def check_api_health() -> bool:
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def analyze_log_file(file) -> Dict:
    """Send log file to backend for analysis"""
    try:
        files = {'file': (file.name, file, 'text/plain')}
        response = requests.post(
            f"{API_BASE_URL}/api/analyze",
            files=files,
            timeout=120
        )
        
        if response.status_code == 200:
            return {'success': True, 'data': response.json()}
        else:
            error_data = response.json()
            return {
                'success': False,
                'error': error_data.get('message', 'Unknown error occurred')
            }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timeout. Please try with a smaller file.'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Cannot connect to backend API. Please ensure it is running.'}
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}'}


def display_summary(summary: Dict):
    """Display summary metrics"""
    st.markdown("## 📊 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Lines Analyzed",
            value=summary.get('total_lines', 0),
            delta=None
        )
    
    with col2:
        critical_count = summary.get('critical_count', 0)
        st.metric(
            label="Critical Errors",
            value=critical_count,
            delta=f"🚨 {critical_count} issues" if critical_count > 0 else "✅ None"
        )
    
    with col3:
        warning_count = summary.get('warning_count', 0)
        st.metric(
            label="Warnings",
            value=warning_count,
            delta=f"⚠️ {warning_count} issues" if warning_count > 0 else "✅ None"
        )


def display_risk_analysis(risk_analysis: Dict):
    """Display risk prediction"""
    st.markdown("## 🔮 Risk Prediction")
    
    risk_level = risk_analysis.get('risk_level', 'UNKNOWN')
    prediction = risk_analysis.get('prediction', 'No prediction available')
    
    if risk_level == 'HIGH':
        st.markdown(f'<div class="risk-high">⚠️ RISK LEVEL: {risk_level}</div>', unsafe_allow_html=True)
        st.error(prediction)
    elif risk_level == 'MEDIUM':
        st.markdown(f'<div class="risk-medium">⚡ RISK LEVEL: {risk_level}</div>', unsafe_allow_html=True)
        st.warning(prediction)
    else:
        st.markdown(f'<div class="risk-low">✅ RISK LEVEL: {risk_level}</div>', unsafe_allow_html=True)
        st.success(prediction)


def display_top_issues(issues: List[Dict]):
    """Display top issues in a structured format"""
    st.markdown("## 🚨 Top Issues")
    
    if not issues:
        st.info("No issues detected in the log file.")
        return
    
    # Create DataFrame for table view
    df_data = []
    for issue in issues[:10]:  # Show top 10
        df_data.append({
            'Title': issue.get('title', 'Unknown'),
            'Severity': issue.get('severity', 'info').upper(),
            'Frequency': issue.get('frequency', 1),
            'Description': issue.get('description', '')[:100] + '...' if len(issue.get('description', '')) > 100 else issue.get('description', '')
        })
    
    df = pd.DataFrame(df_data)
    
    # Apply color coding
    def color_severity(val):
        if val == 'CRITICAL':
            return 'background-color: #ff4444; color: white'
        elif val == 'WARNING':
            return 'background-color: #ffaa00; color: white'
        else:
            return 'background-color: #4444ff; color: white'
    
    styled_df = df.style.applymap(color_severity, subset=['Severity'])
    st.dataframe(styled_df, use_container_width=True, height=400)


def display_root_cause_analysis(issues: List[Dict]):
    """Display detailed root cause analysis"""
    st.markdown("## 🧠 Root Cause Analysis")
    
    if not issues:
        st.info("No issues to analyze.")
        return
    
    for idx, issue in enumerate(issues[:5], 1):  # Show top 5 detailed
        severity = issue.get('severity', 'info').lower()
        
        with st.expander(f"**{idx}. {issue.get('title', 'Unknown Issue')}** ({severity.upper()}) - Frequency: {issue.get('frequency', 1)}"):
            st.markdown(f"**Description:**")
            st.write(issue.get('description', 'No description available'))
            
            st.markdown(f"**Root Cause:**")
            st.info(issue.get('root_cause', 'No root cause identified'))
            
            st.markdown(f"**Log Reference:**")
            st.code(issue.get('line_reference', 'No reference available'), language='log')


def display_suggested_fixes(issues: List[Dict]):
    """Display actionable fix recommendations"""
    st.markdown("## 💡 Suggested Fixes")
    
    if not issues:
        st.info("No fixes needed.")
        return
    
    # Group by severity
    critical_fixes = [i for i in issues if i.get('severity', '').lower() == 'critical']
    warning_fixes = [i for i in issues if i.get('severity', '').lower() == 'warning']
    
    if critical_fixes:
        st.markdown("### 🔴 Critical - Immediate Action Required")
        for idx, issue in enumerate(critical_fixes[:5], 1):
            st.markdown(f"**{idx}. {issue.get('title', 'Unknown')}**")
            st.error(f"✅ {issue.get('fix', 'No fix available')}")
    
    if warning_fixes:
        st.markdown("### 🟡 Warnings - Recommended Actions")
        for idx, issue in enumerate(warning_fixes[:5], 1):
            st.markdown(f"**{idx}. {issue.get('title', 'Unknown')}**")
            st.warning(f"✅ {issue.get('fix', 'No fix available')}")


def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🤖 AI Log Intelligence Agent</h1>', unsafe_allow_html=True)
    st.markdown("### Powered by IBM watsonx.ai | Analyze logs with AI precision")
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Backend API is not running. Please start the Flask backend first.")
        st.code("cd backend && python app.py", language="bash")
        return
    
    st.success("✅ Backend API is running")
    
    # File uploader
    st.markdown("---")
    uploaded_file = st.file_uploader(
        "Upload your log file (.log or .txt)",
        type=['log', 'txt'],
        help="Maximum file size: 10MB"
    )
    
    # Analyze button
    if uploaded_file is not None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_button = st.button("🔍 Analyze Logs", use_container_width=True, type="primary")
        
        if analyze_button:
            # Show loading spinner
            with st.spinner('🤖 AI is analyzing your logs... This may take a minute.'):
                # Simulate progress
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # Analyze the file
                result = analyze_log_file(uploaded_file)
            
            # Clear progress bar
            progress_bar.empty()
            
            if result['success']:
                st.success("✅ Analysis complete!")
                
                data = result['data']
                
                # Display all sections
                st.markdown("---")
                display_summary(data.get('summary', {}))
                
                st.markdown("---")
                display_risk_analysis(data.get('risk_analysis', {}))
                
                st.markdown("---")
                display_top_issues(data.get('issues', []))
                
                st.markdown("---")
                display_root_cause_analysis(data.get('issues', []))
                
                st.markdown("---")
                display_suggested_fixes(data.get('issues', []))
                
                # Download results
                st.markdown("---")
                st.markdown("###Download Results")
                st.download_button(
                    label="Download JSON Report",
                    data=str(data),
                )
                st.download_button(
                    label="Download JSON Report",
                    data=str(data),
                    file_name="log_analysis_report.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main()