import { Marked } from "marked";
import { markedHighlight } from "marked-highlight";
import hljs from "highlight.js";

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
 * @returns {{text: string, html: string}} - An object containing the cleaned text and the rendered HTML.
 */
export const processBotMessage = (content) => {
  try {
    if (typeof content !== "string") {
      console.error("processBotMessage received non-string content:", content);
      return { text: "", html: "" };
    }
    // This regex removes the specific Kramdown attribute list for target="_blank"
    const cleanedText = content.replace(/{:target="_blank"}/g, "");
    const html = marked.parse(cleanedText);
    return { text: cleanedText, html };
  } catch (e) {
    console.error("Error parsing content with marked.js:", e);
    console.error("Original content:", content);
    // Fallback to returning the original content unprocessed but safely wrapped
    return { text: content, html: content };
  }
};
