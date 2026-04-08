# Agentic Invoice Processing Workflow

An AI-powered application that turns raw PDF invoices into processed, categorized data. It employs a fully native FastAPI agentic workflow leveraging Google's Gemini models for high-reasoning multimodal extraction and fast cloud-based categorization.

## 🚀 How It Works (High Level)

1. **Upload via UI**: The user uploads one or more PDF invoices via the native **FastAPI HTML** frontend.
2. **Extraction Agent (LLM 1)**: The application triggers a **Gemini 1.5 Flash** agent using LangChain. Gemini analyzes the invoice (multimodal task) and extracts the raw structured data (Vendor, Date, Total, Tax, Line Items) strictly as JSON.
3. **Categorization Agent (LLM 2)**: The structured item data is forwarded to a secondary Gemini agent (**gemini-3.1-flash-lite-preview**). This agent intelligently assigns each item to an accounting category (e.g., Office, Travel, Software).
4. **Agentic Validation**: The workflow performs checks on the results (e.g., verifying `Total = Subtotal + Tax`).
5. **Human-In-The-Loop Review**: Extracted and categorized data is returned to the **Web UI** where a human accountant can review the results, look out for flagged errors, and ultimately download the processed data as a `.csv` file.

## 🛠️ Tools & Tech Stack

- **Python 3.10+** - Core language.
- **FastAPI** - Backend orchestration and Native Static UI serving.
- **LangChain & LangGraph** - Orchestrates the LLM workflow and pipeline between agents.
- **Gemini 1.5 Flash API** - Heavy lifting for Vision and multimodality extraction capabilities.
- **Gemini 3.1 Flash Lite API** - Fast and lightweight LLM for text-based categorization.
- **Pandas** - Data manipulation and CSV creation.

## 💻 Best Platforms to Run This

Because this architecture utilizes a **Pure Cloud Strategy** (Cloud API for both extraction and categorization), it is incredibly lightweight and can be deployed almost anywhere!

1. **Docker Container**: Setup via simple uvicorn backend routing.
2. **PaaS (Render / Railway / Heroku)**: Can easily be hosted utilizing standard Dockerfiles or Python buildpacks.

## ⚙️ Installation & Requirements

### Pre-requisites

To run this application locally, you'll need the following installed on your machine:
- **Python (3.10+)**
- A **Gemini Developer API Key**

### 1. Clone & Environment Setup

Create a virtual environment and install the required Python libraries.

```bash
# Set up a virtual environment (Linux/macOS)
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

*(Key libraries included: `fastapi`, `langchain`, `langchain-google-genai`, `pandas`)*

### 2. Configure Environment Variables

Create a file named `.env` in the root of the project to set up the Gemini extraction API key:

```env
GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

## ▶️ Running the Application Locally

You only need one command to run the whole unified application:

```bash
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

*The App should now automatically serve the frontend in your web browser at `http://127.0.0.1:8000`. Navigate there directly!*
