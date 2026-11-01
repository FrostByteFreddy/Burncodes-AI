import { cva } from "class-variance-authority";

export { default as Alert } from "./Alert.vue";
export { default as AlertAction } from "./AlertAction.vue";
export { default as AlertDescription } from "./AlertDescription.vue";
export { default as AlertTitle } from "./AlertTitle.vue";

export const alertVariants = cva(
  "grid gap-0.5 rounded-lg border p-4 text-left text-base has-data-[slot=alert-action]:relative has-data-[slot=alert-action]:pr-18 has-[>svg]:grid-cols-[auto_1fr] has-[>svg]:gap-x-3 *:[svg]:row-span-2 *:[svg]:translate-y-0.5 *:[svg]:text-current *:[svg:not([class*=size-])]:size-5 group/alert relative w-full",
  {
    variants: {
      variant: {
        default: "bg-card text-card-foreground",
        info: "border-transparent bg-[var(--interactive-soft)] text-foreground *:[svg]:text-[var(--interactive)]",
        success: "border-transparent bg-[var(--status-ok-soft)] text-foreground *:[svg]:text-[var(--status-ok)]",
        warning: "border-transparent bg-[var(--status-warn-soft)] text-foreground *:[svg]:text-[var(--status-warn)]",
        error: "border-transparent bg-[var(--status-error-soft)] text-foreground *:[svg]:text-[var(--status-error)]",
        ai: "border-transparent bg-[var(--ai-soft)] text-foreground *:[svg]:text-[var(--ai-text)]",
        tip: "border-transparent bg-[var(--surface-2)] text-foreground *:[svg]:text-[var(--text-secondary)]",
        destructive:
          "text-destructive bg-card *:data-[slot=alert-description]:text-destructive/90 *:[svg]:text-current",
      },
    },
    defaultVariants: { variant: "default" },
  },
);
