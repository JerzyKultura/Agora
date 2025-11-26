export const config = {
  supabase: {
    url: import.meta.env.VITE_SUPABASE_URL || 'https://iaxukinontzmlwoikdwj.supabase.co',
    anonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlheHVraW5vbnR6bWx3b2lrZHdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxMTEzNTUsImV4cCI6MjA3OTY4NzM1NX0.XggVqy0YNhVkpav5jBU4lBV_G8Rf4uUpyc4r2bxPVrY'
  }
}
