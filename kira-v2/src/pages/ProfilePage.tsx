import { motion } from "framer-motion";
import * as Dialog from "@radix-ui/react-dialog";
import * as Switch from "@radix-ui/react-switch";
import { useMemo, useState } from "react";

const fadeUp = {
  hidden: { opacity: 0, y: 4 },
  show: { opacity: 1, y: 0 },
};

type UserRole = "Owner" | "Admin" | "Member" | "Read-Only";

type ProjectUser = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: "Active" | "Invited";
};

const initialUsers: ProjectUser[] = [
  { id: "U-1", name: "Olivia Bennett", email: "olivia.bennett@kira.internal", role: "Owner", status: "Active" },
  { id: "U-2", name: "Aarav Singh", email: "aarav.singh@kira.internal", role: "Admin", status: "Active" },
  { id: "U-3", name: "Maya Chen", email: "maya.chen@kira.internal", role: "Member", status: "Active" },
  { id: "U-4", name: "Noah Patel", email: "noah.patel@kira.internal", role: "Read-Only", status: "Invited" },
];

function roleBadgeClass(role: UserRole) {
  if (role === "Owner") {
    return "border-border-primary bg-surface-elevated font-medium text-text-primary";
  }

  if (role === "Read-Only") {
    return "border-border-soft bg-surface-primary font-normal text-text-muted";
  }

  if (role === "Admin") {
    return "border-border-primary bg-surface-primary font-medium text-text-secondary";
  }

  return "border-border-soft bg-surface-primary font-normal text-text-secondary";
}

function inputClass(isEditable: boolean) {
  return [
    "h-11 w-full rounded-[10px] border px-3 text-sm outline-none transition-colors",
    isEditable
      ? "border-border-soft bg-bg-secondary text-text-primary focus:border-border-primary"
      : "cursor-not-allowed border-border-soft bg-bg-secondary text-text-disabled",
  ].join(" ");
}

