import fs from 'node:fs';
import {validateFeed} from '../src/feed.mjs';
const file = process.argv[2];
if (!file) throw new Error('Usage: node scripts/validate-feed.mjs feed/v1/leaderboard.json');
const data = validateFeed(JSON.parse(fs.readFileSync(file,'utf8')));
console.log(JSON.stringify({valid:true,revision:data.revision,systems:data.systems,queries:data.queries,reports:data.reports}));
