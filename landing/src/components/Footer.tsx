export default function Footer() {
  return (
    <footer className="border-t border-white/5 py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Logo & tagline */}
          <div className="flex items-center gap-3">
            <img src="/agora-logo.svg" alt="Agora" className="w-7 h-7" />
            <div>
              <span className="text-white font-semibold">Agora</span>
              <span className="text-gray-600 text-sm ml-3">Workflow Orchestration with Observability</span>
            </div>
          </div>

          {/* Links */}
          <div className="flex items-center gap-8">
            <a
              href="https://github.com/JerzyKultura/Agora"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-gray-500 hover:text-white transition-colors duration-200"
            >
              GitHub
            </a>
            <a
              href="#features"
              className="text-sm text-gray-500 hover:text-white transition-colors duration-200"
            >
              Features
            </a>
            <a
              href="#quickstart"
              className="text-sm text-gray-500 hover:text-white transition-colors duration-200"
            >
              Quick Start
            </a>
            <a
              href="#beta"
              className="text-sm text-gray-500 hover:text-white transition-colors duration-200"
            >
              Beta
            </a>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-white/5 text-center">
          <p className="text-xs text-gray-600">
            &copy; {new Date().getFullYear()} Agora. Open source under the MIT License.
          </p>
        </div>
      </div>
    </footer>
  )
}
