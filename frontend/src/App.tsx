import { NavLink, Route, Routes } from "react-router-dom";

import { BootOverlay, DeckBackground } from "./components/hud";
import Insights from "./pages/Insights";
import Live from "./pages/Live";
import Overview from "./pages/Overview";
import ProjectDetail from "./pages/ProjectDetail";
import Projects from "./pages/Projects";
import Session from "./pages/Session";
import TechTooling from "./pages/TechTooling";

const NAV = [
  { to: "/", label: "Overview", end: true },
  { to: "/insights", label: "Insights" },
  { to: "/projects", label: "Projects" },
  { to: "/tech", label: "Tech & Tooling" },
  { to: "/live", label: "Live" },
];

export default function App() {
  return (
    <>
      <DeckBackground />
      <BootOverlay />
      <div className="relative z-10 mx-auto flex min-h-screen max-w-[1180px] flex-col px-4 py-5">
        <header className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-grid pb-4">
          <NavLink to="/" className="flex items-baseline gap-3">
            <h1 className="animate-flicker font-display text-xl font-700 tracking-[0.2em] text-bone">
              CC<span className="text-brand">Dashboard</span>
            </h1>
            <span className="hidden font-mono text-[11px] uppercase tracking-[0.3em] text-haze sm:inline">
              ▏ télémétrie claude code
            </span>
          </NavLink>
          <nav className="flex items-center gap-1">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  `px-3 py-1.5 font-display text-[11px] font-600 uppercase tracking-[0.2em] transition ${
                    isActive
                      ? "animate-glow-pulse bg-brand/10 text-brand"
                      : "text-ash hover:text-bone"
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:name" element={<ProjectDetail />} />
            <Route path="/sessions/:id" element={<Session />} />
            <Route path="/tech" element={<TechTooling />} />
            <Route path="/live" element={<Live />} />
          </Routes>
        </main>

        <footer className="mt-8 border-t border-grid pt-3 font-mono text-[10px] uppercase tracking-[0.25em] text-haze">
          CCDashboard ▏ sessions claude code locales ▏ coût · tokens · activité
        </footer>
      </div>
    </>
  );
}
