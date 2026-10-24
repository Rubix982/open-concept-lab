import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, Project } from "@site/plugins/lab-data";
import PageArt from "@site/src/components/PageArt";
import Stage from "@site/src/components/writing/Stage";

export function useProjects(): Project[] {
  return (usePluginData("ocl-lab-data") as LabData).projects;
}

/** "14 Oct 2026" */
function shortDate(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(iso));
}

/**
 * One project as a card: its drawing, its name, the phase it is in, and the
 * objective from its own plan.md.
 */
export function ProjectCard({ project }: { project: Project }): ReactNode {
  return (
    <Link className="ocl-home__project ocl-project" to={project.notebook}>
      <PageArt name={project.name} kind="projects" />
      <span className="ocl-project__body">
        <span className="ocl-home__projectName">{project.name}</span>
        <span className="ocl-project__phase" title={project.phaseDetail}>
          <Stage status={project.tone} label={false} />
          {project.phase}
        </span>
        <span className="ocl-home__projectWhat">{project.what}</span>
        {project.updated ? (
          <span className="ocl-home__projectDate">Plan updated {shortDate(project.updated)}</span>
        ) : null}
      </span>
    </Link>
  );
}

/**
 * The projects, as cards. Everything but the stage mark comes from each
 * project's own plan.md, so this follows the work instead of being kept in
 * step with it by hand.
 */
export default function Projects(): ReactNode {
  const projects = useProjects();
  return (
    <div className="ocl-home__projects ocl-projects">
      {projects.map((project) => (
        <ProjectCard key={project.name} project={project} />
      ))}
    </div>
  );
}
