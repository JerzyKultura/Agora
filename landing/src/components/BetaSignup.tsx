import { useState, type FormEvent } from 'react'
import { submitBetaSignup, isValidEmail } from '../utils/api'

export default function BetaSignup() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    if (!isValidEmail(email)) {
      setStatus('error')
      setMessage('Please enter a valid email address.')
      return
    }

    setStatus('loading')
    const result = await submitBetaSignup(email)

    if (result.success) {
      setStatus('success')
      setMessage(result.message)
      setEmail('')
    } else {
      setStatus('error')
      setMessage(result.message)
    }
  }

  return (
    <section id="beta" className="relative py-32">
      <div className="max-w-3xl mx-auto px-6">
        <div className="animate-on-scroll">
          <div className="glass neon-border rounded-3xl p-10 sm:p-14 text-center glow-violet relative overflow-hidden">
            {/* Background accent */}
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-neon-violet/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-neon-blue/10 rounded-full blur-3xl pointer-events-none" />

            <div className="relative">
              <div className="inline-block px-4 py-1.5 rounded-full glass text-xs font-medium text-neon-violet tracking-wide uppercase mb-6">
                Early Access
              </div>

              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Join the Agora Cloud{' '}
                <span className="gradient-text">Beta</span>
              </h2>

              <p className="text-gray-400 text-lg mb-10 max-w-lg mx-auto">
                Get early access to the hosted platform — workflow monitoring,
                execution visualization, and analytics in one dashboard.
              </p>

              {status === 'success' ? (
                <div className="py-6">
                  <div className="inline-flex items-center gap-3 px-6 py-3 rounded-xl bg-neon-cyan/10 border border-neon-cyan/20">
                    <svg className="w-5 h-5 text-neon-cyan" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span className="text-neon-cyan font-medium">{message}</span>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value)
                      if (status === 'error') setStatus('idle')
                    }}
                    placeholder="you@company.com"
                    className="flex-1 px-5 py-3.5 rounded-xl bg-dark-800 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-neon-violet/50 focus:ring-1 focus:ring-neon-violet/30 transition-all duration-200 font-mono text-sm"
                    disabled={status === 'loading'}
                  />
                  <button
                    type="submit"
                    disabled={status === 'loading'}
                    className="px-8 py-3.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-neon-violet to-neon-blue text-white hover:shadow-xl hover:shadow-neon-violet/25 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  >
                    {status === 'loading' ? (
                      <span className="flex items-center gap-2 justify-center">
                        <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
                          <path d="M12 2a10 10 0 019.95 9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className="opacity-75" />
                        </svg>
                        Submitting...
                      </span>
                    ) : (
                      'Request Access'
                    )}
                  </button>
                </form>
              )}

              {status === 'error' && (
                <p className="mt-3 text-sm text-red-400">{message}</p>
              )}

              <p className="mt-6 text-xs text-gray-600">
                No spam, ever. We'll only email you about the beta launch.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
