# Password Reset Guide

## Overview

Agora uses **Supabase Auth's built-in password reset** functionality. All password reset logic is handled client-side using the Supabase JavaScript client - no custom backend endpoints needed!

## User Flow

1. **Request Reset**: User enters email on `/forgot-password`
2. **Email Sent**: Supabase sends password reset email with magic link
3. **Click Link**: User clicks link (redirects to `/reset-password` with token in URL hash)
4. **Set New Password**: User enters new password
5. **Success**: Password updated, user redirected to login

## Implementation

### Frontend: Request Password Reset

**File**: `platform/frontend/src/pages/ForgotPassword.tsx`

```typescript
import { supabase } from '../lib/supabase'

const { error } = await supabase.auth.resetPasswordForEmail(email, {
  redirectTo: `${window.location.origin}/reset-password`,
})
```

**What happens:**
- Supabase sends email with reset link
- Link contains authentication token in URL hash
- User is redirected to your `/reset-password` page

### Frontend: Update Password

**File**: `platform/frontend/src/pages/ResetPassword.tsx`

```typescript
import { supabase } from '../lib/supabase'

// Supabase automatically reads the token from URL hash
const { error } = await supabase.auth.updateUser({
  password: newPassword
})
```

**What happens:**
- Supabase client automatically extracts token from URL
- Token authenticates the user temporarily
- Password is updated in Supabase Auth
- User can now login with new password

## Supabase Configuration

### 1. Configure Redirect URLs

In Supabase Dashboard → Authentication → URL Configuration:

**Site URL**: `http://localhost:5173` (development)
**Redirect URLs**: Add these URLs:
- `http://localhost:5173/reset-password` (development)
- `https://yourdomain.com/reset-password` (production)

### 2. Customize Email Template

In Supabase Dashboard → Authentication → Email Templates → Reset Password:

```html
<h2>Reset Your Password</h2>
<p>Click the link below to reset your password:</p>
<p><a href="{{ .ConfirmationURL }}">Reset Password</a></p>
<p>If you didn't request this, you can safely ignore this email.</p>
<p>This link expires in 1 hour.</p>
```

### 3. Email Settings

- **Enable email confirmations**: Optional (for new signups)
- **Token expiry**: Default 1 hour (configurable)
- **SMTP**: Use Supabase's built-in SMTP or configure custom

## Routes

Add these routes to `App.tsx`:

```typescript
<Route path="/forgot-password" element={<ForgotPassword />} />
<Route path="/reset-password" element={<ResetPassword />} />
```

Add link to Login page:

```typescript
<Link to="/forgot-password">Forgot password?</Link>
```

## Testing

### Manual Test Flow

1. **Start the app**:
   ```bash
   npm run dev
   ```

2. **Request reset**:
   - Go to `http://localhost:5173/login`
   - Click "Forgot password?"
   - Enter your email
   - Check email inbox

3. **Reset password**:
   - Click link in email
   - Should redirect to `/reset-password`
   - Enter new password (min 8 chars)
   - Confirm password
   - Click "Update Password"

4. **Login**:
   - Should redirect to `/login`
   - Login with new password
   - Should work!

### Edge Cases to Test

- **Non-existent email**: Should still show success (security)
- **Expired token**: Click old reset link → should show error
- **Passwords don't match**: Should show validation error
- **Password too short**: Should show "min 8 characters" error
- **Token already used**: Try using same link twice → should fail second time

## Security Features

✅ **Client-side only**: No backend endpoints = smaller attack surface
✅ **Token in URL hash**: Hash fragment never sent to server
✅ **One-time tokens**: Each reset link can only be used once
✅ **Time-limited**: Tokens expire after 1 hour
✅ **Supabase managed**: Token generation/validation handled by Supabase

## Troubleshooting

### Email not received

1. Check spam/junk folder
2. Verify email exists in Supabase users table
3. Check Supabase logs: Dashboard → Authentication → Logs
4. Verify SMTP settings (if using custom SMTP)

### "Invalid or expired reset token"

- Token expired (>1 hour old)
- Token already used
- **Solution**: Request new reset email

### Password not updating

1. Check browser console for errors
2. Verify Supabase client initialized correctly
3. Check Network tab for failed requests
4. Ensure redirect URL is whitelisted in Supabase

### Redirect not working

1. Verify redirect URL in Supabase settings
2. Check that URL matches exactly (including protocol)
3. Ensure `redirectTo` parameter is set correctly

## Production Checklist

- [ ] Update redirect URLs in Supabase to production domain
- [ ] Customize email template with branding
- [ ] Test email delivery in production
- [ ] Verify HTTPS is enforced
- [ ] Consider custom SMTP for better deliverability
- [ ] Set up email monitoring/alerts
- [ ] Test on multiple email providers (Gmail, Outlook, etc.)

## Why This Approach?

**Advantages over custom backend:**
- ✅ Less code to maintain
- ✅ Supabase handles security best practices
- ✅ Built-in token management
- ✅ Automatic email sending
- ✅ No backend endpoints to secure
- ✅ Faster implementation

**When you might need custom backend:**
- Custom email provider (not Supabase SMTP)
- Complex password policies
- Additional verification steps
- Custom audit logging

For most use cases, Supabase's built-in password reset is perfect!