export function ProfilePage() {
  const [currentUserRole] = useState<UserRole>("Admin");
  const canManageProject = currentUserRole === "Owner" || currentUserRole === "Admin";

  const [projectName, setProjectName] = useState("KIRA EU Regulatory Program");
  const [clientNumber, setClientNumber] = useState("CL-90314");
  const [cuid, setCuid] = useState("CUID-77A4-LX2");
  const [genAiEnabled, setGenAiEnabled] = useState(true);
  const [users, setUsers] = useState<ProjectUser[]>(initialUsers);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<UserRole>("Member");

  const roleOptions = useMemo<UserRole[]>(() => ["Owner", "Admin", "Member", "Read-Only"], []);

  const handleRoleChange = (id: string, nextRole: UserRole) => {
    if (!canManageProject) {
      return;
    }

    setUsers((previousUsers) =>
      previousUsers.map((user) => (user.id === id ? { ...user, role: nextRole } : user))
    );
  };

  const handleRemoveUser = (id: string) => {
    if (!canManageProject) {
      return;
    }

    setUsers((previousUsers) => previousUsers.filter((user) => user.id !== id));
  };

  const handleInvite = () => {
    if (!canManageProject || inviteEmail.trim().length === 0) {
      return;
    }

    const localPart = inviteEmail.split("@")[0] ?? "new.user";
    const generatedName = localPart
      .split(/[._-]/)
      .filter(Boolean)
      .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
      .join(" ");

    setUsers((previousUsers) => [
      ...previousUsers,
      {
        id: `U-${Date.now()}`,
        name: generatedName || "New User",
        email: inviteEmail.trim(),
        role: inviteRole,
        status: "Invited",
      },
    ]);

    setInviteEmail("");
    setInviteRole("Member");
    setInviteOpen(false);
  };

  return (
    <div className="mx-auto w-full max-w-[1100px] px-8 pb-20">
      <motion.section
        initial="hidden"
        animate="show"
        variants={fadeUp}
        transition={{ duration: 0.24 }}
        className="pt-12"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">Profile Settings</p>
        <h2 className="mt-4 text-[40px] font-semibold tracking-tight text-text-primary md:text-5xl">
          Project Configuration &amp; Access Control
        </h2>
        <p className="mt-4 max-w-3xl text-base leading-8 text-text-secondary">
          Manage project identity, AI capabilities, and user permissions.
        </p>
      </motion.section>

      <motion.section
        initial="hidden"
        animate="show"
        variants={fadeUp}
        transition={{ duration: 0.25 }}
        className="mt-12"
      >
        <section className="rounded-md border border-border-primary bg-surface-card p-8">
          <h3 className="text-xl font-semibold text-text-primary">Project Configuration</h3>

          <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="projectName" className="text-xs font-medium uppercase tracking-[0.08em] text-text-muted">
                Project Name
              </label>
              <input
                id="projectName"
                value={projectName}
                onChange={(event) => setProjectName(event.target.value)}
                disabled={!canManageProject}
                className={inputClass(canManageProject)}
              />
              <p className="text-xs text-text-muted">Primary compliance workspace identifier.</p>
            </div>

            <div className="space-y-2">
              <label htmlFor="clientNumber" className="text-xs font-medium uppercase tracking-[0.08em] text-text-muted">
                Client Number
              </label>
              <input
                id="clientNumber"
                value={clientNumber}
                onChange={(event) => setClientNumber(event.target.value)}
                disabled={!canManageProject}
                className={inputClass(canManageProject)}
              />
              <p className="text-xs text-text-muted">Linked commercial account record.</p>
            </div>

            <div className="space-y-2 lg:col-span-2">
              <label htmlFor="cuid" className="text-xs font-medium uppercase tracking-[0.08em] text-text-muted">
                CUID
              </label>
              <input
                id="cuid"
                value={cuid}
                onChange={(event) => setCuid(event.target.value)}
                disabled={!canManageProject}
                className={inputClass(canManageProject)}
              />
              <p className="text-xs text-text-muted">Compliance unit identifier for audit traceability.</p>
            </div>
          </div>

          <div className="mt-6 rounded-md border border-border-soft bg-surface-primary p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h4 className="text-sm font-semibold text-text-primary">Enable Gen AI Processing</h4>
                <p className="mt-2 max-w-2xl text-sm text-text-secondary">
                  Allow AI-powered regulatory parsing and impact modeling for this project.
                </p>
              </div>

              <Switch.Root
                checked={genAiEnabled}
                onCheckedChange={setGenAiEnabled}
                disabled={!canManageProject}
                aria-label="Enable Gen AI Processing"
                className={[
                  "relative h-7 w-12 rounded-full border transition-colors",
                  genAiEnabled
                    ? "border-border-primary bg-surface-elevated"
                    : "border-border-soft bg-bg-secondary",
                  canManageProject ? "cursor-pointer" : "cursor-not-allowed opacity-60",
                ].join(" ")}
              >
                <Switch.Thumb
                  className={[
                    "block h-5 w-5 translate-x-1 rounded-full transition-transform",
                    genAiEnabled ? "translate-x-6 bg-text-primary" : "bg-surface-elevated",
                  ].join(" ")}
                />
              </Switch.Root>
            </div>
          </div>
        </section>
      </motion.section>

      <motion.section
        initial="hidden"
        animate="show"
        variants={fadeUp}
        transition={{ duration: 0.26 }}
        className="mt-16"
      >
        <section className="rounded-md border border-border-primary bg-surface-card p-8">
          <header className="flex flex-wrap items-center justify-between gap-4">
            <h3 className="text-xl font-semibold text-text-primary">Users in This Project</h3>

            <Dialog.Root open={inviteOpen} onOpenChange={setInviteOpen}>
              <Dialog.Trigger asChild>
                <button
                  type="button"
                  disabled={!canManageProject}
                  className={[
                    "rounded-[10px] border border-border-primary bg-surface-elevated px-4 py-2 text-sm text-text-primary transition-opacity",
                    canManageProject ? "hover:opacity-90" : "cursor-not-allowed text-text-disabled opacity-70",
                  ].join(" ")}
                >
                  Invite User
                </button>
              </Dialog.Trigger>

              <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 z-40 bg-bg-primary/70" />
                <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[92vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-md border border-border-primary bg-surface-card p-6">
                  <Dialog.Title className="text-lg font-semibold text-text-primary">Invite User</Dialog.Title>
                  <Dialog.Description className="mt-2 text-sm text-text-secondary">
                    Add a user to this project with a predefined role.
                  </Dialog.Description>

                  <div className="mt-6 space-y-4">
                    <div className="space-y-2">
                      <label htmlFor="invite-email" className="text-xs font-medium uppercase tracking-[0.08em] text-text-muted">
                        Email
                      </label>
                      <input
                        id="invite-email"
                        type="email"
                        value={inviteEmail}
                        onChange={(event) => setInviteEmail(event.target.value)}
                        placeholder="name@company.com"
                        className="h-11 w-full rounded-[10px] border border-border-soft bg-bg-secondary px-3 text-sm text-text-primary outline-none transition-colors focus:border-border-primary"
                      />
                    </div>

                    <div className="space-y-2">
                      <label htmlFor="invite-role" className="text-xs font-medium uppercase tracking-[0.08em] text-text-muted">
                        Role
                      </label>
                      <select
                        id="invite-role"
                        value={inviteRole}
                        onChange={(event) => setInviteRole(event.target.value as UserRole)}
                        className="h-11 w-full rounded-[10px] border border-border-soft bg-bg-secondary px-3 text-sm text-text-primary outline-none transition-colors focus:border-border-primary"
                      >
                        {roleOptions.map((roleOption) => (
                          <option key={roleOption} value={roleOption}>
                            {roleOption}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="mt-6 flex items-center justify-end gap-3">
                    <Dialog.Close asChild>
                      <button
                        type="button"
                        className="rounded-[10px] border border-border-primary bg-transparent px-4 py-2 text-sm text-text-secondary transition-opacity hover:opacity-90"
                      >
                        Cancel
                      </button>
                    </Dialog.Close>
                    <button
                      type="button"
                      onClick={handleInvite}
                      className="rounded-[10px] border border-border-primary bg-surface-elevated px-4 py-2 text-sm text-text-primary transition-opacity hover:opacity-90"
                    >
                      Invite
                    </button>
                  </div>
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>
          </header>

          <div className="mt-6 hidden overflow-x-auto lg:block">
            <table className="min-w-full border-separate border-spacing-y-2">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.08em] text-text-muted">
                  <th className="rounded-l-md bg-surface-primary px-4 py-3">Name</th>
                  <th className="bg-surface-primary px-4 py-3">Email</th>
                  <th className="bg-surface-primary px-4 py-3">Role</th>
                  <th className="bg-surface-primary px-4 py-3">Status</th>
                  <th className="rounded-r-md bg-surface-primary px-4 py-3">Actions</th>
                </tr>
              </thead>

              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="text-sm text-text-secondary">
                    <td className="rounded-l-md border border-border-soft border-r-0 bg-bg-secondary px-4 py-3 font-medium text-text-primary">
                      {user.name}
                    </td>
                    <td className="border border-border-soft border-l-0 border-r-0 bg-bg-secondary px-4 py-3">{user.email}</td>
                    <td className="border border-border-soft border-l-0 border-r-0 bg-bg-secondary px-4 py-3">
                      <span className={["inline-flex rounded-md border px-2.5 py-1 text-xs", roleBadgeClass(user.role)].join(" ")}>
                        {user.role}
                      </span>
                    </td>
                    <td className="border border-border-soft border-l-0 border-r-0 bg-bg-secondary px-4 py-3 text-text-secondary">
                      {user.status}
                    </td>
                    <td className="rounded-r-md border border-border-soft border-l-0 bg-bg-secondary px-4 py-3">
                      <div className="flex items-center gap-2">
                        <select
                          value={user.role}
                          onChange={(event) => handleRoleChange(user.id, event.target.value as UserRole)}
                          disabled={!canManageProject}
                          className={[
                            "h-9 rounded-[10px] border border-border-soft bg-surface-primary px-2 text-xs outline-none transition-colors",
                            canManageProject
                              ? "text-text-primary focus:border-border-primary"
                              : "cursor-not-allowed text-text-disabled",
                          ].join(" ")}
                        >
                          {roleOptions.map((roleOption) => (
                            <option key={roleOption} value={roleOption}>
                              {roleOption}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          onClick={() => handleRemoveUser(user.id)}
                          disabled={!canManageProject}
                          className={[
                            "h-9 rounded-[10px] border border-border-primary bg-transparent px-3 text-xs",
                            canManageProject
                              ? "text-text-muted transition-opacity hover:opacity-90"
                              : "cursor-not-allowed text-text-disabled",
                          ].join(" ")}
                        >
                          Remove User
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 space-y-4 lg:hidden">
            {users.map((user) => (
              <article key={user.id} className="rounded-md border border-border-soft bg-bg-secondary p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-text-primary">{user.name}</p>
                    <p className="mt-1 text-xs text-text-secondary">{user.email}</p>
                  </div>
                  <span className={["inline-flex rounded-md border px-2.5 py-1 text-xs", roleBadgeClass(user.role)].join(" ")}>
                    {user.role}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-xs uppercase tracking-[0.08em] text-text-muted">Status</p>
                    <p className="mt-2 text-sm text-text-secondary">{user.status}</p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-[0.08em] text-text-muted">Change Role</p>
                    <select
                      value={user.role}
                      onChange={(event) => handleRoleChange(user.id, event.target.value as UserRole)}
                      disabled={!canManageProject}
                      className={[
                        "mt-2 h-10 w-full rounded-[10px] border border-border-soft bg-surface-primary px-2 text-xs outline-none transition-colors",
                        canManageProject
                          ? "text-text-primary focus:border-border-primary"
                          : "cursor-not-allowed text-text-disabled",
                      ].join(" ")}
                    >
                      {roleOptions.map((roleOption) => (
                        <option key={roleOption} value={roleOption}>
                          {roleOption}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleRemoveUser(user.id)}
                  disabled={!canManageProject}
                  className={[
                    "mt-4 h-10 rounded-[10px] border border-border-primary px-4 text-xs",
                    canManageProject
                      ? "bg-transparent text-text-muted transition-opacity hover:opacity-90"
                      : "cursor-not-allowed bg-transparent text-text-disabled",
                  ].join(" ")}
                >
                  Remove User
                </button>
              </article>
            ))}
          </div>
        </section>
      </motion.section>
    </div>
  );
}
