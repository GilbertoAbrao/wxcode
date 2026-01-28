"use client";

/**
 * ConfigurationSelector - Dropdown for KB configurations.
 *
 * Optional dropdown allowing selection of a configuration to filter
 * which elements are included in the output project.
 */

import { cn } from "@/lib/utils";
import type { Configuration } from "@/types/output-project";

export interface ConfigurationSelectorProps {
  configurations: Configuration[];
  selectedId: string | null;
  onSelect: (configId: string | null) => void;
  disabled?: boolean;
}

export function ConfigurationSelector({
  configurations,
  selectedId,
  onSelect,
  disabled = false,
}: ConfigurationSelectorProps) {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onSelect(value === "" ? null : value);
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-zinc-300">
        Configuration{" "}
        <span className="text-zinc-500 font-normal">(optional)</span>
      </label>
      <select
        value={selectedId ?? ""}
        onChange={handleChange}
        disabled={disabled || configurations.length === 0}
        className={cn(
          "w-full rounded-lg px-4 py-2.5",
          "border outline-none transition-all duration-200",
          "bg-zinc-800 border-zinc-700 text-sm text-zinc-100",
          "hover:border-zinc-600",
          "focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          // Style for select arrow
          "appearance-none bg-no-repeat bg-right",
          "pr-10"
        )}
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
          backgroundPosition: "right 12px center",
        }}
      >
        <option value="">None (all elements)</option>
        {configurations.map((config) => (
          <option key={config.configuration_id} value={config.configuration_id}>
            {config.name}
          </option>
        ))}
      </select>
      {configurations.length === 0 && (
        <p className="text-xs text-zinc-500">
          No configurations available for this Knowledge Base.
        </p>
      )}
    </div>
  );
}
