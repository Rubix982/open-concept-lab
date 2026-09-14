import type { ReactNode } from "react";
import clsx from "clsx";
import Layout from "@theme/Layout";
import WritingSwitcher from "@site/src/components/WritingSwitcher";
import type { Props } from "@theme/BlogLayout";

/**
 * Two columns: the article, and a contents rail.
 *
 * The stock layout is article + "recent posts" rail + contents, built from
 * Infima's offset grid. That rail duplicates /writing, and it squeezed the
 * contents column to 184px, which wrapped every heading to three lines. More
 * importantly the article column ended up narrow enough that a wide figure had
 * nowhere to go but on top of the contents.
 *
 * Here the article gets its own column and figures are bounded by it, so an
 * overlap is not expressible rather than merely avoided.
 */
export default function BlogLayout(props: Props): ReactNode {
  const { toc, children, ...layoutProps } = props;

  return (
    <Layout {...layoutProps}>
      <div className={clsx("ocl-article", { "ocl-article--toc": Boolean(toc) })}>
        <main className="ocl-article__body">{children}</main>
        {toc ? (
          <aside className="ocl-article__toc">
            <WritingSwitcher />
            {toc}
          </aside>
        ) : null}
      </div>
    </Layout>
  );
}
