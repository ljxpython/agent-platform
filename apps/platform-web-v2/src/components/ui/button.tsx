import { Slot } from "@radix-ui/react-slot";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  variant?: "primary" | "ghost" | "link";
  size?: "default" | "sm";
};

function getVariantStyle(variant: NonNullable<ButtonProps["variant"]>) {
  if (variant === "primary") {
    return {
      background: "var(--button-primary-background)",
      color: "var(--button-primary-foreground)",
      borderColor: "transparent",
    };
  }

  if (variant === "link") {
    return {
      color: "var(--button-link-foreground)",
      borderColor: "transparent",
      background: "transparent",
    };
  }

  return {
    background: "var(--button-ghost-background)",
    color: "var(--button-ghost-foreground)",
    borderColor: "var(--border)",
  };
}

export function Button({
  asChild = false,
  className,
  size = "default",
  style,
  variant = "ghost",
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";

  return (
    <Comp
      className={cn(
        "inline-flex items-center justify-center rounded-xl border text-sm font-semibold transition duration-150 disabled:pointer-events-none disabled:opacity-60",
        size === "sm" ? "h-8 px-3" : "h-10 px-4",
        variant === "link" ? "h-auto rounded-none px-0" : "shadow-sm",
        className,
      )}
      style={{ ...getVariantStyle(variant), ...style }}
      {...props}
    />
  );
}
