import fs from 'node:fs/promises';
import path from 'node:path';

async function pathExists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function findChromiumExecutableIn(baseDir) {
  try {
    const entries = await fs.readdir(baseDir, { withFileTypes: true });
    const chromiumDirs = entries
      .filter((entry) => entry.isDirectory() && entry.name.startsWith('chromium-'))
      .map((entry) => entry.name)
      .sort((a, b) => b.localeCompare(a));

    for (const dirName of chromiumDirs) {
      const dirPath = path.join(baseDir, dirName);
      const candidates = [
        path.join(dirPath, 'chrome-win', 'chrome.exe'),
        path.join(dirPath, 'chrome-win64', 'chrome.exe'),
        path.join(dirPath, 'chrome-linux', 'chrome'),
        path.join(dirPath, 'chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium')
      ];

      for (const candidate of candidates) {
        if (await pathExists(candidate)) {
          return candidate;
        }
      }
    }
  } catch {
    return '';
  }
  return '';
}

export async function resolvePlaywrightLaunchOptions(initialOptions = {}) {
  const options = { ...initialOptions };
  const msPlaywrightDir = process.env.LOCALAPPDATA
    ? path.join(process.env.LOCALAPPDATA, 'ms-playwright')
    : '';

  if (!msPlaywrightDir || !(await pathExists(msPlaywrightDir))) {
    return { launchOptions: options, usedFallbackExecutable: false, fallbackExecutablePath: '' };
  }

  const fallbackExecutable = await findChromiumExecutableIn(msPlaywrightDir);
  if (!fallbackExecutable) {
    return { launchOptions: options, usedFallbackExecutable: false, fallbackExecutablePath: '' };
  }

  return {
    launchOptions: {
      ...options,
      executablePath: fallbackExecutable
    },
    usedFallbackExecutable: true,
    fallbackExecutablePath: fallbackExecutable
  };
}
