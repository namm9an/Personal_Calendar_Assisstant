"use client";

import { useRouter } from "next/navigation";

export interface User {
  id: string;
  email: string;
  name?: string;
  timezone?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

/**
 * Helper for making authenticated fetch requests
 */
export async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  
  // Always include credentials for auth cookies
  const fetchOptions: RequestInit = {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  };

  const response = await fetch(url, fetchOptions);

  // Handle common auth errors
  if (response.status === 401) {
    // Try to refresh the token if unauthorized
    try {
      const refreshed = await refreshToken();
      if (refreshed) {
        // Retry the original request with new token
        return fetchWithAuth<T>(endpoint, options);
      }
    } catch (error) {
      // If refresh fails, redirect to login
      window.location.href = "/login";
      throw new Error("Authentication failed. Please login again.");
    }
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Request failed");
  }

  return response.json();
}

/**
 * Login with email and password
 */
export async function login(email: string, password: string): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append("username", email); // OAuth2 spec uses 'username'
  formData.append("password", password);

  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Login failed");
  }

  return response.json();
}

/**
 * Signup with email and password
 */
export async function signup(
  email: string,
  password: string,
  name?: string
): Promise<AuthResponse> {
  const body = { email, password };
  if (name) {
    Object.assign(body, { name });
  }

  const response = await fetch(`${API_URL}/api/v1/auth/signup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Signup failed");
  }

  return response.json();
}

/**
 * Logout the current user
 */
export async function logout(): Promise<void> {
  await fetch(`${API_URL}/api/v1/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
  
  // Redirect to login page
  window.location.href = "/login";
}

/**
 * Get the current user profile
 */
export async function getProfile(): Promise<User> {
  try {
    return await fetchWithAuth<User>("/api/v1/auth/me");
  } catch (error) {
    throw new Error("Failed to get user profile");
  }
}

/**
 * Refresh the access token
 */
export async function refreshToken(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) {
      return false;
    }

    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Custom hook for auth actions
 */
export function useAuth() {
  const router = useRouter();

  return {
    login: async (email: string, password: string) => {
      const result = await login(email, password);
      router.push("/dashboard");
      return result;
    },
    signup: async (email: string, password: string, name?: string) => {
      const result = await signup(email, password, name);
      router.push("/dashboard");
      return result;
    },
    logout: async () => {
      await logout();
      router.push("/login");
    },
    getProfile,
    refreshToken,
    fetchWithAuth,
  };
} 