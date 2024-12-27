from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
from tools import search_documents, get_llm_response
from embedder import get_embedder
from chat_history import ChatHistoryManager
import logging
import uuid
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'pdf_files'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-123')

# Initialize managers
chat_history = ChatHistoryManager()
embedder = get_embedder()

# Process any existing PDFs at startup
try:
    embedder.process_new_pdfs()
except Exception as e:
    print(f"Error initializing PDFEmbedder: {str(e)}")

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        if not message:
            return jsonify({'error': 'Empty message'}), 400
            
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        # Get existing conversation or initialize new one
        conversation = chat_history.get_conversation(conversation_id)
        if conversation:
            messages = conversation.get('messages', [])
        else:
            messages = []
            # Add initial greeting if this is a new conversation
            messages.append({
                'role': 'assistant',
                'content': "Hello! I'm REAIC, your real estate AI consultant. I can help you with property valuation, market analysis, investment strategies, and more. How can I assist you today?"
            })
        
        # Add user message
        messages.append({
            'role': 'user',
            'content': message
        })
        
        # Search for relevant documents
        results = search_documents(message)
        
        # Get LLM response with full conversation history
        response = get_llm_response(
            query=message,
            context_chunks=results,
            conversation_history=messages
        )
        
        # Add assistant response
        messages.append({
            'role': 'assistant',
            'content': response
        })
        
        # Save conversation to disk
        chat_history.save_conversation(
            conversation_id=conversation_id,
            messages=messages
        )
        
        return jsonify({
            'response': response,
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run the app on 0.0.0.0 to make it accessible from outside the container
    app.run(host='0.0.0.0', port=5000, debug=True)
