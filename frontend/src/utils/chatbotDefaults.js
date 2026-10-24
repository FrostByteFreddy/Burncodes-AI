// Starting texts for a chatbot, in the language residents write in.
// The prompt template only needs {persona} and {fine_tune_instructions};
// the documents are attached by the chat worker, not through the template.

export const CHATBOT_LANGUAGES = [
  { value: 'de', text: 'Deutsch' },
  { value: 'fr', text: 'Français' },
  { value: 'en', text: 'English' },
];

export const PROMPT_TEMPLATES = {
  de: '{persona}\n\n{fine_tune_instructions}\n\nBeantworte Fragen nur anhand der bereitgestellten Dokumente. Wenn die Dokumente keine Antwort enthalten, sag das ehrlich und rate nicht.',
  en: "{persona}\n\n{fine_tune_instructions}\n\nAnswer questions only from the provided documents. If the documents don't contain the answer, say so honestly instead of guessing.",
  fr: "{persona}\n\n{fine_tune_instructions}\n\nRéponds uniquement à partir des documents fournis. Si les documents ne contiennent pas la réponse, dis-le honnêtement au lieu de deviner.",
};

export const INTRO_MESSAGES = {
  de: 'Grüezi! Ich beantworte Ihre Fragen rund um unsere Website. Was möchten Sie wissen?',
  en: 'Hello! I answer questions about our website. What would you like to know?',
  fr: 'Bonjour ! Je réponds à vos questions sur notre site. Que souhaitez-vous savoir ?',
};

// Tone presets fill the personality text; people can edit it afterwards
export const TONES = {
  formal: {
    de: 'Du bist der digitale Assistent unserer Organisation. Du antwortest höflich, sachlich und gut verständlich und sprichst die Leute mit «Sie» an. Bei Fragen, die du nicht beantworten kannst, verweist du freundlich an unsere Kontaktstelle.',
    en: 'You are the digital assistant of our organisation. You answer politely, factually and in plain language. If you cannot answer a question, you kindly refer people to our contact desk.',
    fr: "Tu es l'assistant numérique de notre organisation. Tu réponds poliment, de manière factuelle et compréhensible, et tu vouvoies les gens. Si tu ne peux pas répondre, tu renvoies aimablement vers notre service de contact.",
  },
  friendly: {
    de: 'Du bist ein freundlicher, hilfsbereiter Assistent. Du antwortest herzlich und locker, duzt die Leute und erklärst Dinge so einfach wie möglich.',
    en: 'You are a friendly, helpful assistant. You answer warmly and casually and explain things as simply as possible.',
    fr: 'Tu es un assistant sympathique et serviable. Tu réponds chaleureusement, tu tutoies les gens et tu expliques les choses aussi simplement que possible.',
  },
  brief: {
    de: 'Du bist ein sachlicher Assistent. Du antwortest so kurz wie möglich, am liebsten in einem Satz oder einer kurzen Liste, und sprichst die Leute mit «Sie» an.',
    en: 'You are a matter-of-fact assistant. You answer as briefly as possible, ideally in one sentence or a short list.',
    fr: 'Tu es un assistant factuel. Tu réponds aussi brièvement que possible, idéalement en une phrase ou une courte liste, et tu vouvoies les gens.',
  },
};

export const defaultsFor = (lang) => ({
  intro_message: INTRO_MESSAGES[lang] || INTRO_MESSAGES.en,
  system_persona: TONES.formal[lang] || TONES.formal.en,
  rag_prompt_template: PROMPT_TEMPLATES[lang] || PROMPT_TEMPLATES.en,
  doc_language: lang,
  translation_target: lang,
});
