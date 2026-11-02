import { toast } from "vue-sonner";

// Short when all is well, longer when someone has to read and act
const DURATIONS = { success: 4000, info: 4000, warning: 6000, error: 9000 };

export function useToast() {
  const addToast = (message, type = "success", duration) => {
    const kind = DURATIONS[type] ? type : "info";
    // The same message again restarts its timer instead of stacking
    return toast[kind](message, { id: `${kind}:${message}`, duration: duration ?? DURATIONS[kind] });
  };
  return { addToast, removeToast: toast.dismiss };
}
