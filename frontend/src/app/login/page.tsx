"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import AuthForm from "../../components/AuthForm";
import { useAuth } from "../../context/AuthContext";

export default function LoginPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If user is already logged in, redirect to dashboard
    if (user && !loading) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center">
      <div className="max-w-md w-full mx-auto">
        <AuthForm mode="login" />
      </div>
    </div>
  );
} 