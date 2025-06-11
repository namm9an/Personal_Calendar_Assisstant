"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import { User, getProfile } from "../lib/auth";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  error: null,
  setUser: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  // Fetch user profile on mount
  useEffect(() => {
    const publicPaths = ["/login", "/signup", "/"];
    const isPublicPath = publicPaths.includes(pathname);

    async function loadUserProfile() {
      try {
        setLoading(true);
        const userData = await getProfile();
        setUser(userData);
      } catch (err) {
        setError("Authentication failed");
        setUser(null);
        
        // Redirect to login if not on a public path
        if (!isPublicPath) {
          router.push("/login");
        }
      } finally {
        setLoading(false);
      }
    }

    loadUserProfile();
  }, [pathname, router]);

  return (
    <AuthContext.Provider value={{ user, loading, error, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
} 