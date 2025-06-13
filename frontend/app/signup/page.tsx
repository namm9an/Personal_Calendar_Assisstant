"use client";

import AuthForm from "@/components/AuthForm";

export default function SignupPage() {
  return (
    <main className="flex items-center justify-center min-h-screen">
      <AuthForm mode="signup" />
    </main>
  );
}
