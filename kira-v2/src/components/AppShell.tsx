import * as Collapsible from "@radix-ui/react-collapsible";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState, type ComponentType, type PropsWithChildren, type SVGProps } from "react";
import {
  ChartBarSquareIcon,
  ChevronRightIcon,
  DocumentTextIcon,
  FolderOpenIcon,
  UserCircleIcon,
} from "@heroicons/react/24/outline";
import { NavLink, useLocation } from "react-router-dom";

type SectionProps = PropsWithChildren<{ className?: string }>;

type MainNavItem = {
  label: string;
  to: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
};

const mainItems: MainNavItem[] = [
  { label: "Dashboard", to: "/dashboard", icon: ChartBarSquareIcon },
  { label: "Profile", to: "/profile", icon: UserCircleIcon },
];

const documentItems = [
  { label: "Document List", to: "/documents" },
  { label: "Analysis & Charts", to: "/documents/analysis/rbi-policy_name" },
];

function NavItem({ item }: { item: MainNavItem }) {
  const Icon = item.icon;

  return (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        [
          "flex items-center gap-3 rounded-md border px-3 py-2.5 text-sm transition-colors",
          isActive
            ? "border-border-primary bg-surface-card font-medium text-text-primary"
            : "border-transparent text-text-secondary hover:bg-surface-elevated hover:text-text-primary",
        ].join(" ")
      }
      end
    >
      <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
      <span>{item.label}</span>
    </NavLink>
  );
}

function DocumentsNav() {
  const location = useLocation();
  const isDocumentsRoute = location.pathname.startsWith("/documents");
  const [manuallyOpen, setManuallyOpen] = useState(false);

  useEffect(() => {
    if (!isDocumentsRoute) {
      setManuallyOpen(false);
    }
  }, [isDocumentsRoute, location.pathname]);

  const isOpen = useMemo(() => isDocumentsRoute || manuallyOpen, [isDocumentsRoute, manuallyOpen]);

  return (
    <Collapsible.Root open={isOpen} onOpenChange={setManuallyOpen}>
      <Collapsible.Trigger asChild>
        <button
          type="button"
          aria-label="Toggle documents navigation"
          className={[
            "flex w-full items-center justify-between rounded-md border px-3 py-2.5 text-sm transition-colors",
            isDocumentsRoute
              ? "border-border-primary bg-surface-card font-medium text-text-primary"
              : "border-transparent text-text-secondary hover:bg-surface-elevated hover:text-text-primary",
          ].join(" ")}
        >
          <span className="flex items-center gap-3">
            <FolderOpenIcon className="h-5 w-5 shrink-0" aria-hidden="true" />
            <span>Documents</span>
          </span>
          <motion.span animate={{ rotate: isOpen ? 90 : 0 }} transition={{ duration: 0.2, ease: "easeOut" }}>
            <ChevronRightIcon className="h-4 w-4" aria-hidden="true" />
          </motion.span>
        </button>
      </Collapsible.Trigger>

      <AnimatePresence initial={false}>
        {isOpen ? (
          <Collapsible.Content forceMount asChild>
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.24, ease: "easeOut" }}
              className="overflow-hidden"
            >
              <motion.ul
                initial="hidden"
                animate="show"
                variants={{
                  hidden: { opacity: 0 },
                  show: { opacity: 1, transition: { staggerChildren: 0.05 } },
                }}
                className="mt-2 space-y-1 pl-5"
              >
                {documentItems.map((subItem) => (
                  <motion.li key={subItem.to} variants={{ hidden: { opacity: 0, y: -2 }, show: { opacity: 1, y: 0 } }}>
                    <NavLink
                      to={subItem.to}
                      className={({ isActive }) =>
                        [
                          "block rounded-md px-3 py-2 text-sm transition-colors",
                          isActive
                            ? "bg-surface-card font-medium text-text-primary"
                            : "text-text-muted hover:bg-surface-elevated hover:text-text-primary",
                        ].join(" ")
                      }
                      end={subItem.to === "/documents"}
                    >
                      <span className="inline-flex items-center gap-2">
                        <DocumentTextIcon className="h-4 w-4" aria-hidden="true" />
                        <span>{subItem.label}</span>
                      </span>
                    </NavLink>
                  </motion.li>
                ))}
              </motion.ul>
            </motion.div>
          </Collapsible.Content>
        ) : null}
      </AnimatePresence>
    </Collapsible.Root>
  );
}

function Sidebar() {
  return (
    <aside id="app-sidebar" className="hidden w-[240px] shrink-0 border-r border-border-primary bg-bg-primary px-4 py-6 lg:block" aria-label="Primary navigation">
      <p className="kira-heading px-1">KIRA AI</p>

      <nav className="mt-8 space-y-2" aria-label="Sidebar">
        <NavItem item={mainItems[0]} />
        <DocumentsNav />
        <NavItem item={mainItems[1]} />
      </nav>
    </aside>
  );
}

function TopBar() {
  return (
    <header className="sticky top-0 z-10 border-b border-border-primary bg-bg-primary/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-content items-center justify-between px-6">
        <h1 className="text-sm font-semibold uppercase tracking-[0.2em] text-text-secondary">Enterprise Compliance Workspace</h1>
      </div>
    </header>
  );
}

function MainContent({ children }: SectionProps) {
  return <main className="mx-auto w-full max-w-content px-8 py-8">{children}</main>;
}

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="flex min-h-screen bg-bg-primary text-text-primary">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col">
        <TopBar />
        <MainContent>{children}</MainContent>
      </div>
    </div>
  );
}
