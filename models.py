from log_config import setup_logger

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

import chromadb
from chromadb.db.base import UniqueConstraintError
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader

logger = setup_logger(__name__, './logs/models.log')

logger.info("Connecting to chroma database...")
try:
    chroma_client = chromadb.PersistentClient(path="./data")
    logger.info("Chroma Heartbeat: " + str(chroma_client.heartbeat()))
    logger.info("Connected to Chroma database.")
except Exception as e:
    logger.error(f"Error connecting to Chroma - {e}")


logger.info("Connecting to SQLite database...")
try:
    engine = create_engine('sqlite:///vectorvision.db')
    logger.info("SQLite Connection established.")
except Exception as e:
    logger.error(f"SQLite Connection failed - {e}")

Base = declarative_base()


class Path(Base):
    __tablename__ = 'paths'

    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True)

    def __repr__(self):
        return self.path


class UploadedFile(Base):
    __tablename__ = 'uploaded_files'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    dirpath=Column(String)

    def __repr__(self):
        return self.dirpath+'/'+self.filename


logger.info("Adding tables to database")
Base.metadata.create_all(engine)

logger.info("Initializing Chroma collection...")
embedding_function = OpenCLIPEmbeddingFunction()
dataloader = ImageLoader()

logger.info("Creating or getting collection")
try:
    collection = chroma_client.create_collection(
        name="image_collection",
        embedding_function=embedding_function,
        data_loader=dataloader,
        metadata={"hnsw:space": "cosine"}
    )
except UniqueConstraintError as e:
    collection = chroma_client.get_collection(
        name="image_collection",
        embedding_function=embedding_function,
        data_loader=dataloader,
    )
logger.info("Successfully created collection")