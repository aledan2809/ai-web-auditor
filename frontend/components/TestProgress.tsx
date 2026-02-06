"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/lib/store";
import { translations } from "@/types";
import { X, Bug, FileSearch, Shield, Code, FileText } from "lucide-react";

export function TestProgress() {
  const { language, currentTest, cancelTest, getProject } = useAppStore();
  const t = translations[language];

  if (!currentTest.isRunning || !currentTest.projectId) return null;

  const project = getProject(currentTest.projectId);
  const progress = currentTest.progress;

  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case "scanning":
        return <FileSearch className="h-5 w-5 animate-pulse" />;
      case "security":
        return <Shield className="h-5 w-5 animate-pulse" />;
      case "code-review":
        return <Code className="h-5 w-5 animate-pulse" />;
      case "report":
        return <FileText className="h-5 w-5 animate-pulse" />;
      default:
        return <Bug className="h-5 w-5 animate-bounce" />;
    }
  };

  return (
    <Card className="border-primary/50 bg-primary/5">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {getPhaseIcon(progress?.phase || "init")}
            {t.testing}
          </CardTitle>
          <Button variant="ghost" size="icon" onClick={cancelTest}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="font-medium">{project?.name}</p>
          <p className="text-sm text-muted-foreground">{project?.path}</p>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>{progress?.phaseDescription}</span>
            <span>{progress?.progress}%</span>
          </div>
          <Progress value={progress?.progress || 0} />
        </div>

        {progress?.currentFile && (
          <p className="text-xs text-muted-foreground truncate">
            {progress.currentFile}
          </p>
        )}

        <div className="flex items-center gap-2 text-sm">
          <Bug className="h-4 w-4 text-destructive" />
          <span>
            {progress?.issuesFound || 0} {t.issues.toLowerCase()}{" "}
            {language === "ro" ? "găsite" : "found"}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
