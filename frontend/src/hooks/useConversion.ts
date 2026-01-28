"use client";

/**
 * Hook para buscar detalhes de uma conversão específica.
 * Usa mock data como fallback quando a API não está disponível.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Conversion, ConversionStatus, ConversionElement } from "@/types/project";
import { mockConversionDetails, mockConversions } from "@/lib/mock-data";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

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

async function fetchConversion(
  conversionId: string
): Promise<Conversion & { elements?: ConversionElement[] }> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 300));

    // Check detailed mock data first
    const detail = mockConversionDetails[conversionId];
    if (detail) {
      return detail;
    }

    // Fallback to basic conversion data
    for (const conversions of Object.values(mockConversions)) {
      const conversion = conversions.find((c) => c.id === conversionId);
      if (conversion) {
        return conversion;
      }
    }

    throw new Error("Conversion not found");
  }

  const response = await fetch(`/api/conversions/${conversionId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch conversion");
  }
  const data = await response.json();

  // Map backend response to frontend format
  return {
    id: data.id,
    projectId: data.project_id || "",
    name: data.project_name || "Conversão",
    description: undefined,
    status: mapPhaseToStatus(data.current_phase),
    elementsTotal: data.total_elements || 0,
    elementsConverted: data.elements_converted || 0,
    tokensUsed: 0,
    createdAt: data.created_at ? new Date(data.created_at) : new Date(),
    updatedAt: data.updated_at ? new Date(data.updated_at) : new Date(),
    elements: data.elements,
  };
}

export function useConversion(conversionId: string) {
  return useQuery({
    queryKey: ["conversion", conversionId],
    queryFn: () => fetchConversion(conversionId),
    enabled: !!conversionId,
  });
}

// Mutations
interface UpdateConversionStatusInput {
  status: ConversionStatus;
  comment?: string;
}

async function updateConversionStatus(
  conversionId: string,
  input: UpdateConversionStatusInput
): Promise<Conversion> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Find and update mock conversion
    for (const conversions of Object.values(mockConversions)) {
      const conversion = conversions.find((c) => c.id === conversionId);
      if (conversion) {
        conversion.status = input.status;
        conversion.updatedAt = new Date();
        return conversion;
      }
    }
    throw new Error("Conversion not found");
  }

  const response = await fetch(`/api/conversions/${conversionId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error("Failed to update conversion status");
  }
  return response.json();
}

export function useUpdateConversionStatus(conversionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: UpdateConversionStatusInput) =>
      updateConversionStatus(conversionId, input),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["conversion", conversionId] });
      queryClient.invalidateQueries({ queryKey: ["conversions", data.projectId] });
    },
  });
}

async function approveConversion(conversionId: string): Promise<Conversion> {
  return updateConversionStatus(conversionId, { status: "completed" });
}

async function rejectConversion(
  conversionId: string,
  comment: string
): Promise<Conversion> {
  return updateConversionStatus(conversionId, { status: "failed", comment });
}

export function useApproveConversion(conversionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => approveConversion(conversionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["conversion", conversionId] });
      queryClient.invalidateQueries({ queryKey: ["conversions", data.projectId] });
    },
  });
}

export function useRejectConversion(conversionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (comment: string) => rejectConversion(conversionId, comment),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["conversion", conversionId] });
      queryClient.invalidateQueries({ queryKey: ["conversions", data.projectId] });
    },
  });
}
