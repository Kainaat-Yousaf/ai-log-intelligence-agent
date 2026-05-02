# 🚀 Quick Start Guide - AI Log Intelligence Agent

## ⚠️ Important: Dependencies Required

Before running the application, you need to install the required Python packages.

## 📦 Installation Steps

### Step 1: Install All Dependencies

Open Command Prompt (CMD) and run:

```cmd
pip install Flask flask-cors ibm-watsonx-ai streamlit requests pandas python-dotenv
```

Or install from requirements.txt:

```cmd
pip install -r requirements.txt
```

### Step 2: Configure IBM watsonx.ai Credentials

1. Create a `.env` file in the `backend/` directory
2. Copy the template from `backend/.env.example`
3. Add your IBM watsonx.ai credentials:

```env
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

**How to get credentials:**
- Sign up at https://cloud.ibm.com/
- Create a watsonx.ai instance
- Navigate to your project and copy the API key and Project ID

## 🏃 Running the Application

### Option 1: Run Backend and Frontend Separately

**Terminal 1 - Start Backend:**
```cmd
cd backend
python app.py
```

Backend will start on: http://localhost:5000

**Terminal 2 - Start Frontend:**
```cmd
cd frontend
streamlit run streamlit_app.py
```

Frontend will open in browser at: http://localhost:8501

### Option 2: Quick Test (Without watsonx.ai)

If you don't have watsonx.ai credentials yet, you can still test the core functionality:

```cmd
python tests/test_backend_simple.py
```

This runs unit tests for:
- Log filtering logic
- File validation
- Risk calculation
- Issue grouping

## 🧪 Running Tests

### Run Simple Tests (No Dependencies):
```cmd
python tests/test_backend_simple.py
```

### Create Sample Log Files:
```cmd
python tests/test_sample_logs.py
```

This creates test log files in `tests/sample_logs/`:
- simple_error.log
- critical_errors.log
- mixed_severity.log
- exceptions.log
- clean.log

## 📝 Using the Application

1. **Start both backend and frontend** (see above)
2. **Open browser** to http://localhost:8501
3. **Upload a log file** (.log or .txt, max 10MB)
4. **Click "Analyze Logs"**
5. **View results:**
   - Summary metrics
   - Risk prediction
   - Top issues table
   - Root cause analysis
   - Suggested fixes

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Install dependencies
```cmd
pip install Flask flask-cors
```

### Error: "ModuleNotFoundError: No module named 'streamlit'"
**Solution:** Install Streamlit
```cmd
pip install streamlit
```

### Error: "Backend API is not running"
**Solution:** Start the backend first
```cmd
cd backend
python app.py
```

### Error: "watsonx.ai authentication failed"
**Solution:** Check your `.env` file in backend/ directory
- Verify API key is correct
- Verify Project ID is correct
- Ensure no extra spaces in credentials

### Port Already in Use
**Backend (port 5000):**
```cmd
# Windows - Find and kill process
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

**Frontend (port 8501):**
```cmd
# Windows - Find and kill process
netstat -ano | findstr :8501
taskkill /PID <process_id> /F
```

## 📊 Test Results Summary

### ✅ Core Functionality Tests (27/27 Passed)

**Test Suite: test_backend_simple.py**
- ✅ Log Filter Pattern (7/7 tests)
- ✅ File Extension Validation (7/7 tests)
- ✅ Log Line Filtering (4/4 tests)
- ✅ Risk Level Calculation (7/7 tests)
- ✅ Issue Grouping (2/2 tests)

**Success Rate: 100%**

All core backend logic is working correctly without external dependencies.

## 🎯 Next Steps

1. **Install dependencies** (if not done)
2. **Configure watsonx.ai** credentials
3. **Start backend** server
4. **Start frontend** UI
5. **Upload and analyze** your log files

## 📚 Additional Resources

- **Backend API Documentation:** See README.md
- **Sample Logs:** tests/sample_logs/
- **Test Cases:** tests/test_backend_simple.py
- **IBM watsonx.ai Docs:** https://www.ibm.com/docs/en/watsonx-as-a-service

---

**Need Help?** Check the troubleshooting section or review the test results above.