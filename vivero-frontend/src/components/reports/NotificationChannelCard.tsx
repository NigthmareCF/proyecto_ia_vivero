type Props = {
  config: any;
};

export function NotificationChannelCard({ config }: Props) {
  return (
    <article className="rounded-3xl border border-ink/10 bg-white p-4">
      <p className="font-semibold">{config.channel}</p>
      <p className="text-sm text-moss">{config.contactValue}</p>
      <p className="mt-2 text-xs uppercase tracking-[0.16em]">{config.active ? "Activo" : "Inactivo"}</p>
    </article>
  );
}
