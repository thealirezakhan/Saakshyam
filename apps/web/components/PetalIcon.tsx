export function PetalIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 2C13.2 5.8 14.5 7.1 18.3 8.3C14.5 9.5 13.2 10.8 12 14.6C10.8 10.8 9.5 9.5 5.7 8.3C9.5 7.1 10.8 5.8 12 2Z" />
      <path
        d="M17.5 14C18.2 16.3 19 17 21.3 17.7C19 18.4 18.2 19.1 17.5 21.4C16.8 19.1 16 18.4 13.7 17.7C16 17 16.8 16.3 17.5 14Z"
        opacity="0.8"
      />
      <path
        d="M6.5 14C7.2 16.3 8 17 10.3 17.7C8 18.4 7.2 19.1 6.5 21.4C5.8 19.1 5 18.4 2.7 17.7C5 17 5.8 16.3 6.5 14Z"
        opacity="0.8"
      />
    </svg>
  );
}
