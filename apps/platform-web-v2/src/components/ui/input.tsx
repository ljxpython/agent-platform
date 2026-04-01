import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

export function Input({ className, style, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-xl border px-3 text-sm outline-none transition duration-150 placeholder:text-[var(--muted-foreground)] focus:ring-2 focus:ring-[color:var(--primary)]/20",
        className,
      )}
      style={{
        background: "var(--input-background)",
        color: "var(--input-foreground)",
        borderColor: "var(--border)",
        ...style,
      }}
      {...props}
    />
  );
}
