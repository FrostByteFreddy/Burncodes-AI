import { cva } from "class-variance-authority";

export { default as Alert } from "./Alert.vue";
export { default as AlertAction } from "./AlertAction.vue";
export { default as AlertDescription } from "./AlertDescription.vue";
export { default as AlertTitle } from "./AlertTitle.vue";

export const alertVariants = cva(
  "grid gap-0.5 rounded-lg border p-4 text-left text-base has-data-[slot=alert-action]:relative has-data-[slot=alert-action]:pr-18 has-[>svg]:grid-cols-[auto_minmax(0,1fr)] has-[>svg]:gap-x-3 *:[svg]:row-span-2 *:[svg]:translate-y-0.5 *:[svg]:text-current *:[svg:not([class*=size-])]:size-5 group/alert relative w-full",
  {
    variants: {
      variant: {
        default: "bg-card text-card-foreground",
        info: "border-transparent bg-accent text-foreground *:[svg]:text-primary",
        success: "border-transparent bg-success-soft text-foreground *:[svg]:text-success",
        warning: "border-transparent bg-warning-soft text-foreground *:[svg]:text-warning",
        error: "border-transparent bg-destructive-soft text-foreground *:[svg]:text-destructive",
        ai: "border-transparent bg-ai-soft text-foreground *:[svg]:text-ai",
        tip: "border-transparent bg-muted text-foreground *:[svg]:text-muted-foreground",
        destructive:
          "text-destructive bg-card *:data-[slot=alert-description]:text-destructive/90 *:[svg]:text-current",
      },
    },
    defaultVariants: { variant: "default" },
  },
);
