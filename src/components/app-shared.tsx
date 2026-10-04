import type { ReactNode } from "react";
import { GanttChartIcon, LibraryIcon, MountainIcon, ScanLineIcon } from "lucide-react";
import { SparkleIcon } from "@/components/ai/sparkle-icon";

export type SidebarNavItem = {
	title: string;
	path?: string;
	icon?: ReactNode;
	isActive?: boolean;
	subItems?: SidebarNavItem[];
};

export type SidebarNavGroup = {
	label?: string;
	items: SidebarNavItem[];
};

export const navGroups: SidebarNavGroup[] = [
	{
		label: "Geology",
		items: [
			{
				title: "Orion",
				path: "/orion",
				icon: <SparkleIcon />,
			},
			{
				title: "Projects",
				path: "/projects",
				icon: <GanttChartIcon />,
			},
			{
				title: "Log Library",
				path: "/log-library",
				icon: <LibraryIcon />,
			},
			{
				title: "Log Digitizer",
				path: "/log-digitizer",
				icon: <ScanLineIcon />,
			},
			{
				title: "Map",
				path: "/map",
				icon: <MountainIcon />,
			},
		],
	},
];

export const footerNavLinks: SidebarNavItem[] = [];

export const navLinks: SidebarNavItem[] = [
	...navGroups.flatMap((group) =>
		group.items.flatMap((item) =>
			item.subItems?.length ? [item, ...item.subItems] : [item]
		)
	),
	...footerNavLinks,
];
