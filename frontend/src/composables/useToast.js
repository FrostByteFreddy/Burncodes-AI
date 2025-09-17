import { reactive } from 'vue'

const toasts = reactive([])

let toastId = 0

export function useToast() {
  const addToast = (message, type = 'success', duration = 3000) => {
    const id = toastId++
    toasts.push({ id, message, type })
    setTimeout(() => removeToast(id), duration)
  }

  const removeToast = (id) => {
    const index = toasts.findIndex(toast => toast.id === id)
    if (index !== -1) {
      toasts.splice(index, 1)
    }
  }

  return { toasts, addToast, removeToast }
}
