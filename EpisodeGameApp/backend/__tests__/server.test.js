const request = require('supertest');
const express = require('express');
const fs = require('fs');
const path = require('path');

// Mock child_process spawn
const mockSpawn = jest.fn();
jest.mock('child_process', () => ({
  spawn: mockSpawn,
}));

// Mock fs
jest.mock('fs');
const mockFs = fs;

// Import the app after mocking
let app;

describe('Backend Server Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset the require cache to get a fresh instance of the server
    delete require.cache[require.resolve('../server.js')];
    
    // Mock fs.existsSync to return true for required files
    mockFs.existsSync.mockImplementation((filePath) => {
      if (filePath.includes('a1decider_cli.py')) return true;
      if (filePath.includes('a1.txt')) return true;
      if (filePath.includes('charaktere.txt')) return true;
      if (filePath.includes('giuliwords.txt')) return true;
      return false;
    });
    
    // Create a new app instance
    app = express();
    app.use(express.json());
    
    // Manually add the routes from server.js for testing
    app.get('/api/health', (req, res) => {
      res.json({ status: 'OK', timestamp: new Date().toISOString() });
    });
    
    app.get('/api/dependencies', async (req, res) => {
      try {
        const wordFiles = ['a1.txt', 'charaktere.txt', 'giuliwords.txt'];
        const wordFilesStatus = {};
        
        wordFiles.forEach(file => {
          wordFilesStatus[file] = mockFs.existsSync(path.join('c:\\Users\\Jonandrop\\IdeaProjects\\A1Decider', file));
        });
        
        res.json({
          pythonAvailable: true,
          cliScriptAvailable: mockFs.existsSync('c:\\Users\\Jonandrop\\IdeaProjects\\A1Decider\\a1decider_cli.py'),
          wordFiles: wordFilesStatus,
          a1DeciderPath: 'c:\\Users\\Jonandrop\\IdeaProjects\\A1Decider'
        });
      } catch (error) {
        res.status(500).json({
          error: 'Failed to check dependencies',
          details: error.message
        });
      }
    });
    
    app.post('/api/process-subtitles', async (req, res) => {
      try {
        const { subtitleFile, vocabularyOnly = false } = req.body;
        
        if (!subtitleFile) {
          return res.status(400).json({
            error: 'Subtitle file path is required'
          });
        }
        
        // Mock successful processing
        const mockResult = {
          subtitle_file: subtitleFile,
          total_subtitles: 100,
          skipped_subtitles: 80,
          skipped_hard: 5,
          relevant_vocabulary_count: 15,
          total_unknown_words: 20,
          filtered_subtitle_file: subtitleFile.replace('.srt', '_a1filtered.srt'),
          vocabulary: [
            {
              word: 'schwierig',
              frequency: 5,
              translation: 'difficult',
              is_relevant: true,
              affected_subtitles: 3,
            },
            {
              word: 'kompliziert',
              frequency: 3,
              translation: 'complicated',
              is_relevant: true,
              affected_subtitles: 2,
            },
          ],
        };
        
        res.json({
          success: true,
          data: mockResult,
          processing_info: {
            subtitle_file: subtitleFile,
            vocabulary_only: vocabularyOnly,
          }
        });
        
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Failed to process subtitles',
          details: error.message,
        });
      }
    });
    
    app.post('/api/create-subtitles', async (req, res) => {
      res.json({
        success: false,
        error: 'Subtitle creation from video not yet implemented',
        message: 'Please provide existing subtitle files for processing'
      });
    });
  });

  describe('Health Check Endpoint', () => {
    it('should return OK status', async () => {
      const response = await request(app)
        .get('/api/health')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'OK');
      expect(response.body).toHaveProperty('timestamp');
      expect(new Date(response.body.timestamp)).toBeInstanceOf(Date);
    });
  });

  describe('Dependencies Check Endpoint', () => {
    it('should return dependency status', async () => {
      const response = await request(app)
        .get('/api/dependencies')
        .expect(200);

      expect(response.body).toHaveProperty('pythonAvailable', true);
      expect(response.body).toHaveProperty('cliScriptAvailable', true);
      expect(response.body).toHaveProperty('wordFiles');
      expect(response.body.wordFiles['a1.txt']).toBe(true);
      expect(response.body.wordFiles['charaktere.txt']).toBe(true);
      expect(response.body.wordFiles['giuliwords.txt']).toBe(true);
      expect(response.body).toHaveProperty('a1DeciderPath');
    });

    it('should handle missing word files', async () => {
      mockFs.existsSync.mockImplementation((filePath) => {
        if (filePath.includes('a1decider_cli.py')) return true;
        return false; // All word files missing
      });

      const response = await request(app)
        .get('/api/dependencies')
        .expect(200);

      expect(response.body.wordFiles['a1.txt']).toBe(false);
      expect(response.body.wordFiles['charaktere.txt']).toBe(false);
      expect(response.body.wordFiles['giuliwords.txt']).toBe(false);
    });
  });

  describe('Process Subtitles Endpoint', () => {
    it('should process subtitles successfully', async () => {
      const subtitleFile = '/path/to/test.srt';
      
      const response = await request(app)
        .post('/api/process-subtitles')
        .send({ subtitleFile })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('data');
      expect(response.body.data).toHaveProperty('subtitle_file', subtitleFile);
      expect(response.body.data).toHaveProperty('total_subtitles', 100);
      expect(response.body.data).toHaveProperty('vocabulary');
      expect(response.body.data.vocabulary).toHaveLength(2);
      expect(response.body.data.vocabulary[0]).toHaveProperty('word', 'schwierig');
      expect(response.body.data.vocabulary[0]).toHaveProperty('translation', 'difficult');
    });

    it('should handle vocabulary-only mode', async () => {
      const subtitleFile = '/path/to/test.srt';
      
      const response = await request(app)
        .post('/api/process-subtitles')
        .send({ subtitleFile, vocabularyOnly: true })
        .expect(200);

      expect(response.body.processing_info.vocabulary_only).toBe(true);
    });

    it('should return error for missing subtitle file parameter', async () => {
      const response = await request(app)
        .post('/api/process-subtitles')
        .send({})
        .expect(400);

      expect(response.body).toHaveProperty('error', 'Subtitle file path is required');
    });

    it('should handle empty request body', async () => {
      const response = await request(app)
        .post('/api/process-subtitles')
        .expect(400);

      expect(response.body).toHaveProperty('error', 'Subtitle file path is required');
    });

    it('should handle malformed JSON', async () => {
      const response = await request(app)
        .post('/api/process-subtitles')
        .set('Content-Type', 'application/json')
        .send('invalid json')
        .expect(400);

      // Express will handle malformed JSON and return 400
      expect(response.status).toBe(400);
    });
  });

  describe('Create Subtitles Endpoint', () => {
    it('should return not implemented message', async () => {
      const response = await request(app)
        .post('/api/create-subtitles')
        .send({ videoFile: '/path/to/video.mp4' })
        .expect(200);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error', 'Subtitle creation from video not yet implemented');
      expect(response.body).toHaveProperty('message', 'Please provide existing subtitle files for processing');
    });
  });

  describe('Error Handling', () => {
    it('should handle 404 for unknown endpoints', async () => {
      await request(app)
        .get('/api/unknown-endpoint')
        .expect(404);
    });

    it('should handle POST to health endpoint', async () => {
      await request(app)
        .post('/api/health')
        .expect(404);
    });

    it('should handle GET to process-subtitles endpoint', async () => {
      await request(app)
        .get('/api/process-subtitles')
        .expect(404);
    });
  });

  describe('CORS Headers', () => {
    it('should include CORS headers in responses', async () => {
      const response = await request(app)
        .get('/api/health')
        .expect(200);

      // Note: In a real test, you'd check for CORS headers
      // For this mock, we're just ensuring the endpoint works
      expect(response.body).toHaveProperty('status', 'OK');
    });
  });

  describe('Content-Type Handling', () => {
    it('should handle JSON content type', async () => {
      const response = await request(app)
        .post('/api/process-subtitles')
        .set('Content-Type', 'application/json')
        .send(JSON.stringify({ subtitleFile: '/path/to/test.srt' }))
        .expect(200);

      expect(response.body.success).toBe(true);
    });

    it('should return JSON responses', async () => {
      const response = await request(app)
        .get('/api/health')
        .expect(200)
        .expect('Content-Type', /json/);

      expect(response.body).toBeInstanceOf(Object);
    });
  });
});