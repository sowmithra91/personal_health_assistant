# Personal Health Assistant
An Agentic AI Implementation of a Health Assistant Persona with LangGraph

## Getting Started

### Prerequisites
Ensure you have Python installed on your system. You can download it from [python.org](https://www.python.org/) if needed. This project is compatible with Python 3.8 or higher.

### Installation
1. **Clone the Repository**  
   Clone this repository to your local machine and navigate to the `multi_ai_agent` directory inside the `personal_health_assistant` project:
   ```bash
   git clone <repository-url>
   cd personal_health_assistant/multi_ai_agent
   ```

2. **Install Dependencies**  
   Install the required Python packages listed in `requirements.txt`:  
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**  
   Update the `.env` file located in the `multi_ai_agent` directory with your own API keys by adding the following:
    ```bash
    OPENAI_API_KEY=<OPENAI_API_KEY>
    LANGSMITH_API_KEY=<LANGSMITH_API_KEY>
    ```

### Running the Application
1. **Start the LangGraph Application**  
   Launch the development server using the following command from the `multi_ai_agent` directory:  
   ```bash
   langgraph dev
   ```
   This runs the application locally in development mode with in-memory storage and hot reloading.

### Accessing the Studio UI
Once the application is running, you can access the LangGraph Studio UI to interact with your Health Assistant:  
- **URL**: [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)  
- Ensure the server is running locally at `http://127.0.0.1:2024` before accessing the UI.

### Accessing API Documentation
The API documentation is available locally when the server is running:  
- **URL**: [http://127.0.0.1:2024/docs](http://127.0.0.1:2024/docs)  
- Open this link in your browser to explore the available endpoints and their usage.
