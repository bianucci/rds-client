from dotenv import load_dotenv
import os


class DBConfiguration:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Load environment variables from .env file
        load_dotenv()

        # Configuration from environment variables
        self.db_name = os.getenv("DB_NAME")
        self.resource_arn = os.getenv("RESOURCE_ARN")
        self.secret_arn = os.getenv("SECRET_ARN")

        # Check if all required environment variables are set
        if not all([self.db_name, self.resource_arn, self.secret_arn]):
            raise ValueError(
                "Missing required environment variables. Please check your .env file."
            )
