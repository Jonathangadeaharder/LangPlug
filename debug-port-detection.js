const axios = require('axios');

async function testPortDetection() {
  console.log('Testing port detection...');
  
  const url = 'http://localhost:3000';
  
  try {
    console.log(`Testing ${url}...`);
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
    console.log(`Response length: ${response.data.length}`);
    
    const hasDoctype = response.data.includes('<!DOCTYPE html>');
    const hasRoot = response.data.includes('id="root"');
    
    console.log(`Has DOCTYPE: ${hasDoctype}`);
    console.log(`Has root ID: ${hasRoot}`);
    
    if (response.status === 200 && 
        typeof response.data === 'string' &&
        hasDoctype &&
        hasRoot) {
      console.log('✅ Frontend detected successfully!');
    } else {
      console.log('❌ Frontend detection failed');
      console.log('First 500 chars:', response.data.substring(0, 500));
    }
    
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
}

testPortDetection();