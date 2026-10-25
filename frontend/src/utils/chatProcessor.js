import { Marked } from "marked";
import { markedHighlight } from "marked-highlight";
import hljs from "highlight.js";
import DOMPurify from "dompurify";

// Configure marked with highlight.js
const marked = new Marked(
  markedHighlight({
    langPrefix: "hljs language-",
    highlight(code, lang) {
      const language = hljs.getLanguage(lang) ? lang : "plaintext";
      return hljs.highlight(code, { language }).value;
    },
  })
);

/**
 * Processes a bot's message content, cleaning it and converting markdown to HTML.
 * @param {string} content - The raw string content from the bot.
 * Calendar markers ([[calendar:key]]) the chatbot adds after giving dates are
 * taken out of the text and returned as `calendars` for the chat to show as buttons.
 * @returns {{text: string, html: string, calendars: string[]}}
 */
const CALENDAR_MARKER = /\[\[calendar:([a-z0-9-]+)\]\]/g;

export const processBotMessage = (content) => {
  try {
    if (typeof content !== "string") {
      console.error("processBotMessage received non-string content:", content);
      return { text: "", html: "" };
    }
    // This regex removes the specific Kramdown attribute list for target="_blank"
    const cleanedText = content.replace(/{:target="_blank"}/g, "");
    const calendars = [...cleanedText.matchAll(CALENDAR_MARKER)].map((m) => m[1]);
    // while an answer streams in, hide a marker that isn't complete yet
    const visible = cleanedText.replace(CALENDAR_MARKER, "").replace(/\[\[[a-z:\-0-9]*\]?$/, "").trimEnd();
    const html = DOMPurify.sanitize(marked.parse(visible));
    return { text: cleanedText, html, calendars: [...new Set(calendars)] };
  } catch (e) {
    console.error("Error parsing content with marked.js:", e);
    console.error("Original content:", content);
    // Fallback to returning the original content unprocessed but safely wrapped
    return { text: content, html: DOMPurify.sanitize(content) };
  }
};
