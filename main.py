from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from tools import initialize_tools, search_documents, process_new_pdfs, get_llm_response
from chat_history import ChatHistoryManager
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_query(query: str, context_chunks=None):
    """Process a user query and return an AI response."""
    try:
        # Initialize LLM with API key
        llm = ChatGroq(
            temperature=0.7,
            model_name="mixtral-8x7b-32768",
            api_key=os.getenv('GROQ_API_KEY')
        )

        # If no context provided, search for relevant documents
        if context_chunks is None:
            context_chunks = search_documents(query)

        # Get response using the LLM
        response = get_llm_response(query, context_chunks)
        return response

    except Exception as e:
        logger.error(f"Error in process_query: {str(e)}")
        return "I apologize, but I encountered a technical issue. Please try again in a moment."

if __name__ == "__main__":
    import webbrowser
    from app import app
    
    # Set the port for the Flask app
    port = 5000
    
    # Open Chrome browser
    chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    
    # Open the URL in Chrome after a slight delay to ensure server is up
    url = f'http://127.0.0.1:{port}'
    
    def open_browser():
        try:
            webbrowser.get('chrome').open_new(url)
        except Exception as e:
            print(f"Could not open Chrome automatically: {e}")
            print(f"Please manually open {url} in your browser")
    
    # Schedule browser opening
    import threading
    threading.Timer(1.5, open_browser).start()
    
    # Run the Flask app
    app.run(port=port, debug=True, use_reloader=False)
