// middleware.ts
import { NextResponse, type NextRequest } from "next/server";
import { jwtVerify } from "jose";

export const config = {
  matcher: ["/schorle/render/:path*"], // matches /schorle/render and all subpaths
};

async function verifyToken(req: NextRequest) {
  try {
    const token = req.headers.get("x-schorle-token");
    if (!token) {
      return new Response("Unauthorized", { status: 401 });
    }
    const SECRET = process.env.SCHORLE_JWT_SECRET ?? "";
    const key = new TextEncoder().encode(SECRET);
    await jwtVerify(token, key, {
      issuer: "schorle-py",
      audience: "nextjs-app",
      clockTolerance: "0.5 s", // small skew tolerance
    });
    return NextResponse.next();
  } catch (error) {
    return new Response("Unauthorized", { status: 401 });
  }
}
export default function middleware(req: NextRequest) {
  return verifyToken(req);
}
