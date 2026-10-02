import { SignJWT } from "jose";
import { NextRequest, NextResponse } from "next/server";

// Demonstration only: anyone may sign in as any name. A real application would check
// credentials here (or hand this step to an identity provider) before signing a token.
export const POST = async (req: NextRequest) => {
  const secret = process.env.AUTH_SECRET;
  if (!secret) {
    return NextResponse.json(
      { error: "AUTH_SECRET is not set on the frontend server." },
      { status: 500 },
    );
  }

  const body = await req.json().catch(() => null);
  const name = typeof body?.name === "string" ? body.name.trim().slice(0, 80) : "";
  if (!name) {
    return NextResponse.json({ error: "Enter a name." }, { status: 400 });
  }

  // The Access token the backend verifies: signed here, where the secret never reaches
  // the browser, and carrying the User's id and display name.
  const token = await new SignJWT({ name })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(crypto.randomUUID())
    .setIssuedAt()
    .setExpirationTime("8h")
    .sign(new TextEncoder().encode(secret));

  return NextResponse.json({ token, name });
};
