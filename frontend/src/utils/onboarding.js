// Guided setup. Any address with ?onboarding opens it once the person is
// logged in (also across the login page); progress survives a reload so a
// half-finished setup continues where it stopped.

export const ONBOARDING_PARAM = 'onboarding';
const PENDING_KEY = 'onboarding_pending';
const PROGRESS_KEY = 'onboarding_progress';

function read(storage, key) {
  try { return storage.getItem(key); } catch { return null; }
}
function write(storage, key, value) {
  try {
    if (value === null) storage.removeItem(key);
    else storage.setItem(key, value);
  } catch { /* private mode: the setup simply starts over after a reload */ }
}

export const markOnboardingPending = () => write(sessionStorage, PENDING_KEY, '1');
export const onboardingPending = () => read(sessionStorage, PENDING_KEY) === '1';

export function loadProgress() {
  try { return JSON.parse(read(localStorage, PROGRESS_KEY) || 'null') || {}; } catch { return {}; }
}
export const saveProgress = (progress) => write(localStorage, PROGRESS_KEY, JSON.stringify(progress));

// Left for now: no more redirects, but ?onboarding continues where it stopped
export const pauseOnboarding = () => write(sessionStorage, PENDING_KEY, null);

// Finished: back to the normal dashboard, and a later ?onboarding starts afresh
export function endOnboarding() {
  write(sessionStorage, PENDING_KEY, null);
  write(localStorage, PROGRESS_KEY, null);
}
