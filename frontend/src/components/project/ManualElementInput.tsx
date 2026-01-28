"use client";

import { useState, KeyboardEvent } from "react";
import { X, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ManualElementInputProps {
  manualElements: string[];
  onManualElementsChange: (elements: string[]) => void;
  isDisabled?: boolean;
}

export function ManualElementInput({
  manualElements,
  onManualElementsChange,
  isDisabled = false,
}: ManualElementInputProps) {
  const [inputValue, setInputValue] = useState("");

  const handleAdd = () => {
    if (!inputValue.trim()) return;

    // Parse comma-separated
    const newElements = inputValue
      .split(",")
      .map((e) => e.trim())
      .filter((e) => e && !manualElements.includes(e));

    if (newElements.length > 0) {
      onManualElementsChange([...manualElements, ...newElements]);
    }

    setInputValue("");
  };

  const handleRemove = (element: string) => {
    onManualElementsChange(manualElements.filter((e) => e !== element));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="space-y-2">
      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Ex: PAGE_Login, proc:MyProc (separados por vírgula)"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isDisabled}
          className={cn(
            "flex-1 px-4 py-2 rounded-lg text-sm",
            "bg-zinc-900 border border-zinc-700",
            "focus:border-blue-500 outline-none",
            "placeholder:text-zinc-500",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        />

        <button
          type="button"
          onClick={handleAdd}
          disabled={isDisabled || !inputValue.trim()}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium",
            "bg-blue-600 hover:bg-blue-700 text-white",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "transition-colors"
          )}
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Tags */}
      {manualElements.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {manualElements.map((element) => (
            <span
              key={element}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-zinc-800 text-zinc-100 rounded-lg text-sm"
            >
              {element}
              <button
                type="button"
                onClick={() => handleRemove(element)}
                disabled={isDisabled}
                className="hover:text-rose-400 transition-colors disabled:opacity-50"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Help text */}
      <p className="text-xs text-zinc-500">
        Digite os nomes separados por vírgula ou pressione Enter para adicionar
      </p>
    </div>
  );
}
