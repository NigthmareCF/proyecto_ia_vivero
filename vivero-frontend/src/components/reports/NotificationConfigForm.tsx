import { NotificationChannelCard } from "./NotificationChannelCard";

type Props = {
  configs: any[];
};

export function NotificationConfigForm({ configs }: Props) {
  return (
    <section className="grid gap-4 md:grid-cols-2">
      {configs.map((config) => (
        <NotificationChannelCard key={config.channel} config={config} />
      ))}
    </section>
  );
}
