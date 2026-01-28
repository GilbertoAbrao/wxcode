/**
 * Catch-all API route proxy para FastAPI backend.
 *
 * Encaminha todas as requisições /api/* para o backend FastAPI,
 * mantendo método, headers e body da requisição original.
 */

import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8052";

async function proxyRequest(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const targetPath = path.join("/");

  // Preserva query string da requisição original
  const searchParams = request.nextUrl.searchParams.toString();
  const queryString = searchParams ? `?${searchParams}` : "";
  const targetUrl = `${API_URL}/api/${targetPath}${queryString}`;

  console.log(`[Proxy] ${request.method} ${targetUrl}`);

  // Prepara headers, removendo headers específicos do Next.js
  const headers = new Headers();
  const contentType = request.headers.get("content-type") || "";
  const isFormData = contentType.includes("multipart/form-data");

  request.headers.forEach((value, key) => {
    const keyLower = key.toLowerCase();
    // Skip headers que não devem ser repassados
    // Para FormData, também pular content-type (fetch vai adicionar com boundary correto)
    if (
      !["host", "connection", "transfer-encoding", "keep-alive"].includes(
        keyLower
      ) &&
      !(isFormData && keyLower === "content-type")
    ) {
      headers.set(key, value);
    }
  });

  // Obtém body se existir
  let body: BodyInit | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    // Para uploads de arquivos (multipart/form-data), repassar o FormData
    if (isFormData) {
      try {
        // Obter FormData da requisição original
        console.log("[Proxy] Parsing FormData...");
        const formData = await request.formData();
        console.log("[Proxy] FormData parsed successfully");
        body = formData;
      } catch (error) {
        console.error("[Proxy] Error parsing FormData:", error);
        // Fallback para body direto
        body = request.body as ReadableStream<Uint8Array>;
      }
    } else {
      // Para outros casos (JSON, texto), ler como texto
      try {
        body = await request.text();
      } catch {
        // Sem body
      }
    }
  }

  try {
    // Debug logging para uploads
    if (isFormData) {
      console.log(`[Proxy] FormData upload to ${targetUrl}`);
    }

    // Faz requisição ao backend
    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body,
    });

    console.log(`[Proxy] Response: ${response.status} ${response.statusText}`);

    // Prepara headers da resposta
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      // Skip headers que causam problemas
      if (!["transfer-encoding", "connection"].includes(key.toLowerCase())) {
        responseHeaders.set(key, value);
      }
    });

    // Para respostas grandes ou streaming, retornar o body diretamente
    // Caso contrário, ler como texto (para manter compatibilidade)
    const contentLength = response.headers.get("content-length");
    const isLargeResponse = contentLength && parseInt(contentLength) > 1024 * 1024; // > 1MB

    if (isLargeResponse || response.body) {
      return new NextResponse(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    }

    // Para respostas pequenas, ler como texto
    const data = await response.text();

    return new NextResponse(data, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error(`Proxy error for ${targetUrl}:`, error);
    return NextResponse.json(
      { error: "Failed to proxy request to backend" },
      { status: 502 }
    );
  }
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, context);
}
