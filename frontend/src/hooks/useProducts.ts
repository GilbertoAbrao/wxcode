"use client";

/**
 * Hooks para buscar e criar produtos.
 *
 * Usa TanStack Query para cache e invalidation automatica.
 * API backend ja esta pronta - sem mock data.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  Product,
  ProductListResponse,
  CreateProductRequest,
} from "@/types/product";

/**
 * Busca produtos de um projeto.
 */
async function fetchProducts(projectId: string): Promise<ProductListResponse> {
  const response = await fetch(`/api/products?project_id=${projectId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch products");
  }
  return response.json();
}

/**
 * Cria um novo produto.
 */
async function createProduct(request: CreateProductRequest): Promise<Product> {
  const response = await fetch("/api/products", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error("Failed to create product");
  }
  return response.json();
}

/**
 * Hook para buscar produtos de um projeto.
 *
 * @param projectId - ID do projeto (ObjectId string)
 * @returns Query result com lista de produtos
 */
export function useProducts(projectId: string) {
  return useQuery({
    queryKey: ["products", projectId],
    queryFn: () => fetchProducts(projectId),
    enabled: !!projectId,
  });
}

/**
 * Hook para criar um novo produto.
 *
 * @returns Mutation para criar produto com invalidation automatica
 */
export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createProduct,
    onSuccess: (data) => {
      // Invalida query de produtos para o projeto
      queryClient.invalidateQueries({
        queryKey: ["products", data.project_id],
      });
    },
  });
}
