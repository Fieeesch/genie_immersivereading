import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_DIRECTORY = "database"

# Number of characters per text chunk for scene splitting
CHUNKSIZE = 5000

# OpenAI Configuration
USE_OPENAI_API = False
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-5.1"