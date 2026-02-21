import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 4 },
  show: { opacity: 1, y: 0 },
};

export function DocumentAnalysisPage() {
  return (
    <div className="mx-auto w-full max-w-[1280px] pb-20">
      <motion.section initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.24 }} className="mb-12">
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">Documents</p>
        <h2 className="mt-4 text-[40px] font-semibold tracking-tight text-text-primary md:text-5xl">Analysis & Charts</h2>
        <p className="mt-4 max-w-4xl text-base leading-8 text-text-secondary">Operational analysis workspace for extraction quality, throughput, and review outcomes.</p>
      </motion.section>

      <motion.section initial="hidden" animate="show" variants={fadeUp} transition={{ duration: 0.25 }}>
        <section className="rounded-md border border-border-primary bg-surface-card p-8">
          <h3 className="text-xl font-semibold text-text-primary">Analysis Overview</h3>
          <p className="mt-4 text-sm text-text-secondary">This route is reserved for document-level analytical views and KPI drilldowns.</p>
        </section>
      </motion.section>
    </div>
  );
}
