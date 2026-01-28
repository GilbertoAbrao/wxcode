"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { useProject } from "@/hooks/useProject";
import { useProducts, useCreateProduct } from "@/hooks/useProducts";
import { ProductGrid, type ProductType } from "@/components/product";
import { ConversionHistory } from "@/components/conversion";
import { Loader2, Package, ArrowRight } from "lucide-react";
import Link from "next/link";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function FactoryPage({ params }: PageProps) {
  const { id: projectId } = use(params);
  const router = useRouter();

  // Get project data (includes the MongoDB ObjectId)
  const { data: project, isLoading: projectLoading } = useProject(projectId);

  // Get products using project.id (ObjectId), NOT projectId (name from URL)
  const { data: products, isLoading: productsLoading } = useProducts(
    project?.id || ""
  );

  // Mutation for creating new products
  const createProduct = useCreateProduct();

  // Handle product selection
  const handleSelectProduct = async (productType: ProductType) => {
    if (!project?.id) return;

    // Check if product already exists
    const existing = products?.products.find(
      (p) => p.product_type === productType
    );
    if (existing) {
      // Navigate to existing product
      router.push(`/project/${projectId}/products/${existing.id}`);
      return;
    }

    // Create new product via API
    const newProduct = await createProduct.mutateAsync({
      project_id: project.id,
      product_type: productType,
    });

    // Navigate to product wizard (wizard route created in Phase 12)
    router.push(`/project/${projectId}/products/${newProduct.id}`);
  };

  // Loading state
  if (projectLoading || productsLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-zinc-950">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  // Map products to ProductInfo format for ProductGrid
  const existingProducts =
    products?.products.map((p) => ({
      id: p.id,
      product_type: p.product_type as ProductType,
      status: p.status,
    })) || [];

  return (
    <div className="max-w-4xl mx-auto p-8 bg-zinc-950 min-h-full">
      {/* Section 1: Product Selection */}
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-zinc-100 mb-2">
          O que vamos criar juntos?
        </h1>
        <p className="text-zinc-400 mb-8">Escolha um produto para comecar</p>

        <ProductGrid
          existingProducts={existingProducts}
          onSelectProduct={handleSelectProduct}
        />
      </div>

      {/* Section 2: Existing Products List (UI-04 requirement) */}
      {products && products.products.length > 0 && (
        <div className="mt-8 border-t border-zinc-800 pt-8">
          <h2 className="text-xl font-semibold text-zinc-100 mb-4">
            Produtos criados
          </h2>
          <div className="space-y-3">
            {products.products.map((product) => (
              <Link
                key={product.id}
                href={`/project/${projectId}/products/${product.id}`}
                className="flex items-center justify-between p-4 bg-zinc-900/50 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Package className="h-5 w-5 text-zinc-400" />
                  <div>
                    <p className="text-zinc-100 font-medium">
                      {product.product_type}
                    </p>
                    <p className="text-sm text-zinc-400">
                      Status: {product.status}
                    </p>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-zinc-500" />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Section 3: Conversion History (PROG-04 requirement) */}
      {project?.id && (
        <div className="mt-8 border-t border-zinc-800 pt-8">
          <h2 className="text-xl font-semibold text-zinc-100 mb-4">
            Historico de conversoes
          </h2>
          <ConversionHistory projectId={project.id} />
        </div>
      )}
    </div>
  );
}
