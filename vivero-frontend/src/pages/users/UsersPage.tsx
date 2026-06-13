import { useEffect, useMemo, useState } from "react";
import { deleteUser, getUsers, updateUser, updateUserPassword } from "../../api/usersApi";

type UserRow = {
  id: number;
  firstName: string;
  lastName: string;
  fullName: string;
  email: string;
  phoneNumber?: string | null;
  role: "ADMIN" | "CONTROLLER" | "VIEWER";
  active: boolean;
};

type DraftsState = Record<number, { password: string }>;

export function UsersPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [drafts, setDrafts] = useState<Record<number, Partial<UserRow>>>({});
  const [passwordDrafts, setPasswordDrafts] = useState<DraftsState>({});
  const [saving, setSaving] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getUsers()
      .then((data) => {
        setUsers(data ?? []);
        const nextDrafts: Record<number, Partial<UserRow>> = {};
        const nextPasswords: DraftsState = {};
        (data ?? []).forEach((user: UserRow) => {
          nextDrafts[user.id] = { ...user };
          nextPasswords[user.id] = { password: "" };
        });
        setDrafts(nextDrafts);
        setPasswordDrafts(nextPasswords);
      })
      .catch(() => {
        setUsers([]);
        setError("No fue posible cargar usuarios.");
      });
  }, []);

  const totalByRole = useMemo(() => {
    return users.reduce(
      (acc, user) => {
        acc[user.role] = (acc[user.role] ?? 0) + 1;
        return acc;
      },
      { ADMIN: 0, CONTROLLER: 0, VIEWER: 0 } as Record<UserRow["role"], number>
    );
  }, [users]);

  async function saveUser(userId: number) {
    const draft = drafts[userId];
    if (!draft) return;
    setSaving(userId);
    setError(null);
    try {
      const updated = await updateUser(userId, {
        firstName: String(draft.firstName ?? "").trim(),
        lastName: String(draft.lastName ?? "").trim(),
        email: String(draft.email ?? "").trim(),
        phoneNumber: draft.phoneNumber ?? null,
        role: draft.role ?? null,
        active: draft.active ?? null,
      });
      setUsers((current) => current.map((user) => (user.id === userId ? updated : user)));
    } catch (err) {
      setError("No fue posible guardar el usuario.");
      console.error(err);
    } finally {
      setSaving(null);
    }
  }

  async function savePassword(userId: number) {
    const password = passwordDrafts[userId]?.password?.trim();
    if (!password) return;
    setSaving(userId);
    setError(null);
    try {
      await updateUserPassword(userId, password);
      setPasswordDrafts((current) => ({ ...current, [userId]: { password: "" } }));
    } catch (err) {
      setError("No fue posible actualizar la contraseña.");
      console.error(err);
    } finally {
      setSaving(null);
    }
  }

  async function removeUser(userId: number) {
    if (!confirm("Eliminar este usuario?")) return;
    setSaving(userId);
    setError(null);
    try {
      await deleteUser(userId);
      setUsers((current) => current.filter((user) => user.id !== userId));
    } catch (err) {
      setError("No fue posible eliminar el usuario.");
      console.error(err);
    } finally {
      setSaving(null);
    }
  }

  return (
    <section className="space-y-6 rounded-[2rem] bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl">Usuarios</h2>
          <p className="text-moss">Edicion de nombre, correo, rol, estado y contraseña.</p>
        </div>
        <div className="text-sm text-moss">
          ADMIN {totalByRole.ADMIN} · CONTROLLER {totalByRole.CONTROLLER} · VIEWER {totalByRole.VIEWER}
        </div>
      </div>

      {error && <p className="rounded-2xl bg-alert/10 p-3 text-sm text-alert">{error}</p>}

      <div className="grid gap-4">
        {users.map((user) => {
          const draft = drafts[user.id] ?? user;
          const password = passwordDrafts[user.id]?.password ?? "";
          return (
            <article key={user.id} className="rounded-[1.75rem] border border-ink/10 p-4">
              <div className="grid gap-4 lg:grid-cols-[1.3fr_1fr_1fr_auto]">
                <div className="grid gap-3">
                  <input
                    className="rounded-2xl border border-ink/10 px-4 py-3"
                    value={draft.firstName ?? ""}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [user.id]: { ...current[user.id], firstName: event.target.value },
                      }))
                    }
                    placeholder="Nombre"
                  />
                  <input
                    className="rounded-2xl border border-ink/10 px-4 py-3"
                    value={draft.lastName ?? ""}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [user.id]: { ...current[user.id], lastName: event.target.value },
                      }))
                    }
                    placeholder="Apellido"
                  />
                </div>

                <div className="grid gap-3">
                  <input
                    className="rounded-2xl border border-ink/10 px-4 py-3"
                    value={draft.email ?? ""}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [user.id]: { ...current[user.id], email: event.target.value },
                      }))
                    }
                    placeholder="Correo"
                  />
                  <input
                    className="rounded-2xl border border-ink/10 px-4 py-3"
                    value={draft.phoneNumber ?? ""}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [user.id]: { ...current[user.id], phoneNumber: event.target.value },
                      }))
                    }
                    placeholder="Telefono"
                  />
                </div>

                <div className="grid gap-3">
                  <select
                    className="rounded-2xl border border-ink/10 px-4 py-3"
                    value={draft.role ?? "VIEWER"}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [user.id]: { ...current[user.id], role: event.target.value as UserRow["role"] },
                      }))
                    }
                  >
                    <option value="ADMIN">ADMIN</option>
                    <option value="CONTROLLER">CONTROLLER</option>
                    <option value="VIEWER">VIEWER</option>
                  </select>
                  <label className="flex items-center gap-3 rounded-2xl border border-ink/10 px-4 py-3">
                    <input
                      type="checkbox"
                      checked={Boolean(draft.active)}
                      onChange={(event) =>
                        setDrafts((current) => ({
                          ...current,
                          [user.id]: { ...current[user.id], active: event.target.checked },
                        }))
                      }
                    />
                    <span className="text-sm">Activo</span>
                  </label>
                </div>

                <div className="grid gap-3">
                  <button
                    type="button"
                    onClick={() => saveUser(user.id)}
                    disabled={saving === user.id}
                    className="rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                  >
                    Guardar perfil
                  </button>
                  <button
                    type="button"
                    onClick={() => removeUser(user.id)}
                    disabled={saving === user.id}
                    className="rounded-2xl bg-alert px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                  >
                    Eliminar
                  </button>
                </div>
              </div>

              <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_auto]">
                <input
                  className="rounded-2xl border border-ink/10 px-4 py-3"
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPasswordDrafts((current) => ({
                      ...current,
                      [user.id]: { password: event.target.value },
                    }))
                  }
                  placeholder="Nueva contraseña"
                />
                <button
                  type="button"
                  onClick={() => savePassword(user.id)}
                  disabled={saving === user.id || !password.trim()}
                  className="rounded-2xl bg-clay px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                >
                  Cambiar contraseña
                </button>
              </div>

              <div className="mt-3 text-sm text-moss">
                {user.fullName} · {user.email} · {user.role} · {user.active ? "activo" : "inactivo"}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
