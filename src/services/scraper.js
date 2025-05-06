import axios from 'axios';
import * as cheerio from 'cheerio';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const BASE_URL = 'https://kanchiuniv.ac.in';
const VISITED_URLS = new Set();
const MAX_PAGES = 50;

async function fetchPage(url) {
  try {
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    console.error(`Error fetching ${url}:`, error.message);
    return null;
  }
}

function extractText($) {
  // Remove script and style elements
  $('script').remove();
  $('style').remove();
  
  // Get text content
  return $('body')
    .text()
    .replace(/\s+/g, ' ')
    .trim();
}

function extractLinks($) {
  const links = new Set();
  $('a').each((_, element) => {
    const href = $(element).attr('href');
    if (href && href.startsWith('/')) {
      links.add(new URL(href, BASE_URL).toString());
    } else if (href && href.startsWith(BASE_URL)) {
      links.add(href);
    }
  });
  return Array.from(links);
}

async function scrapeWebsite(url, content = []) {
  if (VISITED_URLS.size >= MAX_PAGES || VISITED_URLS.has(url)) {
    return content;
  }

  console.log(`Scraping: ${url}`);
  VISITED_URLS.add(url);

  const html = await fetchPage(url);
  if (!html) return content;

  const $ = cheerio.load(html);
  const pageText = extractText($);
  content.push({
    url,
    text: pageText,
  });

  const links = extractLinks($);
  for (const link of links) {
    await scrapeWebsite(link, content);
  }

  return content;
}

async function processContent(content) {
  const processedContent = content
    .map(page => page.text)
    .join('\n\n')
    .replace(/\s+/g, ' ')
    .trim();

  const context = {
    university_info: processedContent,
    last_updated: new Date().toISOString(),
    source: BASE_URL,
  };

  await fs.writeFile(
    path.join(__dirname, 'university_context.json'),
    JSON.stringify(context, null, 2)
  );

  console.log('Content processed and saved successfully!');
}

async function main() {
  console.log('Starting web scraping...');
  const content = await scrapeWebsite(BASE_URL);
  await processContent(content);
}

main().catch(console.error);