"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Header } from "@/components/layout";
import { WizardStepper } from "@/components/wizard/WizardStepper";
import { LogViewer } from "@/components/wizard/LogViewer";
import { StepSummary } from "@/components/wizard/StepSummary";
import { Step1_ProjectSelection } from "@/components/wizard/steps";
import { useImportWizard } from "@/hooks/useImportWizard";

export default function ImportPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | undefined>();

  const {
    currentStep,
    status,
    logs,
    stepResults,
    stepProgress,
    isConnected,
    error,
    projectName,
    start,
    cancel,
  } = useImportWizard(sessionId);

  const handleProjectSelection = async (projectPath: string, pdfDocsPath?: string) => {
    try {
      // Create session with FormData via Next.js proxy
      const formData = new FormData();
      formData.append("project_path", projectPath);
      if (pdfDocsPath) {
        formData.append("pdf_docs_path", pdfDocsPath);
      }

      console.log("Creating session with:", { projectPath, pdfDocsPath });

      const response = await fetch(`/api/import-wizard/sessions`, {
        method: "POST",
        body: formData,
      });

      console.log("Session creation response:", response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Session creation failed:", errorText);
        throw new Error(`Failed to create session: ${response.status}`);
      }

      const data = await response.json();
      console.log("Session created:", data);
      setSessionId(data.session_id);

      // Start wizard automatically
      setTimeout(() => start(), 500);
    } catch (err) {
      console.error("Error creating session:", err);
    }
  };

  const handleContinue = () => {
    if (projectName) {
      router.push(`/project/${projectName}/factory`);
    }
  };

  // Step 1: Project Selection
  if (!sessionId) {
    return (
      <div className="min-h-screen bg-zinc-950">
        <Header
          breadcrumbs={[
            { label: "Knowledge Base", href: "/dashboard" },
            { label: "Importar Projeto" },
          ]}
        >
          <button
            onClick={() => router.push("/dashboard")}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </button>
        </Header>
        <Step1_ProjectSelection onNext={handleProjectSelection} />
      </div>
    );
  }

  // Steps 2-6: Running wizard
  return (
    <div className="min-h-screen bg-zinc-950">
      <Header
        breadcrumbs={[
          { label: "Knowledge Base", href: "/dashboard" },
          { label: "Importar Projeto" },
        ]}
      >
        {status !== "running" && (
          <button
            onClick={() => router.push("/dashboard")}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </button>
        )}
      </Header>

      {/* Stepper */}
      <WizardStepper currentStep={currentStep} stepResults={stepResults} stepProgress={stepProgress} />

      {/* Main Content */}
      <div className="max-w-6xl mx-auto p-8">
        {/* Status Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-zinc-100 mb-2">
            {status === "running" && "Construindo Knowledge Database..."}
            {status === "completed" && "✓ Knowledge Database Construída!"}
            {status === "failed" && "Erro na Importação"}
            {status === "cancelled" && "Importação Cancelada"}
          </h1>

          {status === "running" && (
            <div className="flex items-center gap-4">
              <p className="text-zinc-400">
                Aguarde enquanto processamos seu projeto
              </p>
              {isConnected && (
                <span className="text-xs text-green-500">● Connected</span>
              )}
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-700 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Step Summary */}
        {currentStep > 1 && stepResults[currentStep - 1] && (
          <div className="mb-6">
            <StepSummary stepResult={stepResults[currentStep - 1]} />
          </div>
        )}

        {/* Log Viewer */}
        <LogViewer logs={logs} className="mb-6" />

        {/* Actions */}
        <div className="flex gap-4">
          {status === "running" && (
            <button
              onClick={cancel}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
            >
              Cancelar
            </button>
          )}

          {status === "completed" && (
            <button
              onClick={handleContinue}
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white font-semibold rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              Prosseguir →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
