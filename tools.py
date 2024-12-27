from langchain.tools import Tool
from typing import List, Dict, Any
import logging
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import os
from dotenv import load_dotenv
from embedder import get_embedder

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_llm_response(query: str, context_chunks: List[Dict] = None, conversation_history: List[Dict] = None) -> str:
    """Get LLM response based on search results and conversation history."""
    try:
        # Initialize LLM
        llm = ChatGroq(
            temperature=0.5,
            model_name="mixtral-8x7b-32768",
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Create system message
        system_message = """You are REAIC, a real estate AI consultant. You help users with property valuation, 
        market analysis, investment strategies, and transaction negotiations. Always be professional, helpful, 
        and respectful. Remember user names and preferences when provided.
        
        Important instructions for handling document context:
        1. Only use information from the given context when answering questions about documents
        2. If you can't answer fully from the context, say what information is missing
        3. Never make up information or use external knowledge about documents
        4. Always cite the source document when providing information
        5. Express uncertainty clearly if unsure about any information
        
        When no document context is provided, you should:
        1. Focus on real estate consulting topics
        2. Use your general knowledge about real estate
        3. Be clear about what information or documents would help provide better answers
        4. Remember and use the user's name and preferences throughout the conversation"""
        
        # Create messages list
        messages = [
            SystemMessage(content=system_message)
        ]
        
        # Add conversation history
        if conversation_history:
            # Extract user's name from history if available
            user_name = None
            for msg in conversation_history:
                if msg['role'] == 'user':
                    # Look for common name introduction patterns
                    content = msg['content'].lower()
                    if "my name is " in content:
                        user_name = content.split("my name is ")[1].split()[0].title()
                        break
                    elif "i am " in content or "i'm " in content:
                        after_am = content.split("i am " if "i am " in content else "i'm ")[1].split()[0].title()
                        if len(after_am) > 2:  # Basic check to avoid "I am a..." cases
                            user_name = after_am
                            break
            
            # Add user context if found
            if user_name:
                messages.append(SystemMessage(
                    content=f"The user's name is {user_name}. Always refer to them by name when appropriate."
                ))
            
            # Add conversation history
            for msg in conversation_history:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
        
        # Add document context if provided
        if context_chunks:
            context_sections = []
            for chunk in context_chunks:
                if not isinstance(chunk, dict) or 'metadata' not in chunk:
                    continue
                    
                metadata = chunk['metadata']
                source = metadata.get('source', 'Unknown Source')
                page_num = metadata.get('page', 1)
                
                # Get content safely
                content = chunk.get('content', '') or chunk.get('page_content', '')
                if not content:
                    continue
                
                context_sections.append(
                    f"Document: {source}\n"
                    f"Page: {page_num}\n"
                    f"Content: {content}\n"
                )
            
            if context_sections:
                messages.append(
                    SystemMessage(content=f"Here is the relevant context from the documents:\n\n{chr(10).join(context_sections)}")
                )
        
        # Add the current query
        messages.append(HumanMessage(content=query))
        
        # Get response from LLM
        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        logger.error(f"Error getting LLM response: {str(e)}")
        return f"I apologize, but I encountered an error: {str(e)}"

def search_documents(query: str, k: int = 4) -> List[Dict]:
    """Search through embedded documents and return relevant information."""
    try:
        if not query:
            logger.warning("Empty query received")
            return []
            
        logger.info(f"Searching documents for query: {query}")
        
        # Get embedder instance
        embedder = get_embedder()
        
        # Check if vector store is empty
        collection_size = len(embedder.vector_store.get()['ids']) if embedder.vector_store.get() else 0
        if collection_size == 0:
            logger.info("Vector store is empty")
            return []
            
        # Perform search
        results = embedder.similarity_search(query, k=k)
        return results
        
    except Exception as e:
        logger.error(f"Error in search_documents: {str(e)}")
        return []

def process_new_pdfs(file_paths: List[str]) -> Dict[str, Any]:
    """Process new PDF files and add them to the vector store."""
    try:
        embedder = get_embedder()
        results = embedder.process_files(file_paths)
        return results
    except Exception as e:
        logger.error(f"Error processing PDFs: {str(e)}")
        return {"error": str(e)}

def initialize_tools() -> List[Tool]:
    """Initialize and return a list of tools for the agent."""
    try:
        tools = [
            Tool(
                name="Search Documents",
                func=search_documents,
                description="Search through uploaded documents using a query. Returns relevant text chunks."
            ),
            Tool(
                name="Process PDFs",
                func=process_new_pdfs,
                description="Process new PDF files and add them to the vector store."
            )
        ]
        return tools
    except Exception as e:
        logger.error(f"Error initializing tools: {str(e)}")
        return []
