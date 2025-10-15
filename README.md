# Intelligent Trip Planner Agent

This project is an AI-driven Trip Planner Agent that uses LangChain, LangGraph, and LangSmith to autonomously plan, evaluate, and optimize travel options.

## Features

- **Weather-Aware Planning**: Integrates with OpenWeatherMap to check weather conditions and suggest alternatives if needed.
- **Hotel and Attraction Search**: Uses DuckDuckGo Search API to find hotels and attractions based on user preferences and budget.
- **Personalized Itinerary**: Generates a day-wise itinerary using Gemini LLM.
- **LangGraph Orchestration**: Uses LangGraph for decision flows and state management.
- **LangSmith Monitoring**: All steps are traced and monitored in LangSmith.

## How to Use

1. Clone the repository.
2. Install the requirements: `pip install -r requirements.txt`
3. Create a `.env` file and set the following environment variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `OPENWEATHER_API_KEY`: Your OpenWeatherMap API key.
   - `LANGCHAIN_API_KEY`: Your LangSmith API key.
4. Run the Streamlit app: `streamlit run app.py`

## Project Structure

- `app.py`: Streamlit UI.
- `agents/`: Contains the LangGraph agent and state definition.
- `tools/`: Contains the tools for weather, search, and travel data.
- `chains/`: Contains the LLM chain for itinerary generation.
- `config/`: Configuration settings.
- `utils/`: Helper functions.

## Note on Deviations from Problem Statement

- **Flight Search**: We are not including flight search due to the lack of a free and reliable flight API. We focus on hotels and attractions.
- **Initial Conversation**: We use a form-based interface to collect user requirements instead of an LLM-based conversation. This is for simplicity and clarity.
- **Feedback Loop**: The feedback loop is implemented by allowing the user to adjust the input and run the entire graph again. We do not have a dynamic retriggering of specific nodes within the same session.

## Deployment

The app can be deployed on Render. Use the provided `render.yaml` for configuration.

## License

MIT