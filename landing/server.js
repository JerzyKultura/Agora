import express from 'express'
import cors from 'cors'
import { readFileSync, writeFileSync, existsSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const EMAILS_FILE = join(__dirname, '.data', 'emails.json')
const ADMIN_KEY = process.env.ADMIN_KEY || 'agora-admin-secret'

const app = express()
const PORT = 3001

app.use(cors())
app.use(express.json())

function readEmails() {
  if (!existsSync(EMAILS_FILE)) {
    writeFileSync(EMAILS_FILE, JSON.stringify([], null, 2))
    return []
  }
  try {
    const data = readFileSync(EMAILS_FILE, 'utf-8')
    return JSON.parse(data)
  } catch {
    return []
  }
}

function saveEmails(emails) {
  writeFileSync(EMAILS_FILE, JSON.stringify(emails, null, 2))
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

app.post('/api/signup', (req, res) => {
  const { email } = req.body

  if (!email || typeof email !== 'string') {
    return res.status(400).json({ error: 'Email is required.' })
  }

  const trimmed = email.trim().toLowerCase()

  if (!isValidEmail(trimmed)) {
    return res.status(400).json({ error: 'Please enter a valid email address.' })
  }

  const emails = readEmails()

  if (emails.some((entry) => entry.email === trimmed)) {
    return res.status(409).json({ error: 'This email is already on the waitlist!' })
  }

  emails.push({
    email: trimmed,
    timestamp: new Date().toISOString(),
  })

  saveEmails(emails)

  console.log(`[Beta Signup] New signup: ${trimmed} (total: ${emails.length})`)

  return res.json({ message: "You're on the list! We'll be in touch soon." })
})

app.get('/api/emails', (req, res) => {
  const key = req.headers['x-admin-key']
  if (!key || key !== ADMIN_KEY) {
    return res.status(401).json({ error: 'Unauthorized. Provide a valid X-Admin-Key header.' })
  }
  const emails = readEmails()
  return res.json({ count: emails.length, emails })
})

app.listen(PORT, () => {
  console.log(`[Agora Landing] Email server running on http://localhost:${PORT}`)
})
