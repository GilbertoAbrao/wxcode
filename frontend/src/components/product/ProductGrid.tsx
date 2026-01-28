"use client";

import { ProductCard, type ProductType } from "./ProductCard";

export interface ProductInfo {
  id: string;
  product_type: ProductType;
  status: string;
}

const PRODUCT_CATALOG = [
  {
    type: "conversion" as const,
    title: "Convert to Modern Stack",
    description: "Convert your WinDev project to a modern stack of your choice with AI assistance",
    isAvailable: true,
  },
  {
    type: "api" as const,
    title: "REST API",
    description: "Generate a modern REST API from your project's procedures",
    isAvailable: false,
  },
  {
    type: "mcp" as const,
    title: "MCP Server",
    description: "Create an MCP server to integrate your system with Claude",
    isAvailable: false,
  },
  {
    type: "agents" as const,
    title: "AI Agents",
    description: "Configure intelligent agents to automate system tasks",
    isAvailable: false,
  },
] as const;

export interface ProductGridProps {
  existingProducts: ProductInfo[];
  onSelectProduct: (productType: ProductType) => void;
}

export function ProductGrid({ existingProducts, onSelectProduct }: ProductGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {PRODUCT_CATALOG.map((product) => {
        const existing = existingProducts.find(
          (p) => p.product_type === product.type
        );

        return (
          <ProductCard
            key={product.type}
            productType={product.type}
            title={product.title}
            description={product.description}
            isAvailable={product.isAvailable}
            existingProduct={existing ? { id: existing.id, status: existing.status } : null}
            onSelect={() => onSelectProduct(product.type)}
          />
        );
      })}
    </div>
  );
}

export default ProductGrid;
