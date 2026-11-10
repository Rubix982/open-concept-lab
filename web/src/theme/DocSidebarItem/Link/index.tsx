import type { ReactNode } from "react";
import Link from "@theme-original/DocSidebarItem/Link";
import type LinkType from "@theme/DocSidebarItem/Link";
import type { WrapperProps } from "@docusaurus/types";
import { projectLabel, type ProjectProps } from "@site/src/components/ProjectLabel";

type Props = WrapperProps<typeof LinkType>;

/**
 * A project whose overview is all there is: one row, straight to the page.
 *
 * It carries the same name, stage and blurb as a project that opens, so the two
 * read as the same kind of thing. Without this, giving the single-page projects
 * a plain row would have stripped them of everything but their directory name —
 * which is the inconsistency the hand-written sidebar exists to avoid.
 */
export default function LinkWrapper(props: Props): ReactNode {
  const custom = (props.item.customProps ?? {}) as ProjectProps;
  if (!custom.blurb && !custom.status) return <Link {...props} />;

  return (
    <Link
      {...props}
      item={{
        ...props.item,
        label: projectLabel(props.item.label, custom) as unknown as string,
      }}
    />
  );
}
