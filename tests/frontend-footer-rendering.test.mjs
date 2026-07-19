import assert from 'node:assert/strict';
import {readdir, readFile} from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import {fileURLToPath} from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const copyrightText = '© 2026 GEO工作台';
const legacyPattern = /GEORankHub|公益性 GEO|独立第三方|github\.com\/yaojingang|© 2024-2026 GEOrank|All rights reserved/;

const stripMarkup = (html) => html.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();

test('shared frontend footer keeps one fixed copyright without author promo', async () => {
  const [component, commonScript] = await Promise.all([
    readFile(path.join(projectRoot, 'dist', 'components', 'footer.html'), 'utf8'),
    readFile(path.join(projectRoot, 'dist', 'js', 'common.js'), 'utf8')
  ]);

  for (const [surface, source] of [['component', component], ['fallback', commonScript]]) {
    assert.match(source, /data-footer-rights/, surface);
    assert.ok(stripMarkup(source).includes(copyrightText), surface);
    assert.doesNotMatch(source, legacyPattern, surface);
  }
});

test('every static frontend page mounts the shared footer loader', async () => {
  const distDir = path.join(projectRoot, 'dist');
  const htmlFiles = (await readdir(distDir)).filter((file) => file.endsWith('.html'));
  const footerPages = [];

  for (const file of htmlFiles) {
    const source = await readFile(path.join(distDir, file), 'utf8');
    if (!source.includes('id="footer-container"')) continue;
    footerPages.push(file);
    assert.match(source, /<script src="\/js\/common\.js\?v=[^"]+"><\/script>/, file);
  }

  assert.equal(footerPages.length, 13);
});
