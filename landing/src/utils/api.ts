export async function submitBetaSignup(email: string): Promise<{ success: boolean; message: string }> {
  try {
    const res = await fetch('/api/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    const data = await res.json();

    if (!res.ok) {
      return { success: false, message: data.error || 'Something went wrong. Please try again.' };
    }

    return { success: true, message: data.message || 'You\'re on the list!' };
  } catch {
    return { success: false, message: 'Network error. Please try again later.' };
  }
}

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
