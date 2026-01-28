"use client";

/**
 * DeleteProjectModal - Modal de confirmacao para exclusao de projeto
 *
 * Requer que o usuario digite o nome exato do projeto para confirmar a exclusao.
 * Exibe aviso sobre o que sera deletado (MongoDB, Neo4j, arquivos locais).
 */

import { useState } from "react";
import * as AlertDialog from "@radix-ui/react-alert-dialog";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useDeleteProject } from "@/hooks";

export interface DeleteProjectModalProps {
  projectId: string;
  projectName: string;
  isOpen: boolean;
  onClose: () => void;
  onDeleted?: () => void;
  stats?: {
    elements: number;
    controls: number;
    procedures: number;
    conversions: number;
  };
}

export function DeleteProjectModal({
  projectId,
  projectName,
  isOpen,
  onClose,
  onDeleted,
  stats,
}: DeleteProjectModalProps) {
  const [confirmText, setConfirmText] = useState("");
  const { mutate, isPending, error, reset } = useDeleteProject();

  const handleOpenChange = (open: boolean) => {
    if (!open && !isPending) {
      setConfirmText("");
      reset();
      onClose();
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    mutate(projectId, {
      onSuccess: () => {
        onClose();
        onDeleted?.();
      },
    });
  };

  const isConfirmValid = confirmText === projectName;

  return (
    <AlertDialog.Root open={isOpen} onOpenChange={handleOpenChange}>
      <AlertDialog.Portal>
        <AlertDialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" />
        <AlertDialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md mx-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl p-6">
            {/* Header with warning icon */}
            <div className="flex items-start gap-4 mb-4">
              <div className="p-2 bg-rose-500/10 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-rose-500" />
              </div>
              <div>
                <AlertDialog.Title className="text-xl font-semibold text-zinc-100">
                  Excluir Projeto
                </AlertDialog.Title>
                <AlertDialog.Description className="text-sm text-zinc-400 mt-1">
                  Esta acao nao pode ser desfeita.
                </AlertDialog.Description>
              </div>
            </div>

            {/* Warning content */}
            <div className="bg-rose-500/5 border border-rose-500/20 rounded-lg p-4 mb-4">
              <p className="text-sm text-zinc-300 mb-2">
                Isso ira excluir permanentemente:
              </p>
              <ul className="text-sm text-zinc-400 space-y-1 list-disc list-inside">
                <li>
                  Todos os dados do MongoDB
                  {stats &&
                    ` (${stats.elements} elementos, ${stats.controls} controles)`}
                </li>
                <li>Dados do Neo4j (grafo de dependencias)</li>
                <li>Arquivos locais do projeto</li>
              </ul>
              {stats && (stats.procedures > 0 || stats.conversions > 0) && (
                <p className="text-sm text-zinc-400 mt-2">
                  Tambem inclui: {stats.procedures > 0 && `${stats.procedures} procedures`}
                  {stats.procedures > 0 && stats.conversions > 0 && ", "}
                  {stats.conversions > 0 && `${stats.conversions} conversoes`}
                </p>
              )}
            </div>

            {/* Confirm input */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-zinc-300 mb-2">
                Digite{" "}
                <span className="font-mono text-rose-400">{projectName}</span>{" "}
                para confirmar:
              </label>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                disabled={isPending}
                placeholder="Nome do projeto"
                className={cn(
                  "w-full rounded-lg px-4 py-2.5",
                  "border outline-none transition-all duration-200",
                  "bg-zinc-800 border-zinc-700 text-sm text-zinc-100",
                  "hover:border-zinc-600",
                  "focus:border-rose-500 focus:ring-1 focus:ring-rose-500/20",
                  "placeholder:text-zinc-500",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              />
            </div>

            {/* Error message */}
            {error && (
              <p className="text-sm text-rose-400 mb-4">{error.message}</p>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3">
              <AlertDialog.Cancel asChild>
                <Button variant="outline" disabled={isPending}>
                  Cancelar
                </Button>
              </AlertDialog.Cancel>
              <AlertDialog.Action asChild>
                <Button
                  variant="destructive"
                  disabled={isPending || !isConfirmValid}
                  onClick={handleDelete}
                >
                  {isPending ? "Excluindo..." : "Excluir Projeto"}
                </Button>
              </AlertDialog.Action>
            </div>
          </div>
        </AlertDialog.Content>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
