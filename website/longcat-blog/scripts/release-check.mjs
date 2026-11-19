import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {fetchFeed} from '../src/feed.mjs';
const config = JSON.parse(fs.readFileSync(new URL('../config.json',import.meta.url),'utf8'));
const missing = [];
for(const key of ['benchmarkCode','benchmarkPaper','benchmarkData']) if(!config.links[key]) missing.push(key);
if(!config.feedUrl) missing.push('public leaderboard feed URL');
if(!config.release.companyApprovalConfirmed) missing.push('company approval');
if(config.feedUrl) { try { await fetchFeed(config.feedUrl,{allowedOrigins:config.allowedFeedOrigins}); } catch(error) { missing.push('live feed check: '+error.message); } }
if(missing.length) { console.error('Not ready for public blog deployment: '+missing.join('; ')); process.exitCode=1; }
else console.log('Required release links configured and public feed validated. Verify destination permissions, final licenses, arXiv submission, and browser CORS/CSP before deployment.');
