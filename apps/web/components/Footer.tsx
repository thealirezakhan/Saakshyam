export function Footer() {
  return (
    <footer className="relative z-10 w-full bg-surface-container-lowest/80 backdrop-blur-md py-space-sm mt-auto">
      <div className="max-w-7xl mx-auto px-margin-mobile lg:px-margin flex flex-col sm:flex-row items-center justify-between gap-space-xs font-label-sm text-label-sm text-on-surface-variant">
        <div className="flex items-center gap-space-sm">
          <span>Institutional AI Assistant</span>
          <span>•</span>
          <span>Autonomous Audit Mesh</span>
        </div>
        <div>© 2025 AICTE Regulatory Governance. All rights reserved.</div>
      </div>
    </footer>
  );
}
