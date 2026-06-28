export const metadata = {
  title: "Hevy API Proxy",
  description: "Vercel-ready proxy for the Hevy workout tracker API",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  );
}
