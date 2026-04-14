import { useEffect, useState } from "react";
import { getUsers } from "../../api/usersApi";

export function UsersPage() {
  const [users, setUsers] = useState<any[]>([]);

  useEffect(() => {
    getUsers().then(setUsers).catch(() => setUsers([]));
  }, []);

  return (
    <section className="rounded-[2rem] bg-white p-6 shadow-sm">
      <h2 className="font-display text-3xl">Usuarios</h2>
      <div className="mt-4 space-y-3">
        {users.map((user) => (
          <article key={user.id} className="rounded-3xl border border-ink/10 p-4">
            <p className="font-semibold">{user.fullName ?? user.email}</p>
            <p className="text-sm text-moss">{user.role}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
