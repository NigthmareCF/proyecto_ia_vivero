type Props = {
  provider: "GOOGLE" | "APPLE";
  onClick: () => void;
};

export function SocialLoginButton({ provider, onClick }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-2xl border border-ink/15 bg-white px-4 py-3 text-sm font-semibold text-ink shadow-sm"
    >
      Entrar con {provider}
    </button>
  );
}
