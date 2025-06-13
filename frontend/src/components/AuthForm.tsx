"use client";

import { useState, ChangeEvent } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FloatingLabelInput } from "@/components/ui/FloatingLabelInput";
import { Loader2 } from "lucide-react";

interface AuthFormProps {
  mode: "login" | "signup";
}

export default function AuthForm({ mode }: AuthFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      let endpoint: string;
      let options: RequestInit;

      if (mode === "login") {
        endpoint = "/api/v1/auth/login";
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        options = {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData,
          credentials: "include",
        };
      } else {
        // signup
        endpoint = "/api/v1/auth/signup";
        options = {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name: name }),
          credentials: "include",
        };
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}${endpoint}`,
        options
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Authentication failed");
      }

      window.location.href = "/"; // Redirect to dashboard
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-md mx-4"
    >
      <Card className="bg-black/20 backdrop-blur-lg border border-white/20 text-white shadow-2xl shadow-black/50">
        <form onSubmit={handleSubmit}>
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white to-neutral-300">
              {mode === "login" ? "Welcome Back" : "Create Account"}
            </CardTitle>
            <CardDescription className="text-neutral-400 pt-1">
              {mode === "login"
                ? "Enter your credentials to continue."
                : "Join us and start organizing."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 pt-2">
            {error && (
              <div className="bg-destructive/20 border border-destructive/50 p-3 rounded-md flex items-center gap-x-2 text-sm text-destructive-foreground">
                <p>{error}</p>
              </div>
            )}
            {mode === "signup" && (
              <FloatingLabelInput
                id="name"
                label="Name"
                value={name}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
                required
                disabled={isLoading}
              />
            )}
            <FloatingLabelInput
              id="email"
              label="Email"
              type="email"
              value={email}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
            <FloatingLabelInput
              id="password"
              label="Password"
              type="password"
              value={password}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              className="w-full h-12 text-lg font-bold text-white bg-gradient-to-r from-primary to-secondary transition-all duration-300 ease-out hover:scale-105 hover:shadow-lg hover:shadow-primary/50 disabled:opacity-50"
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="animate-spin" />
              ) : mode === "login" ? (
                "Sign In"
              ) : (
                "Create Account"
              )}
            </Button>
            <div className="text-center text-sm text-neutral-400">
              {mode === "login" ? (
                <p>
                  Don't have an account?{" "}
                  <Link
                    href="/signup"
                    className="font-semibold text-accent-foreground hover:underline"
                  >
                    Sign up
                  </Link>
                </p>
              ) : (
                <p>
                  Already have an account?{" "}
                  <Link
                    href="/login"
                    className="font-semibold text-accent-foreground hover:underline"
                  >
                    Log in
                  </Link>
                </p>
              )}
            </div>
          </CardFooter>
        </form>
      </Card>
    </motion.div>
  );
}