// Starting texts for a chatbot. Instructions to the model are English only;
// the chatbot replies in whatever language the visitor writes (the chat
// worker adds that rule). Visitor-facing texts follow the dashboard language.

export const PROMPT_TEMPLATE =
  "{persona}\n\n{fine_tune_instructions}\n\nAnswer questions only from the provided documents. If the documents don't contain the answer, say so honestly instead of guessing.";

export const INTRO_MESSAGES = {
  de: 'Grüezi! Ich beantworte Ihre Fragen rund um unsere Website. Was möchten Sie wissen?',
  en: 'Hello! I answer questions about our website. What would you like to know?',
  fr: 'Bonjour ! Je réponds à vos questions sur notre site. Que souhaitez-vous savoir ?',
};

// Tone presets fill the personality text; people can edit it afterwards
export const TONES = {
  formal: 'You are the digital assistant of our organisation. You answer politely, factually and in plain language, and address people formally unless they write informally. If you cannot answer a question, you kindly refer people to our contact desk.',
  friendly: 'You are a friendly, helpful assistant. You answer warmly and casually, address people informally and explain things as simply as possible.',
  brief: 'You are a matter-of-fact assistant. You answer as briefly as possible, ideally in one sentence or a short list, and address people formally unless they write informally.',
};

export const defaultsFor = (locale) => ({
  intro_message: INTRO_MESSAGES[locale] || INTRO_MESSAGES.en,
  system_persona: TONES.formal,
  rag_prompt_template: PROMPT_TEMPLATE,
});

// Who the chatbot answers; decides what the crawl considers worth learning
export const AUDIENCES = ['municipality', 'general'];
export const DEFAULT_AUDIENCE = 'municipality';

// Sample exchange for designing the chat window, per audience, in the dashboard language
const MUNICIPALITY_SAMPLE = {
  de: {
    question: 'Wann ist die nächste Papiersammlung?',
    answer: 'Die nächste Papiersammlung ist am **Dienstag, 3. November**. Bitte stellen Sie das gebündelte Papier bis 7 Uhr an den Strassenrand.',
    newQuestion: 'Neue Frage',
  },
  en: {
    question: 'When is the next paper collection?',
    answer: 'The next paper collection is on **Tuesday, 3 November**. Please put the bundled paper out by the road by 7 am.',
    newQuestion: 'New question',
  },
  fr: {
    question: 'Quand a lieu le prochain ramassage du papier ?',
    answer: 'Le prochain ramassage du papier a lieu le **mardi 3 novembre**. Merci de déposer le papier ficelé au bord de la route avant 7 h.',
    newQuestion: 'Nouvelle question',
  },
};

const GENERAL_SAMPLE = {
  de: {
    question: 'Wann sind Sie telefonisch erreichbar?',
    answer: 'Sie erreichen uns **Montag bis Freitag von 8 bis 17 Uhr** unter 044 123 45 67. Ausserhalb dieser Zeiten können Sie uns gerne eine E-Mail schreiben.',
    newQuestion: 'Neue Frage',
  },
  en: {
    question: 'When can I reach you by phone?',
    answer: 'You can reach us **Monday to Friday, 8 am to 5 pm** on 044 123 45 67. Outside these hours, feel free to send us an email.',
    newQuestion: 'New question',
  },
  fr: {
    question: 'Quand puis-je vous joindre par téléphone ?',
    answer: 'Vous pouvez nous joindre **du lundi au vendredi, de 8 h à 17 h** au 044 123 45 67. En dehors de ces horaires, écrivez-nous volontiers un e-mail.',
    newQuestion: 'Nouvelle question',
  },
};

export const SAMPLE_CONVERSATION = { municipality: MUNICIPALITY_SAMPLE, general: GENERAL_SAMPLE };
