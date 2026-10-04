"use client"

import { Toaster as Sonner, type ToasterProps } from "sonner"

/**
 * App toaster. Positioned bottom-right per the in-app alerts spec. Themed via CSS
 * variables mapped to our design tokens so toasts match the app in light + dark
 * (sonner's default theme="system" follows prefers-color-scheme; the project has
 * no next-themes provider to read from).
 */
function Toaster(props: ToasterProps) {
  return (
    <Sonner
      className="toaster group"
      position="bottom-right"
      richColors
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
        } as React.CSSProperties
      }
      {...props}
    />
  )
}

export { Toaster }
