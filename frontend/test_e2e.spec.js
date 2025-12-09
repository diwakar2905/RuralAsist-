const fs = require('fs');
const path = require('path');

describe('End-to-end tests', () => {
  let loginJsContent;
  let swJsContent;

  beforeAll(() => {
    // Read the content of the files before the tests
    loginJsContent = fs.readFileSync(path.resolve(__dirname, 'assets/js/login.js'), 'utf8');
    swJsContent = fs.readFileSync(path.resolve(__dirname, 'sw.js'), 'utf8');
  });

  // Test for login.js
  test('login.js should use AppConfig.API_BASE_URL', () => {
    // Check if API_BASE_URL is replaced with AppConfig.API_BASE_URL
    expect(loginJsContent).not.toContain('const res = await fetch(`${API_BASE_URL}/auth/send-email-otp`');
    expect(loginJsContent).toContain('const res = await fetch(`${AppConfig.API_BASE_URL}/auth/send-email-otp`');
  });

  // Test for sw.js
  test('sw.js should not contain missing files in urlsToCache', () => {
    // Check if the missing files are removed from urlsToCache
    expect(swJsContent).not.toContain('/assets/js/chat_float.js');
    expect(swJsContent).not.toContain('/assets/images/icon-192.png');
    expect(swJsContent).not.toContain('/assets/images/icon-512.png');
  });
});