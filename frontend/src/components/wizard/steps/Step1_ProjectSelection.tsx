"use client";

import React, { useState } from "react";
import { FolderOpen, Upload, Loader2, X, FileText, AlertCircle, CheckCircle } from "lucide-react";
import { getBackendHttpUrl } from "@/lib/api";

interface Step1Props {
  onNext: (projectPath: string, pdfDocsPath?: string) => void;
}

export function Step1_ProjectSelection({ onNext }: Step1Props) {
  const [projectFile, setProjectFile] = useState<File | null>(null);
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  // Verificar se backend está acessível
  React.useEffect(() => {
    const checkBackend = async () => {
      const backendUrl = getBackendHttpUrl();
      try {
        const response = await fetch(`${backendUrl}/docs`, { method: "HEAD" });
        setBackendStatus(response.ok ? "online" : "offline");
      } catch {
        setBackendStatus("offline");
      }
    };
    checkBackend();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!projectFile) {
      setError("Selecione o arquivo .zip do projeto");
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // Upload project file
      setUploadProgress("Fazendo upload do projeto...");
      const projectFormData = new FormData();
      projectFormData.append("file", projectFile);

      console.log("Uploading project file:", projectFile.name, projectFile.size, "bytes");

      // Upload direto para o backend (não passa pelo proxy Next.js para evitar problemas com arquivos grandes)
      const backendUrl = getBackendHttpUrl();

      let projectResponse;
      try {
        projectResponse = await fetch(`${backendUrl}/api/import-wizard/upload/project`, {
          method: "POST",
          body: projectFormData,
        });
        console.log("Upload response status:", projectResponse.status);
      } catch (fetchError) {
        console.error("Fetch error:", fetchError);
        throw new Error(`Erro de rede ao fazer upload: ${fetchError instanceof Error ? fetchError.message : "Desconhecido"}`);
      }

      if (!projectResponse.ok) {
        let errorMessage = "Erro ao fazer upload do projeto";
        try {
          const errorText = await projectResponse.text();
          console.log("Error response text:", errorText);
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (parseError) {
          // Se não conseguir parsear JSON, usar mensagem padrão
          errorMessage = `${errorMessage} (Status: ${projectResponse.status})`;
        }
        console.error("Upload error:", errorMessage);
        throw new Error(errorMessage);
      }

      let projectData;
      try {
        projectData = await projectResponse.json();
      } catch (jsonError) {
        console.error("Error parsing response JSON:", jsonError);
        throw new Error("Erro ao processar resposta do servidor");
      }
      const projectPath = projectData.file_path;

      // Upload PDF files if provided
      let pdfPath: string | undefined;
      if (pdfFiles.length > 0) {
        setUploadProgress(`Fazendo upload de ${pdfFiles.length} PDF(s)...`);
        const pdfFormData = new FormData();

        // Adicionar todos os PDFs ao FormData
        pdfFiles.forEach((file) => {
          pdfFormData.append("files", file);
        });

        const pdfResponse = await fetch(`${backendUrl}/api/import-wizard/upload/pdfs`, {
          method: "POST",
          body: pdfFormData,
        });

        if (!pdfResponse.ok) {
          let errorMessage = "Erro ao fazer upload dos PDFs";
          try {
            const errorData = await pdfResponse.json();
            errorMessage = errorData.detail || errorMessage;
          } catch {
            errorMessage = `${errorMessage} (Status: ${pdfResponse.status})`;
          }
          throw new Error(errorMessage);
        }

        const pdfData = await pdfResponse.json();
        pdfPath = pdfData.file_path;
      }

      setUploadProgress("Uploads concluídos!");
      onNext(projectPath, pdfPath);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
      setIsUploading(false);
    }
  };

  const handleProjectFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith(".zip")) {
        setError("O arquivo do projeto deve ser .zip");
        return;
      }
      setProjectFile(file);
      setError(null);
    }
  };

  const handlePdfFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);

    // Validar que todos são PDFs
    const invalidFiles = files.filter(f => !f.name.toLowerCase().endsWith(".pdf"));
    if (invalidFiles.length > 0) {
      setError(`Arquivos inválidos: ${invalidFiles.map(f => f.name).join(", ")}`);
      return;
    }

    setPdfFiles(files);
    setError(null);
  };

  const removePdfFile = (index: number) => {
    setPdfFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const totalPdfSize = pdfFiles.reduce((sum, file) => sum + file.size, 0);

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="text-center mb-8">
        <FolderOpen className="w-16 h-16 text-blue-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-zinc-100 mb-2">
          Selecione o Projeto
        </h2>
        <p className="text-zinc-400">
          Construa a Knowledge Database do seu projeto WinDev/WebDev
        </p>
      </div>

      {/* Backend Status */}
      <div className="mb-6 p-3 bg-zinc-800 rounded-lg flex items-center gap-2">
        {backendStatus === "checking" && (
          <>
            <Loader2 className="w-4 h-4 text-zinc-400 animate-spin" />
            <span className="text-sm text-zinc-400">Verificando conexão com backend...</span>
          </>
        )}
        {backendStatus === "online" && (
          <>
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-sm text-zinc-300">Backend conectado</span>
          </>
        )}
        {backendStatus === "offline" && (
          <>
            <AlertCircle className="w-4 h-4 text-red-500" />
            <span className="text-sm text-red-400">
              Backend offline. Inicie o backend em: <code className="text-xs bg-zinc-900 px-1 py-0.5 rounded">cd src && uvicorn wxcode.main:app --reload</code>
            </span>
          </>
        )}
      </div>

      {backendStatus === "online" ? (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Project File Upload */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Arquivo .zip do Projeto <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type="file"
                accept=".zip"
                onChange={handleProjectFileChange}
                disabled={isUploading}
                className="hidden"
                id="project-file"
              />
              <label
                htmlFor="project-file"
                className="flex items-center gap-3 w-full px-4 py-3 bg-zinc-800 border-2 border-dashed border-zinc-700 rounded-lg cursor-pointer hover:border-blue-500 transition-colors"
              >
                <Upload className="w-5 h-5 text-zinc-500" />
                <span className="text-zinc-300">
                  {projectFile ? projectFile.name : "Clique para selecionar o arquivo .zip"}
                </span>
              </label>
            </div>
            {projectFile && (
              <p className="text-xs text-zinc-500 mt-1">
                Tamanho: {formatFileSize(projectFile.size)}
              </p>
            )}
          </div>

          {/* PDF Files Upload (Multiple, Optional) */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Arquivos PDF de Documentação (opcional)
            </label>
            <div className="relative">
              <input
                type="file"
                accept=".pdf"
                multiple
                onChange={handlePdfFilesChange}
                disabled={isUploading}
                className="hidden"
                id="pdf-files"
              />
              <label
                htmlFor="pdf-files"
                className="flex items-center gap-3 w-full px-4 py-3 bg-zinc-800 border-2 border-dashed border-zinc-700 rounded-lg cursor-pointer hover:border-blue-500 transition-colors"
              >
                <FileText className="w-5 h-5 text-zinc-500" />
                <span className="text-zinc-300">
                  {pdfFiles.length > 0
                    ? `${pdfFiles.length} arquivo(s) selecionado(s)`
                    : "Clique para selecionar arquivos PDF"}
                </span>
              </label>
            </div>

            {/* Lista de PDFs selecionados */}
            {pdfFiles.length > 0 && (
              <div className="mt-3 space-y-2">
                {pdfFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between px-3 py-2 bg-zinc-800/50 rounded border border-zinc-700"
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <FileText className="w-4 h-4 text-zinc-500 flex-shrink-0" />
                      <span className="text-sm text-zinc-300 truncate">{file.name}</span>
                      <span className="text-xs text-zinc-500 flex-shrink-0">
                        {formatFileSize(file.size)}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removePdfFile(index)}
                      disabled={isUploading}
                      className="ml-2 p-1 hover:bg-zinc-700 rounded transition-colors disabled:opacity-50"
                    >
                      <X className="w-4 h-4 text-zinc-500" />
                    </button>
                  </div>
                ))}
                <p className="text-xs text-zinc-500">
                  Total: {formatFileSize(totalPdfSize)}
                </p>
              </div>
            )}

            <p className="text-xs text-zinc-500 mt-1">
              Documentação em PDF para enriquecimento de controles
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-900/20 border border-red-700 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Upload Progress */}
          {isUploading && uploadProgress && (
            <div className="p-3 bg-blue-900/20 border border-blue-700 rounded-lg text-blue-400 text-sm flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              {uploadProgress}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!projectFile || isUploading}
            className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-800 disabled:text-zinc-600 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Fazendo upload...
              </>
            ) : (
              "Iniciar Importação"
            )}
          </button>
        </form>
      ) : (
        <div className="text-center py-12">
          <p className="text-zinc-400">
            {backendStatus === "checking"
              ? "Aguardando conexão com o backend..."
              : "Inicie o backend para continuar"}
          </p>
        </div>
      )}
    </div>
  );
}
