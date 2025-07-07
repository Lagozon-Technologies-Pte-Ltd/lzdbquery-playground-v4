import chromadb
from chromadb.utils import embedding_functions
import json
import os
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExampleManager:
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize the ExampleManager with persistent storage.
        
        Args:
            persist_directory: Directory to store ChromaDB data. If None, uses environment variable.
        """
        self.client = chromadb.PersistentClient(
            path=persist_directory or os.environ.get('Chroma_Query_Examples', "./chroma_data")
        )
        self.embedding_function = self._get_embedding_function()
        self.collections: Dict[str, chromadb.Collection] = {}
        self._initialize_all_collections()

    def _get_embedding_function(self):
        """Create the Azure OpenAI embedding function."""
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ['AZURE_OPENAI_API_KEY'],
            api_base=os.environ['AZURE_OPENAI_ENDPOINT'],
            api_type="azure",
            api_version=os.environ.get('AZURE_OPENAI_API_VERSION', "2024-02-01"),
            model_name=os.environ['AZURE_EMBEDDING_DEPLOYMENT_NAME']
        )

    def _initialize_all_collections(self):
        """Initialize all example collections."""
        collections_config = {
            "generic": "sql_query_examples_generic.json",
            "usecase": "sql_query_examples_usecase.json"
        }
        
        for question_type, file_path in collections_config.items():
            try:
                self._initialize_collection(question_type, file_path)
            except Exception as e:
                logger.error(f"Failed to initialize {question_type} collection: {str(e)}")
                raise

    def _initialize_collection(self, question_type: str, file_path: str):
        """Initialize a single collection with examples from a JSON file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                examples = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading examples for {question_type}: {str(e)}")
            raise

        collection_name = f"examples_{question_type}"
        
        # Get or create collection (without deleting first)
        collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
        # Check if collection is empty before adding examples
        if collection.count() == 0:
            # Prepare and add examples
            inputs = [item['input'] for item in examples]
            queries = [item['query'] for item in examples]
            
            collection.add(
                ids=[f"{question_type}ex{i}" for i in range(len(inputs))],
                documents=inputs,
                metadatas=[{"query": q} for q in queries]
            )
            logger.info(f"Added {len(inputs)} examples to {collection_name}")
        else:
            logger.info(f"Using existing collection {collection_name} with {collection.count()} items")
        
        self.collections[question_type] = collection

    def get_collection(self, question_type: str) -> chromadb.Collection:
        """Get a collection by question type."""
        if question_type not in self.collections:
            raise ValueError(f"Invalid question type: {question_type}. Must be one of {list(self.collections.keys())}")
        return self.collections[question_type]

# Initialize manager with error handling
try:
    example_manager = ExampleManager()
except Exception as e:
    logger.error(f"Critical error initializing ExampleManager: {str(e)}")
    # Depending on your use case, you might want to exit or raise
    raise