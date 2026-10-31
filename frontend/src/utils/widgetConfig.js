// The chat widget's configuration as the dashboard edits it: defaults, the
// form built from a saved chatbot, and the look taken from its website.
import { colorOf, contrast } from '../components/tenant/settings/palette';
import { DEFAULT_AUDIENCE } from './chatbotDefaults';

export const defaultWidgetConfig = () => ({
  chatbot_title: '',
  logo: null,
  launcher_icon: null,
  show_reset_button: true,
  show_share_button: false,
  widget_enabled: true,
  input_placeholder: '',
  thinking_messages: [],
  conversation_starters: [],
  starter_background_color: 'c_primary',
  starter_text_color: 'c_white',
  color_palette: [
    { id: 'c_primary',   name: 'Primary',   value: '#5F6DFF' },
    { id: 'c_secondary', name: 'Secondary', value: '#F3F4F6' },
    { id: 'c_black',     name: 'Black',     value: '#1F2937' },
    { id: 'c_white',     name: 'White',     value: '#FFFFFF' },
  ],
  component_styles: {
    header_background_color: 'c_secondary', header_text_color: 'c_black',
    user_message_background_color: 'c_primary', user_message_text_color: 'c_white',
    bot_message_background_color: 'c_secondary', bot_message_text_color: 'c_black',
    send_button_background_color: 'c_primary', send_button_text_color: 'c_white',
    input_background_color: 'c_secondary', input_text_color: 'c_black',
    footer_background_color: 'c_secondary', chat_background_color: 'c_white',
    reset_button_color: 'c_primary', reset_button_icon_color: 'c_white',
    close_button_background_color: 'c_primary', close_button_icon_color: 'c_white',
    share_button_color: 'c_primary', share_button_icon_color: 'c_white',
    launcher_background_color: 'c_primary',
  },
});

const FIELDS = ['name', 'intro_message', 'system_persona', 'rag_prompt_template'];

// Plain deep copy; store objects are reactive proxies, which structuredClone rejects
const clone = (v) => JSON.parse(JSON.stringify(v));

// The editable form of a saved chatbot, with defaults for anything never set
export const fromTenant = (tenant) => {
  const saved = tenant.widget_config || {};
  const base = defaultWidgetConfig();
  return {
    ...Object.fromEntries(FIELDS.map((f) => [f, tenant[f] ?? ''])),
    audience: tenant.audience || DEFAULT_AUDIENCE,
    widget_config: {
      ...base,
      ...clone(saved),
      color_palette: clone(saved.color_palette || base.color_palette),
      component_styles: {
        ...base.component_styles,
        // the footer used to follow the header colour; keep that look until changed
        footer_background_color: saved.component_styles?.header_background_color || base.component_styles.footer_background_color,
        ...(saved.component_styles || {}),
      },
    },
  };
};

// Spots that show Primary by default, with the text or icon drawn on them
const ON_PRIMARY = {
  user_message_background_color: 'user_message_text_color',
  send_button_background_color: 'send_button_text_color',
  reset_button_color: 'reset_button_icon_color',
  close_button_background_color: 'close_button_icon_color',
  share_button_color: 'share_button_icon_color',
  launcher_background_color: null,
};

// Applies what POST /tenants/<id>/branding found: the brand colour becomes
// Primary everywhere Primary belongs, plus logo and name. Returns whether
// anything was found.
export function applyBranding(cfg, branding) {
  const [primary] = branding.colors || [];
  if (primary) {
    cfg.color_palette.find((c) => c.id === 'c_primary').value = primary;
    // white text on a brand colour unless it's unreadable there; measured against
    // the palette's own white and black, not pure #FFF/#000
    const [white, black] = ['c_white', 'c_black'].map((id) => contrast(primary, colorOf(cfg, id)));
    const text = white >= 4.5 || white >= black ? 'c_white' : 'c_black';
    for (const [bg, fg] of Object.entries(ON_PRIMARY)) {
      cfg.component_styles[bg] = 'c_primary';
      if (fg) cfg.component_styles[fg] = text;
    }
    cfg.starter_background_color = 'c_primary';
    cfg.starter_text_color = text;
  }
  if (branding.logo) cfg.logo = branding.logo;
  if (!cfg.chatbot_title && branding.site_name) cfg.chatbot_title = branding.site_name;
  return Boolean(primary || branding.logo);
}
