import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData, Project } from "@site/plugins/lab-data";

export function useProjects(): Project[] {
  return (usePluginData("ocl-lab-data") as LabData).projects;
}

/**
 * The project table. Everything but the status dot comes from each project's
 * own plan.md, so this follows the work instead of being kept in step with it
 * by hand.
 */
export default function Projects({
  showUpdated = false,
}: {
  /** Add a column with each plan's last-updated date. */
  showUpdated?: boolean;
}): ReactNode {
  const projects = useProjects();

  return (
    <table className="ocl-table ocl-table--flush">
      <tbody>
        {projects.map((project) => (
          <tr key={project.name}>
            <td className="ocl-table__key">
              <Link to={project.notebook}>{project.name}</Link>
            </td>
            <td className="ocl-table__main">{project.what}</td>
            {showUpdated ? (
              <td className="ocl-table__num">{project.updated ?? "—"}</td>
            ) : null}
            <td className="ocl-table__right">
              <span
                className={`ocl-status ocl-status--${project.tone}`}
                title={project.phaseDetail}
              >
                {project.phase}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
