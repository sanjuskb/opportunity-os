import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'NexteRaS — The Upcoming Era. | AI Career Intelligence System',
  description: 'An AI-powered career intelligence and autonomous employability system across 7 regional languages.',
  openGraph: {
    title: 'NexteRaS — The Upcoming Era.',
    description: 'An AI-powered career intelligence and autonomous employability system.',
    siteName: 'NexteRaS',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
