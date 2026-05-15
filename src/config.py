from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    
    # LLM Configuration
    llm_provider: str = Field(default="groq", env="LLM_PROVIDER")  # "openai" or "groq"
    openai_model: str = Field(default="openai/gpt-oss-20b", env="OPENAI_MODEL")
    groq_model: str = Field(default="openai/gpt-oss-120b", env="GROQ_MODEL")
    
    # Database
    database_url: str = Field(default="sqlite:///./data/legal_ai.db", env="DATABASE_URL")
    
    # Paths
    chroma_db_path: str = Field(default="./data/chroma_db", env="CHROMA_DB_PATH")
    sample_docs_path: str = Field(default="./data/sample_docs", env="SAMPLE_DOCS_PATH")
    outputs_path: str = Field(default="./data/outputs", env="OUTPUTS_PATH")
    
    # Models
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # Server
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # Chunking
    chunk_size: int = 800
    chunk_overlap: int = 150
    max_retrieval_results: int = 6

    class Config:
        env_file = ".env"
        extra = "ignore"

    def ensure_dirs(self):
        for path in [self.chroma_db_path, self.sample_docs_path, self.outputs_path]:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    @property
    def current_model(self) -> str:
        """Get the currently configured model name"""
        return self.groq_model if self.llm_provider == "groq" else self.openai_model


settings = Settings()
settings.ensure_dirs()
