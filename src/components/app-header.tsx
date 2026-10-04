import { Separator } from "@/components/ui/separator";
import { DecorIcon } from "@/components/decor-icon";
import { AppBreadcrumbs } from "@/components/app-breadcrumbs";
import { CustomSidebarTrigger } from "@/components/custom-sidebar-trigger";
import { AiDrawerTrigger } from "@/components/ai/ai-drawer-trigger";
import { NavUser } from "@/components/nav-user";
import { displayFirstName } from "@/lib/user";
import type { Account } from "@/lib/auth/account";

// AppHeader lives inside the client AppShell, so it can't fetch data itself.
// The account is read in the server layout and passed down.
export function AppHeader({ account }: { account: Account | null }) {
	return (
		<header className="sticky top-0 z-50 flex h-14 shrink-0 items-center justify-between gap-2 border-b bg-background/95 px-4 backdrop-blur-sm supports-backdrop-filter:bg-background/50 md:px-6">
			<DecorIcon className="hidden md:block" position="bottom-left" />
			<div className="flex items-center gap-3">
				<CustomSidebarTrigger />
				<Separator
					className="mr-2 h-4 data-[orientation=vertical]:self-center"
					orientation="vertical"
				/>
				<AppBreadcrumbs />
			</div>
			<div className="flex items-center gap-3">
				<AiDrawerTrigger />
				{account && (
					<>
						<Separator
							className="h-4 data-[orientation=vertical]:self-center"
							orientation="vertical"
						/>
						<NavUser
							name={account.name || displayFirstName(null, account.email)}
							email={account.email}
							avatarUrl={account.avatarUrl}
							credits={account.credits}
							orgs={account.orgs}
							currentOrgId={account.currentOrgId}
						/>
					</>
				)}
			</div>
		</header>
	);
}
