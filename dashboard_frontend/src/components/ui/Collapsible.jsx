// src/components/ui/Collapsible.jsx
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";
import { cn } from "../../lib/utils";

export function Collapsible({ open, onOpenChange, children, className }) {
  return (
    <CollapsiblePrimitive.Root open={open} onOpenChange={onOpenChange} className={cn("space-y-2", className)}>
      {children}
    </CollapsiblePrimitive.Root>
  );
}

export function CollapsibleTrigger({ children, className, ...props }) {
  return (
    <CollapsiblePrimitive.Trigger
      className={cn(
        "flex w-full items-center justify-between text-sm font-medium transition-all hover:underline",
        className
      )}
      {...props}
    >
      {children}
    </CollapsiblePrimitive.Trigger>
  );
}

export function CollapsibleContent({ children, className, ...props }) {
  return (
    <CollapsiblePrimitive.Content
      className={cn("overflow-hidden text-sm transition-all data-[state=open]:animate-slideDown data-[state=closed]:animate-slideUp", className)}
      {...props}
    >
      {children}
    </CollapsiblePrimitive.Content>
  );
}
