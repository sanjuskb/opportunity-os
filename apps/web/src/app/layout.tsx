import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Opportunity OS - Voice-First AI Career Intelligence',
  description: 'Multilingual career and internship intelligence platform for Indian students',
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
