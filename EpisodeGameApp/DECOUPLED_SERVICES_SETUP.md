# Decoupled Services Setup Guide

This guide explains how to set up and run the decoupled Node.js backend and Python API services.

## Architecture Overview

The application now consists of two separate services:

1. **Node.js Backend** (`EpisodeGameApp/backend/`) - Handles HTTP requests and forwards subtitle processing to Python API
2. **Python API Server** (`A1Decider/python_api_server.py`) - Processes subtitles using the modular pipeline architecture

## Prerequisites

- Node.js (v14 or higher)
- Python 3.8+
- Required Python packages: `fastapi`, `uvicorn`, `python-multipart`
- Required Node.js packages: `express`, `axios`, `cors`, `dotenv`

## Setup Instructions

### 1. Install Python Dependencies

```bash
cd c:\Users\Jonandrop\IdeaProjects\A1Decider
pip install fastapi uvicorn python-multipart
```

### 2. Install Node.js Dependencies

```bash
cd c:\Users\Jonandrop\IdeaProjects\EpisodeGameApp\backend
npm install
```

### 3. Configure Environment Variables

Create a `.env` file in `EpisodeGameApp/backend/` based on `.env.example`:

```env
PORT=3001
PYTHON_API_URL=http://localhost:8000
A1_DECIDER_PATH=c:\Users\Jonandrop\IdeaProjects\A1Decider
```

## Running the Services

### Start Python API Server (Terminal 1)

```bash
cd c:\Users\Jonandrop\IdeaProjects\A1Decider
uvicorn python_api_server:app --host 0.0.0.0 --port 8000 --reload
```

The Python API will be available at: `http://localhost:8000`

### Start Node.js Backend (Terminal 2)

```bash
cd c:\Users\Jonandrop\IdeaProjects\EpisodeGameApp\backend
npm start
```

The Node.js backend will be available at: `http://localhost:3001`

## API Endpoints

### Node.js Backend Endpoints

- `GET /api/health` - Health check
- `GET /api/dependencies` - Check Python API connectivity
- `POST /api/process-subtitles` - Process existing subtitle files
- `POST /api/create-subtitles` - Create subtitles from video files
- `GET /api/subtitles` - List available subtitle files

### Python API Endpoints

- `GET /health` - Health check
- `GET /dependencies` - Check dependencies
- `POST /process-subtitles` - Process subtitle files
- `POST /process-video` - Process video files
- `POST /upload-and-process` - Upload and process files
- `GET /download/{filename}` - Download processed files
- `GET /pipeline-configs` - Get available pipeline configurations

## Testing the Integration

1. Start both services as described above
2. Visit `http://localhost:3001/api/health` to check Node.js backend
3. Visit `http://localhost:8000/health` to check Python API
4. Visit `http://localhost:3001/api/dependencies` to verify integration

## Troubleshooting

### Python API Not Accessible

- Ensure Python API server is running on port 8000
- Check firewall settings
- Verify `PYTHON_API_URL` in `.env` file

### Import Errors in Python API

- Ensure all required packages are installed
- Check that `python_api_server.py` is in the A1Decider directory
- Verify Python path and working directory

### Node.js Backend Issues

- Run `npm install` to ensure all dependencies are installed
- Check that `.env` file exists and contains correct values
- Verify axios dependency is installed

## Benefits of Decoupled Architecture

- **Independent Scaling**: Each service can be scaled independently
- **Technology Flexibility**: Services can use different technologies
- **Fault Isolation**: Issues in one service don't affect the other
- **Development Independence**: Teams can work on services separately
- **Deployment Flexibility**: Services can be deployed to different environments

## Next Steps

- Configure production environment variables
- Set up Docker containers for each service
- Implement service discovery and load balancing
- Add monitoring and logging
- Set up CI/CD pipelines for independent deployments