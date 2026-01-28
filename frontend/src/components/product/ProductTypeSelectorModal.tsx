"use client";

/**
 * ProductTypeSelectorModal - Modal for selecting the type of output project.
 *
 * Shows the ProductGrid with 4 product types. When user selects a type,
 * calls onSelectType with the selected type.
 */

import * as Dialog from "@radix-ui/react-dialog";
import { X, Sparkles } from "lucide-react";
import { ProductGrid, type ProductInfo } from "./ProductGrid";
import type { ProductType } from "./ProductCard";

export interface ProductTypeSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectType: (type: ProductType) => void;
  existingProducts?: ProductInfo[];
}

export function ProductTypeSelectorModal({
  isOpen,
  onClose,
  onSelectType,
  existingProducts = [],
}: ProductTypeSelectorModalProps) {
  const handleSelect = (type: ProductType) => {
    onSelectType(type);
    // Don't close - let parent handle the flow
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-3xl mx-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl">
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-zinc-800">
              <div className="flex items-start gap-4">
                <div className="p-2 bg-purple-500/10 rounded-lg">
                  <Sparkles className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                  <Dialog.Title className="text-xl font-semibold text-zinc-100">
                    What shall we create?
                  </Dialog.Title>
                  <Dialog.Description className="text-sm text-zinc-400 mt-1">
                    Select a product type to get started
                  </Dialog.Description>
                </div>
              </div>
              <Dialog.Close asChild>
                <button className="p-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </Dialog.Close>
            </div>

            {/* Body */}
            <div className="p-6">
              <ProductGrid
                existingProducts={existingProducts}
                onSelectProduct={handleSelect}
              />
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
