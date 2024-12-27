import json
import os
from datetime import datetime
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    def __init__(self, history_dir="chat_history"):
        """Initialize chat history manager."""
        self.history_dir = history_dir
        os.makedirs(history_dir, exist_ok=True)
    
    def save_conversation(self, conversation_id: str, messages: List[Dict]) -> bool:
        """Save a conversation thread to a JSON file."""
        try:
            # Create a unique filename for the conversation
            filename = os.path.join(self.history_dir, f"conversation_{conversation_id}.json")
            
            # Get existing conversation if it exists
            existing_messages = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    existing_messages = data.get('messages', [])
            
            # Update conversation data
            conversation_data = {
                "conversation_id": conversation_id,
                "last_updated": datetime.now().isoformat(),
                "messages": messages,
                "title": self._generate_title(messages)
            }
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Conversation saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            return False
    
    def get_conversation(self, conversation_id: str) -> Dict:
        """Get a specific conversation by ID."""
        try:
            filename = os.path.join(self.history_dir, f"conversation_{conversation_id}.json")
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            return None
    
    def get_all_conversations(self) -> List[Dict]:
        """Get all conversations with their metadata."""
        try:
            conversations = []
            for file in os.listdir(self.history_dir):
                if file.startswith('conversation_') and file.endswith('.json'):
                    filepath = os.path.join(self.history_dir, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        conversation = json.load(f)
                        # Add a preview of the conversation
                        conversation['preview'] = self._generate_preview(conversation['messages'])
                        conversations.append(conversation)
            
            # Sort by last updated time, newest first
            return sorted(
                conversations,
                key=lambda x: x.get('last_updated', ''),
                reverse=True
            )
            
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []
    
    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation by its ID."""
        try:
            # Get the conversation file path
            conversation_file = os.path.join(self.history_dir, f"conversation_{conversation_id}.json")
            
            # Check if file exists
            if not os.path.exists(conversation_file):
                raise FileNotFoundError(f"Conversation {conversation_id} not found")
                
            # Delete the file
            os.remove(conversation_file)
            logger.info(f"Deleted conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            raise
    
    def _generate_title(self, messages: List[Dict]) -> str:
        """Generate a title for the conversation based on the first user message."""
        try:
            for msg in messages:
                if msg['role'] == 'user':
                    # Take first 50 chars of first user message
                    title = msg['content'][:50]
                    if len(msg['content']) > 50:
                        title += '...'
                    return title
            return "New Conversation"
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            return "New Conversation"
    
    def _generate_preview(self, messages: List[Dict]) -> str:
        """Generate a preview of the conversation."""
        try:
            if not messages:
                return "Empty conversation"
            
            # Get the last message
            last_msg = messages[-1]
            preview = last_msg['content'][:100]
            if len(last_msg['content']) > 100:
                preview += '...'
            return preview
            
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}")
            return "Preview not available"

def get_tools(embedder):
    return [
        Tool(
            name="Query Documents",
            func=lambda query: embedder.similarity_search(query),
            description="Useful for searching through documents. Input should be a search query."
        )
    ]

def create_agent(embedder):
    tools = get_tools(embedder)
    
    # Initialize memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Create prompt template
    template = """You are a helpful assistant that can search through documents and answer questions.
    Use the tools available to you to search through documents and provide relevant information.
    
    If the user asks to search for something, ALWAYS use the Query Documents tool with their search query.
    After getting search results, summarize the relevant information in a clear and concise way.
    
    If no relevant information is found, politely inform the user.
    
    Chat History: {chat_history}
    Human: {input}
    Assistant: Let me help you with that."""
    
    prompt = PromptTemplate(
        input_variables=["chat_history", "input"],
        template=template
    )
    
    # Create conversation chain
    llm_chain = LLMChain(
        llm=ChatGroq(temperature=0, model_name="mixtral-8x7b-32768"),
        prompt=prompt,
        verbose=True,
        memory=memory,
    )
    
    agent = initialize_agent(
        tools,
        llm_chain.llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        memory=memory
    )
    
    return agent
