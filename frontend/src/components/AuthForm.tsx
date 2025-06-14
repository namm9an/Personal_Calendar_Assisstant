"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FloatingLabelInput } from "@/components/ui/FloatingLabelInput";

const MotionDiv = motion.div;

interface AuthFormProps {
  mode: "login" | "signup";
}

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (mode === "login") {
        // Login API call would go here
        console.log("Login with", { email, password });
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        router.push("/dashboard");
      } else {
        // Signup API call would go here
        console.log("Signup with", { name, email, password });
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        router.push("/dashboard");
      }
    } catch (err) {
      console.error("Auth error:", err);
      setError("Authentication failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MotionDiv
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-md mx-auto"
    >
      <Card className="glass-card border-gradient-br">
        <CardHeader className="space-y-2">
          <CardTitle className="text-center text-2xl">
            {mode === "login" ? "Welcome Back" : "Create Account"}
          </CardTitle>
          <CardDescription className="text-center">
            {mode === "login"
              ? "Enter your credentials to access your account"
              : "Fill in your details to get started"}
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6">
            {error && (
              <MotionDiv
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="p-3 rounded-md bg-destructive/20 border border-destructive/50 text-white text-sm"
              >
                {error}
              </MotionDiv>
            )}

            {mode === "signup" && (
              <FloatingLabelInput
                id="name"
                label="Full Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoComplete="name"
                className="w-full"
              />
            )}

            <FloatingLabelInput
              id="email"
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full"
            />

            <FloatingLabelInput
              id="password"
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              className="w-full"
            />
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button 
              type="submit" 
              className="w-full relative overflow-hidden group" 
              variant="gradient"
              disabled={isLoading}
            >
              <span className="relative z-10">
                {isLoading
                  ? "Processing..."
                  : mode === "login"
                  ? "Log In"
                  : "Sign Up"}
              </span>
              <span className="absolute inset-0 w-full h-full bg-white/20 animate-shine" />
            </Button>

            <div className="text-sm text-center text-white/70">
              {mode === "login" ? (
                <>
                  Don't have an account?{" "}
                  <Link href="/signup" className="text-primary hover:text-primary-light underline underline-offset-4">
                    Sign up
                  </Link>
                </>
              ) : (
                <>
                  Already have an account?{" "}
                  <Link href="/login" className="text-primary hover:text-primary-light underline underline-offset-4">
                    Log in
                  </Link>
                </>
              )}
            </div>
          </CardFooter>
        </form>
      </Card>
    </MotionDiv>
  );
}