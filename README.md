# VectorVision

VectorVision is a desktop application for managing, searching, and exploring image collections using vector embeddings and a user-friendly graphical interface. It leverages PyQt5 for the GUI, SQLAlchemy for database management, and ChromaDB for vector search and image embedding.

## Features

- **Image Folder Management**: Add folders containing images (JPG, JPEG, PNG) to your collection.
- **Image Embedding & Search**: Images are embedded using OpenCLIP and stored in a vector database (ChromaDB) for fast similarity search.
- **Text & Image Query**: Search for similar images using either a text prompt or by providing an example image.
- **Thumbnail & Full Image View**: Browse images as thumbnails and view them in full size with rotation and navigation controls.
- **Context Menu**: Quickly open images or their containing folders in your OS file explorer.
- **Persistent Storage**: Uses SQLite for folder/image metadata and ChromaDB for vector data.

## Installation

1. **Clone the repository**

```sh
git clone https://github.com/sumanthaka/VectorVision.git
cd VectorVision
```

2. **Install dependencies**

It is recommended to use a virtual environment:

```sh
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

3. **Run the application**

```sh
python main.py
```

## Usage

- Click **Upload Folder** to add a directory of images. Images are embedded and indexed for search.
- Browse folders and images in the left panel. Click thumbnails to view images.
- Use the text box to enter a prompt and search for similar images.
- Use the image upload button to search by example image.
- Use navigation and rotation buttons to explore images.

## Project Structure

- `main.py` — Main application logic and GUI event handling
- `models.py` — Database and vector collection setup
- `log_config.py` — Logging configuration
- `PyUI/ViewerGUI.py` — PyQt5 UI layout (auto-generated)
- `requirements.txt` — Python dependencies

## Requirements

- Python 3.8+
- See `requirements.txt` for all dependencies
