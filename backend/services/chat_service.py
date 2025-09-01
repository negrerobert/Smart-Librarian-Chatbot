import openai
import json
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from ..database.vector_store import BookVectorStore
from ..database.book_summaries import get_summary_by_title, get_all_book_titles
from .filter_service import content_filter

load_dotenv()


class SmartLibrarianChatService:
    """
    Main chat service that integrates OpenAI GPT with RAG and function calling.
    """

    def __init__(self):
        # Initialize OpenAI client
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # Initialize vector store
        self.vector_store = BookVectorStore()

        # System prompt for the AI librarian
        self.system_prompt = """
        You are a smart AI librarian assistant that helps users find books based on their interests. 

        Your capabilities:
        1. You have access to a database of book summaries through RAG (semantic search)
        2. You can get detailed summaries of specific books using the get_summary_by_title function
        3. You should be conversational, helpful, and enthusiastic about books

        Instructions:
        - When a user asks for book recommendations, search the database using the provided context
        - Always recommend specific books from your database, not general suggestions
        - After recommending a book, automatically call get_summary_by_title to provide detailed information
        - Be conversational and ask follow-up questions to help users find their perfect book
        - If a user asks about a specific book title, use get_summary_by_title to provide detailed information
        - Keep responses engaging and personal, like a friendly librarian would

        Available books in your database include classics like 1984, The Hobbit, Pride and Prejudice, 
        Harry Potter, The Great Gatsby, and many more.
        """

        # Define the tool schema for OpenAI function calling (updated syntax)
        self.tool_schema = {
            "type": "function",
            "function": {
                "name": "get_summary_by_title",
                "description": "Get a detailed summary of a book by its exact title. Use this after recommending a book or when a user asks about a specific book.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The exact title of the book to get the summary for"
                        }
                    },
                    "required": ["title"]
                }
            }
        }

    def _search_books_for_context(self, query: str, n_results: int = 3) -> str:
        """
        Search books using RAG and format results for context.

        Args:
            query (str): User query
            n_results (int): Number of results to include

        Returns:
            str: Formatted search results for context
        """
        search_results = self.vector_store.search_books(query, n_results)

        if not search_results:
            return "No relevant books found in the database."

        context = "Relevant books from the database:\n\n"
        for result in search_results:
            context += f"**{result['title']}**\n"
            context += f"Summary: {result['summary']}\n"
            context += f"Relevance Score: {result['similarity_score']:.2f}\n\n"

        return context

    def _execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute function calls from the AI model.

        Args:
            function_name (str): Name of the function to call
            arguments (Dict[str, Any]): Function arguments

        Returns:
            str: Function result
        """
        if function_name == "get_summary_by_title":
            title = arguments.get("title", "")
            return get_summary_by_title(title)
        else:
            return f"Unknown function: {function_name}"

    def chat(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process user message and return AI response.

        Args:
            user_message (str): User's message
            conversation_history (Optional[List[Dict[str, str]]]): Previous conversation messages

        Returns:
            Dict[str, Any]: Response containing AI message and metadata
        """
        try:
            # Apply content filter
            is_appropriate, filter_response = content_filter.filter_message(user_message)

            if not is_appropriate:
                return {
                    'success': True,
                    'message': filter_response,
                    'filtered': True,
                    'function_calls': [],
                    'search_results': []
                }

            # Search for relevant books using RAG
            search_context = self._search_books_for_context(user_message)
            search_results = self.vector_store.search_books(user_message, 3)

            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Keep last 6 messages for context

            # Add current user message with RAG context
            user_message_with_context = f"""
            User query: {user_message}

            {search_context}

            Based on the relevant books above, please provide a helpful response and recommendation.
            """

            messages.append({"role": "user", "content": user_message_with_context})

            # Call OpenAI API with tool calling
            response = openai.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                tools=[self.tool_schema],
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000
            )

            ai_message = response.choices[0].message
            function_calls = []

            # Handle tool calls
            if ai_message.tool_calls:
                # Add the assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": ai_message.content,
                    "tool_calls": ai_message.tool_calls
                })

                # Process all tool calls and add their responses
                for tool_call in ai_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    # Execute the function
                    function_result = self._execute_function_call(function_name, function_args)

                    function_calls.append({
                        'function': function_name,
                        'arguments': function_args,
                        'result': function_result
                    })

                    # Add tool response message
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": function_result
                    })

                # Get final response after all tool calls are processed
                final_response = openai.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )

                final_message = final_response.choices[0].message.content
            else:
                final_message = ai_message.content

            return {
                'success': True,
                'message': final_message,
                'filtered': False,
                'function_calls': function_calls,
                'search_results': [{'title': r['title'], 'similarity': r['similarity_score']} for r in search_results]
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                'filtered': False,
                'function_calls': [],
                'search_results': [],
                'error': str(e)
            }

    def get_available_books(self) -> List[str]:
        """Get list of all available book titles."""
        return get_all_book_titles()

    def initialize_database(self, summaries_file_path: str = "data/book_summaries.txt"):
        """Initialize the vector database with book summaries."""
        self.vector_store.populate_database(summaries_file_path)

    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the database."""
        return self.vector_store.get_collection_info()


# Create a global instance
smart_librarian = SmartLibrarianChatService()
