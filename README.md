# EXL FNOL Transcript Analyzer

## 🚀 Industrial-Grade Application for Insurance Call Transcript Analysis

An enterprise-ready Streamlit application that analyzes First Notice of Loss (FNOL) call transcripts for SOP compliance using Claude AI.

![EXL Logo](assets/exl_logo.png)

---

## 📋 Features

- **AI-Powered Analysis**: Leverages Claude AI for intelligent transcript analysis
- **SOP Compliance Checking**: Validates against 12 standard FNOL requirements
- **Severity Classification**: Categorizes findings as High, Medium, or Low severity
- **Batch Processing**: Process multiple transcripts with progress tracking
- **Export Capabilities**: Download results in Excel or CSV format
- **Modern UI**: EXL-branded interface with responsive design

---

## 🏗️ Project Structure

```
Transcript_Analysis_Streamlit/
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
│
├── .streamlit/
│   └── config.toml            # Streamlit configuration
│
├── config/
│   ├── __init__.py
│   ├── settings.py            # Application settings & configuration
│   └── theme.py               # EXL theme & styling
│
├── components/
│   ├── __init__.py
│   ├── sidebar.py             # Sidebar component
│   ├── header.py              # Header component
│   ├── file_uploader.py       # File upload component
│   ├── results_display.py     # Results display component
│   └── metrics.py             # Metrics & KPI components
│
├── services/
│   ├── __init__.py
│   ├── claude_service.py      # Claude AI integration
│   └── file_service.py        # File handling operations
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py             # Helper utilities
│   └── validators.py          # Input validation
│
└── assets/
    └── exl_logo.png           # EXL logo asset
```

---

## 🛠️ Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone or navigate to the project directory**

   ```bash
   cd Transcript_Analysis_Streamlit
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo ANTHROPIC_API_KEY=your_api_key_here > .env
   ```

---

## 🚀 Running the Application

### Development Mode

```bash
streamlit run app.py
```

### Production Mode

```bash
streamlit run app.py --server.port 8501 --server.headless true
```

The application will be available at `http://localhost:8501`

---

## 📊 Usage

1. **Upload File**: Upload an Excel (.xlsx, .xls) or CSV file containing transcripts
2. **Select Column**: Choose the column containing the call transcripts
3. **Configure Processing**: Select the number of transcripts to analyze
4. **Start Analysis**: Click "Start Analysis" to begin processing
5. **Review Results**: View compliance findings with severity indicators
6. **Export**: Download results in Excel or CSV format

---

## 📁 Input File Format

Your input file should contain:

| Column        | Description                     |
| ------------- | ------------------------------- |
| transcript_id | Unique identifier for each call |
| transcript    | The actual conversation text    |

Additional columns will be preserved in the output.

---

## 🎯 SOP Compliance Checks

The analyzer validates transcripts against these FNOL requirements:

1. ✅ Policyholder verification (name, policy number)
2. ✅ Date, time, and location of incident
3. ✅ Description of what happened
4. ✅ Parties involved (names, contact info)
5. ✅ Injuries reported (severity, medical attention)
6. ✅ Property damage details
7. ✅ Police report filed (report number)
8. ✅ Witness information
9. ✅ Photos/documentation mentioned
10. ✅ Next steps communicated
11. ✅ Claim number assigned
12. ✅ Professional and empathetic tone

---

## ⚙️ Configuration

### Environment Variables

| Variable            | Description                    | Required |
| ------------------- | ------------------------------ | -------- |
| `ANTHROPIC_API_KEY` | Claude API key                 | Yes      |
| `APP_ENVIRONMENT`   | development/staging/production | No       |

### Streamlit Configuration

Edit `.streamlit/config.toml` to customize:

- Theme colors
- Server settings
- Upload limits
- Logging levels

---

## 🔒 Security

- API keys should be stored as environment variables
- File uploads are validated and size-limited
- XSRF protection enabled
- No sensitive data logged

---

## 📈 Performance

- Batch processing with progress tracking
- Rate limiting for API calls
- Retry logic for failed requests
- Efficient DataFrame operations

---

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

---

## 📝 License

Proprietary - EXL Service

---

## 👥 Support

For issues or questions, contact the EXL Analytics team.

---

**Powered by EXL × Claude AI**
