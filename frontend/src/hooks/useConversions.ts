"use client";

/**
 * Hook para buscar conversões de um projeto.
 * Usa mock data como fallback quando a API não está disponível.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Conversion, ConversionStatus } from "@/types/project";
import { mockConversions } from "@/lib/mock-data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

interface UseConversionsOptions {
  status?: ConversionStatus;
}

function mapPhaseToStatus(phase: string): ConversionStatus {
  const phaseMap: Record<string, ConversionStatus> = {
    pending: "pending",
    schema: "in_progress",
    domain: "in_progress",
    business: "in_progress",
    api: "in_progress",
    ui: "in_progress",
    validation: "review",
    completed: "completed",
    error: "failed",
  };
  return phaseMap[phase] || "pending";
}

async function fetchConversions(
  projectId: string,
  options?: UseConversionsOptions
): Promise<Conversion[]> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 400));
    let conversions = mockConversions[projectId] || [];

    if (options?.status) {
      conversions = conversions.filter((c) => c.status === options.status);
    }

    return conversions;
  }

  // Try the conversions endpoint with project_id filter
  const params = new URLSearchParams();
  params.set("project_id", projectId);
  if (options?.status) params.set("status", options.status);

  try {
    const response = await fetch(`/api/conversions?${params}`);
    if (!response.ok) {
      // Endpoint may not exist yet, return empty array
      console.warn("Conversions endpoint not available");
      return [];
    }
    const data = await response.json();
    const conversions = data.conversions || data || [];
    return conversions.map((conversion: Record<string, unknown>) => ({
      id: conversion.id as string,
      projectId: projectId,
      name: conversion.project_name as string,
      description: undefined,
      status: mapPhaseToStatus(conversion.current_phase as string),
      elementsTotal: conversion.total_elements as number,
      elementsConverted: conversion.elements_converted as number,
      tokensUsed: 0,
      createdAt: conversion.created_at ? new Date(conversion.created_at as string) : new Date(),
      updatedAt: conversion.updated_at ? new Date(conversion.updated_at as string) : new Date(),
    }));
  } catch (error) {
    console.error("Failed to fetch conversions:", error);
    return [];
  }
}

export function useConversions(projectId: string, options?: UseConversionsOptions) {
  return useQuery({
    queryKey: ["conversions", projectId, options],
    queryFn: () => fetchConversions(projectId, options),
    enabled: !!projectId,
  });
}

// Mutations
interface CreateConversionInput {
  name: string;
  description?: string;
  targetStack?: string;
  layer?: string;
  elementNames?: string[];
}

async function createConversion(
  projectId: string,
  input: CreateConversionInput
): Promise<Conversion> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 500));
    const newConversion: Conversion = {
      id: `conv-${Date.now()}`,
      projectId,
      name: input.name,
      description: input.description,
      status: "pending",
      elementsTotal: 0,
      elementsConverted: 0,
      tokensUsed: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    return newConversion;
  }

  // 1. Buscar projeto para pegar nome
  const projectResponse = await fetch(`/api/projects/${projectId}`);
  if (!projectResponse.ok) {
    throw new Error("Project not found");
  }
  const project = await projectResponse.json();

  // 2. Chamar endpoint correto
  const response = await fetch("/api/conversions/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_name: project.name,
      target_stack: input.targetStack || "fastapi-jinja2",
      layer: input.layer || undefined,
      element_names: input.elementNames || undefined,
    }),
  });
  if (!response.ok) {
    throw new Error("Failed to create conversion");
  }

  const backend = await response.json();

  // 3. Mapear resposta backend para frontend
  return {
    id: backend.id,
    projectId: projectId,
    name: input.name,
    description: input.description,
    status: mapPhaseToStatus(backend.current_phase),
    elementsTotal: backend.total_elements,
    elementsConverted: backend.elements_converted,
    tokensUsed: 0,
    createdAt: new Date(),
    updatedAt: new Date(),
  };
}

export function useCreateConversion(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateConversionInput) => createConversion(projectId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversions", projectId] });
    },
  });
}
