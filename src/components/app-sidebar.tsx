"use client";

import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";
import {
	Sidebar,
	SidebarContent,
	SidebarFooter,
	SidebarHeader,
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
} from "@/components/ui/sidebar";
import { footerNavLinks, navGroups } from "@/components/app-shared";
import { NavGroup } from "@/components/nav-group";

export function AppSidebar() {
	return (
		<Sidebar
			className={cn(
				"*:data-[slot=sidebar-inner]:bg-background",
				"*:data-[slot=sidebar-inner]:dark:bg-[radial-gradient(60%_18%_at_10%_0%,--theme(--color-foreground/.08),transparent)]",
				"**:data-[slot=sidebar-menu-button]:[&>span]:text-foreground/75"
			)}
			collapsible="icon"
			variant="sidebar"
		>
			<SidebarHeader className="h-14 justify-center border-b px-2">
				<SidebarMenuButton render={<a href="#link" />}><Image src="/slim_normal.png" alt="WildcatIQ logo" width={16} height={16} className="size-4 shrink-0" /><span className="text-base font-semibold text-foreground!">WildcatIQ</span></SidebarMenuButton>
			</SidebarHeader>
			<SidebarContent>
				{navGroups.map((group, index) => (
					<NavGroup key={`sidebar-group-${index}`} {...group} />
				))}
			</SidebarContent>
			<SidebarFooter className="gap-0 p-0">
				{footerNavLinks.length > 0 && (
					<SidebarMenu className="border-t p-2">
						{footerNavLinks.map((item) => (
							<SidebarMenuItem key={item.title}>
								<SidebarMenuButton className="text-muted-foreground" isActive={item.isActive} size="sm" render={<Link href={item.path ?? "#"} />}>{item.icon}<span>{item.title}</span></SidebarMenuButton>
							</SidebarMenuItem>
						))}
					</SidebarMenu>
				)}
				<div className="border-t px-4 pt-4 pb-2 transition-opacity group-data-[collapsible=icon]:pointer-events-none group-data-[collapsible=icon]:opacity-0">
					<p className="text-nowrap text-[9px] text-muted-foreground">
						© {new Date().getFullYear()} Wildcat Labs, Inc.
					</p>
				</div>
			</SidebarFooter>
		</Sidebar>
	);
}
