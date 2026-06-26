import './globals.css';
import Link from 'next/link';

const nav = [
  ['Dashboard', '/'], ['Templates', '/templates'], ['Agent Packs', '/packs'], ['Workflow Designer', '/workflow'], ['Run Console', '/runs'],
  ['Trace Viewer', '/traces'], ['Evaluation Lab', '/evals'], ['Approvals', '/approvals'], ['Tools', '/tools'],
  ['Memory', '/memory'], ['Settings', '/settings'], ['Docs', '/docs']
];

export const metadata = { title: 'AgentForge Studio v2', description: 'Self-hosted multi-agent system builder' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>
    <div className="flex min-h-screen">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-slate-800 bg-slate-950/95 p-5 lg:block">
        <div className="mb-8">
          <div className="text-xl font-bold">AgentForge Studio</div>
          <div className="text-xs text-slate-400">v2 · Self-hosted AgentOps platform</div>
        </div>
        <nav className="space-y-1">
          {nav.map(([label, href]) => <Link key={href} href={href} className="block rounded-xl px-3 py-2 text-sm text-slate-300 hover:bg-slate-900 hover:text-white">{label}</Link>)}
        </nav>
        <div className="absolute bottom-5 left-5 right-5 rounded-2xl border border-slate-800 bg-slate-900 p-4 text-xs text-slate-400">
          Queue-backed runs, keyword memory, policy traces, and local-first safety.
        </div>
      </aside>
      <main className="flex-1 p-4 lg:ml-72 lg:p-8">
        <header className="mb-8 flex flex-col gap-4 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 to-slate-950 p-5 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-3xl font-bold">AgentForge Studio v2</div>
            <div className="text-slate-400">Build, run, trace, approve, evaluate, and extend agent teams locally.</div>
          </div>
          <div className="flex gap-2"><span className="badge-green">Local-first</span><span className="badge">Queue-backed</span></div>
        </header>
        {children}
      </main>
    </div>
  </body></html>;
}
