"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAppStore } from "@/lib/store";
import { translations, type ProjectType, type Project } from "@/types";

interface AddProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddProjectDialog({ open, onOpenChange }: AddProjectDialogProps) {
  const { language, addProject } = useAppStore();
  const t = translations[language];

  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [type, setType] = useState<ProjectType>("web-fullstack");
  const [stack, setStack] = useState("");

  const projectTypes: { value: ProjectType; label: string }[] = [
    { value: "web-frontend", label: "Web Frontend" },
    { value: "web-fullstack", label: "Web Full Stack" },
    { value: "api", label: "API Only" },
    { value: "mobile", label: "Mobile App" },
    { value: "desktop", label: "Desktop App" },
    { value: "library", label: "Library/Package" },
  ];

  const handleSubmit = () => {
    if (!name || !path) return;

    const project: Project = {
      id: crypto.randomUUID(),
      name,
      path,
      type,
      stack: stack.split(",").map((s) => s.trim()).filter(Boolean),
      reports: [],
    };

    addProject(project);
    onOpenChange(false);
    resetForm();
  };

  const resetForm = () => {
    setName("");
    setPath("");
    setType("web-fullstack");
    setStack("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{t.newProject}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">
              {language === "ro" ? "Nume Proiect" : "Project Name"}
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My App"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">{t.projectPath}</label>
            <Input
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="C:\Projects\my-app"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">{t.projectType}</label>
            <Select value={type} onValueChange={(v) => setType(v as ProjectType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {projectTypes.map((pt) => (
                  <SelectItem key={pt.value} value={pt.value}>
                    {pt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">
              Stack ({language === "ro" ? "separat prin virgulă" : "comma separated"})
            </label>
            <Input
              value={stack}
              onChange={(e) => setStack(e.target.value)}
              placeholder="React, TypeScript, Node.js"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t.cancel}
          </Button>
          <Button onClick={handleSubmit} disabled={!name || !path}>
            {t.save}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
