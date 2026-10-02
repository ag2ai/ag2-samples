import type { Metadata } from "next";

import { Session } from "../components/session";

import "@copilotkit/react-core/v2/styles.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "CopilotKit-AG2 Starter",
  description: "CopilotKit-AG2 Starter",
};

export default function RootLayout({ children }: { children: any }) {
  return (
    <html lang="en">
      <body>
        <Session>{children}</Session>
      </body>
    </html>
  );
}
