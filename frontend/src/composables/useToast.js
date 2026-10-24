import { reactive } from "vue";

// Short when all is well, longer when someone has to read and act
const DURATIONS = { success: 4000, info: 4000, warning: 6000, error: 9000 };
const MAX_VISIBLE = 3;

const toasts = reactive([]);
const timers = new Map();
let toastId = 0;

function startTimer(toast) {
  clearTimeout(timers.get(toast.id));
  toast.startedAt = Date.now();
  timers.set(toast.id, setTimeout(() => removeToast(toast.id), toast.remaining));
}

function removeToast(id) {
  clearTimeout(timers.get(id));
  timers.delete(id);
  const index = toasts.findIndex((t) => t.id === id);
  if (index !== -1) toasts.splice(index, 1);
}

export function useToast() {
  const addToast = (message, type = "success", duration) => {
    const kind = DURATIONS[type] ? type : "info";
    const ms = duration ?? DURATIONS[kind];

    // The same message again restarts its timer instead of stacking
    const same = toasts.find((t) => t.message === message && t.type === kind);
    if (same) {
      same.duration = ms;
      same.remaining = ms;
      same.paused = false;
      same.restarts += 1;
      startTimer(same);
      return same.id;
    }

    const toast = reactive({ id: toastId++, message, type: kind, duration: ms, remaining: ms, paused: false, restarts: 0, startedAt: 0 });
    toasts.push(toast);
    while (toasts.length > MAX_VISIBLE) removeToast(toasts[0].id);
    startTimer(toast);
    return toast.id;
  };

  // Hovering a toast holds it until the pointer leaves
  const pauseToast = (id) => {
    const toast = toasts.find((t) => t.id === id);
    if (!toast || toast.paused) return;
    clearTimeout(timers.get(id));
    toast.remaining = Math.max(0, toast.remaining - (Date.now() - toast.startedAt));
    toast.paused = true;
  };
  const resumeToast = (id) => {
    const toast = toasts.find((t) => t.id === id);
    if (!toast || !toast.paused) return;
    toast.paused = false;
    startTimer(toast);
  };

  return { toasts, addToast, removeToast, pauseToast, resumeToast };
}
