import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <div className="flex flex-col items-center gap-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight">WXCODE</h1>
        <p className="max-w-md text-lg text-muted-foreground">
          Conversor universal de projetos WinDev/WebDev para stacks modernos
        </p>
      </div>

      <div className="flex gap-4">
        <Button variant="default" asChild>
          <Link href="/dashboard">Dashboard</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="https://github.com/wxk/wxcode" target="_blank" rel="noopener noreferrer">
            Documentação
          </Link>
        </Button>
      </div>

      <footer className="absolute bottom-8 text-sm text-muted-foreground">
        Frontend Setup v0.1.0
      </footer>
    </div>
  );
}
