// Debug port detection
import axios from 'axios';

async function testPortDetection() {
  const url = 'http://localhost:3000';

  console.log(`Testing ${url}...`);

  try {
    const response = await axios.get(url, {
      timeout: 5000,
      validateStatus: () => true,
      headers: {
        'User-Agent': 'E2E-Test-Client/1.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
      }
    });

    console.log(`Status: ${response.status}`);
    console.log(`Content-Type: ${response.headers['content-type']}`);
    console.log(`Has HTML: ${typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')}`);
    console.log(`Has root: ${typeof response.data === 'string' && response.data.includes('id="root"')}`);

    if (response.status === 200 &&
        typeof response.data === 'string' &&
        response.data.includes('<!DOCTYPE html>') &&
        response.data.includes('id="root"')) {
      console.log('✅ Frontend should be detected!');
    } else {
      console.log('❌ Frontend detection failed');
    }

  } catch (error) {
    console.error('❌ Request failed:', error.message);
  }
}

testPortDetection();
