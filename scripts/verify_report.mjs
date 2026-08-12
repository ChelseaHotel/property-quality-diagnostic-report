#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require=createRequire(path.join(process.env.NODE_PATH||process.cwd(),"package.json"));
const { chromium }=require("playwright");

const args=process.argv.slice(2);if(!args.length){console.error("Usage: verify_report.mjs <report.html> [--out <dir>]");process.exit(2)}
const report=path.resolve(args[0]);const outIndex=args.indexOf("--out");const out=path.resolve(outIndex>=0?args[outIndex+1]:path.join(path.dirname(report),"verification"));await fs.mkdir(out,{recursive:true});
let browser;try{browser=await chromium.launch({channel:process.env.PW_CHANNEL||"msedge",headless:true})}catch(channelError){try{browser=await chromium.launch({headless:true})}catch(defaultError){console.error(`Unable to launch a browser. Set PW_CHANNEL to an installed Chromium channel.\n${channelError}\n${defaultError}`);process.exit(2)}}const page=await browser.newPage({viewport:{width:1366,height:900}});const errors=[];page.on("pageerror",e=>errors.push(String(e)));await page.goto(pathToFileURL(report).href,{waitUntil:"load"});
const result={title:await page.title(),details:await page.locator("#detailBody tr").count(),pending:await page.locator("#pendingBody tr").count(),external:await page.evaluate(()=>performance.getEntriesByType("resource").filter(x=>/^https?:/.test(x.name)).map(x=>x.name)),pageErrors:errors};
result.context=await page.evaluate(()=>({records:ctx.metrics.records,pending:ctx.metrics.pending,boards:ctx.boards.length}));
result.alignment=await page.evaluate(()=>{const left=[...document.querySelectorAll('#boardChart .bar-row')],right=[...document.querySelectorAll('#riskShare .share-row')];return left.map((el,i)=>Math.abs(el.getBoundingClientRect().top-(right[i]?.getBoundingClientRect().top??Infinity)))});
result.overflow1366=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth);await page.screenshot({path:path.join(out,"desktop.png"),fullPage:true});await page.screenshot({path:path.join(out,"dashboard.png")});await page.locator("section").nth(2).screenshot({path:path.join(out,"risk-analysis.png")});await page.locator("section").nth(4).screenshot({path:path.join(out,"problem-list.png")});await page.setViewportSize({width:390,height:844});result.overflow390=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth);await page.screenshot({path:path.join(out,"mobile.png"),fullPage:true});
if(result.details!==result.context.records)throw new Error(`detail rows ${result.details} != ${result.context.records}`);if(result.pending!==result.context.pending)throw new Error(`pending rows ${result.pending} != ${result.context.pending}`);if(result.external.length||result.pageErrors.length)throw new Error("external resources or page errors detected");if(result.alignment.some(x=>x>1))throw new Error(`board alignment failed: ${result.alignment}`);if(result.overflow1366||result.overflow390)throw new Error("page-level horizontal overflow detected");console.log(JSON.stringify(result,null,2));await browser.close();
