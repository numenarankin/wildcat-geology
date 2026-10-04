import fs from "node:fs";
import sharp from "sharp";
import { toPages } from "./src/lib/raster-log/to-raster";
import { redrawPage } from "./src/lib/raster-log/digitize/digitize";
import { boxToPixels } from "./src/lib/raster-log/multipage/read";
import { fullTrackBand } from "./src/lib/raster-log/multipage/geometry";
const pages = await toPages(fs.readFileSync("Todd 1 Dual Density Logs.pdf"), "x.pdf");
const png = pages[2]; const { width = 0, height = 0 } = await sharp(png).metadata();
const crop = await sharp(png).extract(boxToPixels([4,69,977,985], width, height)).png().toBuffer();
const r = await redrawPage(crop, "p3");
fs.writeFileSync("/tmp/claude-1000/-home-linuxuser-dev/60bbdaca-4be3-4896-83f9-ce586f51f812/scratchpad/p3-redraw.png", r.cleaned.image);
const t = r.trace;
console.log("redraw", t.width, "x", t.height, "tracks", JSON.stringify(t.tracks));
const cols = t.gridColumns; const centres=[]; let run=[];
for (const x of cols) { if (!run.length || x - run[run.length-1] <= 2) run.push(x); else { centres.push((run[0]+run[run.length-1])/2); run=[x]; } }
if (run.length) centres.push((run[0]+run[run.length-1])/2);
console.log("grid centres", centres.slice(0,4).join(" "), "...", centres.slice(-4).join(" "));
for (const [i, tr] of t.tracks.entries()) console.log("track", i, "full band log 0.2-2000:", JSON.stringify(fullTrackBand(t, tr, { name:"", mnemonic:"ILD", unit:"", left:0.2, right:2000, scale:"log", line:"solid", span:[0,1] })));
