"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAppStore } from "@/lib/store";
import {
  translations,
  type TestReport,
  type Issue,
  type Severity,
  type IssueCategory,
} from "@/types";
import { formatDate, getSeverityIcon } from "@/lib/utils";
import {
  ArrowLeft,
  Download,
  Filter,
  AlertCircle,
  CheckCircle,
  FileCode,
  ExternalLink,
} from "lucide-react";

interface ReportViewProps {
  report: TestReport;
  onBack: () => void;
}

export function ReportView({ report, onBack }: ReportViewProps) {
  const { language } = useAppStore();
  const t = translations[language];

  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");
  const [categoryFilter, setCategoryFilter] = useState<IssueCategory | "all">("all");

  const filteredIssues = report.issues.filter((issue) => {
    if (severityFilter !== "all" && issue.severity !== severityFilter) return false;
    if (categoryFilter !== "all" && issue.category !== categoryFilter) return false;
    return true;
  });

  const severities: Severity[] = ["critical", "high", "medium", "low", "info"];
  const categories: IssueCategory[] = [
    "functional",
    "security",
    "ui-ux",
    "performance",
    "code-quality",
    "improvement",
  ];

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getSeverityBadgeVariant = (severity: Severity) => {
    return severity as "critical" | "high" | "medium" | "low" | "info";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            {t.back}
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{report.projectName}</h1>
            <p className="text-muted-foreground">
              {formatDate(report.createdAt)}
            </p>
          </div>
        </div>
        <Button variant="outline">
          <Download className="h-4 w-4 mr-2" />
          {t.exportPdf}
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{t.score}</p>
                <p className={`text-3xl font-bold ${getScoreColor(report.score || 0)}`}>
                  {report.score}/100
                </p>
              </div>
              {(report.score || 0) >= 80 ? (
                <CheckCircle className="h-10 w-10 text-green-600" />
              ) : (
                <AlertCircle className="h-10 w-10 text-red-600" />
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">{t.issues}</p>
            <p className="text-3xl font-bold">{report.issues.length}</p>
            <div className="flex gap-1 mt-2">
              {severities.map((sev) => {
                const count = report.statistics?.bySeverity[sev] || 0;
                if (count === 0) return null;
                return (
                  <Badge key={sev} variant={getSeverityBadgeVariant(sev)} className="text-xs">
                    {count}
                  </Badge>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">{t.filesAnalyzed}</p>
            <p className="text-3xl font-bold">{report.filesAnalyzed || "-"}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">{t.linesAnalyzed}</p>
            <p className="text-3xl font-bold">
              {report.linesAnalyzed?.toLocaleString() || "-"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Executive Summary */}
      {report.summary && (
        <Card>
          <CardHeader>
            <CardTitle>{t.executiveSummary}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground whitespace-pre-wrap">
              {report.summary}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Issues */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{t.issues}</CardTitle>
            <div className="flex gap-2">
              <Select
                value={severityFilter}
                onValueChange={(v) => setSeverityFilter(v as Severity | "all")}
              >
                <SelectTrigger className="w-[140px]">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.all}</SelectItem>
                  {severities.map((sev) => (
                    <SelectItem key={sev} value={sev}>
                      {getSeverityIcon(sev)} {t[sev]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={categoryFilter}
                onValueChange={(v) => setCategoryFilter(v as IssueCategory | "all")}
              >
                <SelectTrigger className="w-[160px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.all}</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {t[cat]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredIssues.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              {language === "ro"
                ? "Nu există probleme cu filtrele selectate"
                : "No issues match the selected filters"}
            </p>
          ) : (
            <Accordion type="multiple" className="space-y-2">
              {filteredIssues.map((issue) => (
                <IssueItem key={issue.id} issue={issue} language={language} />
              ))}
            </Accordion>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function IssueItem({ issue, language }: { issue: Issue; language: "ro" | "en" }) {
  const t = translations[language];

  return (
    <AccordionItem value={issue.id} className="border rounded-lg px-4">
      <AccordionTrigger className="hover:no-underline">
        <div className="flex items-center gap-3 text-left">
          <span className="text-lg">{getSeverityIcon(issue.severity)}</span>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Badge variant={issue.severity as "critical" | "high" | "medium" | "low" | "info"}>
                {t[issue.severity]}
              </Badge>
              <Badge variant="outline">{t[issue.category]}</Badge>
              <span className="text-xs text-muted-foreground">{issue.id}</span>
            </div>
            <p className="font-medium mt-1">{issue.title}</p>
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="space-y-4 pt-4">
        {/* Location */}
        {issue.file && (
          <div className="flex items-center gap-2 text-sm">
            <FileCode className="h-4 w-4" />
            <code className="bg-muted px-2 py-1 rounded">
              {issue.file}
              {issue.line && `:${issue.line}`}
              {issue.lineEnd && `-${issue.lineEnd}`}
            </code>
          </div>
        )}

        {/* Description */}
        <div>
          <h4 className="font-medium mb-1">{t.description}</h4>
          <p className="text-muted-foreground">{issue.description}</p>
        </div>

        {/* Steps to Reproduce */}
        {issue.stepsToReproduce && issue.stepsToReproduce.length > 0 && (
          <div>
            <h4 className="font-medium mb-1">{t.stepsToReproduce}</h4>
            <ol className="list-decimal list-inside text-muted-foreground space-y-1">
              {issue.stepsToReproduce.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </div>
        )}

        {/* Actual vs Expected */}
        {(issue.actualBehavior || issue.expectedBehavior) && (
          <div className="grid grid-cols-2 gap-4">
            {issue.actualBehavior && (
              <div>
                <h4 className="font-medium mb-1 text-red-600">
                  {t.actualBehavior}
                </h4>
                <p className="text-muted-foreground">{issue.actualBehavior}</p>
              </div>
            )}
            {issue.expectedBehavior && (
              <div>
                <h4 className="font-medium mb-1 text-green-600">
                  {t.expectedBehavior}
                </h4>
                <p className="text-muted-foreground">{issue.expectedBehavior}</p>
              </div>
            )}
          </div>
        )}

        {/* Code Snippet */}
        {issue.codeSnippet && (
          <div>
            <h4 className="font-medium mb-1">
              {language === "ro" ? "Cod Problematic" : "Problematic Code"}
            </h4>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
              <code>{issue.codeSnippet}</code>
            </pre>
          </div>
        )}

        {/* Suggested Fix */}
        {issue.suggestedFix && (
          <div>
            <h4 className="font-medium mb-1 text-green-600">{t.suggestedFix}</h4>
            <pre className="bg-green-50 dark:bg-green-950 p-4 rounded-lg overflow-x-auto text-sm border border-green-200 dark:border-green-800">
              <code>{issue.suggestedFix}</code>
            </pre>
          </div>
        )}

        {/* Impact */}
        {issue.impact && (
          <div>
            <h4 className="font-medium mb-1">{t.impact}</h4>
            <div className="grid grid-cols-3 gap-2 text-sm">
              {issue.impact.user && (
                <div className="bg-muted p-2 rounded">
                  <p className="font-medium">User</p>
                  <p className="text-muted-foreground">{issue.impact.user}</p>
                </div>
              )}
              {issue.impact.business && (
                <div className="bg-muted p-2 rounded">
                  <p className="font-medium">Business</p>
                  <p className="text-muted-foreground">{issue.impact.business}</p>
                </div>
              )}
              {issue.impact.technical && (
                <div className="bg-muted p-2 rounded">
                  <p className="font-medium">Technical</p>
                  <p className="text-muted-foreground">{issue.impact.technical}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* References */}
        {issue.references && issue.references.length > 0 && (
          <div>
            <h4 className="font-medium mb-1">{t.references}</h4>
            <ul className="space-y-1">
              {issue.references.map((ref, i) => (
                <li key={i} className="flex items-center gap-1 text-sm">
                  <ExternalLink className="h-3 w-3" />
                  <a
                    href={ref}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    {ref}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}
