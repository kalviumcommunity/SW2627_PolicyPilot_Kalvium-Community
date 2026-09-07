import "./globals.css";

export const metadata = {
  title: "PolicyPilot Support Chat",
  description: "E-commerce Policy RAG Assistant",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
