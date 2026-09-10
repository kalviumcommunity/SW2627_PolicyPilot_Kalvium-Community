import "./globals.css";

export const metadata = {
  title: "PolicyPilot - RAG Document Assistant",
  description: "Enterprise RAG Application with real-time streaming, citations, and caching",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
