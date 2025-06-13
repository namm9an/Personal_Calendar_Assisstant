"use client";

import AuthForm from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <main className="flex items-center justify-center min-h-screen">
      <AuthForm mode="login" />
    </main>
  );
}
