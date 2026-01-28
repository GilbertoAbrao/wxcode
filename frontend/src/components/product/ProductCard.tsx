"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Zap, Server, Plug, Bot, Lock } from "lucide-react";
import { cn } from "@/lib/utils";

export type ProductType = "conversion" | "api" | "mcp" | "agents";

export interface ProductCardProps {
  productType: ProductType;
  title: string;
  description: string;
  isAvailable: boolean;
  existingProduct?: { id: string; status: string } | null;
  onSelect: () => void;
}

const productIcons = {
  conversion: Zap,
  api: Server,
  mcp: Plug,
  agents: Bot,
};

const productColors = {
  conversion: {
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    hoverBg: "group-hover:bg-blue-500/20",
    glow: "rgba(59, 130, 246, 0.15)",
    glowOuter: "rgba(59, 130, 246, 0.05)",
  },
  api: {
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    hoverBg: "group-hover:bg-purple-500/20",
    glow: "rgba(168, 85, 247, 0.15)",
    glowOuter: "rgba(168, 85, 247, 0.05)",
  },
  mcp: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    hoverBg: "group-hover:bg-emerald-500/20",
    glow: "rgba(16, 185, 129, 0.15)",
    glowOuter: "rgba(16, 185, 129, 0.05)",
  },
  agents: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    hoverBg: "group-hover:bg-amber-500/20",
    glow: "rgba(245, 158, 11, 0.15)",
    glowOuter: "rgba(245, 158, 11, 0.05)",
  },
};

const statusLabels: Record<string, string> = {
  pending: "Pending",
  in_progress: "In Progress",
  paused: "Paused",
  completed: "Completed",
  failed: "Failed",
};

function ProductCardComponent({
  productType,
  title,
  description,
  isAvailable,
  existingProduct,
  onSelect,
}: ProductCardProps) {
  const Icon = productIcons[productType];
  const colors = productColors[productType];

  const handleClick = () => {
    if (isAvailable) {
      onSelect();
    }
  };

  return (
    <motion.button
      onClick={handleClick}
      whileHover={isAvailable ? {
        scale: 1.02,
        boxShadow: `0 0 30px ${colors.glow}, 0 0 60px ${colors.glowOuter}`,
      } : undefined}
      whileTap={isAvailable ? { scale: 0.98 } : undefined}
      transition={{ duration: 0.2, ease: "easeOut" }}
      disabled={!isAvailable}
      className={cn(
        "w-full p-6 text-left relative",
        "bg-zinc-900/80 rounded-xl",
        "border border-zinc-800",
        "transition-colors duration-200",
        "group",
        isAvailable && "hover:border-zinc-700 cursor-pointer",
        !isAvailable && "opacity-50 cursor-not-allowed"
      )}
    >
      {/* Unavailable overlay badge */}
      {!isAvailable && (
        <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2 py-1 rounded-md bg-zinc-800 text-zinc-400 text-xs">
          <Lock className="w-3 h-3" />
          <span>Coming Soon</span>
        </div>
      )}

      {/* Existing product status badge */}
      {existingProduct && (
        <div className={cn(
          "absolute top-3 right-3 px-2 py-1 rounded-md text-xs",
          existingProduct.status === "completed" && "bg-emerald-500/10 text-emerald-400",
          existingProduct.status === "in_progress" && "bg-blue-500/10 text-blue-400",
          existingProduct.status === "paused" && "bg-amber-500/10 text-amber-400",
          existingProduct.status === "failed" && "bg-red-500/10 text-red-400",
          existingProduct.status === "pending" && "bg-zinc-500/10 text-zinc-400"
        )}>
          {statusLabels[existingProduct.status] || existingProduct.status}
        </div>
      )}

      {/* Header with icon and title */}
      <div className="flex items-start gap-4">
        <motion.div
          whileHover={isAvailable ? { rotate: [0, -10, 10, 0] } : undefined}
          transition={{ duration: 0.4 }}
          className={cn(
            "p-3 rounded-lg",
            colors.bg,
            colors.text,
            isAvailable && colors.hoverBg,
            "transition-colors duration-200"
          )}
        >
          <Icon className="w-6 h-6" />
        </motion.div>
        <div className="flex-1 min-w-0">
          <h3 className={cn(
            "text-lg font-semibold text-zinc-100",
            isAvailable && "group-hover:text-white",
            "transition-colors duration-200"
          )}>
            {title}
          </h3>
          <p className="text-sm text-zinc-400 mt-1">
            {description}
          </p>
        </div>
      </div>
    </motion.button>
  );
}

export const ProductCard = memo(ProductCardComponent);
export default ProductCard;
