# AI-Based Collections Strategy Optimizer

An AI-powered collections strategy assistant prototype that recommends the most appropriate outreach approach for delinquent borrowers, ensuring a respectful, compliant communication tone.

## Tech Stack
- **Backend:** Python, Django
- **Frontend:** Django Templates, Tailwind CSS
- **Containerization:** Docker & Docker Compose
- **AI Integration:** Secure API Wrapper for an external LLM

## Running the Application

### Prerequisites
- Docker and Docker Compose installed on your system.

### Setup Steps
1. Clone the repository and navigate into the project directory.
2. In the `.env` file, ensure your LLM configuration is correctly set:
   ```env
   LLM_API_URL=https://llm-wrapper-741152993481.asia-south1.run.app/llm/query
   LLM_API_TOKEN=YOUR_API_TOKEN_HERE
   ```
3. Start the application:
   ```bash
   docker-compose up --build
   ```
4. Access the Agent Dashboard at `http://localhost:8000/`.

## Data Schema & Assumptions
This prototype uses synthetic data generated in `load_data.py`. 
- `Borrower` Model Attributes:
  - `name`: String
  - `days_past_due`: Integer
  - `amount_owed`: Decimal
  - `prior_payment_behavior`: String describing past history.
  - `hardship_indicator`: Boolean
  - `preferred_channel`: String (e.g., SMS, Email)

**Assumptions:**
- **Simplified Workflow:** Real telephony/SMS integrations are mocked.
- **LLM Output:** The prompt is heavily engineered to return a raw JSON object. The `LLMWrapperClient` in `strategy/llm_client.py` includes robust parsing logic to extract this JSON even if the API responds with markdown formatting or wrapped dictionaries.

## Simulated Security & Privacy
In a real-world scenario, this application would enforce strict data privacy:
- **Role-Based Access Control (RBAC):** Access to borrower profiles and the "Generate Strategy" button would be restricted exclusively to authenticated Agents. Supervisors might have access to aggregated dashboards.
- **Data Isolation:** Collections data would be isolated at the tenant/agency level.
- **Secrets Management:** The `LLM_API_TOKEN` is strictly consumed via `.env` files server-side and never exposed to the frontend/browser.

## Prompt Engineering Strategy
A "from-scratch" zero-shot prompt engineering approach is used.
- The prompt forcefully structures the output into exactly four keys: `segment`, `recommendedAction`, `messageDraft`, and `explanation`.
- It imposes a hard constraint on the `messageDraft` to be respectful, empathetic, and compliant, preventing harassing language.
- By injecting dynamic borrower attributes into the context window, the LLM makes tailored decisions (e.g., recognizing hardship indicators to suggest support rather than escalation).

## Failure Modes & Fallbacks
- **API Timeout/Error:** If the LLM API fails or times out, the `LLMWrapperClient` catches the exception and returns a safe fallback strategy ("Manual Review") with an explanation of the error.
- **Malformed JSON:** If the LLM hallucinates or returns invalid JSON text that the backend cannot parse, the system is designed to either gracefully attempt fallback parsing or alert the agent that a manual review is needed.
