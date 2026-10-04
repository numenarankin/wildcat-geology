"use client";

import { usePathname } from "next/navigation";

/**
 * Main content wrapper. Most routes get a padded, full-width container whose
 * left edge lines up with the header (and its breadcrumb). Full-bleed routes
 * (the Orion chat page, the map, the log digitizer's centred drop zone) fill the entire area
 * flush to the sidebar, top bar, and screen edges.
 */
export function AppMain({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const fullBleed =
    pathname === "/" ||
		pathname === "/orion" ||
		pathname === "/map" ||
		pathname === "/log-digitizer";

  if (fullBleed) {
    // Bound to the viewport minus the h-14 (3.5rem) top bar so the page itself
    // never scrolls — scrolling happens inside the route's own panes (e.g. the
    // Orion conversation history), keeping the top bar and composer in view.
    return (
      <div className="flex h-[calc(100svh-3.5rem)] min-h-0 flex-col overflow-hidden">
        {children}
      </div>
    );
  }

  // Left padding lines the content up with the topbar's page-label icon, which
  // sits past the sidebar toggle + separator, not at the header padding edge:
  //   px-4 (16) + trigger (28) + gap-3 (12) + separator (1) + mr-2 (8) + gap-3 (12) = 77px
  //   px-6 (24) + trigger (28) + gap-3 (12) + separator (1) + mr-2 (8) + gap-3 (12) = 85px
  return (
    <div className="flex w-full flex-1 flex-col py-4 px-[77px] md:py-6 md:px-[85px]">
      {children}
    </div>
  );
}
