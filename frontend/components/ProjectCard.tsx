"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/lib/store";
import { translations, type Project } from "@/types";
import { formatDate } from "@/lib/utils";
import {
  FolderOpen,
  Play,
  FileText,
  Trash2,
  AlertCircle,
  CheckCircle,
  Clock,
} from "lucide-react";

interface ProjectCardProps {
  project: Project;
  onStartTest: (projectId: string) => void;
  onViewReport: (projectId: string) => void;
  onDelete: (projectId: string) => void;
}

export function ProjectCard({
  project,
  onStartTest,
  onViewReport,
  onDelete,
}: ProjectCardProps) {
  const { language, currentTest } = useAppStore();
  const t = translations[language];

  const isTestingThis = currentTest.isRunning && currentTest.projectId === project.id;
  const hasReports = project.reports && project.reports.length > 0;

  const getScoreColor = (score: number | undefined) => {
    if (!score) return "text-muted-foreground";
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreIcon = (score: number | undefined) => {
    if (!score) return <Clock className="h-5 w-5 text-muted-foreground" />;
    if (score >= 80) return <CheckCircle className="h-5 w-5 text-green-600" />;
    return <AlertCircle className="h-5 w-5 text-red-600" />;
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">{project.name}</CardTitle>
          </div>
          <Badge variant="secondary">{project.type}</Badge>
        </div>
        <p className="text-sm text-muted-foreground truncate">{project.path}</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="flex items-center justify-center gap-1">
                {getScoreIcon(project.lastScore)}
                <span className={`text-2xl font-bold ${getScoreColor(project.lastScore)}`}>
                  {project.lastScore ?? "-"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{t.score}</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{project.totalIssues ?? "-"}</p>
              <p className="text-xs text-muted-foreground">{t.issues}</p>
            </div>
            <div>
              <p className="text-sm font-medium">
                {project.lastTested ? formatDate(project.lastTested) : "-"}
              </p>
              <p className="text-xs text-muted-foreground">{t.lastTested}</p>
            </div>
          </div>

          {/* Stack tags */}
          {project.stack && project.stack.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {project.stack.map((tech) => (
                <Badge key={tech} variant="outline" className="text-xs">
                  {tech}
                </Badge>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <Button
              className="flex-1"
              onClick={() => onStartTest(project.id)}
              disabled={currentTest.isRunning}
            >
              {isTestingThis ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  {t.testing}
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  {t.startTest}
                </>
              )}
            </Button>
            {hasReports && (
              <Button
                variant="outline"
                onClick={() => onViewReport(project.id)}
              >
                <FileText className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onDelete(project.id)}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
