import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Features from './components/Features'
import Demo from './components/Demo'
import QuickStart from './components/QuickStart'
import BetaSignup from './components/BetaSignup'
import Footer from './components/Footer'
import { useScrollReveal } from './hooks/useScrollReveal'

export default function App() {
  useScrollReveal()
  return (
    <div className="min-h-screen bg-dark-900 bg-grid relative">
      {/* Background orbs */}
      <div className="orb w-[600px] h-[600px] bg-neon-blue/5 top-[-200px] left-[-200px] fixed" />
      <div className="orb w-[500px] h-[500px] bg-neon-violet/5 top-[40%] right-[-150px] fixed" style={{ animationDelay: '-7s' }} />
      <div className="orb w-[400px] h-[400px] bg-neon-cyan/5 bottom-[-100px] left-[30%] fixed" style={{ animationDelay: '-13s' }} />

      <Navbar />

      <main>
        <Hero />
        <Features />
        <Demo />
        <QuickStart />
        <BetaSignup />
      </main>

      <Footer />
    </div>
  )
}
