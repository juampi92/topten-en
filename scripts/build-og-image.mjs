#!/usr/bin/env node
import { existsSync, statSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { platform, homedir } from 'node:os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = resolve(__dirname, '..');
const svgPath = resolve(projectRoot, 'public', 'og-image.svg');
const pngPath = resolve(projectRoot, 'public', 'og-image.png');

function findChrome() {
  if (platform() === 'darwin') {
    const candidates = [
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      `${homedir()}/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`,
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
      `${homedir()}/Applications/Chromium.app/Contents/MacOS/Chromium`,
    ];
    for (const p of candidates) {
      if (existsSync(p)) return p;
    }
  }
  for (const bin of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']) {
    const found = which(bin);
    if (found) return found;
  }
  return null;
}

function which(bin) {
  const path = process.env.PATH || '';
  const sep = platform() === 'win32' ? ';' : ':';
  for (const dir of path.split(sep)) {
    const candidate = resolve(dir, bin);
    if (existsSync(candidate)) return candidate;
  }
  return null;
}

function runChrome(chrome, args) {
  return new Promise((resolveProm, rejectProm) => {
    const child = spawn(chrome, args, { stdio: ['ignore', 'inherit', 'inherit'] });
    child.on('error', rejectProm);
    child.on('close', (code) => {
      if (code === 0) resolveProm();
      else rejectProm(new Error(`Chrome exited with code ${code}`));
    });
  });
}

async function main() {
  if (!existsSync(svgPath)) {
    console.error(`Missing SVG: ${svgPath}`);
    process.exit(1);
  }

  const chrome = findChrome();
  if (!chrome) {
    console.error(
      'Could not find Google Chrome or Chromium on this system.\n' +
        'Install Google Chrome (https://www.google.com/chrome/) and re-run, or\n' +
        'temporarily install puppeteer as a dev dependency and update this script.'
    );
    process.exit(1);
  }

  console.log(`Using Chrome: ${chrome}`);
  console.log(`Rendering ${svgPath} -> ${pngPath}`);

  const fileUrl = `file://${svgPath}`;
  const args = [
    '--headless=new',
    '--hide-scrollbars',
    '--disable-gpu',
    '--force-device-scale-factor=1',
    '--no-sandbox',
    `--window-size=1200,630`,
    `--virtual-time-budget=2000`,
    `--screenshot=${pngPath}`,
    fileUrl,
  ];

  await runChrome(chrome, args);

  if (!existsSync(pngPath)) {
    console.error(`Chrome did not write ${pngPath}`);
    process.exit(1);
  }
  const { size } = statSync(pngPath);
  console.log(`Wrote ${pngPath} (${size} bytes)`);
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
