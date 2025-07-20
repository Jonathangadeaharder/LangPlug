// Load environment variables from .env file
require('dotenv').config();

const express = require('express');
const axios = require('axios');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Python API configuration
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

// Legacy configuration (for backward compatibility)
const A1_DECIDER_PATH = process.env.A1_DECIDER_PATH || 'c:\\Users\\Jonandrop\\IdeaProjects\\A1Decider';
const CLI_SCRIPT_PATH = path.join(A1_DECIDER_PATH, 'a1decider_cli.py');

// Validate Python API connection on startup
async function validatePythonAPI() {
  try {
    const response = await axios.get(`${PYTHON_API_URL}/health`, { timeout: 5000 });
    console.log('✓ Python API server is accessible');
    return true;
  } catch (error) {
    console.warn(`⚠ Warning: Python API server not accessible at ${PYTHON_API_URL}`);
    console.warn('Make sure the Python API server is running or update PYTHON_API_URL environment variable.');
    return false;
  }
}

// Validate on startup
validatePythonAPI();

/**
 * Make HTTP request to Python API
 */
async function callPythonAPI(endpoint, method = 'GET', data = null) {
  try {
    const config = {
      method,
      url: `${PYTHON_API_URL}${endpoint}`,
      timeout: 30000, // 30 second timeout
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
    if (data) {
      config.data = data;
    }
    
    console.log(`Making ${method} request to: ${config.url}`);
    const response = await axios(config);
    
    return {
      success: true,
      data: response.data,
      status: response.status
    };
  } catch (error) {
    console.error('Python API request failed:', error.message);
    
    if (error.response) {
      // Server responded with error status
      return {
        success: false,
        error: error.response.data?.detail || error.response.data?.error || 'API request failed',
        status: error.response.status,
        data: error.response.data
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        success: false,
        error: 'Python API server is not responding. Make sure it is running.',
        status: 503
      };
    } else {
      // Something else happened
      return {
        success: false,
        error: error.message,
        status: 500
      };
    }
  }
}

/**
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

/**
 * Check if Python API and dependencies are available
 */
app.get('/api/dependencies', async (req, res) => {
  try {
    // Check if Python API is available
    const apiHealthCheck = await callPythonAPI('/health');
    
    // Check if dependencies endpoint is available
    const dependenciesCheck = await callPythonAPI('/dependencies');
    
    if (apiHealthCheck.success && dependenciesCheck.success) {
      res.json({
        pythonApiAvailable: true,
        pythonApiUrl: PYTHON_API_URL,
        dependencies: dependenciesCheck.data,
        status: 'All systems operational'
      });
    } else {
      res.status(503).json({
        pythonApiAvailable: false,
        pythonApiUrl: PYTHON_API_URL,
        error: 'Python API server is not accessible',
        details: apiHealthCheck.error || dependenciesCheck.error
      });
    }
  } catch (error) {
    res.status(500).json({
      error: 'Failed to check dependencies',
      details: error.message,
      pythonApiUrl: PYTHON_API_URL
    });
  }
});

/**
 * Process subtitles using Python API
 */
app.post('/api/process-subtitles', async (req, res) => {
  try {
    const { subtitleFile, vocabularyOnly = false, pipelineConfig = 'default' } = req.body;
    
    if (!subtitleFile) {
      return res.status(400).json({
        error: 'Subtitle file path is required'
      });
    }
    
    // Check if subtitle file exists
    if (!fs.existsSync(subtitleFile)) {
      return res.status(404).json({
        error: 'Subtitle file not found',
        path: subtitleFile
      });
    }
    
    // Prepare request data for Python API
    const requestData = {
      subtitle_file: subtitleFile,
      vocabulary_only: vocabularyOnly,
      pipeline_config: pipelineConfig
    };
    
    console.log('Processing subtitles with Python API...');
    const result = await callPythonAPI('/process-subtitles', 'POST', requestData);
    
    if (result.success) {
      res.json({
        success: true,
        data: result.data,
        processing_info: {
          subtitle_file: subtitleFile,
          vocabulary_only: vocabularyOnly,
          pipeline_config: pipelineConfig
        }
      });
    } else {
      res.status(result.status || 500).json({
        success: false,
        error: result.error,
        details: result.data
      });
    }
    
  } catch (error) {
    console.error('Error processing subtitles:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to process subtitles',
      details: error.message
    });
  }
});

/**
 * Create subtitles from video using Python API
 */
app.post('/api/create-subtitles', async (req, res) => {
  try {
    const { videoFile, language = 'de', pipelineConfig = 'default' } = req.body;
    
    if (!videoFile) {
      return res.status(400).json({
        error: 'Video file path is required'
      });
    }
    
    // Check if video file exists
    if (!fs.existsSync(videoFile)) {
      return res.status(404).json({
        error: 'Video file not found',
        path: videoFile
      });
    }
    
    // Prepare request data for Python API
    const requestData = {
      video_file: videoFile,
      language: language,
      pipeline_config: pipelineConfig
    };
    
    console.log('Creating subtitles from video using Python API...');
    const result = await callPythonAPI('/process-video', 'POST', requestData);
    
    if (result.success) {
      res.json({
        success: true,
        data: result.data,
        processing_info: {
          video_file: videoFile,
          language: language,
          pipeline_config: pipelineConfig
        }
      });
    } else {
      res.status(result.status || 500).json({
        success: false,
        error: result.error,
        details: result.data
      });
    }
    
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to create subtitles',
      details: error.message
    });
  }
});

/**
 * Get available subtitle files in a directory
 */
app.get('/api/subtitles', (req, res) => {
  try {
    // Return a list of available subtitle files from the A1Decider directory
    const subtitleDir = A1_DECIDER_PATH;
    
    if (!fs.existsSync(subtitleDir)) {
      return res.json({
        directory: subtitleDir,
        files: [],
        message: 'A1Decider directory not found'
      });
    }
    
    const files = fs.readdirSync(subtitleDir)
      .filter(file => file.endsWith('.srt') || file.endsWith('.vtt'))
      .map(file => ({
        name: file,
        path: path.join(subtitleDir, file),
        size: fs.statSync(path.join(subtitleDir, file)).size,
        modified: fs.statSync(path.join(subtitleDir, file)).mtime
      }));
    
    res.json({
      directory: subtitleDir,
      files: files,
      count: files.length
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to list subtitle files',
      details: error.message
    });
  }
});

/**
 * Get available subtitle files in a specific directory
 */
app.get('/api/subtitle-files', (req, res) => {
  try {
    const { directory } = req.query;
    
    if (!directory || !fs.existsSync(directory)) {
      return res.status(400).json({
        error: 'Valid directory path is required'
      });
    }
    
    const files = fs.readdirSync(directory)
      .filter(file => file.endsWith('.srt') || file.endsWith('.vtt'))
      .map(file => ({
        name: file,
        path: path.join(directory, file),
        size: fs.statSync(path.join(directory, file)).size,
        modified: fs.statSync(path.join(directory, file)).mtime
      }));
    
    res.json({
      directory: directory,
      files: files
    });
    
  } catch (error) {
    res.status(500).json({
      error: 'Failed to list subtitle files',
      details: error.message
    });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({
    error: 'Internal server error',
    details: error.message
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`A1Decider Backend Server running on port ${PORT}`);
  console.log(`A1Decider path: ${A1_DECIDER_PATH}`);
  console.log(`CLI script path: ${CLI_SCRIPT_PATH}`);
});

module.exports = app;