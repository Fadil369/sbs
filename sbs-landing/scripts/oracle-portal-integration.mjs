/**
 * Oracle Portal Integration Script
 * Automates login to Oracle portal at https://128.1.1.185/prod/faces/Home
 * Uses Playwright for browser automation
 */

import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import { buildNormalizedExtraction, clean } from './lib/portal-extraction.mjs';
import { resolvePlaywrightLaunchOptions } from './lib/playwright-launch.mjs';
import { publishNormalizedExtraction } from './lib/publish-extraction.mjs';

const USERNAME_SELECTORS = [
  'input[type="text"]',
  'input[name*="user" i]',
  'input[id*="user" i]',
  'input[name*="username" i]',
  'input[id*="username" i]'
];

const PASSWORD_SELECTORS = [
  'input[type="password"]',
  'input[name*="password" i]',
  'input[id*="password" i]'
];

const OTP_SELECTORS = [
  'input[name*="otp" i]',
  'input[id*="otp" i]',
  'input[name*="code" i]',
  'input[id*="code" i]'
];

const SUBMIT_SELECTORS = [
  'button[type="submit"]',
  'input[type="submit"]',
  'button:has-text("Login")',
  'button:has-text("Sign In")',
  'button:has-text("Continue")'
];

async function safeScreenshot(page, filePath) {
  try {
    await page.screenshot({ path: filePath, fullPage: true, timeout: 60000 });
    return true;
  } catch {
    try {
      await page.screenshot({ path: filePath, fullPage: false, timeout: 15000 });
      return true;
    } catch {
      return false;
    }
  }
}

async function findFirstVisible(page, selectors) {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    try {
      if ((await locator.count()) > 0 && (await locator.isVisible())) {
        return locator;
      }
    } catch {
      // ignore unsupported selectors and race conditions
    }
  }
  return null;
}

async function maybeFill(locator, value) {
  if (!locator || !value) return false;
  await locator.click({ timeout: 2000 }).catch(() => {});
  await locator.fill(value, { timeout: 5000 });
  return true;
}

async function maybeClick(page, selectors) {
  const locator = await findFirstVisible(page, selectors);
  if (!locator) return false;
  await locator.click({ timeout: 5000 });
  return true;
}

function inferOracleLoginSuccess(currentUrl, title, bodyText) {
  const source = `${currentUrl} ${title} ${bodyText}`.toLowerCase();
  const loginSignals = /(login|sign in|username|password|otp|verification code)/.test(source);
  const appSignals = /(logout|sign out|welcome|claims|authorization|dashboard|search|home)/.test(source);
  return appSignals || !loginSignals;
}

/**
 * Oracle Portal Scanner
 * @param {Object} options - Configuration options
 * @param {string} options.url - Oracle portal URL (default: from env)
 * @param {string} options.username - Login username (default: from env)
 * @param {string} options.password - Login password (default: from env)
 * @param {string} options.otp - Optional OTP code (default: from env)
 * @param {boolean} options.headless - Run in headless mode (default: true)
 * @param {string} options.artifactsDir - Directory for screenshots (default: artifacts/oracle-portal)
 * @returns {Promise<Object>} - Result with success, timestamp, title, screenshot
 */
