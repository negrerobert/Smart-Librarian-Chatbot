import chromadb
from chromadb.config import Settings
import openai
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from .book_summaries import load_book_summaries_for_vectorization

load_dotenv()


class BookVectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the ChromaDB vector store for book summaries.

        Args:
            persist_directory (str): Directory to persist the ChromaDB data
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.collection_name = "book_summaries"

        # Set up OpenAI API key
        openai.api_key = os.getenv('OPENAI_API_KEY')

        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self._initialize_chroma()

    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create ChromaDB client with persistence
            self.client = chromadb.PersistentClient(path=self.persist_directory)

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )

            print(f"ChromaDB initialized with collection: {self.collection_name}")

        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise

    def _get_openai_embedding(self, text: str) -> List[float]:
        """
        Get embedding from OpenAI API.

        Args:
            text (str): Text to embed

        Returns:
            List[float]: Embedding vector
        """
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting OpenAI embedding: {e}")
            raise

    def populate_database(self, summaries_file_path: str = None):
        """
        Populate the ChromaDB with book summaries from file.

        Args:
            summaries_file_path (str): Path to the book summaries text file
        """
        try:
            # Use default path if none provided
            if summaries_file_path is None:
                from pathlib import Path
                project_root = Path(__file__).parent.parent.parent
                summaries_file_path = project_root / "data" / "book_summaries.txt"

            print(f"Attempting to populate database from: {summaries_file_path}")

            # Check if collection already has data
            if self.collection.count() > 0:
                print(f"Collection already contains {self.collection.count()} documents. Skipping population.")
                return

            # Load book summaries
            summaries = load_book_summaries_for_vectorization(str(summaries_file_path))

            if not summaries:
                print("No summaries loaded. Please check the file path and format.")
                return

            print(f"Loading {len(summaries)} book summaries into ChromaDB...")

            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            embeddings = []

            for i, summary in enumerate(summaries):
                # Get embedding from OpenAI
                embedding = self._get_openai_embedding(summary['content'])

                documents.append(summary['content'])
                metadatas.append({
                    'title': summary['title'],
                    'summary': summary['summary']
                })
                ids.append(f"book_{i}")
                embeddings.append(embedding)

                print(f"Processed: {summary['title']}")

            # Add to ChromaDB collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )

            print(f"Successfully added {len(summaries)} books to ChromaDB")

        except Exception as e:
            print(f"Error populating database: {e}")
            raise

    def search_books(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for books based on user query using semantic similarity.

        Args:
            query (str): User's search query
            n_results (int): Number of results to return

        Returns:
            List[Dict[str, Any]]: List of matching books with metadata
        """
        try:
            # Get embedding for the query
            query_embedding = self._get_openai_embedding(query)

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )

            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'title': results['metadatas'][0][i]['title'],
                        'summary': results['metadatas'][0][i]['summary'],
                        'document': results['documents'][0][i],
                        'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    })

            return formatted_results

        except Exception as e:
            print(f"Error searching books: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the current collection.

        Returns:
            Dict[str, Any]: Collection information
        """
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {}

    def reset_database(self):
        """Reset the database by deleting all documents."""
        try:
            # Delete the collection
            self.client.delete_collection(self.collection_name)

            # Recreate the collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            print("Database reset successfully")

        except Exception as e:
            print(f"Error resetting database: {e}")


# Initialize vector store instance
def create_vector_store() -> BookVectorStore:
    """Create and return a BookVectorStore instance."""
    return BookVectorStore()

