import { NextRequest, NextResponse } from "next/server";
import { routeAI } from "@/lib/ai-router";
import type { AIRequest } from "@/lib/ai-router";

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as AIRequest;

    if (!body.messages || !Array.isArray(body.messages) || body.messages.length === 0) {
      return NextResponse.json({ error: "messages array is required" }, { status: 400 });
    }

    const response = await routeAI(body);
    return NextResponse.json(response);
  } catch (err) {
    const message = err instanceof Error ? err.message : "AI routing failed";
    return NextResponse.json({ error: message, fallback: false }, { status: 502 });
  }
}
