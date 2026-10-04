import { getGridFrame, getMapCorners, getSubsurfaceSummary } from "@/lib/subsurface/maps";
import { SubsurfaceMapWorkspace } from "@/components/subsurface/subsurface-map-workspace";

export const metadata = {
  title: "Map",
  description: "Subsurface maps: structure and isopach maps gridded from a tops export.",
};

/**
 * Structure and isopach maps, read from the files `npm run build:subsurface`
 * writes under data/subsurface/maps. Every map shares one grid, so one set of
 * corners places them all.
 */
export default async function MapPage() {
  const summary = await getSubsurfaceSummary();
  const maps = summary?.maps ?? [];
  const [corners, frame] = maps.length > 0 ? await Promise.all([getMapCorners(maps[0].id), getGridFrame()]) : [null, null];
  return (
    <SubsurfaceMapWorkspace
      maps={corners ? maps : []}
      corners={corners ?? [[0, 0], [0, 0], [0, 0], [0, 0]]}
      frame={frame}
    />
  );
}
