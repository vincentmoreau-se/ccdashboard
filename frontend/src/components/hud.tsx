import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

/** Background atmosphere layers — mounted once at the app root. */
export function DeckBackground() {
  return (
    <>
      <div className="deck-bg" />
      <div className="deck-sweep" />
      <div className="scanlines" />
    </>
  );
}

/**
 * One-shot "power-on" overlay: HUD boot lines + filling progress bar, then
 * fades away. Purely cosmetic — unmounts after ~1s. Skipped under
 * prefers-reduced-motion so it never flashes for those users.
 */
export function BootOverlay() {
  const reduce = useReducedMotion();
  const [done, setDone] = useState(false);
  useEffect(() => {
    if (reduce) return;
    const t = setTimeout(() => setDone(true), 1150);
    return () => clearTimeout(t);
  }, [reduce]);
  if (reduce) return null;
  return (
    <AnimatePresence>
      {!done && (
        <motion.div
          className="fixed inset-0 z-[60] grid place-items-center bg-void"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="w-[min(420px,80vw)]">
            <div className="mb-3 font-display text-sm uppercase tracking-[0.4em] text-brand">
              CC<span className="text-bone">DASHBOARD</span>
            </div>
            <div className="mb-2 font-mono text-[11px] tracking-[0.25em] text-ash">
              <Typewriter text="INITIALISATION DU TABLEAU DE BORD…" />
            </div>
            <div className="h-1 w-full overflow-hidden rounded-full bg-grid">
              <div className="h-full animate-boot-bar bg-brand shadow-glow" />
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/** Tiny typewriter that reveals `text` character by character. */
function Typewriter({ text }: { text: string }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setN((v) => (v < text.length ? v + 1 : v)), 22);
    return () => clearInterval(id);
  }, [text]);
  return (
    <span>
      {text.slice(0, n)}
      <span className="text-brand">▍</span>
    </span>
  );
}
