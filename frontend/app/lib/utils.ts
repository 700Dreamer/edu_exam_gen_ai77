import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const API_BASE =
  typeof window !== "undefined"
    ? (window.location.port === "3000"
      ? `http://${window.location.hostname}:8000`
      : "")
    : "";

export const authFetch = async (url: string, options: RequestInit = {}) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("edulytics_token") : null;
  const headers = {
    ...options.headers,
    ...(token ? { "Authorization": `Bearer ${token}` } : {})
  };

  let fetchUrl = url;
  if (url.startsWith("/") && API_BASE) {
    fetchUrl = `${API_BASE}${url}`;
  }

  try {
    const response = await window.fetch(fetchUrl, { ...options, headers });
    if (response.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("edulytics_token");
        window.dispatchEvent(new Event("edulytics_logout"));
      }
    }
    return response;
  } catch (error) {
    console.warn(`[authFetch] Network error reaching ${fetchUrl}:`, error);
    return new Response(
      JSON.stringify({
        error: "Backend server unreachable. Ensure API backend on port 8000 is active.",
        insights: "<p class='text-xs text-red-500 italic'>Backend server unreachable. Ensure API backend on port 8000 is running and try again.</p>"
      }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
};

export type Page = "onboarding" | "roster" | "assessment" | "gradebook" | "analytics";
