import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {validateFeed} from '../src/feed.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sourceSite = path.resolve(root, '..');
const dist = path.join(root, 'dist');
const arg = process.argv.indexOf('--longcat-repo');
const longcat = arg >= 0 ? path.resolve(process.argv[arg + 1]) : null;
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const config = read(path.join(root, 'config.json'));
const snapshotFile = path.join(root, 'feed/v1/leaderboard.json');
fs.mkdirSync(path.dirname(snapshotFile), {recursive:true});
if (!fs.existsSync(snapshotFile) || process.argv.includes('--refresh-paper-snapshot')) {
  const source = read(path.join(sourceSite, 'dist/leaderboard.json'));
  const snapshot = validateFeed({...source, schema_version:1, revision:`paper-${source.snapshot_date}-main9-v1`});
  fs.writeFileSync(snapshotFile, JSON.stringify(snapshot, null, 2) + '\n');
}
const snapshot = validateFeed(read(snapshotFile));
for (const dir of ['assets','data','licenses']) fs.mkdirSync(path.join(dist, dir), {recursive:true});
for (const file of ['app.mjs','content.mjs','feed.mjs','blog.css']) fs.copyFileSync(path.join(root,'src',file), path.join(dist,'assets',file));
fs.copyFileSync(path.join(root,'src/index.html'),path.join(dist,'index.html'));
const js = value => JSON.stringify(value).replaceAll('<', '\\u003c').replaceAll('\u2028', '\\u2028').replaceAll('\u2029', '\\u2029');
fs.writeFileSync(path.join(dist,'assets/config.js'), 'window.BLOG_CONFIG = ' + js(config) + ';\n');
fs.writeFileSync(path.join(dist,'assets/snapshot.js'), 'window.BUNDLED_LEADERBOARD = ' + js(snapshot) + ';\n');
fs.writeFileSync(path.join(dist,'data/leaderboard.snapshot.json'), JSON.stringify(snapshot,null,2)+'\n');
const authors = read(path.join(sourceSite,'site_metadata.json'));
fs.writeFileSync(path.join(dist,'assets/authors.js'), 'window.BLOG_AUTHORS = ' + js({authors:authors.authors,affiliations:authors.affiliations}) + ';\n');
fs.copyFileSync(path.join(sourceSite,'dist/assets/framework.png'),path.join(dist,'assets/framework.png'));
if (longcat) {
  for (const f of ['longcat_logo.png','harness_overview.png']) fs.copyFileSync(path.join(longcat,'assets',f),path.join(root,'vendor',f));
  fs.copyFileSync(path.join(longcat,'LICENSE'),path.join(root,'vendor/LONGCAT_MIT_LICENSE.txt'));
}
for (const f of ['longcat_logo.png','harness_overview.png']) fs.copyFileSync(path.join(root,'vendor',f),path.join(dist,'assets',f));
fs.copyFileSync(path.join(root,'vendor/LONGCAT_MIT_LICENSE.txt'),path.join(dist,'licenses/LONGCAT_MIT_LICENSE.txt'));
fs.copyFileSync(path.join(root,'THIRD_PARTY_NOTICES.md'),path.join(dist,'licenses/THIRD_PARTY_NOTICES.md'));
const hashes = {};
function walk(dir) { for (const item of fs.readdirSync(dir,{withFileTypes:true})) { const p=path.join(dir,item.name); if(item.isDirectory()) walk(p); else hashes[path.relative(dist,p)] = createHash('sha256').update(fs.readFileSync(p)).digest('hex'); } }
walk(dist);
fs.writeFileSync(path.join(root,'BUILD_MANIFEST.json'),JSON.stringify({schema:1,files:hashes,snapshot_revision:snapshot.revision,remote_configured:!!config.feedUrl},null,2)+'\n');
console.log(JSON.stringify({dist,files:Object.keys(hashes).length,revision:snapshot.revision,systems:snapshot.systems,queries:snapshot.queries,remote_configured:!!config.feedUrl}));
