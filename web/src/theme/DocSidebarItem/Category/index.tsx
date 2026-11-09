import type { ReactNode } from "react";
import Category from "@theme-original/DocSidebarItem/Category";
import type CategoryType from "@theme/DocSidebarItem/Category";
import type { WrapperProps } from "@docusaurus/types";

type Props = WrapperProps<typeof CategoryType>;

/**
 * A project in the notebook rail is a name, the stage it is at, and a few
 * words saying what it is. Docusaurus takes a category label as a string;
 * it renders whatever it is given, so this replaces the label with a node
 * before handing the item back to the original component.
 *
 * `blurb` and `status` come from sidebars.ts, which reads the stage from
 * data/projects.yml. A category without them renders exactly as before.
 */
export default function CategoryWrapper(props: Props): ReactNode {
  const { blurb, status } = (props.item.customProps ?? {}) as {
    blurb?: string;
    status?: string;
  };

  if (!blurb && !status) {
    return <Category {...props} />;
  }

  const label = (
    <span className="ocl-proj">
      <span className="ocl-proj__row">
        <span className="ocl-proj__name">{props.item.label}</span>
        {status ? <span className="ocl-proj__stage">{status}</span> : null}
      </span>
      {blurb ? <span className="ocl-proj__blurb">{blurb}</span> : null}
    </span>
  );

  return (
    <Category
      {...props}
      item={{ ...props.item, label: label as unknown as string }}
    />
  );
}
