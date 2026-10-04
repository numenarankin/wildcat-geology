"use client";

import { motion, useReducedMotion } from "framer-motion";
import { usePathname } from "next/navigation";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppHeader } from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { AppMain } from "@/components/app-main";
import { BreadcrumbProvider } from "@/components/breadcrumb-context";
import type { Account } from "@/lib/auth/account";

/** Routes that render full-screen, outside the app chrome (sidebar/topbar). From Wildcat. */
const BARE_ROUTES = ["/auth"];

export function AppShell({
	children,
	account,
}: {
	children: React.ReactNode;
	/** The signed-in account, read in the server layout. Null when signed out. */
	account: Account | null;
}) {
	const pathname = usePathname();
	const still = useReducedMotion();
	const bare = BARE_ROUTES.some(
		(route) => pathname === route || pathname.startsWith(`${route}/`)
	);
	if (bare) {
		return <>{children}</>;
	}
	return (
		<BreadcrumbProvider>
			<motion.div
				initial={{ opacity: 0 }}
				animate={{ opacity: 1 }}
				transition={{ duration: still ? 0 : 0.14, ease: [0.16, 1, 0.3, 1] }}
			>
				<SidebarProvider>
					<AppSidebar />
					<SidebarInset className="min-w-0">
						<AppHeader account={account} />
						<AppMain>{children}</AppMain>
					</SidebarInset>
				</SidebarProvider>
			</motion.div>
		</BreadcrumbProvider>
	);
}
