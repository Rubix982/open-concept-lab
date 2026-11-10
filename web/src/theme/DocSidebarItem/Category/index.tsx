import type { ReactNode } from "react";
import Category from "@theme-original/DocSidebarItem/Category";
import type CategoryType from "@theme/DocSidebarItem/Category";
import type { WrapperProps } from "@docusaurus/types";
import { projectLabel, type ProjectProps } from "@site/src/components/ProjectLabel";

type Props = WrapperProps<typeof CategoryType>;

/**
 * A project that has pages beyond its overview. The row opens; the name itself
 * links to the overview, so no child stands in for it.
 *
 * A category without a blurb or stage renders exactly as before.
 */
export default function CategoryWrapper(props: Props): ReactNode {
  const custom = (props.item.customProps ?? {}) as ProjectProps;
  if (!custom.blurb && !custom.status) return <Category {...props} />;

  return (
    <Category
      {...props}
      item={{
        ...props.item,
        label: projectLabel(props.item.label, custom) as unknown as string,
      }}
    />
  );
}
