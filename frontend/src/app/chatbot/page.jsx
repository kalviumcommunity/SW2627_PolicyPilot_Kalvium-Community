'use client';

import { useEffect } from "react";
import Home from "../page";

export default function ChatbotPage() {
  useEffect(() => {
    const timer = window.setTimeout(() => {
      window.dispatchEvent(new Event("open-policy-chat"));
    }, 100);
    return () => window.clearTimeout(timer);
  }, []);

  return <Home initialNav="Policy assistant" />;
}