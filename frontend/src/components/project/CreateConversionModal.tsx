"use client";

/**
 * CreateConversionModal - Modal para criar nova conversão
 *
 * Permite configurar nome, descrição, target stack, layer e elementos específicos para conversão.
 */

import { useState, FormEvent, useMemo } from "react";
import { X, ChevronDown, ChevronUp } from "lucide-react";
import { GlowInput } from "@/components/ui/GlowInput";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ElementSelector } from "./ElementSelector";
import { ManualElementInput } from "./ManualElementInput";
import type { CreateConversionData } from "@/types/project";

export interface CreateConversionModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateConversionData) => Promise<void>;
  isLoading?: boolean;
}

const LAYER_OPTIONS = [
  { value: "", label: "Todos (ordem topológica completa)" },
  { value: "schema", label: "Schema (Pydantic models)" },
  { value: "domain", label: "Domain (classes de domínio)" },
  { value: "business", label: "Business (services)" },
  { value: "api", label: "API (rotas FastAPI)" },
  { value: "ui", label: "UI (templates Jinja2)" },
];

export function CreateConversionModal({
  projectId,
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
}: CreateConversionModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [targetStack, setTargetStack] = useState("fastapi-jinja2");
  const [layer, setLayer] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [selectedElements, setSelectedElements] = useState<Set<string>>(new Set());
  const [manualElements, setManualElements] = useState<string[]>([]);
  const [showElementSelector, setShowElementSelector] = useState(false);

  // Computed values
  const allSelectedElements = useMemo(() => {
    const combined = new Set(selectedElements);
    manualElements.forEach((e) => combined.add(e));
    return Array.from(combined);
  }, [selectedElements, manualElements]);

  const totalSelected = allSelectedElements.length;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    // Validação
    const newErrors: Record<string, string> = {};
    if (!name.trim() || name.trim().length < 3) {
      newErrors.name = "Nome deve ter pelo menos 3 caracteres";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});

    try {
      await onSubmit({
        name: name.trim(),
        description: description.trim() || undefined,
        targetStack: targetStack || undefined,
        layer: layer || undefined,
        elementNames: totalSelected > 0 ? allSelectedElements : undefined,
      });

      // Reset form
      setName("");
      setDescription("");
      setTargetStack("fastapi-jinja2");
      setLayer("");
      setSelectedElements(new Set());
      setManualElements([]);
      setShowElementSelector(false);
    } catch (error) {
      console.error("Failed to create conversion:", error);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setName("");
      setDescription("");
      setTargetStack("fastapi-jinja2");
      setLayer("");
      setErrors({});
      setSelectedElements(new Set());
      setManualElements([]);
      setShowElementSelector(false);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-lg mx-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-zinc-800">
            <h2 className="text-xl font-semibold text-zinc-100">
              Nova Conversão
            </h2>
            <button
              onClick={handleClose}
              disabled={isLoading}
              className={cn(
                "text-zinc-400 hover:text-zinc-100 transition-colors",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Nome */}
            <GlowInput
              label="Nome da Conversão *"
              placeholder="Ex: Conversão v1.0"
              value={name}
              onChange={(e) => setName(e.target.value)}
              error={errors.name}
              disabled={isLoading}
              fullWidth
              required
            />

            {/* Descrição */}
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-zinc-300">
                Descrição
              </label>
              <textarea
                placeholder="Descrição opcional da conversão..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={isLoading}
                rows={3}
                className={cn(
                  "w-full rounded-lg font-medium px-4 py-2.5",
                  "border outline-none transition-all duration-200",
                  "bg-zinc-900 border-zinc-700 text-sm",
                  "hover:border-zinc-600",
                  "focus:border-blue-500",
                  "placeholder:text-zinc-500",
                  "disabled:opacity-50 disabled:cursor-not-allowed",
                  "resize-none"
                )}
              />
            </div>

            {/* Target Stack */}
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-zinc-300">
                Target Stack
              </label>
              <select
                value={targetStack}
                onChange={(e) => setTargetStack(e.target.value)}
                disabled={isLoading}
                className={cn(
                  "w-full rounded-lg font-medium px-4 h-10 text-sm",
                  "border outline-none transition-all duration-200",
                  "bg-zinc-900 border-zinc-700",
                  "hover:border-zinc-600",
                  "focus:border-blue-500",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                <option value="fastapi-jinja2">FastAPI + Jinja2</option>
              </select>
              <p className="text-xs text-zinc-500 mt-1">
                Atualmente apenas FastAPI + Jinja2 está disponível
              </p>
            </div>

            {/* Layer */}
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-zinc-300">
                Layer
              </label>
              <select
                value={layer}
                onChange={(e) => setLayer(e.target.value)}
                disabled={isLoading}
                className={cn(
                  "w-full rounded-lg font-medium px-4 h-10 text-sm",
                  "border outline-none transition-all duration-200",
                  "bg-zinc-900 border-zinc-700",
                  "hover:border-zinc-600",
                  "focus:border-blue-500",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                {LAYER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-zinc-500 mt-1">
                Selecione uma layer específica ou converta todas em ordem
                topológica
              </p>
            </div>

            {/* Element Selection */}
            <div className="space-y-1.5">
              <button
                type="button"
                onClick={() => setShowElementSelector(!showElementSelector)}
                disabled={isLoading}
                className={cn(
                  "w-full flex items-center justify-between px-4 py-3 rounded-lg",
                  "bg-zinc-800 hover:bg-zinc-700 transition-colors",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-zinc-300">
                    Selecionar Elementos Específicos
                  </span>
                  {totalSelected > 0 && (
                    <span className="px-2 py-0.5 bg-blue-600 text-white text-xs rounded">
                      {totalSelected}
                    </span>
                  )}
                </div>
                {showElementSelector ? (
                  <ChevronUp className="w-4 h-4 text-zinc-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-zinc-500" />
                )}
              </button>

              {showElementSelector && (
                <div className="p-4 bg-zinc-800/50 rounded-lg space-y-4">
                  <ElementSelector
                    projectId={projectId}
                    selectedElements={selectedElements}
                    onSelectionChange={setSelectedElements}
                    isLoading={isLoading}
                  />

                  <div className="border-t border-zinc-700 pt-4">
                    <label className="block text-sm font-medium text-zinc-300 mb-2">
                      Entrada Manual
                    </label>
                    <ManualElementInput
                      manualElements={manualElements}
                      onManualElementsChange={setManualElements}
                      isDisabled={isLoading}
                    />
                  </div>
                </div>
              )}

              <p className="text-xs text-zinc-500 mt-1">
                Opcional: Selecione elementos específicos ou deixe vazio para converter por layer/projeto inteiro
              </p>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isLoading}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "Criando..." : "Criar Conversão"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
