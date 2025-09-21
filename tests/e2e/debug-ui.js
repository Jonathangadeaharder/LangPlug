import puppeteer from 'puppeteer';

async function debugPages() {
  const frontendUrl = 'http://localhost:3000'; // Use detected URL from earlier
  console.log(`🔍 Debugging pages on ${frontendUrl}`);
  
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    // Check login page
    console.log('\n📋 Checking /login page...');
    await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle0' });
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const loginContent = await page.content();
    console.log('Login page title:', await page.title());
    console.log('Login page has forms:', loginContent.includes('<form'));
    console.log('Login page has inputs:', loginContent.includes('<input'));
    console.log('Login page has buttons:', loginContent.includes('<button'));
    
    // Get all button text
    const buttons = await page.$$eval('button', btns => btns.map(btn => btn.textContent?.trim()));
    console.log('Button texts:', buttons);
    
    // Get all link text
    const links = await page.$$eval('a', links => links.map(link => link.textContent?.trim()));
    console.log('Link texts:', links);
    
    // Check home page
    console.log('\n🏠 Checking / (home) page...');
    await page.goto(`${frontendUrl}/`, { waitUntil: 'networkidle0' });
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    console.log('Home page title:', await page.title());
    const homeButtons = await page.$$eval('button', btns => btns.map(btn => btn.textContent?.trim()));
    const homeLinks = await page.$$eval('a', links => links.map(link => link.textContent?.trim()));
    console.log('Home buttons:', homeButtons);
    console.log('Home links:', homeLinks);
    
    // Take screenshots for debugging
    await page.goto(`${frontendUrl}/login`);
    await new Promise(resolve => setTimeout(resolve, 2000));
    
  } catch (error) {
    console.error('Debug error:', error);
  } finally {
    await browser.close();
  }
}

debugPages().catch(console.error);