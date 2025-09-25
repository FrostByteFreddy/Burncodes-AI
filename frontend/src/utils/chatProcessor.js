import { marked } from "marked";

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
    const html = marked(cleanedText);
    return { text: cleanedText, html };
  } catch (e) {
    console.error("Error parsing content with marked.js:", e);
    console.error("Original content:", content);
    // Fallback to returning the original content unprocessed but safely wrapped
    return { text: content, html: content };
  }
};