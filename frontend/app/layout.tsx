import Link from "next/link";
import "./globals.css";

// Runtime <link> rather than next/font/google: the build container's network
// is flaky, and a build-time font fetch fails the whole build. If Google
// Fonts is unreachable the declared system-ui fallback still renders.
const FONTS_HREF =
  "https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Fira+Sans:wght@400;500;600;700&display=swap";

export const metadata = {
  title: "Molecule Scout",
  description:
    "AI research assistant for early-stage drug discovery — retrieval, generation, filtering, docking.",
};

function Wordmark() {
  return (
    <span className="flex items-center gap-2.5">
      {/* Two fused rings: the most honest small mark for a molecule tool. */}
      <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true">
        <circle cx="10" cy="13" r="7" stroke="#D97706" strokeWidth="1.75" />
        <circle cx="17.5" cy="13" r="7" stroke="#10B981" strokeWidth="1.75" />
      </svg>
      <span className="text-[15px] font-semibold tracking-tight text-lab-text">
        Molecule Scout
      </span>
    </span>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="stylesheet" href={FONTS_HREF} />
      </head>
      <body>
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-lab-amber focus:px-3 focus:py-2 focus:text-lab-bg"
        >
          Skip to content
        </a>
        <header className="sticky top-0 z-40 border-b border-lab-line bg-lab-bg/90 backdrop-blur">
          <div className="bench flex items-center justify-between py-3.5">
            <Link href="/" aria-label="Molecule Scout home">
              <Wordmark />
            </Link>
            <nav className="flex items-center gap-6 text-sm text-lab-muted">
              <Link href="/" className="transition hover:text-lab-text">
                New project
              </Link>
              <span className="chip" title="V1–V6 delivered">
                V6 · docking
              </span>
            </nav>
          </div>
        </header>
        <main id="main">{children}</main>
        <footer className="mt-16 border-t border-lab-line">
          <div className="bench py-6 text-xs leading-relaxed text-lab-muted">
            Generated molecules are not validated drug candidates — output is a
            triage aid requiring human and wet-lab verification.
          </div>
        </footer>
      </body>
    </html>
  );
}