export async function scanOraclePortal(options = {}) {
  const config = {
    url: options.url || process.env.ORACLE_PORTAL_URL || 'https://128.1.1.185/prod/faces/Home',
    username: options.username || process.env.ORACLE_USERNAME,
    password: options.password || process.env.ORACLE_PASSWORD,
    otp: options.otp || process.env.ORACLE_OTP,
    headless: options.headless !== undefined ? options.headless : 
              (process.env.ORACLE_HEADLESS !== 'false'),
    artifactsDir: path.resolve(process.cwd(), options.artifactsDir || process.env.ORACLE_ARTIFACTS_DIR || 'artifacts/oracle-portal')
  };

  // Validation
  if (!config.username || !config.password) {
    throw new Error('ORACLE_USERNAME and ORACLE_PASSWORD are required');
  }

  console.log('🚀 Oracle Portal Scanner starting...');
  console.log(`   URL: ${config.url}`);
  console.log(`   User: ${config.username}`);
  console.log(`   Headless: ${config.headless}`);

  let browser;
  let page;
  const startedAt = new Date().toISOString();
  const result = {
    success: false,
    startedAt,
    finishedAt: null,
    portalUrl: config.url,
    currentUrl: config.url,
    title: null,
    loginAttempted: false,
    loginLikelySuccessful: false,
    artifacts: {},
    setupHints: null,
    notes: []
  };

  try {
    // Ensure artifacts directory exists
    await fs.mkdir(config.artifactsDir, { recursive: true });

    // Launch browser
    const launchConfig = await resolvePlaywrightLaunchOptions({
      headless: config.headless,
      args: ['--ignore-certificate-errors'] // For self-signed SSL
    });
    browser = await chromium.launch(launchConfig.launchOptions);
    result.browserExecutableFallbackUsed = launchConfig.usedFallbackExecutable;
    result.browserExecutablePath = launchConfig.fallbackExecutablePath || '';

    const context = await browser.newContext({
      ignoreHTTPSErrors: true, // Accept self-signed certificates
      viewport: { width: 1920, height: 1080 }
    });

    page = await context.newPage();

    // Navigate to portal
    console.log('📡 Navigating to Oracle portal...');
    await page.goto(config.url, { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });

    const beforeShot = path.join(config.artifactsDir, '01-landing.png');
    if (await safeScreenshot(page, beforeShot)) {
      result.artifacts.beforeScreenshot = beforeShot;
    }

    // Wait for login form
    console.log('🔍 Waiting for login form...');
    await page.waitForSelector('input[type="text"], input[name*="user"], input[id*="user"]', {
      timeout: 10000
    });

    // Fill username
    console.log('👤 Entering username...');
    const usernameField = await findFirstVisible(page, USERNAME_SELECTORS);
    await maybeFill(usernameField, config.username);

    // Fill password
    console.log('🔐 Entering password...');
    const passwordField = await findFirstVisible(page, PASSWORD_SELECTORS);
    await maybeFill(passwordField, config.password);
    result.loginAttempted = true;

    // Handle OTP if provided
    if (config.otp && config.otp !== 'false') {
      console.log('🔢 Entering OTP...');
      const otpField = await findFirstVisible(page, OTP_SELECTORS);
      if (otpField) {
        await maybeFill(otpField, config.otp);
        result.notes.push('OTP value submitted from ORACLE_OTP.');
      }
    }

    // Click login button
    console.log('🔘 Clicking login button...');
    const loginClicked = await maybeClick(page, SUBMIT_SELECTORS);
    if (!loginClicked) {
      result.notes.push('Login button was not auto-detected.');
    }

    // Wait for navigation after login
    console.log('⏳ Waiting for login to complete...');
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});

    // Check if login was successful (adjust selectors based on actual portal)
    const title = await page.title();
    const currentUrl = page.url();
    const bodyText = await page.locator('body').innerText().catch(() => '');
    const content = await page.content();
    console.log(`✅ Page loaded: ${title}`);

    result.currentUrl = currentUrl;
    result.title = title;
    result.loginLikelySuccessful = inferOracleLoginSuccess(currentUrl, title, bodyText);

    const afterShot = path.join(config.artifactsDir, '02-after-login-attempt.png');
    if (await safeScreenshot(page, afterShot)) {
      result.artifacts.afterScreenshot = afterShot;
    }

    const links = await page.$$eval('a[href]', (els) =>
      els.map((el) => ({
        text: (el.textContent || '').trim(),
        href: String(el.getAttribute('href') || '').trim()
      }))
    ).catch(() => []);

    const formHints = await page.$$eval('input,button,label', (els) =>
      els.slice(0, 200).map((el) => ({
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute('type') || '',
        name: el.getAttribute('name') || '',
        id: el.getAttribute('id') || '',
        placeholder: el.getAttribute('placeholder') || '',
        text: (el.textContent || '').trim().slice(0, 120)
      }))
    ).catch(() => []);

    const tables = await page.$$eval('table', (els) =>
      els.slice(0, 10).map((table) => {
        const rows = Array.from(table.querySelectorAll('tr')).map((row) =>
          Array.from(row.querySelectorAll('th,td')).map((cell) => (cell.textContent || '').replace(/\s+/g, ' ').trim()).filter(Boolean)
        ).filter((row) => row.length > 0);

        const headers = rows.find((row) => row.length > 0) || [];
        return {
          headers,
          rows: rows.slice(headers.length > 0 ? 1 : 0, 11),
          rowCount: rows.length
        };
      })
    ).catch(() => []);

    const normalizedExtraction = buildNormalizedExtraction({
      source: 'oracle',
      portalUrl: config.url,
      currentUrl,
      title,
      capturedAt: new Date().toISOString(),
      auth: {
        attempted: result.loginAttempted,
        mode: 'password',
        likelySuccessful: result.loginLikelySuccessful
      },
      bodyText,
      html: content,
      links,
      formHints,
      tables,
      notes: result.notes
    });

    result.setupHints = normalizedExtraction.endpoints;

    const linksPath = path.join(config.artifactsDir, 'links.json');
    await fs.writeFile(linksPath, JSON.stringify(links, null, 2), 'utf8');
    result.artifacts.links = linksPath;

    const formHintsPath = path.join(config.artifactsDir, 'form-hints.json');
    await fs.writeFile(formHintsPath, JSON.stringify(formHints, null, 2), 'utf8');
    result.artifacts.formHints = formHintsPath;

    const tablesPath = path.join(config.artifactsDir, 'table-data.json');
    await fs.writeFile(tablesPath, JSON.stringify(tables, null, 2), 'utf8');
    result.artifacts.tables = tablesPath;

    const normalizedPath = path.join(config.artifactsDir, 'normalized-extraction.json');
    await fs.writeFile(normalizedPath, JSON.stringify(normalizedExtraction, null, 2), 'utf8');
    result.artifacts.normalizedExtraction = normalizedPath;

    const publishReport = await publishNormalizedExtraction(normalizedExtraction);
    const publishPath = path.join(config.artifactsDir, 'publish-report.json');
    await fs.writeFile(publishPath, JSON.stringify(publishReport, null, 2), 'utf8');
    result.artifacts.publishReport = publishPath;
    if (publishReport.notes?.length) {
      result.notes.push(...publishReport.notes);
    }
    if (publishReport.results?.length) {
      const failedTargets = publishReport.results.filter((item) => !item.ok).map((item) => `${item.target} (${item.status})`);
      if (failedTargets.length > 0) {
        result.notes.push(`Artifact publish failed for: ${failedTargets.join(', ')}`);
      }
    }

    result.success = true;
    result.finishedAt = new Date().toISOString();
    const summaryPath = path.join(config.artifactsDir, 'summary.json');
    await fs.writeFile(summaryPath, JSON.stringify(result, null, 2), 'utf8');
    result.artifacts.summary = summaryPath;

    return {
      success: true,
      timestamp: result.finishedAt,
      title,
      screenshot: result.artifacts.afterScreenshot || result.artifacts.beforeScreenshot || '',
      url: config.url,
      currentUrl,
      loginLikelySuccessful: result.loginLikelySuccessful,
      normalizedExtraction: normalizedPath,
      summary: summaryPath
    };

  } catch (error) {
    console.error('❌ Oracle portal scan failed:', error.message);
    result.finishedAt = new Date().toISOString();
    result.notes.push(clean(error.message));
    const summaryPath = path.join(config.artifactsDir, 'summary.json');
    await fs.writeFile(summaryPath, JSON.stringify(result, null, 2), 'utf8');
    throw new Error(`Oracle portal scan failed: ${error.message}`);
  } finally {
    // Cleanup
    if (browser) {
      await browser.close();
      console.log('🔒 Browser closed');
    }
  }
}

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
  scanOraclePortal()
    .then(result => {
      console.log('\n✅ Success!');
      console.log(JSON.stringify(result, null, 2));
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ Error:', error.message);
      process.exit(1);
    });
}
