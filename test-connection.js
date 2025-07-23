// Simple connection test script
async function testConnection() {
  const baseUrl = 'http://localhost:5001';
  
  console.log('Testing connection to video converter backend...');
  
  try {
    const response = await fetch(`${baseUrl}/api/health`);
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Backend is running successfully!');
      console.log('Response:', data);
    } else {
      console.log('❌ Backend responded with error:', response.status, response.statusText);
    }
  } catch (error) {
    console.log('❌ Cannot connect to backend:', error.message);
    console.log('');
    console.log('Troubleshooting steps:');
    console.log('1. Make sure the backend is running on port 5001');
    console.log('2. Run: ./start-backend.sh');
    console.log('3. Check if FFmpeg is installed: ffmpeg -version');
    console.log('4. Check Python dependencies are installed');
  }
}

testConnection();